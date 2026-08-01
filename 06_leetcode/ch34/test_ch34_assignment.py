"""
Ch34 作业测试。运行: uv run pytest 06_leetcode/ch34/test_ch34_assignment.py -v

每题一个 TestXxx 类,覆盖:正常用例 + 边界(空、单元素、LeetCode 经典 case)。
断言依据来自 tutorial 里给的题目示例(对齐 LC703/LC35/LC509 等)。
"""
import pytest

from ch34_assignment import (
    char_frequency,
    dedup_keep_order,
    fib,
    kth_largest,
    search_insert_pos,
)


# ---------- char_frequency ----------
class TestCharFrequency:
    def test_basic(self):
        # 题目示例:b 出现 3 次最多
        assert char_frequency("aabbbc") == [("b", 3), ("a", 2), ("c", 1)]

    def test_empty(self):
        # 空串 -> []
        assert char_frequency("") == []

    def test_fewer_than_three(self):
        # 不足 3 个字符,返回实际数量
        result = char_frequency("ab")
        assert len(result) == 2
        assert ("a", 1) in result
        assert ("b", 1) in result

    def test_single_char(self):
        assert char_frequency("aaaa") == [("a", 4)]

    def test_top_three_among_many(self):
        # 多于 3 种字符,只取前 3
        result = char_frequency("aaabbbccd")
        assert len(result) == 3
        assert result[0] == ("a", 3)
        assert result[1] == ("b", 3)
        assert result[2] == ("c", 2)

    def test_returns_tuples_of_char_and_count(self):
        result = char_frequency("aabbbc")
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)
        assert all(isinstance(c, str) and isinstance(n, int) for c, n in result)


# ---------- kth_largest ----------
class TestKthLargest:
    def test_k2(self):
        # 题目示例
        assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5

    def test_k1_returns_max(self):
        assert kth_largest([3, 2, 1, 5, 6, 4], 1) == 6

    def test_k_equals_len_returns_min(self):
        assert kth_largest([3, 2, 1, 5, 6, 4], 6) == 1

    def test_single_element(self):
        assert kth_largest([1], 1) == 1

    def test_duplicates(self):
        # 第 2 大:[5,5,4] 的 nlargest(2) = [5,5], [-1] = 5
        assert kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4

    def test_two_elements(self):
        assert kth_largest([2, 1], 1) == 2
        assert kth_largest([2, 1], 2) == 1


# ---------- search_insert_pos ----------
class TestSearchInsertPos:
    def test_target_found(self):
        # 题目示例:命中
        assert search_insert_pos([1, 3, 5, 6], 5) == 2

    def test_insert_in_middle(self):
        # 题目示例:2 不在,插到下标 1
        assert search_insert_pos([1, 3, 5, 6], 2) == 1

    def test_insert_at_end(self):
        # 题目示例:7 比所有大,插末尾下标 4
        assert search_insert_pos([1, 3, 5, 6], 7) == 4

    def test_insert_at_start(self):
        # 0 比所有小,插开头下标 0
        assert search_insert_pos([1, 3, 5, 6], 0) == 0

    def test_empty_array(self):
        # 空数组,插哪都是 0
        assert search_insert_pos([], 5) == 0

    def test_single_element_found(self):
        assert search_insert_pos([1], 1) == 0

    def test_single_element_insert_before(self):
        assert search_insert_pos([2], 1) == 0

    def test_single_element_insert_after(self):
        assert search_insert_pos([2], 3) == 1

    def test_duplicates_target(self):
        # 有重复时,bisect_left 返回第一个 >= target 的位置(最左)
        assert search_insert_pos([1, 2, 2, 2, 3], 2) == 1


# ---------- dedup_keep_order ----------
class TestDedupKeepOrder:
    def test_basic_ints(self):
        # 题目示例
        assert dedup_keep_order([1, 2, 2, 3, 1, 4]) == [1, 2, 3, 4]

    def test_basic_strings(self):
        # 题目示例
        assert dedup_keep_order(["b", "a", "b", "c"]) == ["b", "a", "c"]

    def test_empty(self):
        assert dedup_keep_order([]) == []

    def test_all_same(self):
        assert dedup_keep_order([3, 3, 3]) == [3]

    def test_single_element(self):
        assert dedup_keep_order([42]) == [42]

    def test_already_unique(self):
        assert dedup_keep_order([1, 2, 3]) == [1, 2, 3]

    def test_keeps_first_occurrence_order(self):
        # 首次出现顺序:5 在 4 之前出现
        assert dedup_keep_order([5, 4, 5, 4, 6]) == [5, 4, 6]

    def test_mixed_types_not_required_but_hashable(self):
        # tuple 元素也可(只要 hashable)
        assert dedup_keep_order([(1, 2), (1, 2), (3, 4)]) == [(1, 2), (3, 4)]


# ---------- fib ----------
class TestFib:
    def test_base_cases(self):
        assert fib(0) == 0
        assert fib(1) == 1

    def test_small_values(self):
        assert fib(2) == 1
        assert fib(3) == 2
        assert fib(4) == 3
        assert fib(5) == 5

    def test_fib_10(self):
        # 题目示例
        assert fib(10) == 55

    def test_fib_20(self):
        # 题目示例
        assert fib(20) == 6765

    def test_recurrence(self):
        # 验证递推关系 fib(n) = fib(n-1) + fib(n-2) 对若干 n 成立
        for n in range(2, 30):
            assert fib(n) == fib(n - 1) + fib(n - 2)

    def test_larger_value_reasonable_time(self):
        # 验证记忆化后大 n 也能快速算(普通递归这里会超时)
        # fib(50) = 12586269025
        assert fib(50) == 12586269025
