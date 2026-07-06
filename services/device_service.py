# -*- coding: utf-8 -*-
import json, sys, os, re, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import DEVICES

PORT = 8002

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
        # 查询设备信息（含保修状态）
        m = re.match(r"/devices/(.+)$", self.path)
        if m:
            name = urllib.parse.unquote(m.group(1))
            d = DEVICES.get(name)
            if not d:
                return self._send(404, {"error": "设备不存在"})
            return self._send(200, d)
        self._send(404, {"error": "未知路径"})

if __name__ == "__main__":
    print(f"[device-service] 启动于 http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()