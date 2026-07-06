# -*- coding: utf-8 -*-
"""BPMN 处理器: 把 aftersale.bpmn 的节点绑定到真实动作(调微服务 / RAG)。"""
import os
from tools import query_ticket, check_network_status, query_device, resolve_ticket, search_policy

BPMN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flows", "aftersale.bpmn")

def h_query_ticket(ctx):
    t = query_ticket(ctx["ticket_id"])
    ctx["ticket"] = t
    ctx["device_name"] = t.get("device")  # 提取设备名，供后续查询使用
    # 模拟 BPMN 网关需要用到的变量
    ctx["issue_type"] = "network" if "网络" in t.get("issue", "") else ("password" if "密码" in t.get("issue", "") else "device")
    return f"调工单服务 (问题类型={ctx['issue_type']})"

def h_diagnose_network(ctx):
    # 调用网络微服务，检查是否能自愈
    n = check_network_status(ctx["device_name"])
    ctx["network_heal"] = n.get("network_heal", False)  # 网关需要的变量
    return f"调网络监测服务 (可自愈={ctx['network_heal']})"

def h_auto_reset(ctx):
    ctx["result"] = "已触发自动密码重置邮件，请查收。"
    return ctx["result"]

def h_device_check(ctx):
    # 调用设备微服务，获取保修状态
    d = query_device(ctx["device_name"])
    ctx["is_in_warranty"] = (d.get("warranty") == "在保")  # 网关需要的变量
    return f"调设备服务 (保修状态: {'在保' if ctx['is_in_warranty'] else '过保'})"

def h_trigger_recovery(ctx):
    r = resolve_ticket(ctx["ticket_id"])
    ctx["result"] = f"已自动触发网络自愈，工单 {ctx['ticket_id']} 状态: {r.get('status')}"
    return ctx["result"]

def h_human_support(ctx):
    ctx["result"] = "网络无法自动恢复，已转交人工网络组处理。"
    return ctx["result"]

def h_replace_device(ctx):
    r = resolve_ticket(ctx["ticket_id"])
    ctx["result"] = f"设备在保，已触发新设备更换申请，工单 {ctx['ticket_id']} 状态: {r.get('status')}"
    return ctx["result"]

def h_procure_device(ctx):
    ctx["result"] = f"设备过保，已触发新设备采购审批流程(预计需3天)。"
    return ctx["result"]

def h_notify_user(ctx):
    pol = "；".join(search_policy("设备更换" if "设备" in ctx.get("result","") else "网络故障"))
    ctx["final"] = f"工单{ctx['ticket_id']}处理结果: {ctx.get('result','')}。相关政策:{pol}"
    return "已通知用户"

# 处理器注册表（必须与 BPMN 节点配置的 delegateExpression 名字一致）
HANDLERS = {
    "h_query_ticket": h_query_ticket,
    "h_diagnose_network": h_diagnose_network,
    "h_auto_reset": h_auto_reset,
    "h_device_check": h_device_check,
    "h_trigger_recovery": h_trigger_recovery,
    "h_human_support": h_human_support,
    "h_replace_device": h_replace_device,
    "h_procure_device": h_procure_device,
    "h_notify_user": h_notify_user,
}

def run_itservice(ticket_id, user_id="u001"):
    """执行 IT 服务 BPMN 流程，返回 (最终答复, 执行轨迹列表)。"""
    from bpmn_engine import run_bpmn
    trace = []
    ctx = {"ticket_id": ticket_id, "user_id": user_id}
    # 注意：这里需要确保 bpmn_engine.py 在目录下
    run_bpmn(BPMN_FILE, HANDLERS, ctx, log=lambda s: trace.append("[BPMN] " + s))
    return ctx.get("final", "流程处理结束，未生成结果。"), trace

if __name__ == "__main__":
    # 注意：这个脚本需要在微服务全启动状态下运行，才能看到真实效果
    print("\n##### 测试 IT 流程：工单 IT-20260601 #####")
    final, trace = run_itservice("IT-20260601")
    for line in trace:
        print(" ", line)
    print("  最终答复:", final)