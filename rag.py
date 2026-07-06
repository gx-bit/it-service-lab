# -*- coding: utf-8 -*-
"""
极简但"真实"的 RAG 检索:用 numpy 实现字符级 n-gram 的 TF 向量 + 余弦相似度。
- 零依赖(只用 numpy),离线可跑,适合课堂理解"向量化—检索"的本质。
"""
import numpy as np
from data import IT_POLICIES  # 注意：这里导入的是你 IT 项目里的 IT_POLICIES

def _ngrams(text, n=(1, 2)):
    text = text.replace(" ", "")
    grams = []
    for k in n:
        grams += [text[i:i+k] for i in range(len(text)-k+1)]
    return grams

class VectorStore:
    def __init__(self, docs: dict):
        self.ids = list(docs.keys())
        self.texts = list(docs.values())
        # 建词表
        vocab = {}
        for t in self.texts:
            for g in _ngrams(t):
                vocab.setdefault(g, len(vocab))
        self.vocab = vocab
        # 文档向量矩阵 (n_docs, vocab)
        self.M = np.zeros((len(self.texts), len(vocab)), dtype=np.float32)
        for i, t in enumerate(self.texts):
            for g in _ngrams(t):
                self.M[i, vocab[g]] += 1.0
        self._norm = np.linalg.norm(self.M, axis=1) + 1e-8

    def _vectorize(self, q):
        v = np.zeros(len(self.vocab), dtype=np.float32)
        for g in _ngrams(q):
            if g in self.vocab:
                v[self.vocab[g]] += 1.0
        return v

    def search(self, query, k=2):
        v = self._vectorize(query)
        sims = (self.M @ v) / (self._norm * (np.linalg.norm(v) + 1e-8))
        order = np.argsort(-sims)[:k]
        return [(self.ids[i], self.texts[i], float(sims[i])) for i in order if sims[i] > 0]

# 全局知识库(用 IT 政策原料构建)
KB = VectorStore(IT_POLICIES)

def retrieve(query, k=2):
    """返回最相关的 k 段政策文本(纯文本列表),供 Agent 拼入提示。"""
    return [t for _id, t, s in KB.search(query, k)]

def retrieve_scored(query, k=3):
    """返回 (标题, 文本, 相似度),用于演示检索排序。"""
    return KB.search(query, k)

if __name__ == "__main__":
    for q in ["公司网络断了怎么办", "电脑蓝屏怎么换新", "怎么重置密码"]:
        print(f"\n问: {q}")
        for _id, txt, s in retrieve_scored(q, 2):
            print(f"  [{s:.3f}] {_id}: {txt[:15]}...")