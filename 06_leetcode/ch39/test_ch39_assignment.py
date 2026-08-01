"""
Ch39 作业测试(动态规划)。运行: uv run pytest 06_leetcode/ch39/test_ch39_assignment.py -v
"""
import pytest

from ch39_assignment import (
    climb_stairs,
    coin_change,
    length_of_lis,
    longest_common_subsequence,
    min_distance,
)


# ---------- climb_stairs (LC70) ----------
class TestClimbStairs:
    def test_leetcode_example_2(self):
        assert climb_stairs(2) == 2  # 1+1, 2

    def test_leetcode_example_3(self):
        assert climb_stairs(3) == 3  # 1+1+1, 1+2, 2+1

    def test_base_one(self):
        assert climb_stairs(1) == 1

    def test_five(self):
        assert climb_stairs(5) == 8  # 斐波那契: 1,2,3,5,8

    def test_ten(self):
        assert climb_stairs(10) == 89

    def test_fibonacci_sequence(self):
        # 验证 f(n)=f(n-1)+f(n-2) 成立
        for n in range(3, 15):
            assert climb_stairs(n) == climb_stairs(n - 1) + climb_stairs(n - 2)


# ---------- coin_change (LC322) ----------
class TestCoinChange:
    def test_leetcode_example(self):
        assert coin_change([1, 2, 5], 11) == 3  # 5+5+1

    def test_impossible(self):
        assert coin_change([2], 3) == -1  # 凑不出 3

    def test_zero_amount(self):
        assert coin_change([1, 2, 5], 0) == 0

    def test_single_coin_denom(self):
        assert coin_change([1], 2) == 2  # 1+1

    def test_single_coin_exact(self):
        assert coin_change([5], 5) == 1

    def test_need_multiple(self):
        assert coin_change([1, 2, 5], 7) == 2  # 5+2

    def test_large_with_one(self):
        # 只能用 2 和 5,凑 13:5+5+2+1? 1 不在 -> 5+5+?3凑不出 -> 2*? 13 奇数不行
        # 改成 [2,5] 凑 12 = 5+5+2 -> 3
        assert coin_change([2, 5], 12) == 3

    def test_impossible_all(self):
        # 面额都 > amount 且 amount != 0 -> 凑不出
        assert coin_change([5, 10], 3) == -1


# ---------- length_of_lis (LC300) ----------
class TestLengthOfLis:
    def test_leetcode_example(self):
        assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4

    def test_second_example(self):
        assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4

    def test_all_equal(self):
        assert length_of_lis([7, 7, 7, 7]) == 1  # 严格递增,只能取 1 个

    def test_empty(self):
        assert length_of_lis([]) == 0

    def test_single(self):
        assert length_of_lis([42]) == 1

    def test_strictly_increasing(self):
        assert length_of_lis([1, 2, 3, 4, 5]) == 5

    def test_strictly_decreasing(self):
        assert length_of_lis([5, 4, 3, 2, 1]) == 1

    def test_two_elements_increasing(self):
        assert length_of_lis([1, 3]) == 2

    def test_negative_numbers(self):
        assert length_of_lis([-1, 0, -2, 3]) == 3  # -1,0,3


# ---------- longest_common_subsequence (LC1143) ----------
class TestLongestCommonSubsequence:
    def test_leetcode_example(self):
        assert longest_common_subsequence("abcde", "ace") == 3  # "ace"

    def test_identical(self):
        assert longest_common_subsequence("abc", "abc") == 3

    def test_no_common(self):
        assert longest_common_subsequence("abc", "def") == 0

    def test_one_empty(self):
        assert longest_common_subsequence("", "abc") == 0
        assert longest_common_subsequence("abc", "") == 0

    def test_both_empty(self):
        assert longest_common_subsequence("", "") == 0

    def test_partial_overlap(self):
        assert longest_common_subsequence("bsbininm", "jmjkbkjkv") == 1  # "b"

    def test_subsequence_at_end(self):
        assert longest_common_subsequence("abcdef", "def") == 3  # "def"

    def test_repeated_chars(self):
        assert longest_common_subsequence("aab", "ab") == 2  # "ab"


# ---------- min_distance (LC72) ----------
class TestMinDistance:
    def test_leetcode_example(self):
        assert min_distance("horse", "ros") == 3

    def test_leetcode_second_example(self):
        assert min_distance("intention", "execution") == 5

    def test_both_empty(self):
        assert min_distance("", "") == 0

    def test_first_empty(self):
        assert min_distance("", "a") == 1  # 插入 a

    def test_second_empty(self):
        assert min_distance("a", "") == 1  # 删除 a

    def test_identical(self):
        assert min_distance("abc", "abc") == 0  # 完全相同

    def test_single_replace(self):
        assert min_distance("a", "b") == 1  # 替换

    def test_single_insert(self):
        assert min_distance("ab", "abc") == 1  # 插入 c

    def test_single_delete(self):
        assert min_distance("abc", "ab") == 1  # 删除 c
