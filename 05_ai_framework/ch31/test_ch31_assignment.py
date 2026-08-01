"""
Ch31 作业测试。运行: uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v
"""
import math

import pytest

from ch31_assignment import (
    build_context,
    chunk_text,
    cosine_similarity,
    hash_embed,
    retrieve_top_k,
)


# ---------- chunk_text ----------
class TestChunkText:
    def test_overlap(self):
        assert chunk_text("abcdef", size=3, overlap=1) == ["abc", "cde", "ef"]

    def test_no_overlap(self):
        assert chunk_text("abcdef", size=3, overlap=0) == ["abc", "def"]

    def test_text_shorter_than_size(self):
        assert chunk_text("abc", size=10, overlap=2) == ["abc"]

    def test_empty(self):
        assert chunk_text("", size=5) == []

    def test_invalid_size(self):
        assert chunk_text("abc", size=0) == []

    def test_default_params(self):
        # 默认 size=100 overlap=20
        result = chunk_text("x" * 250)
        assert len(result) > 1
        assert all(len(c) <= 100 for c in result)


# ---------- cosine_similarity ----------
class TestCosineSimilarity:
    def test_identical(self):
        assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite(self):
        assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_diagonal(self):
        assert cosine_similarity([1, 0], [1, 1]) == pytest.approx(1 / math.sqrt(2))

    def test_zero_vector(self):
        assert cosine_similarity([0, 0], [1, 1]) == 0.0
        assert cosine_similarity([0, 0], [0, 0]) == 0.0

    def test_three_dim(self):
        assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


# ---------- retrieve_top_k ----------
class TestRetrieveTopK:
    def test_ordering(self):
        docs = [("苹果", [1, 0]), ("香蕉", [0, 1]), ("梨", [1, 1])]
        assert retrieve_top_k([1, 0], docs, k=2) == ["苹果", "梨"]

    def test_k_larger_than_docs(self):
        docs = [("a", [1, 0]), ("b", [0, 1])]
        assert set(retrieve_top_k([1, 0], docs, k=10)) == {"a", "b"}

    def test_k_one(self):
        docs = [("近", [1, 0]), ("远", [0, 1])]
        assert retrieve_top_k([1, 0], docs, k=1) == ["近"]

    def test_empty(self):
        assert retrieve_top_k([1, 0], [], k=3) == []

    def test_all_equal_similarities(self):
        docs = [("a", [1, 0]), ("b", [1, 0])]
        result = retrieve_top_k([1, 0], docs, k=2)
        assert set(result) == {"a", "b"}


# ---------- build_context ----------
class TestBuildContext:
    def test_join(self):
        assert build_context(["片段A", "片段B"]) == "片段A\n\n片段B"

    def test_custom_sep(self):
        assert build_context(["a", "b"], sep=" | ") == "a | b"

    def test_empty(self):
        assert build_context([]) == ""

    def test_single(self):
        assert build_context(["only"]) == "only"


# ---------- hash_embed ----------
class TestHashEmbed:
    def test_dimension(self):
        assert len(hash_embed("x", dim=8)) == 8
        assert len(hash_embed("x")) == 16  # 默认 dim=16

    def test_deterministic(self):
        assert hash_embed("苹果") == hash_embed("苹果")

    def test_different_text_different_vec(self):
        assert hash_embed("苹果") != hash_embed("香蕉")

    def test_values_in_range(self):
        v = hash_embed("test", dim=32)
        assert all(-1.0 <= x <= 1.0 for x in v)

    def test_not_all_zero(self):
        v = hash_embed("hello", dim=16)
        assert any(abs(x) > 0.01 for x in v)
