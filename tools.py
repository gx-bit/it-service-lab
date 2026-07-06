# -*- coding: utf-8 -*-
import os, json, requests
# RAG 工具在实验三会写，这里先预留引用，你暂时不需要管报错
from rag import retrieve

POLICY_K = int(os.getenv("POLICY_K", "2"))

# 微服务地址
TICKET = os.getenv("ORDER_URL", "http://localhost:8001")
DEVICE = os.getenv("PRODUCT_URL", "http://localhost:8002")
NETWORK = os.getenv("LOGISTICS_URL", "http://localhost:8003")

# ---- 工具实现 ----
def query_ticket(ticket_id: str) -> dict:
    try:
        return requests.get(f"{TICKET}/tickets/{ticket_id}", timeout=3).json()
    except Exception as e:
        return {"error": f"工单服务不可用: {e}"}

def check_network_status(device_id: str) -> dict:
    try:
        return requests.get(f"{NETWORK}/status/{device_id}", timeout=3).json()
    except Exception as e:
        return {"error": f"网络服务不可用: {e}"}

def query_device(name: str) -> dict:
    try:
        return requests.get(f"{DEVICE}/devices/{name}", timeout=3).json()
    except Exception as e:
        return {"error": f"设备服务不可用: {e}"}

def resolve_ticket(ticket_id: str) -> dict:
    try:
        return requests.post(f"{TICKET}/tickets/{ticket_id}/resolve", timeout=3).json()
    except Exception as e:
        return {"error": f"工单处理失败: {e}"}

def search_policy(q: str) -> list:
    # 这个函数的代码在实验三 rag.py 编写完毕后会自动生效
    return ["政策检索结果..."]

FUNCS = {
    "query_ticket": query_ticket,
    "check_network_status": check_network_status,
    "query_device": query_device,
    "resolve_ticket": resolve_ticket,
    "search_policy": search_policy
}

# ---- 工具契约 (Agent 识别时用的说明书) ----
TOOLS = [
    {"type": "function", "function": {
        "name": "query_ticket", "description": "根据工单号查询 IT 故障工单详情",
        "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}}},
    {"type": "function", "function": {
        "name": "check_network_status", "description": "检查特定设备的网络连通状态，返回是否可自愈",
        "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}}, "required": ["device_id"]}}},
    {"type": "function", "function": {
        "name": "query_device", "description": "查询 IT 设备详情（含价格、库存、是否在保修期）",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "resolve_ticket", "description": "完成工单处理，将状态置为已解决",
        "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}}},
]