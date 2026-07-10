# -*- coding: utf-8 -*-
import requests
import time
import json

SERVICES = [
    {"name": "工单微服务", "url": "http://localhost:8001/tickets/IT-20260601"},
    {"name": "设备微服务", "url": "http://localhost:8002/devices/办公笔记本"},
    {"name": "网络微服务", "url": "http://localhost:8003/status/办公笔记本"},
    {"name": "Web服务入口", "url": "http://localhost:8000/"}
]

def check_health():
    print("=" * 60)
    print("  企业IT服务台 - 服务质量(SLA)监控报告")
    print("=" * 60)
    print(f"{'服务名称':<15} | {'状态':<8} | {'响应时间(ms)':<15}")
    print("-" * 60)

    report = {"total": 0, "up": 0, "down": 0, "latencies": []}

    for svc in SERVICES:
        start = time.time()
        try:
            # 设置2秒超时，检测健壮性
            r = requests.get(svc["url"], timeout=2)
            status = "🟢 正常"
            report["up"] += 1
        except Exception as e:
            status = "🔴 不可用"
            report["down"] += 1
        
        elapsed = round((time.time() - start) * 1000, 2) # 毫秒
        report["total"] += 1
        report["latencies"].append(elapsed)
        
        print(f"{svc['name']:<15} | {status:<8} | {elapsed:<15}")

    print("-" * 60)
    availability = (report["up"] / report["total"]) * 100
    avg_latency = sum(report["latencies"]) / len(report["latencies"])
    
    print(f"\n📊 核心指标汇总:")
    print(f"  • 可用性 (Availability): {availability}% (存活 {report['up']}/{report['total']})")
    print(f"  • 平均响应时间 (Avg Latency): {avg_latency} ms")
    print(f"  • 健壮性 (Robustness): 超时阈值设为 2 秒，异常已捕获处理")
    print("=" * 60)

if __name__ == "__main__":
    check_health()