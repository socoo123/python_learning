"""
Ch31 作业:RAG 实战(向量检索)。

RAG = Retrieval-Augmented Generation:让 LLM 基于【你的文档】回答。
管道:文档切片 → 向量化(embedding)→ 存向量库 → 用问句检索 top-k → 拼成上下文 → 喂 LLM。

设计要点:本作业【不用真实 embedding 模型】(那要 torch/sentence-transformers,很重)。
用纯 Python 实现 RAG 的核心数学:切片、余弦相似度、top-k 检索。embedding 用一个
确定性的 hash_embed(假向量)替代,理解原理即可。真实场景把 hash_embed 换成真模型。

5 个函数,纯 Python。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v

全绿 = 你掌握了 Ch31。
"""
import hashlib
import math


# ========== §31.2 切片:chunk_text ==========


def chunk_text(text: str, size: int = 100, overlap: int = 20) -> list[str]:
    """
    【切片 · §31.2】把长文本按 size 字符切片,相邻片之间重叠 overlap 字符(保上下文连贯)。

    示例:
        chunk_text("abcdef", size=3, overlap=1)  -> ["abc", "cde", "ef"]   # step=2
        chunk_text("abcdef", size=3, overlap=0)  -> ["abc", "def"]
        chunk_text("", size=5)                   -> []

    思路(滑动窗口,step = size - overlap):
        if size <= 0: return []
        step = max(1, size - overlap)
        return [text[i:i+size] for i in range(0, len(text), step)]
    """
    # TODO: step=size-overlap;滑动窗口切片
    ...


# ========== §31.3 余弦相似度:cosine_similarity ==========


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    【相似度 · §31.3】两个向量的余弦相似度:cosθ = a·b / (|a||b|)。
    值域 [-1, 1]:1=同向(最相似),0=正交(无关),-1=反向。RAG 用它排相似度。

    示例:
        cosine_similarity([1,0], [1,0])   -> 1.0
        cosine_similarity([1,0], [0,1])   -> 0.0
        cosine_similarity([1,0], [-1,0])  -> -1.0
        cosine_similarity([0,0], [1,1])   -> 0.0   # 零向量防除零

    思路:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot / (na * nb) if na and nb else 0.0
    """
    # TODO: 点积 / (模*模),零向量返回 0.0
    ...


# ========== §31.4 top-k 检索:retrieve_top_k ==========


def retrieve_top_k(
    query_vec: list[float],
    doc_vecs: list[tuple[str, list[float]]],
    k: int = 3,
) -> list[str]:
    """
    【检索 · §31.4】从 (文本, 向量) 列表里,按与 query_vec 的相似度降序取前 k 个文本。
    doc_vecs = [("苹果", [1,0]), ...]。

    示例:
        docs = [("苹果",[1,0]), ("香蕉",[0,1]), ("梨",[1,1])]
        retrieve_top_k([1,0], docs, k=2)  -> ["苹果", "梨"]   # 苹果1.0 > 梨0.707 > 香蕉0

    思路(算相似度 → 排序 → 取前 k 的文本):
        scored = [(cosine_similarity(query_vec, v), t) for t, v in doc_vecs]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:k]]
    """
    # TODO: 算每个 doc 的相似度,降序取前 k 个文本
    ...


# ========== §31.5 拼上下文:build_context ==========


def build_context(chunks: list[str], sep: str = "\n\n") -> str:
    """
    【上下文 · §31.5】把检索到的若干片段拼成一个上下文字符串,塞进 prompt。
    通常加分隔符让 LLM 知道是不同片段。

    示例:
        build_context(["片段A", "片段B"]) -> "片段A\\n\\n片段B"
        build_context([])                 -> ""

    思路:
        return sep.join(chunks)
    """
    # TODO: sep.join(chunks)
    ...


# ========== §31.6 假 embedding:hash_embed ==========


def hash_embed(text: str, dim: int = 16) -> list[float]:
    """
    【embedding · §31.6】【确定性假向量】——为相同文本生成相同的 dim 维向量(用 hash)。
    仅用于离线测试 RAG 流程;真实场景换成 sentence-transformers / OpenAI embedding。

    示例:
        hash_embed("苹果")          -> 16 维 list[float]
        hash_embed("苹果") == hash_embed("苹果")   # 确定性
        hash_embed("苹果") != hash_embed("香蕉")   # 不同文本不同向量
        len(hash_embed("x", dim=8)) == 8

    思路(每维用 md5(text:i) 取一个字节,映射到 -1..1):
        vec = []
        for i in range(dim):
            b = hashlib.md5(f"{text}:{i}".encode()).digest()[0]
            vec.append((b - 127) / 127.0)
        return vec
    """
    # TODO: 循环 dim,每维 md5(text:i) 取字节映射 -1..1
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(chunk_text("abcdef", size=3, overlap=1))
    print(cosine_similarity([1, 0], [1, 1]))
    docs = [("苹果", hash_embed("苹果")), ("香蕉", hash_embed("香蕉"))]
    print(retrieve_top_k(hash_embed("苹果"), docs, k=1))
