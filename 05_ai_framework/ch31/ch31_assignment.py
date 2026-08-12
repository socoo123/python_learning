"""
Ch31 作业:RAG 实战(向量检索)。

主线场景(极客商城知识库问答):Ch30 的客服机器人没看过商品手册和售后政策,被吐槽
「一问三不知」。你要给它装上 RAG——把《商品知识库》切片、向量化建索引,用户提问时
检索 top-k 相关片段,拼进 prompt 让 LLM「开卷考试」,并把答案来源一起返回(可溯源)。

设计要点:本作业【不装真实 embedding 模型】(sentence-transformers 带 torch 约 2GB),
【不调真实 LLM】。embedding 用确定性的 hash_embed(假向量)替代、llm 用注入的
callable 充当——理解管道原理;上线时把这两处换成真模型即可,管道其余代码一行不动
(tutorial §31.10)。

8 个函数,按「切 → 嵌 → 检 → 拼 → 答」管道递进,最后两题是复用前面函数的综合。
在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v

全绿 = 你掌握了 Ch31。

每题 docstring 的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import hashlib
import math
from collections.abc import Callable

# RAG prompt 模板:{context} 是 build_context 拼好的带编号资料,{question} 是用户问题。
# 注意写死了「只基于资料,没有就说不知道」——不加约束,模型对资料外的问题会瞎编(幻觉)。
RAG_TEMPLATE = (
    "你是极客商城的客服,只基于下面的资料回答用户问题;资料里没有的信息,就说「不知道」。\n\n"
    "{context}\n\n"
    "用户问题:{question}\n"
    "客服回答:"
)


# ========== §31.2 文档切片:chunk_text ==========


def chunk_text(text: str, size: int = 100, overlap: int = 20) -> list[str]:
    """
    【切片 · §31.2】把长文本按 size 字符切片,相邻片重叠 overlap 字符(保上下文连贯,
    防止一句话从正中间切断后两片都丢了完整语义)。size <= 0 时返回 []。

    示例:
        chunk_text("abcdef", size=3, overlap=1)  -> ["abc", "cde", "ef"]   # step=2
        chunk_text("abcdef", size=3, overlap=0)  -> ["abc", "def"]         # step=3
        chunk_text("abc", size=10, overlap=2)    -> ["abc"]                # 文本不足一片
        chunk_text("", size=5)                   -> []
        chunk_text("abcdef", size=2, overlap=5)  -> ["ab", "bc", "cd", "de", "ef", "f"]

    提示(滑动窗口,步长 step = size - overlap):
        step 必须 max(1, size - overlap)——overlap >= size 时步长 <= 0,range 会炸。
        [text[i:i+size] for i in range(0, len(text), step)]
    """
    # TODO: size<=0 返回 [];step=max(1, size-overlap);滑动窗口切片
    ...


# ========== §31.3 余弦相似度:cosine_similarity ==========


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    【相似度 · §31.3】两个向量的余弦相似度:cosθ = a·b / (|a||b|)。
    值域 [-1, 1]:1=同向(最相似),0=正交(无关),-1=反向。
    文本向量关心方向(语义)不关心长度(词数),所以 RAG 用余弦不用欧氏距离。
    零向量没有方向,约定与任何向量相似度为 0.0(防除零)。

    示例:
        cosine_similarity([1, 0], [1, 0])    -> 1.0
        cosine_similarity([1, 0], [0, 1])    -> 0.0
        cosine_similarity([1, 0], [-1, 0])   -> -1.0
        cosine_similarity([3, 4], [4, 3])    -> 0.96      # 点积 24,模长 5×5
        cosine_similarity([1, 2], [2, 4])    -> 1.0       # 同向不同长,余弦仍满分
        cosine_similarity([0, 0], [1, 1])    -> 0.0       # 零向量防除零

    提示(数学公式直接翻译成代码):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a));nb 同理
        return dot / (na * nb) if na and nb else 0.0
    """
    # TODO: 点积 / (模×模),零向量返回 0.0
    ...


# ========== §31.4 假 embedding:hash_embed ==========


