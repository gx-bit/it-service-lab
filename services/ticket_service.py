# -*- coding: utf-8 -*-
import json, sys, os, re
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import TICKETS

PORT = 8001

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
        # 修正正则表达式，允许匹配连字符 -
        m = re.match(r"/tickets/([a-zA-Z0-9\-_]+)$", self.path)
        if m:
            t = TICKETS.get(m.group(1))
            return self._send(200, t) if t else self._send(404, {"error": "工单不存在"})
        self._send(404, {"error": "未知路径"})

    def do_POST(self):
        m = re.match(r"/tickets/([a-zA-Z0-9\-_]+)/resolve$", self.path)
        if m:
            t = TICKETS.get(m.group(1))
            if not t:
                return self._send(404, {"error": "工单不存在"})
            t["status"] = "已解决"
            return self._send(200, {"ticket_id": m.group(1), "status": "已解决", "msg": "工单已处理完毕。"})
        self._send(404, {"error": "未知路径"})

if __name__ == "__main__":
    print(f"[ticket-service] 启动于 http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()