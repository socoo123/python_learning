"""
Ch31 作业测试。运行: uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v

全程离线:embedding 用确定性 hash_embed(假向量),llm 用注入的假 callable,
不装 sentence-transformers、不调真实 LLM。
"""
import math

import pytest

from ch31_assignment import (
    RAG_TEMPLATE,
    build_context,
    build_rag_prompt,
    chunk_text,
    cosine_similarity,
    hash_embed,
    rag_answer,
    retrieve_top_k,
    search_knowledge_base,
)

# 迷你知识库(每篇 < 100 字符,默认切片参数下恰好一篇一片)
PHONE = "《极客手机 X1 说明书》:5000mAh 电池,支持 65W 快充,IP68 防水。"
HEADPHONE = "《极客耳机 Pro 说明书》:主动降噪 45dB,续航 36 小时,蓝牙 5.4。"
POLICY = "《售后政策》:7 天无理由退货,15 天换货,整机保修 2 年。"
DOCS = [PHONE, HEADPHONE, POLICY]


# ---------- §31.2 chunk_text ----------
class TestChunkText:
    def test_overlap(self):
        # step = 3-1 = 2 → i=0,2,4
        assert chunk_text("abcdef", size=3, overlap=1) == ["abc", "cde", "ef"]

    def test_no_overlap(self):
        assert chunk_text("abcdef", size=3, overlap=0) == ["abc", "def"]

    def test_real_manual_snippet(self):
        # 真实场景:切《售后政策》,overlap 让切缝处的词("由退"/"保修")在相邻片里重复
        text = "支持7天无理由退货,整机保修2年。"
        assert chunk_text(text, size=8, overlap=2) == [
            "支持7天无理由退",
            "由退货,整机保修",
            "保修2年。",
        ]

    def test_text_shorter_than_size(self):
        assert chunk_text("abc", size=10, overlap=2) == ["abc"]

    def test_empty(self):
        assert chunk_text("", size=5) == []

    def test_invalid_size(self):
        assert chunk_text("abc", size=0) == []
        assert chunk_text("abc", size=-1) == []

    def test_overlap_ge_size_no_dead_loop(self):
        # overlap >= size 时 step=max(1, ...)=1,保证不死循环不炸
        assert chunk_text("abcdef", size=2, overlap=5) == ["ab", "bc", "cd", "de", "ef", "f"]

    def test_default_params(self):
        # 默认 size=100 overlap=20 → step=80:250 字符 → 4 片 [100,100,100,10]
        result = chunk_text("x" * 250)
        assert len(result) == 4
        assert all(len(c) <= 100 for c in result)


# ---------- §31.3 cosine_similarity ----------
class TestCosineSimilarity:
    def test_identical(self):
        assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite(self):
        assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_known_value(self):
        # 点积 3*4+4*3=24,模长 5×5 → 24/25
        assert cosine_similarity([3, 4], [4, 3]) == pytest.approx(0.96)

    def test_diagonal(self):
        assert cosine_similarity([1, 0], [1, 1]) == pytest.approx(1 / math.sqrt(2))

    def test_direction_over_length(self):
        # 为什么用余弦:同方向不同长度仍满分(欧氏距离会给 2.236)
        assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1.0)

    def test_zero_vector(self):
        assert cosine_similarity([0, 0], [1, 1]) == 0.0
        assert cosine_similarity([0, 0], [0, 0]) == 0.0


# ---------- §31.4 hash_embed ----------
class TestHashEmbed:
    def test_dimension(self):
        assert len(hash_embed("x", dim=8)) == 8
        assert len(hash_embed("x")) == 16  # 默认 dim=16

    def test_deterministic(self):
        assert hash_embed("苹果") == hash_embed("苹果")
        assert hash_embed("") == hash_embed("")

    def test_different_text_different_vec(self):
        assert hash_embed("苹果") != hash_embed("香蕉")

    def test_values_in_range(self):
        for text in ["", "a", "苹果", "x" * 100]:
            v = hash_embed(text, dim=64)
            assert all(-1.0 <= x <= 1.0 for x in v)

    def test_not_all_zero(self):
        # 零向量会让余弦相似度恒 0,假向量必须非零
        v = hash_embed("hello", dim=16)
        assert any(abs(x) > 0.01 for x in v)


# ---------- §31.5 retrieve_top_k ----------
class TestRetrieveTopK:
    def test_ordering_with_scores(self):
        docs = [("苹果", [1, 0]), ("香蕉", [0, 1]), ("梨", [1, 1])]
        top = retrieve_top_k([1, 0], docs, k=2)
        assert [t for t, _ in top] == ["苹果", "梨"]
        assert top[0][1] == pytest.approx(1.0)
        assert top[1][1] == pytest.approx(1 / math.sqrt(2))

    def test_k_one(self):
        docs = [("近", [1, 0]), ("远", [0, 1])]
        assert retrieve_top_k([1, 0], docs, k=1) == [("近", pytest.approx(1.0))]

    def test_k_larger_than_docs(self):
        docs = [("a", [1, 0]), ("b", [0, 1])]
        top = retrieve_top_k([1, 0], docs, k=10)
        assert {t for t, _ in top} == {"a", "b"}

    def test_zero_score_still_returned(self):
        # 契约:不做阈值过滤,分数 0 也在 k 内照返
        docs = [("a", [1, 0]), ("b", [0, 1])]
        top = retrieve_top_k([1, 0], docs, k=2)
        assert top[1][0] == "b"
        assert top[1][1] == pytest.approx(0.0)

    def test_stable_tie(self):
        # 同分保持原先后顺序(sort 稳定排序)
        docs = [("a", [1, 0]), ("b", [1, 0])]
        assert [t for t, _ in retrieve_top_k([1, 0], docs, k=2)] == ["a", "b"]

    def test_empty(self):
        assert retrieve_top_k([1, 0], [], k=3) == []