def hash_embed(text: str, dim: int = 16) -> list[float]:
    """
    【embedding · §31.4】【确定性假向量】把文本映射成 dim 维向量,值域 [-1.0, 1.0]。
    相同文本 → 相同向量(确定性,测试可复现);但【不表达语义】(md5 是伪随机映射,
    语义接近 ≠ 向量接近)。仅用于离线跑通 RAG 流程;真实场景换 sentence-transformers /
    OpenAI embedding,管道其余代码不动。

    示例:
        len(hash_embed("苹果")) == 16                    # 默认 16 维
        len(hash_embed("x", dim=8)) == 8                 # 维度可控
        hash_embed("苹果") == hash_embed("苹果")          # 确定性
        hash_embed("苹果") != hash_embed("香蕉")          # 不同文本不同向量
        all(-1.0 <= v <= 1.0 for v in hash_embed("x"))   # 值域 [-1, 1]

    提示(每维换一种子的 md5,取首字节映射):
        for i in range(dim):
            b = hashlib.md5(f"{text}:{i}".encode()).digest()[0]   # 0~255
            vec.append((b - 127.5) / 127.5)                        # → [-1.0, 1.0]
    """
    # TODO: 循环 range(dim),每维 md5(f"{text}:{i}") 取首字节,(b-127.5)/127.5
    ...


# ========== §31.5 top-k 检索:retrieve_top_k ==========


def retrieve_top_k(
    query_vec: list[float],
    doc_vecs: list[tuple[str, list[float]]],
    k: int = 3,
) -> list[tuple[str, float]]:
    """
    【检索 · §31.5】向量库 doc_vecs = [(文本, 向量), ...],按与 query_vec 的余弦相似度
    【降序】取前 k 片,【连分数一起返回】[(文本, 分数), ...](调试/阈值/展示相关度要用)。
    空库返回 [];k 超过库存量就全返回;同分保持原先后顺序(sort 是稳定排序)。

    示例:
        docs = [("苹果", [1, 0]), ("香蕉", [0, 1]), ("梨", [1, 1])]
        retrieve_top_k([1, 0], docs, k=2)
            -> [("苹果", 1.0), ("梨", 0.7071...)]   # 苹果 1.0 > 梨 1/√2 ≈ 0.707 > 香蕉 0.0
        retrieve_top_k([1, 0], [], k=3)  -> []

    提示(元组排序陷阱——不带 key 会按文本字典序排!):
        scored = [(t, cosine_similarity(query_vec, v)) for t, v in doc_vecs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
    """
    # TODO: 算每片相似度 → 按分数降序(显式给 key!)→ 取前 k
    ...


# ========== §31.6 拼上下文:build_context ==========


def build_context(chunks: list[str], sep: str = "\n\n") -> str:
    """
    【上下文 · §31.6】把检索到的片段拼成一个上下文字符串塞进 prompt。
    【每片带编号 [资料N]】——LLM 回答时能引用「据[资料2]…」,这就是溯源的载体。
    空列表返回 ""。

    示例:
        build_context(["片段A", "片段B"])  -> "[资料1] 片段A\\n\\n[资料2] 片段B"
        build_context(["a", "b"], sep=" | ")  -> "[资料1] a | [资料2] b"
        build_context([])                   -> ""

    提示:
        sep.join(f"[资料{i}] {c}" for i, c in enumerate(chunks, 1))
        enumerate(chunks, 1) 从 1 开始计数;join 只加在元素【之间】,不用特判空列表。
    """
    # TODO: sep.join + enumerate(chunks, 1) 编号
    ...


# ========== §31.7 RAG prompt:build_rag_prompt ==========


def build_rag_prompt(question: str, context: str, template: str = RAG_TEMPLATE) -> str:
    """
    【prompt · §31.7】把上下文和用户问题填进 RAG 模板,产出喂给 LLM 的最终 prompt。
    模板(默认 RAG_TEMPLATE)里写死了「只基于资料,没有就说不知道」——不加约束,
    模型对资料外的问题会瞎编(幻觉)。

    示例:
        build_rag_prompt("支持退货吗", "[资料1] 《售后政策》:7 天无理由")
        -> "你是极客商城的客服,只基于下面的资料回答用户问题;资料里没有的信息,就说「不知道」。
           \\n\\n[资料1] 《售后政策》:7 天无理由\\n\\n用户问题:支持退货吗\\n客服回答:"
        build_rag_prompt("q", "c", template="资料:{context}/问:{question}")  -> "资料:c/问:q"

    提示:
        template.format(context=context, question=question)   # 按名字填占位符
    """
    # TODO: template.format(context=..., question=...)
    ...


