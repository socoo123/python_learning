"""
Ch35 作业测试。运行: uv run pytest 06_leetcode/ch35/test_ch35_assignment.py -v
"""
import pytest

from ch35_assignment import (
    length_of_longest_substring,
    max_area,
    min_sub_array_len,
    min_window,
    move_zeroes,
    three_sum,
    two_sum_sorted,
)


# ---------- two_sum_sorted(§35.2 对撞双指针原型) ----------
class TestTwoSumSorted:
    def test_found(self):
        assert two_sum_sorted([1, 2, 3, 4, 6], 6) == [2, 4]

    def test_first_pair(self):
        assert two_sum_sorted([2, 7, 11, 15], 9) == [2, 7]

    def test_not_found(self):
        assert two_sum_sorted([1, 2, 3, 9], 8) is None

    def test_empty(self):
        assert two_sum_sorted([], 0) is None

    def test_single_element(self):
        assert two_sum_sorted([5], 5) is None  # 一个数构不成 pair

    def test_negative_numbers(self):
        # -1 + 2 == 1(且这是唯一和为 1 的对)
        assert two_sum_sorted([-3, -2, -1, 2, 5], 1) == [-1, 2]


# ---------- move_zeroes(§35.3 快慢指针,LC283) ----------
class TestMoveZeroes:
    def test_leetcode_example(self):
        assert move_zeroes([0, 1, 0, 3, 12]) == [1, 3, 12, 0, 0]

    def test_all_zero(self):
        assert move_zeroes([0, 0, 0]) == [0, 0, 0]

    def test_no_zero(self):
        assert move_zeroes([1, 2, 3]) == [1, 2, 3]

    def test_empty(self):
        assert move_zeroes([]) == []

    def test_single_zero(self):
        assert move_zeroes([0]) == [0]

    def test_single_nonzero(self):
        assert move_zeroes([1]) == [1]

    def test_zeros_front(self):
        assert move_zeroes([0, 0, 1]) == [1, 0, 0]

    def test_mixed_long(self):
        # LeetCode 经典例:非零相对顺序必须保持
        assert move_zeroes([4, 2, 4, 0, 0, 3, 0, 5, 1, 0]) == [4, 2, 4, 3, 5, 1, 0, 0, 0, 0]

    def test_in_place(self):
        # 关键区分项:必须【原地】修改传入的 list(返回新数组的写法过不了)
        nums = [0, 1, 0, 3]
        result = move_zeroes(nums)
        assert result is nums
        assert nums == [1, 3, 0, 0]


# ---------- max_area(§35.4 对撞 + 贪心,LC11) ----------
class TestMaxArea:
    def test_leetcode_example(self):
        assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49

    def test_two_equal(self):
        assert max_area([1, 1]) == 1

    def test_symmetric(self):
        assert max_area([4, 3, 2, 1, 4]) == 16

    def test_ascending(self):
        # 最优:line2(3)和line5(6) → 宽3*min(3,6)=9
        assert max_area([1, 2, 3, 4, 5, 6]) == 9

    def test_descending(self):
        assert max_area([6, 5, 4, 3, 2, 1]) == 9

    def test_single_pair(self):
        assert max_area([2, 3]) == 2  # 宽1 * min(2,3)=2

    def test_large(self):
        # 两端最高,中间最低
        assert max_area([100, 1, 1, 1, 100]) == 400  # 宽4 * min(100,100)


# ---------- length_of_longest_substring(§35.5 滑窗 + set,LC3) ----------
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

    def test_while_not_if(self):
        # 区分「while 收缩」与「if 收缩」:第二个 b 出现时需连吐 2 个字符
        # if 写法会在 idx3 残留一个 b,后续 best 被算小
        assert length_of_longest_substring("abba") == 2  # "ab" 或 "ba"


# ---------- min_sub_array_len(§35.6 滑窗求最短,LC209) ----------
class TestMinSubArrayLen:
    def test_leetcode_example(self):
        assert min_sub_array_len(7, [2, 3, 1, 2, 4, 3]) == 2  # [4,3]

    def test_single_element_enough(self):
        assert min_sub_array_len(4, [1, 4, 4]) == 1

    def test_not_possible(self):
        assert min_sub_array_len(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0

    def test_whole_array(self):
        assert min_sub_array_len(15, [1, 2, 3, 4, 5]) == 5

    def test_big_element_at_end(self):
        assert min_sub_array_len(5, [1, 1, 1, 1, 10]) == 1  # [10]

    def test_empty(self):
        assert min_sub_array_len(100, []) == 0

    def test_sum_below_target(self):
        assert min_sub_array_len(3, [1, 1]) == 0

    def test_first_element_alone(self):
        assert min_sub_array_len(6, [10, 2, 3]) == 1  # [10]

    def test_exact_window_middle(self):
        # 所有 len<4 的窗口和都 < 8;[1,2,3,2] 和 [2,3,2,1] 恰好 = 8
        assert min_sub_array_len(8, [1, 2, 3, 2, 1]) == 4


# ---------- three_sum(§35.7 排序 + 对撞 + 两处去重,LC15) ----------
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
        assert result == [[-1, 0, 1], [0, 0, 0]]

    def test_negative_and_positive(self):
        assert three_sum([-2, 0, 1, 1, 2]) == [[-2, 0, 2], [-2, 1, 1]]

    def test_all_negative(self):
        assert three_sum([-5, -4, -3, -2, -1]) == []

    def test_all_positive(self):
        assert three_sum([1, 2, 3, 4, 5]) == []

    def test_repeated_first_value(self):
        # 首数重复:去重①和 i-1 比;误写成和 i+1 比会漏掉 [-1,-1,2]
        assert three_sum([-1, -1, 2]) == [[-1, -1, 2]]


# ---------- min_window(§35.8 滑窗 + Counter,LC76 Hard) ----------
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
        # t 要两个 A。s = A D O B E C O D E B A N C, A 在 idx0 和 idx10
        # 两个 A 之间的最短窗口即 [0..10]="ADOBECODEBA"
        assert min_window("ADOBECODEBANC", "AA") == "ADOBECODEBA"

    def test_t_empty(self):
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