# ---------- §31.6 build_context ----------
class TestBuildContext:
    def test_numbered_join(self):
        # 带编号 [资料N] —— 溯源的载体
        assert build_context(["片段A", "片段B"]) == "[资料1] 片段A\n\n[资料2] 片段B"

    def test_custom_sep(self):
        assert build_context(["a", "b"], sep=" | ") == "[资料1] a | [资料2] b"

    def test_single(self):
        assert build_context(["only"]) == "[资料1] only"

    def test_empty(self):
        assert build_context([]) == ""


# ---------- §31.7 build_rag_prompt ----------
class TestBuildRagPrompt:
    def test_render(self):
        expected = (
            "你是极客商城的客服,只基于下面的资料回答用户问题;资料里没有的信息,就说「不知道」。\n\n"
            "[资料1] 《售后政策》:7 天无理由\n\n"
            "用户问题:支持退货吗\n"
            "客服回答:"
        )
        assert build_rag_prompt("支持退货吗", "[资料1] 《售后政策》:7 天无理由") == expected

    def test_custom_template(self):
        assert (
            build_rag_prompt("q", "c", template="资料:{context}/问:{question}") == "资料:c/问:q"
        )

    def test_template_has_anti_hallucination(self):
        # 防幻觉约束是模板的一部分(没有它模型会瞎编)
        assert "不知道" in RAG_TEMPLATE
        assert "{context}" in RAG_TEMPLATE and "{question}" in RAG_TEMPLATE


# ---------- §31.8 search_knowledge_base ----------
class TestSearchKnowledgeBase:
    def test_exact_match_top1(self):
        # query 恰好等于某篇文档 → 相似度满分排第一(hash_embed 确定性保证)
        top = search_knowledge_base(POLICY, DOCS, k=1)
        assert top[0][0] == POLICY
        assert top[0][1] == pytest.approx(1.0)

    def test_scores_descending(self):
        top = search_knowledge_base(PHONE, DOCS, k=3)
        scores = [s for _, s in top]
        assert scores == sorted(scores, reverse=True)

    def test_k_limit(self):
        top = search_knowledge_base(PHONE, DOCS, k=2)
        assert len(top) == 2
        assert all(t in DOCS for t, _ in top)

    def test_custom_dim(self):
        # query 与建库用同一 dim → 依然满分命中(维度不一致会静默算错,见 §31.8)
        top = search_knowledge_base(POLICY, DOCS, k=1, dim=8)
        assert top[0][0] == POLICY
        assert top[0][1] == pytest.approx(1.0)

    def test_long_doc_gets_chunked(self):
        # 250 字符的文档按默认 size=100 切片 → 命中的都是 <=100 字符的片段
        long_doc = "极" * 250
        top = search_knowledge_base("查询", [long_doc], k=3)
        assert len(top) == 3
        assert all(len(t) <= 100 and t in long_doc for t, _ in top)

    def test_empty_documents(self):
        assert search_knowledge_base("问", [], k=3) == []


# ---------- §31.9 rag_answer ----------
class TestRagAnswer:
    def test_pipeline_with_captured_prompt(self):
        seen = []

        def fake_llm(p: str) -> str:
            seen.append(p)
            return "假回答"

        answer, sources = rag_answer(POLICY, DOCS, fake_llm, k=2)
        assert answer == "假回答"
        assert sources[0] == POLICY  # 满分命中排第一
        assert len(sources) == 2
        # llm 只调一次,且收到的 prompt 是完整 RAG 模板:约束 + 编号资料 + 用户问题
        assert len(seen) == 1
        prompt = seen[0]
        assert prompt.startswith("你是极客商城的客服")
        assert f"[资料1] {POLICY}" in prompt
        assert "[资料2] " in prompt
        assert f"用户问题:{POLICY}" in prompt

    def test_sources_for_citation(self):
        # 溯源:sources 就是检索命中的片段,与 search_knowledge_base 一致
        answer, sources = rag_answer(PHONE, DOCS, lambda p: "x", k=2)
        expected = [t for t, _ in search_knowledge_base(PHONE, DOCS, k=2)]
        assert sources == expected

    def test_empty_knowledge_base(self):
        seen = []
        answer, sources = rag_answer("退货吗", [], lambda p: seen.append(p) or "不知道")
        assert answer == "不知道"
        assert sources == []
        assert "用户问题:退货吗" in seen[0]

    def test_llm_dependency_injection(self):
        # 换 llm 实现,管道其余行为不变 —— 依赖注入的意义
        a1, _ = rag_answer(POLICY, DOCS, lambda p: "A", k=1)
        a2, _ = rag_answer(POLICY, DOCS, lambda p: "B", k=1)
        assert (a1, a2) == ("A", "B")
