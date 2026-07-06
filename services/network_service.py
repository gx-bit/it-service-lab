# -*- coding: utf-8 -*-
import json, sys, os, re
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import DEVICES

PORT = 8003

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

    def do_GET(self):
        # 检查设备网络状态
        m = re.match(r"/status/(\w+)$", self.path)
        if m:
            device_id = m.group(1)
            # 模拟数据：写死为判断某款设备是否在线（这里根据 BPMN，我们返回是否能自动自愈的变量 network_heal）
            is_online = True if device_id == "办公笔记本" else False
            return self._send(200, {"device_id": device_id, "is_online": is_online, "network_heal": is_online})
        self._send(404, {"error": "未知路径"})

if __name__ == "__main__":
    print(f"[network-service] 启动于 http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()