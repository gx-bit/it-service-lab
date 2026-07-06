# -*- coding: utf-8 -*-
"""会话记忆与上下文工程: 滑动窗口 + 摘要压缩 + 长期画像。"""
from llm import chat

class Memory:
    def __init__(self, window=6):
        self.window = window
        self.history = []
        self.summary = ""
        self.profile = {}

    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.window:
            old = self.history[:-self.window]
            self.history = self.history[-self.window:]
            self.summary = self._summarize(old)

    def _summarize(self, msgs):
        text = "\n".join(f"{m['role']}: {m['content']}" for m in msgs)
        prompt = "把以下对话压缩成要点，务必保留工单号、设备名、诉求:\n" + \
                 ((self.summary + "\n") if self.summary else "") + text
        return chat([{"role": "user", "content": prompt}]).content

    def remember(self, key, value):
        self.profile[key] = value

    def build(self, system):
        msgs = [{"role": "system", "content": system}]
        if self.profile:
            msgs.append({"role": "system", "content": "用户画像:" + str(self.profile)})
        if self.summary:
            msgs.append({"role": "system", "content": "历史摘要:" + self.summary})
        return msgs + self.history

    def recall_ticket(self):
        """从记忆中回忆最近提到的工单号。"""
        import re
        for m in reversed(self.history):
            ids = re.findall(r"IT-\d+", m.get("content", ""))
            if ids:
                return ids[-1]
        ids = re.findall(r"IT-\d+", self.summary)
        return ids[-1] if ids else None