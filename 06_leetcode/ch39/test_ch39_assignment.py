"""
Ch39 作业测试(动态规划)。运行: uv run pytest 06_leetcode/ch39/test_ch39_assignment.py -v
"""
import pytest

from ch39_assignment import (
    climb_stairs,
    coin_change,
    length_of_lis,
    longest_common_subsequence,
    max_sub_array,
    min_distance,
    rob,
    unique_paths,
)


# ---------- climb_stairs (LC70) §39.2 ----------
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

    def test_large_45(self):
        # n=45 是 LC 上界;记忆化后毫秒级,答案 1836311903
        assert climb_stairs(45) == 1836311903

    def test_fibonacci_recurrence(self):
        # 验证 f(n)=f(n-1)+f(n-2) 成立(拦硬编码)
        for n in range(3, 15):
            assert climb_stairs(n) == climb_stairs(n - 1) + climb_stairs(n - 2)


# ---------- max_sub_array (LC53) §39.3 ----------
class TestMaxSubArray:
    def test_leetcode_example(self):
        assert max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6  # [4,-1,2,1]

    def test_all_positive(self):
        assert max_sub_array([5, 4, -1, 7, 8]) == 23  # 整个数组全要

    def test_single(self):
        assert max_sub_array([1]) == 1

    def test_all_negative(self):
        # 边界之王:全负时取「最大的一个」;初始化成 0 的实现会错答 0
        assert max_sub_array([-2, -1]) == -1
        assert max_sub_array([-3, -2, -5]) == -2

    def test_answer_not_at_end(self):
        # 最大子数组不在末尾,拦「return dp[-1]」的错误实现
        assert max_sub_array([5, 4, -100, 1]) == 9  # [5,4]

    def test_drop_negative_prefix(self):
        assert max_sub_array([8, -19, 5, -4, 20]) == 21  # [5,-4,20]


# ---------- rob (LC198) §39.4 ----------
class TestRob:
    def test_leetcode_example_1(self):
        assert rob([1, 2, 3, 1]) == 4  # 1+3

    def test_leetcode_example_2(self):
        assert rob([2, 7, 9, 3, 1]) == 12  # 2+9+1

    def test_greedy_counterexample(self):
        # 贪心「见大就偷」只得 2+1=3;最优 2+2=4
        assert rob([2, 1, 1, 2]) == 4

    def test_empty(self):
        assert rob([]) == 0

    def test_single(self):
        assert rob([5]) == 5

    def test_two_houses(self):
        assert rob([1, 2]) == 2  # 只能偷一间,取大的

    def test_skip_is_better(self):
        # 每次都偷会得 1+2=3;最优是不偷中间,偷 100
        assert rob([1, 100, 2]) == 100

    def test_longer(self):
        assert rob([6, 6, 4, 8, 4, 3, 3, 10]) == 27  # 6+8+3+10


# ---------- coin_change (LC322) §39.5 ----------
class TestCoinChange:
    def test_leetcode_example(self):
        assert coin_change([1, 2, 5], 11) == 3  # 5+5+1

    def test_greedy_counterexample(self):
        # 贪心 4+1+1=3 枚;最优 3+3=2 枚
        assert coin_change([1, 3, 4], 6) == 2

    def test_impossible(self):
        assert coin_change([2], 3) == -1

    def test_zero_amount(self):
        assert coin_change([1, 2, 5], 0) == 0

    def test_single_coin_denom(self):
        assert coin_change([1], 2) == 2  # 1+1

    def test_single_coin_exact(self):
        assert coin_change([5], 5) == 1

    def test_need_multiple(self):
        assert coin_change([1, 2, 5], 7) == 2  # 5+2

    def test_no_small_denom(self):
        # 面额都 > amount 且 amount != 0 → 凑不出
        assert coin_change([5, 10], 3) == -1

    def test_leetcode_large(self):
        # LC 官方大用例,拦「贪心 + 硬编码」
        assert coin_change([186, 419, 83, 408], 6249) == 20


# ---------- length_of_lis (LC300) §39.6 ----------
class TestLengthOfLis:
    def test_leetcode_example(self):
        assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4

    def test_second_example(self):
        assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4  # [0,1,2,3]

    def test_answer_not_at_end(self):
        # LIS=[1,2,3] 长 3,但以 0 结尾只有 1——拦「return dp[-1]」
        assert length_of_lis([1, 2, 3, 0]) == 3

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

    def test_negative_numbers(self):
        assert length_of_lis([-1, 0, -2, 3]) == 3  # [-1,0,3]

    def test_dip_in_middle(self):
        assert length_of_lis([3, 4, -1, 0, 6, 2, 3]) == 4  # [-1,0,2,3]


# ---------- unique_paths (LC62) §39.7 ----------
class TestUniquePaths:
    def test_leetcode_example_3x7(self):
        assert unique_paths(3, 7) == 28

    def test_leetcode_example_3x2(self):
        assert unique_paths(3, 2) == 3

    def test_single_cell(self):
        assert unique_paths(1, 1) == 1

    def test_single_row(self):
        assert unique_paths(1, 5) == 1  # 只能一直向右

    def test_single_column(self):
        assert unique_paths(5, 1) == 1  # 只能一直向下

    def test_square_2x2(self):
        assert unique_paths(2, 2) == 2

    def test_square_3x3(self):
        assert unique_paths(3, 3) == 6

    def test_10x10(self):
        # C(18,9)=48620,拦「边界忘填 1 / 浅拷贝表」的实现
        assert unique_paths(10, 10) == 48620


# ---------- longest_common_subsequence (LC1143) §39.8 ----------
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

    def test_leetcode_official_2(self):
        assert longest_common_subsequence("ezupkr", "ubmrapg") == 2  # "ur"/"up"

    def test_partial_overlap(self):
        assert longest_common_subsequence("bsbininm", "jmjkbkjkv") == 1  # "b"

    def test_subsequence_at_end(self):
        assert longest_common_subsequence("abcdef", "def") == 3  # "def"

    def test_repeated_chars(self):
        assert longest_common_subsequence("aab", "ab") == 2  # "ab"


# ---------- min_distance (LC72) §39.9 ----------
class TestMinDistance:
    def test_leetcode_example(self):
        assert min_distance("horse", "ros") == 3

    def test_leetcode_second_example(self):
        assert min_distance("intention", "execution") == 5

    def test_kitten_sitting(self):
        # 经典例:换 k→s、换 e→i、末尾插 g
        assert min_distance("kitten", "sitting") == 3

    def test_both_empty(self):
        assert min_distance("", "") == 0

    def test_first_empty(self):
        assert min_distance("", "a") == 1  # 插入 a

    def test_second_empty(self):
        assert min_distance("a", "") == 1  # 删除 a

    def test_longer_empty(self):
        # 拦「边界不填 dp[i][0]=i」的实现
        assert min_distance("abc", "") == 3
        assert min_distance("", "abc") == 3

    def test_identical(self):
        # 相等时白嫖不 +1;「相等也 +1」的实现会错答 3
        assert min_distance("abc", "abc") == 0

    def test_single_replace(self):
        assert min_distance("a", "b") == 1  # 替换(漏「替换」分支会错答 2)

    def test_single_insert(self):
        assert min_distance("ab", "abc") == 1  # 插入 c

    def test_single_delete(self):
        assert min_distance("abc", "ab") == 1  # 删除 c

    def test_flaw_to_lawn(self):
        assert min_distance("flaw", "lawn") == 2  # 删 f、末尾插 n
