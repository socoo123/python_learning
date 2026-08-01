"""
Ch35 作业测试。运行: uv run pytest 06_leetcode/ch35/test_ch35_assignment.py -v
"""
import pytest

from ch35_assignment import (
    length_of_longest_substring,
    max_area,
    min_window,
    three_sum,
    two_sum_sorted,
)


# ---------- two_sum_sorted(原型,辅助理解对撞双指针) ----------
class TestTwoSumSorted:
    def test_found(self):
        assert two_sum_sorted([1, 2, 3, 4, 6], 6) == [2, 4]

    def test_first_pair(self):
        assert two_sum_sorted([2, 7, 11, 15], 9) == [2, 7]

    def test_not_found(self):
        assert two_sum_sorted([1, 2, 3, 9], 8) is None

    def test_empty(self):
        assert two_sum_sorted([], 0) is None

    def test_negative_numbers(self):
        # -1 + 2 == 1(且这是唯一和为 1 的对)
        assert two_sum_sorted([-3, -2, -1, 2, 5], 1) == [-1, 2]


# ---------- max_area(LC11) ----------
class TestMaxArea:
    def test_leetcode_example(self):
        assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49

    def test_two_equal(self):
        assert max_area([1, 1]) == 1

    def test_symmetric(self):
        assert max_area([4, 3, 2, 1, 4]) == 16

    def test_ascending(self):
        # 全程右端更高,左端一路推进;最优:line2(3)和line5(6) → 宽3*min(3,6)=9
        assert max_area([1, 2, 3, 4, 5, 6]) == 9

    def test_descending(self):
        assert max_area([6, 5, 4, 3, 2, 1]) == 9

    def test_single_pair(self):
        assert max_area([2, 3]) == 2  # 宽1 * min(2,3)=2

    def test_large(self):
        # 两端最高,中间最低
        assert max_area([100, 1, 1, 1, 100]) == 400  # 宽4 * min(100,100)


# ---------- length_of_longest_substring(LC3) ----------
class TestLengthOfLongestSubstring:
    def test_leetcode1(self):
        assert length_of_longest_substring("abcabcbb") == 3

    def test_all_same(self):
        assert length_of_longest_substring("bbbbb") == 1

    def test_leetcode3(self):
        assert length_of_longest_substring("pwwkew") == 3

    def test_empty(self):
        assert length_of_longest_substring("") == 0

    def test_single_space(self):
        assert length_of_longest_substring(" ") == 1

    def test_two_chars(self):
        assert length_of_longest_substring("au") == 2

    def test_no_repeat(self):
        assert length_of_longest_substring("abcdef") == 6

    def test_repeat_at_end(self):
        # "abcdeaf":a 在 idx0、5;收缩后 "bcdeaf" 长度 6
        assert length_of_longest_substring("abcdeaf") == 6

    def test_single_char(self):
        assert length_of_longest_substring("a") == 1

    def test_space_and_letters(self):
        assert length_of_longest_substring("ab c") == 4  # 含空格不重复


# ---------- three_sum(LC15) ----------
class TestThreeSum:
    def test_leetcode_example(self):
        assert three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]

    def test_no_triplet(self):
        assert three_sum([0, 1, 1]) == []

    def test_three_zeros(self):
        assert three_sum([0, 0, 0]) == [[0, 0, 0]]

    def test_empty(self):
        assert three_sum([]) == []

    def test_too_short(self):
        assert three_sum([1, 2]) == []

    def test_duplicates_removed(self):
        # 多个 -1 / 0 / 1 不应产生重复三元组
        result = three_sum([-1, -1, -1, 0, 0, 0, 1, 1, 1])
        # 真实期望:[[-1,0,1],[0,0,0]]
        assert result == [[-1, 0, 1], [0, 0, 0]]

    def test_negative_and_positive(self):
        assert three_sum([-2, 0, 1, 1, 2]) == [[-2, 0, 2], [-2, 1, 1]]

    def test_all_negative(self):
        assert three_sum([-5, -4, -3, -2, -1]) == []

    def test_all_positive(self):
        assert three_sum([1, 2, 3, 4, 5]) == []


# ---------- min_window(LC76) ----------
class TestMinWindow:
    def test_leetcode_example(self):
        assert min_window("ADOBECODEBANC", "ABC") == "BANC"

    def test_exact_match(self):
        assert min_window("a", "a") == "a"

    def test_insufficient_chars(self):
        assert min_window("a", "aa") == ""

    def test_char_not_in_s(self):
        assert min_window("a", "b") == ""

    def test_full_window(self):
        assert min_window("abc", "abc") == "abc"

    def test_substring_in_middle(self):
        assert min_window("aab", "ab") == "ab"

    def test_repeated_need(self):
        # t 要两个 A。s = A D O B E C O D E B A N C, A 出现在 idx0 和 idx10
        # 两个 A 之间的最短窗口即 [0..10]="ADOBECODEBA"
        assert min_window("ADOBECODEBANC", "AA") == "ADOBECODEBA"

    def test_t_empty(self):
        # t 为空通常约定返回 ""(无需求)
        assert min_window("abc", "") == ""

    def test_s_empty(self):
        assert min_window("", "a") == ""

    def test_t_longer_than_s(self):
        assert min_window("ab", "abcd") == ""

    def test_minimal_window_at_end(self):
        # 最短覆盖恰好在末尾
        assert min_window("aabc", "bc") == "bc"

    def test_single_char_t(self):
        assert min_window("xyzabc", "a") == "a"
