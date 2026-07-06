# -*- coding: utf-8 -*-
import time, json, io, contextlib
from guardrails import input_guard, pii_mask
from agent import orchestrate
from memory import Memory

def serve_struct(user_id, text, memory=None):
    t0 = time.time()
    ok, msg = input_guard(text)
    if not ok:
        return {"reply": msg, "intent": "BLOCKED", "trace": "[输入护栏] 命中提示注入，已拦截", "latency": 0.0}
    
    if memory: memory.add("user", text)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = orchestrate(text, memory=memory, verbose=True)
    
    answer = pii_mask(result["answer"])
    if memory: memory.add("assistant", answer)
    
    return {"reply": answer, "intent": result["intent"], "trace": buf.getvalue().strip() or "(无工具调用)", "latency": round(time.time() - t0, 3)}