# -*- coding: utf-8 -*-
"""
统一的大模型客户端。

设计要点(重要):
- 对外暴露与 OpenAI 完全一致的接口:client.chat.completions.create(model, messages, tools, ...)
  返回对象 .choices[0].message,message 有 .content 与 .tool_calls。
- 若环境变量里配置了 OPENAI_API_KEY,则使用真实的 OpenAI 兼容大模型(openai SDK)。
- 否则回退到 MockLLM —— 一个确定性的"教学桩",用规则模拟大模型的"意图判断/工具选择/
  生成回复",让整套系统在【无密钥、无网络】的情况下也能完整跑通、输出可复现。
  学生在自己电脑上 `export OPENAI_API_KEY=...` 后,同一套代码即调用真实模型,无需改动。

这正是工程上的"接口隔离":上层 Agent/编排逻辑只依赖接口,不关心背后是真模型还是桩。
"""
import os, re, json, uuid

def _load_dotenv():
    """无依赖加载同目录下的 .env(每行 KEY=VALUE),已存在的环境变量不覆盖。
    这就是配置大模型 API Key 的地方:把 .env.example 复制成 .env 并填入 key。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v:                       # 空值不设置,避免空字符串误判为"已配置"
            os.environ.setdefault(k.strip(), v)

_load_dotenv()

CHAT_MODEL = os.getenv("CHAT_MODEL", "mock-llm")

# ----------------------------------------------------------------------
# 模拟 OpenAI 返回对象的最小数据结构
# ----------------------------------------------------------------------
class _Fn:
    def __init__(self, name, arguments): self.name = name; self.arguments = arguments
class _ToolCall:
    def __init__(self, name, args):
        self.id = "call_" + uuid.uuid4().hex[:8]; self.type = "function"
        self.function = _Fn(name, json.dumps(args, ensure_ascii=False))
class _Msg:
    def __init__(self, content=None, tool_calls=None, role="assistant"):
        self.content = content; self.tool_calls = tool_calls or None; self.role = role
    def model_dump(self):
        d = {"role": self.role, "content": self.content or ""}
        if self.tool_calls:
            d["tool_calls"] = [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name,
                                             "arguments": tc.function.arguments}}
                               for tc in self.tool_calls]
        return d
class _Choice:
    def __init__(self, m): self.message = m
class _Resp:
    def __init__(self, m): self.choices = [_Choice(m)]


def _norm(messages):
    """把 messages 里可能混入的对象统一成 dict,便于桩解析。"""
    out = []
    for m in messages:
        if isinstance(m, dict): out.append(m)
        elif hasattr(m, "model_dump"): out.append(m.model_dump())
        else: out.append({"role": getattr(m, "role", "assistant"),
                          "content": getattr(m, "content", "")})
    return out


# ----------------------------------------------------------------------
# MockLLM:确定性教学桩
# ----------------------------------------------------------------------
class _MockCompletions:
    def create(self, model=None, messages=None, tools=None,
               temperature=0, response_format=None, **kw):
        msgs = _norm(messages)
        sys_txt = " ".join(m.get("content", "") or "" for m in msgs if m.get("role") == "system")
        user_txt = " ".join(m.get("content", "") or "" for m in msgs if m.get("role") == "user")

        # 1) 路由:system 要求"只回一个词"
        if "只回一个词" in sys_txt or "只回复一个词" in sys_txt:
            return _Resp(_Msg(content=self._route(user_txt)))

        # 2) 摘要压缩:system/user 要求"压缩成要点"
        if "压缩成要点" in sys_txt + user_txt or "压缩成" in user_txt:
            return _Resp(_Msg(content=self._summarize(user_txt)))

        # 3) 评测打分:judge,要求输出 {"pass": ...}
        if response_format and '"pass"' in (sys_txt + user_txt):
            return _Resp(_Msg(content=self._judge(user_txt)))

        # 4) 意图识别:要求输出 {"intent": ...}
        if response_format and ("意图" in sys_txt or '"intent"' in sys_txt):
            return _Resp(_Msg(content=self._intent(user_txt)))

        # 5) 工具调用 / ReAct:提供了 tools。决策以"当前(最后一条)用户消息"为准,
        #    历史仅作背景,避免把上一轮诉求误带入本轮。
        if tools:
            last_user = next((m.get("content", "") for m in reversed(msgs)
                              if m.get("role") == "user"), user_txt)
            return self._tool_step(msgs, tools, last_user)

        # 6) 兜底:普通生成
        return _Resp(_Msg(content=self._final_answer(msgs, user_txt)))

    # ---- 子能力 ----
    def _route(self, t):
        # 【修改为 IT 服务台专属规则】
        if re.search(r"工单|IT-|报修|电脑|笔记本|键盘|鼠标|设备|蓝屏|换新", t): return "设备咨询"
        if re.search(r"网络|断网|交换机|外网|网线|不能上网", t): return "网络故障"
        if re.search(r"密码|账号|登录|重置", t): return "密码问题"
        return "其他"

    def _summarize(self, t):
        # 【修改为 IT 服务台专属摘要提取】
        ticket = "、".join(set(re.findall(r"IT-\d+", t)))
        kw = [k for k in ["工单", "网络", "设备", "密码", "重置", "故障", "报修"] if k in t]
        parts = []
        if ticket: parts.append(f"涉及工单 {ticket}")
        if kw: parts.append("诉求关键词:" + "/".join(kw))
        return ";".join(parts) if parts else "用户进行了若干轮IT咨询。"

    def _judge(self, t):
        # 从 "要点:[...]" 与 "回答:..." 中判断要点是否被覆盖
        m_must = re.search(r"要点[:：]\s*(\[[^\]]*\])", t)
        m_ans = re.search(r"回答[:：]\s*(.+)", t, re.S)
        must, ans = [], ""
        if m_must:
            try: must = json.loads(m_must.group(1).replace("'", '"'))
            except Exception: must = re.findall(r"[\"']([^\"']+)[\"']", m_must.group(1))
        if m_ans: ans = m_ans.group(1)
        ok = all(str(x) in ans for x in must) if must else True
        return json.dumps({"pass": bool(ok)}, ensure_ascii=False)

    def _intent(self, t):
        # 【修改为 IT 服务台专属意图识别】
        if re.search(r"网络|断网|交换机|外网|网线|不能上网", t): intent = "网络故障"
        elif re.search(r"密码|账号|登录|重置", t): intent = "密码问题"
        elif re.search(r"工单|IT-|报修|电脑|笔记本|键盘|鼠标|设备|蓝屏", t): intent = "设备咨询"
        else: intent = "其他"
        
        ent = {}
        ticket = re.findall(r"IT-\d+", t)
        if ticket: ent["ticket_id"] = ticket[0]
        # 检查你 data.py 里的设备名
        for p in ["办公笔记本", "网络交换机", "服务器"]:
            if p in t: ent["device"] = p
        return json.dumps({"intent": intent, "entities": ent}, ensure_ascii=False)

    def _called_tools(self, msgs):
        names = []
        for m in msgs:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                names += [tc["function"]["name"] for tc in m["tool_calls"]]
        return names

    def _observations(self, msgs):
        obs = []
        for m in msgs:
            if m.get("role") == "tool":
                try: obs.append(json.loads(m["content"]))
                except Exception: obs.append(m["content"])
        return obs

    def _tool_step(self, msgs, tools, user_txt):
        """ReAct 决策:已有观察则决定下一步,信息齐全则给最终答案。"""
        avail = {t["function"]["name"] for t in tools}
        called = self._called_tools(msgs)
        ticket_list = re.findall(r"IT-\d+", user_txt)
        ticket_id = ticket_list[0] if ticket_list else None
        
        # 【修改为 IT 服务台专属决策意图】
        wants_status = bool(re.search(r"工单|IT-|状态|查一下|报修|设备|故障", user_txt))
        wants_policy = bool(re.search(r"政策|手册|规定|如何|怎么办|怎么处理", user_txt))
        wants_device = bool(re.search(r"多少钱|价格|库存|有没有|设备|电脑|笔记本|换新", user_txt))

        # 第一步:查工单/状态
        if ticket_id and wants_status and "query_ticket" in avail and "query_ticket" not in called:
            return _Resp(_Msg(tool_calls=[_ToolCall("query_ticket", {"ticket_id": ticket_id})]))
        
        # 第二步:查政策 (RAG)
        if wants_policy and "search_policy" in avail and "search_policy" not in called:
            return _Resp(_Msg(tool_calls=[_ToolCall("search_policy", {"q": user_txt})]))
            
        # 第三步:查设备/库存
        if wants_device and "query_device" in avail and "query_device" not in called:
            device = next((p for p in ["办公笔记本", "网络交换机", "服务器"] if p in user_txt), "办公笔记本")
            return _Resp(_Msg(tool_calls=[_ToolCall("query_device", {"name": device})]))
            
        # 信息齐全 → 终态回复
        return _Resp(_Msg(content=self._final_answer(msgs, user_txt)))

    def _final_answer(self, msgs, user_txt):
        obs = self._observations(msgs)
        ticket = next((o for o in obs if isinstance(o, dict) and "status" in o), None)
        policy = next((o for o in obs if isinstance(o, list)), None)
        device = next((o for o in obs if isinstance(o, dict) and "price" in o and "status" not in o), None)
        
        parts = []
        
        # 【修改为 IT 专属回复结构】
        if ticket and "error" not in ticket:
            seg = f"您查询的工单 {ticket.get('ticket_id','')} 当前状态: {ticket.get('status')}"
            if ticket.get("device"): seg += f", 涉及设备: {ticket.get('device')}"
            parts.append(seg + "。")
            
        if policy:
            parts.append("参考政策:" + "；".join(policy))
            
        if device and "error" not in device:
            parts.append(f"设备 {device['name']} 参考价格: {device['price']}元, 库存: {device['stock']}件, 保修状态: {device['warranty']}。")
            
        if any(isinstance(o, dict) and o.get("error") for o in obs):
            parts.append("抱歉,未能查询到对应信息,请核对工单号或设备名后重试。")
            
        if not parts:
            parts.append("您好,我是企业IT服务助理,可以帮您查询工单状态、报修设备、解决网络故障或重置密码,请问需要什么帮助?")
        return "".join(parts)


class _MockChat:
    def __init__(self): self.completions = _MockCompletions()
class MockLLM:
    def __init__(self): self.chat = _MockChat()


# ----------------------------------------------------------------------
# 对外:client + chat() 便捷函数(真实/桩 自动切换)
# ----------------------------------------------------------------------
if os.getenv("OPENAI_API_KEY"):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"))
    BACKEND = "real:" + CHAT_MODEL
else:
    client = MockLLM()
    BACKEND = "mock-llm(教学桩,离线可复现)"


def chat(messages, **kw):
    """无工具的便捷调用,返回 message 对象。"""
    return client.chat.completions.create(model=CHAT_MODEL, messages=messages, **kw).choices[0].message


if __name__ == "__main__":
    print("当前后端:", BACKEND)
    print(chat([{"role": "user", "content": "你好"}]).content)