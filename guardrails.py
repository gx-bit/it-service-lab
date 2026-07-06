# -*- coding: utf-8 -*-
"""护栏:输入(防注入)、授权(防越权)、输出(PII 脱敏)。"""
import re
from data import TICKETS

INJECTION = ["忽略以上", "忽略之前", "ignore previous", "ignore above", "你现在是", "扮演"]

def input_guard(text):
    low = text.lower()
    if any(k.lower() in low for k in INJECTION):
        return False, "⚠️ 检测到可疑指令(疑似提示注入)，已拦截。"
    return True, ""

def authz_guard(user_id, ticket_id):
    t = TICKETS.get(ticket_id)
    if not t:
        return False, "未找到该工单。"
    if t["user"] != user_id:
        return False, "⚠️ 无权操作该工单(工单不属于当前用户)，已拒绝。"
    return True, ""

def pii_mask(text):
    return re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text or "")