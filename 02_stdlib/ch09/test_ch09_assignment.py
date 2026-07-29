"""
Ch09 作业测试。运行: uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v
"""
import pytest

from ch09_assignment import (
    flatten,
    group_by_sorted,
    pair_combinations,
    multiply_all,
    cached_fib,
)
from conftest import load_mock_json


@pytest.fixture
def access_logs():
    return load_mock_json("access_logs.json")


# ---------- flatten:itertools.chain ----------
class TestFlatten:
    def test_two_lists(self):
        assert flatten([1, 2], [3, 4]) == [1, 2, 3, 4]

    def test_three_lists(self):
        assert flatten([1], [2, 3], [4]) == [1, 2, 3, 4]

    def test_empty(self):
        assert flatten([], []) == []

    def test_accepts_tuples_too(self):
        assert flatten((1, 2), [3]) == [1, 2, 3]


# ---------- group_by_sorted:itertools.groupby ----------
class TestGroupBySorted:
    def test_numbers(self):
        # 先排序后分组,1 出现两次合并成一组
        assert group_by_sorted([1, 2, 1, 3, 2], lambda x: x) == {
            1: [1, 1], 2: [2, 2], 3: [3],
        }

    def test_by_status_from_logs(self, access_logs):
        result = group_by_sorted(access_logs, lambda log: log["status"])
        assert len(result[200]) == 13
        assert len(result[500]) == 3

    def test_strings_by_length(self):
        result = group_by_sorted(["a", "bb", "c", "ddd"], len)
        assert result[1] == ["a", "c"]
        assert result[3] == ["ddd"]

    def test_returns_dict(self):
        assert isinstance(group_by_sorted([1], lambda x: x), dict)


# ---------- pair_combinations:itertools.combinations ----------
class TestPairCombinations:
    def test_three_items(self):
        assert pair_combinations(["a", "b", "c"]) == [
            ("a", "b"), ("a", "c"), ("b", "c"),
        ]

    def test_count_is_n_choose_2(self):
        assert len(pair_combinations([1, 2, 3, 4])) == 6   # C(4,2)

    def test_two_items(self):
        assert pair_combinations([1, 2]) == [(1, 2)]

    def test_less_than_two_returns_empty(self):
        assert pair_combinations([1]) == []
        assert pair_combinations([]) == []


# ---------- multiply_all:functools.reduce ----------
class TestMultiplyAll:
    def test_basic(self):
        assert multiply_all([2, 3, 4]) == 24

    def test_single(self):
        assert multiply_all([7]) == 7

    def test_empty_returns_identity(self):
        assert multiply_all([]) == 1   # 乘法单位元

    def test_with_zero(self):
        assert multiply_all([5, 0, 9]) == 0


# ---------- cached_fib:functools.lru_cache ----------
class TestCachedFib:
    def test_base_cases(self):
        assert cached_fib(0) == 0
        assert cached_fib(1) == 1

    def test_small(self):
        assert cached_fib(10) == 55

    def test_large_fast(self):
        # 没记忆化会慢到不可用;有 lru_cache 秒算
        assert cached_fib(50) == 12586269025

    def test_cache_hit_recorded(self):
        cached_fib(60)
        info = cached_fib.cache_info()
        assert info.hits >= 1

    def test_has_cache_info(self):
        # lru_cache 装饰的函数带 cache_info / cache_clear
        assert hasattr(cached_fib, "cache_info")
