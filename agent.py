# -*- coding: utf-8 -*-
import json, re
from llm import client, chat, CHAT_MODEL
from tools import TOOLS, FUNCS
from rag import retrieve

# ---------- 实验3: 多 Agent 路由 + 专家 ----------
def router(text):
    """路由 Agent: 判断 IT 诉求类别。"""
    return chat([{"role": "system", "content": "判断用户意图,只回一个词:网络故障/设备咨询/密码问题/其他"},
                 {"role": "user", "content": text}], temperature=0).content.strip()

def expert_network(text, ctx=None, verbose=False):
    return "【网络专家】" + react_agent(text, verbose=verbose, extra_msgs=ctx)

def expert_password(text, ctx=None, verbose=False):
    return "【密码专家】" + react_agent(text, verbose=verbose, extra_msgs=ctx)

def expert_device(text, ctx=None, verbose=False):
    # 设备专家: 若带工单号，触发 BPMN 流程
    tickets = re.findall(r"IT-\d+", text)
    if tickets:
        from bpmn_handlers import run_itservice
        final, trace = run_itservice(tickets[0])
        if verbose:
            for line in trace:
                print("  " + line)
        return "【设备专家·BPMN流程】" + final
    return "【设备专家】" + react_agent(text, verbose=verbose, extra_msgs=ctx)

def expert_other(text, ctx=None, verbose=False):
    return "【通用助手】" + react_agent(text, verbose=verbose, extra_msgs=ctx)

EXPERTS = {"网络故障": expert_network, "设备咨询": expert_device, "密码问题": expert_password, "其他": expert_other}

def orchestrate(text, memory=None, verbose=True):
    ctx = None
    if memory is not None:
        ctx = memory.build("")[1:]
    intent = router(text)
    if verbose:
        print(f"  [路由] 判定意图 = {intent}")
    expert = EXPERTS.get(intent, expert_other)
    answer = expert(text, ctx, verbose)
    return {"intent": intent, "answer": answer}

# ---------- 遗留 ReAct (供专家内部调用) ----------
PLAN_SYSTEM = """你是企业IT智能助理。面对复杂问题:先拆成多个步骤,每次只调用一个最必要的工具;信息齐全后再综合回答。"""
def react_agent(user_text, max_steps=6, verbose=True, extra_msgs=None):
    msgs = [{"role": "system", "content": PLAN_SYSTEM}]
    if extra_msgs: msgs += extra_msgs
    msgs.append({"role": "user", "content": user_text})
    for step in range(1, max_steps + 1):
        m = client.chat.completions.create(model=CHAT_MODEL, messages=msgs, tools=TOOLS).choices[0].message
        msgs.append(m.model_dump() if hasattr(m, "model_dump") else m)
        if not m.tool_calls:
            if verbose: print(f"  [第{step}步] 思考→信息已齐全,生成最终答复")
            return m.content
        for tc in m.tool_calls:
            args = json.loads(tc.function.arguments)
            obs = FUNCS[tc.function.name](**args)
            if verbose:
                print(f"  [第{step}步] 行动→调用 {tc.function.name}({args})")
                print(f"           观察← {json.dumps(obs, ensure_ascii=False)[:80]}")
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(obs, ensure_ascii=False)})
    return "(已达最大步数,请缩小问题范围)"