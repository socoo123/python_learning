"""Ch36 · 哈希表 / 前缀和 —— 测试。

运行:
    uv run pytest 06_leetcode/ch36/test_ch36_assignment.py -v
"""

import pytest

from ch36_assignment import (
    group_anagrams,
    longest_consecutive,
    subarray_sum,
    two_sum,
)


# ---------------------------------------------------------------------------
# LC1 两数之和
# ---------------------------------------------------------------------------
class TestTwoSum:
    def test_leetcode_example1(self):
        # [2,7,11,15], target=9 -> [0,1]
        assert two_sum([2, 7, 11, 15], 9) == [0, 1]

    def test_leetcode_example2(self):
        # [3,2,4], target=6 -> [1,2]
        assert two_sum([3, 2, 4], 6) == [1, 2]

    def test_leetcode_example3_duplicate_values(self):
        # [3,3], target=6 -> [0,1]  (两个相同值相加)
        assert two_sum([3, 3], 6) == [0, 1]

    def test_first_two(self):
        assert two_sum([1, 2, 3], 3) == [0, 1]

    def test_last_two(self):
        assert two_sum([1, 2, 3, 4], 7) == [2, 3]

    def test_negative_numbers(self):
        assert two_sum([-1, -2, -3, -4, -5], -8) == [2, 4]

    def test_mixed_signs(self):
        assert two_sum([-3, 4, 3, 90], 0) == [0, 2]

    def test_two_elements_only(self):
        assert two_sum([5, 5], 10) == [0, 1]

    def test_returns_indices_not_values(self):
        # 确保返回的是下标, 不是值
        result = two_sum([10, 20, 30, 40, 50], 90)
        assert result == [3, 4]
        assert all(isinstance(x, int) for x in result)
        assert all(0 <= x < 5 for x in result)


# ---------------------------------------------------------------------------
# LC49 字母异位词分组
# ---------------------------------------------------------------------------
class TestGroupAnagrams:
    def _normalize(self, groups: list[list[str]]) -> list[list[str]]:
        """把分组结果规整成可比较的形式:每组内排序、再按组排序。"""
        return sorted(sorted(g) for g in groups)

    def test_leetcode_example(self):
        result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
        expected = [["bat"], ["eat", "tea", "ate"], ["tan", "nat"]]
        assert self._normalize(result) == self._normalize(expected)

    def test_single_empty_string(self):
        assert group_anagrams([""]) == [[""]]

    def test_single_char(self):
        assert group_anagrams(["a"]) == [["a"]]

    def test_empty_input(self):
        assert group_anagrams([]) == []

    def test_all_same_anagram(self):
        result = group_anagrams(["abc", "bca", "cab", "abc"])
        assert self._normalize(result) == [["abc", "abc", "bca", "cab"]]

    def test_no_anagrams(self):
        result = group_anagrams(["abc", "def", "ghi"])
        assert self._normalize(result) == [["abc"], ["def"], ["ghi"]]

    def test_group_count(self):
        result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
        # 题面例子: 3 组
        assert len(result) == 3

    def test_preserves_all_words(self):
        words = ["eat", "tea", "tan", "ate", "nat", "bat"]
        result = group_anagrams(words)
        # 所有词都被分到某个组里, 没丢
        flat = [w for g in result for w in g]
        assert sorted(flat) == sorted(words)

    def test_duplicate_letters(self):
        # 含重复字母的异位词
        result = group_anagrams(["aab", "aba", "baa", "abc"])
        assert self._normalize(result) == [["aab", "aba", "baa"], ["abc"]]


# ---------------------------------------------------------------------------
# LC560 和为 K 的子数组个数
# ---------------------------------------------------------------------------
class TestSubarraySum:
    def test_leetcode_example1(self):
        assert subarray_sum([1, 1, 1], 2) == 2

    def test_leetcode_example2(self):
        assert subarray_sum([1, 2, 3], 3) == 2  # [1,2] 和 [3]

    def test_single_element_equal_k(self):
        # 从下标 0 开始的子数组和正好 = k, 考验 {0:1} 初始项
        assert subarray_sum([5], 5) == 1

    def test_single_element_not_equal_k(self):
        assert subarray_sum([1], 0) == 0

    def test_empty_array(self):
        assert subarray_sum([], 0) == 0

    def test_empty_array_k_nonzero(self):
        assert subarray_sum([], 5) == 0

    def test_all_negative(self):
        # [-1,-1,1], k=0 -> 1 (整个数组)
        assert subarray_sum([-1, -1, 1], 0) == 1

    def test_negative_prefix_needed(self):
        # 负数: 多个子数组可能和为 k
        # [1,-1,1,-1,1] 和为 0 的连续子数组:
        #   [1,-1](0-1), [1,-1,1,-1](0-3), [-1,1](1-2), [-1,1,-1,1](1-4),
        #   [1,-1](2-3), [-1,1](3-4) -> 6 个
        assert subarray_sum([1, -1, 1, -1, 1], 0) == 6

    def test_k_zero_with_zeros(self):
        # [0,0,0], k=0: 所有非空连续子数组和都为 0
        # 长度 3 的数组共 n(n+1)/2 = 6 个非空连续子数组, 全部和为 0
        assert subarray_sum([0, 0, 0], 0) == 6

    def test_no_subarray_sums_to_k(self):
        assert subarray_sum([1, 2, 3], 100) == 0

    def test_whole_array_equals_k(self):
        assert subarray_sum([1, 2, 3], 6) == 1

    def test_multiple_overlapping(self):
        # [1,2,1,2,1], k=3 -> [1,2](0-1),[2,1](1-2),[1,2](2-3),[2,1](3-4) = 4
        assert subarray_sum([1, 2, 1, 2, 1], 3) == 4


# ---------------------------------------------------------------------------
# LC128 最长连续序列
# ---------------------------------------------------------------------------
class TestLongestConsecutive:
    def test_leetcode_example1(self):
        # [100,4,200,1,3,2] -> 4 (序列 1,2,3,4)
        assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4

    def test_leetcode_example2(self):
        # [0,3,7,2,5,8,4,6,0,1] -> 9 (序列 0..8)
        assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9

    def test_empty(self):
        assert longest_consecutive([]) == 0

    def test_single_element(self):
        assert longest_consecutive([1]) == 1

    def test_all_duplicates(self):
        # 重复元素只算一次
        assert longest_consecutive([1, 1, 1, 1]) == 1

    def test_no_consecutive(self):
        # 全是隔开的数, 每个序列长度都是 1
        assert longest_consecutive([10, 20, 30, 40]) == 1

    def test_negative_numbers(self):
        assert longest_consecutive([-1, -2, -3, 0, 1]) == 5  # -3,-2,-1,0,1

    def test_negative_only(self):
        assert longest_consecutive([-5, -4, -3, -2, -1]) == 5

    def test_with_duplicates_in_sequence(self):
        # [1,2,0,1] -> 序列 0,1,2 -> 3 (重复的 1 不增加长度)
        assert longest_consecutive([1, 2, 0, 1]) == 3

    def test_mixed_signs_large_gap(self):
        # 序列 A: -2,-1,0,1 (长 4); 序列 B: 3,4,5,6,7,8,9 (长 7) -> 最长 7
        assert longest_consecutive([9, 1, 4, 7, 3, -1, 0, 5, 8, -2, 6]) == 7

    def test_two_element_consecutive(self):
        assert longest_consecutive([1, 2]) == 2

    def test_two_element_gap(self):
        assert longest_consecutive([1, 3]) == 1