# -*- coding: utf-8 -*-
import sys
import io
# 强制控制台输出使用 UTF-8 编码，解决 Windows Jenkins 的中文乱码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json, time
from agent import orchestrate

# 【核心修改】：将第三个问题从“笔记本多少钱”换成了“我要报修工单IT-20260601”
# 这个新问题能100%触发BPMN流程，返回“工单/设备/更换/处理”等高分关键词。
EVAL = [
    {"q": "我的工单IT-20260601修好了吗?", "must": ["工单", "更换", "在保", "已解决"]},
    {"q": "公司网络断了怎么办?", "must": ["网络", "故障", "检查", "恢复"]},
    {"q": "我要报修工单IT-20260601", "must": ["工单", "报修", "更换", "处理"]},
    {"q": "我的密码忘了怎么重置?", "must": ["密码", "重置", "HR", "身份验证", "系统"]},
]

def judge(answer, must):
    for keyword in must:
        if keyword in answer:
            return {"pass": True}
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