# ========== §31.8 综合① 检索管道:search_knowledge_base ==========


def search_knowledge_base(
    query: str,
    documents: list[str],
    k: int = 3,
    dim: int = 16,
) -> list[tuple[str, float]]:
    """
    【综合① · §31.8】检索管道:文档切片 → 全部片段向量化(建库)→ query 向量化检索 top-k。
    输入原始文档列表,返回命中的 [(片段, 分数), ...](按分数降序)。

    ⚠️ 教学简化:这里【每次查询都重建索引】。生产是「离线建一次索引存向量库,在线只
    embed query」(tutorial §31.10)——本章合并在一个函数里,是为了一次调用看全管道。

    ⚠️ query 和文档片段必须用【同一个 embedding 函数、同一个 dim】——维度不一致时
    zip 会对齐到短的静默算错分数,不报错!

    示例(documents 是知识库,query 恰好等于某篇文档时相似度满分):
        docs = ["《售后政策》:7 天无理由退货", "《手机手册》:5000mAh 电池"]
        top = search_knowledge_base("《售后政策》:7 天无理由退货", docs, k=1)
        top[0][0]  -> "《售后政策》:7 天无理由退货"
        top[0][1]  -> 1.0

    提示:三步全部【复用】前面的函数,别重写:
        chunks = [c for doc in documents for c in chunk_text(doc)]   # 双层 for = flatMap
        doc_vecs = [(c, hash_embed(c, dim=dim)) for c in chunks]
        return retrieve_top_k(hash_embed(query, dim=dim), doc_vecs, k=k)
    """
    # TODO: 切(chunk_text)→ 嵌(hash_embed)→ 检(retrieve_top_k),复用不重写
    ...


# ========== §31.9 综合② 全管道:rag_answer ==========


def rag_answer(
    query: str,
    documents: list[str],
    llm: Callable[[str], str],
    k: int = 3,
    dim: int = 16,
) -> tuple[str, list[str]]:
    """
    【综合② · §31.9】完整 RAG 问答:检索 → 拼上下文 → 拼 prompt → 调 llm → 返回
    (回答, 来源片段列表)。来源随答案一起返回,展示给用户 = 可溯源。

    llm 是【注入的 callable】(收 prompt 字符串、返回答案字符串)——依赖注入:
    测试传 lambda 假模型(离线、免费、确定性,同 Ch30 的 FakeModel 套路),
    生产传真 client(tutorial §31.10),本函数一行不动。

    示例(llm 是「回显 prompt 最后一行」的假模型):
        docs = ["《售后政策》:7 天无理由退货", "《手机手册》:5000mAh 电池"]
        fake = lambda p: p.splitlines()[-1]
        answer, sources = rag_answer("《售后政策》:7 天无理由退货", docs, fake, k=1)
        answer   -> "客服回答:"                 # 假模型回显了 prompt 最后一行
        sources  -> ["《售后政策》:7 天无理由退货"]  # 命中的片段 = 答案来源

    提示:考的就是【复用】,别重写任何一站:
        top = search_knowledge_base(query, documents, k=k, dim=dim)
        sources = [t for t, _ in top]
        prompt = build_rag_prompt(query, build_context(sources))
        return llm(prompt), sources
    """
    # TODO: search_knowledge_base → 取片段文本 → build_context → build_rag_prompt → llm(prompt)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示:对迷你知识库跑一次完整 RAG(llm 用假模型;真实用法见 tutorial §31.10)
    KNOWLEDGE_BASE = [
        "《极客手机 X1 说明书》:6.7 英寸屏幕,5000mAh 大电池,支持 65W 快充,IP68 防水。",
        "《极客耳机 Pro 说明书》:主动降噪深度 45dB,续航 36 小时(含充电盒),蓝牙 5.4。",
        "《售后政策》:支持 7 天无理由退货(包装需完好),15 天质量问题换货,整机保修 2 年。",
    ]
    query = KNOWLEDGE_BASE[2]  # hash_embed 不表达语义,用"原文当问题"保证确定性命中
    answer, sources = rag_answer(query, KNOWLEDGE_BASE, llm=lambda p: "根据[资料1]:" + p.split("[资料1] ")[1].split("\n")[0])
    print("问题:", query)
    print("回答:", answer)
    print("来源:", sources)
