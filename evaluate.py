# -*- coding: utf-8 -*-
import json, time
from llm import chat
from agent import orchestrate

EVAL = [
    {"q": "我的工单IT-20260601修好了吗?", "must": ["更换", "在保"]},
    {"q": "公司网络断了怎么办?", "must": ["本地局域网", "备份线路"]},
    {"q": "笔记本多少钱?", "must": ["8000"]},
    {"q": "我的密码忘了怎么重置?", "must": ["HR", "身份验证"]},
]

def judge(answer, must):
    prompt = f'判断回答是否覆盖了所有要点。要点:{must}\n回答:{answer}\n只输出 JSON: {{"pass": true/false}}'
    try:
        return json.loads(chat([{"role": "user", "content": prompt}], temperature=0, response_format={"type": "json_object"}).content)
    except Exception:
        return {"pass": False}

def run_eval(verbose=True):
    passed, rows = 0, []
    for c in EVAL:
        t0 = time.time()
        ans = orchestrate(c["q"], verbose=False)["answer"]
        r = judge(ans, c["must"])
        ok = bool(r.get("pass"))
        passed += ok
        rows.append((c["q"], ok, round(time.time()-t0, 3), ans))
        if verbose:
            print(f"[{'PASS' if ok else 'FAIL'}] {c['q']}")
            print(f"        答:{ans[:70]}")
    print(f"\n==== 通过率: {passed}/{len(EVAL)} = {passed/len(EVAL)*100:.0f}% ====")
    return rows

if __name__ == "__main__":
    run_eval()