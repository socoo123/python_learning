"""Ch40 测试:回溯 / 贪心。

每个函数一个 TestXxx 类。LeetCode「顺序不限」的答案用 sorted 规范化后再比。
"""

from __future__ import annotations

import pytest

from ch40_assignment import (
    can_jump,
    combination_sum,
    max_profit,
    permute,
    subsets,
)


# ---------------------------------------------------------------------
# §40.2 全排列 permute (LC46)
# ---------------------------------------------------------------------
class TestPermute:
    def _norm(self, ans):
        return sorted(sorted(p) for p in ans)

    def test_lc_example_123(self):
        # 题面:[1,2,3] -> 6 个排列
        ans = permute([1, 2, 3])
        assert self._norm(ans) == self._norm(
            [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
        )

    def test_count(self):
        assert len(permute([1, 2, 3])) == 6
        assert len(permute([0, 1])) == 2

    def test_two(self):
        ans = permute([0, 1])
        assert self._norm(ans) == self._norm([[0, 1], [1, 0]])

    def test_single(self):
        assert permute([1]) == [[1]]

    def test_four_count(self):
        # n=4 应有 4! = 24 个排列,且互不重复
        ans = permute([1, 2, 3, 4])
        assert len(ans) == 24
        assert len({"#".join(map(str, p)) for p in ans}) == 24

    def test_each_permutation_uses_all(self):
        for p in permute([5, 6, 7]):
            assert sorted(p) == [5, 6, 7]


# ---------------------------------------------------------------------
# §40.3 子集 subsets (LC78)
# ---------------------------------------------------------------------
class TestSubsets:
    def _norm(self, ans):
        return sorted(sorted(s) for s in ans)

    def test_lc_example_123(self):
        ans = subsets([1, 2, 3])
        assert self._norm(ans) == self._norm(
            [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]
        )

    def test_count(self):
        # n 个元素 -> 2^n 个子集
        assert len(subsets([1, 2, 3])) == 8
        assert len(subsets([1, 2, 3, 4])) == 16

    def test_contains_empty(self):
        assert [] in subsets([1, 2])

    def test_contains_full(self):
        assert [1, 2] in [sorted(s) for s in subsets([1, 2])]

    def test_single(self):
        ans = subsets([0])
        assert self._norm(ans) == self._norm([[], [0]])

    def test_empty_input(self):
        assert subsets([]) == [[]]

    def test_all_distinct(self):
        ans = subsets([1, 2, 3])
        keys = {"#".join(map(str, sorted(s))) for s in ans}
        assert len(keys) == len(ans)


# ---------------------------------------------------------------------
# §40.4 组合总和 combination_sum (LC39)
# ---------------------------------------------------------------------
class TestCombinationSum:
    def _norm(self, ans):
        return sorted(sorted(c) for c in ans)

    def test_lc_example_1(self):
        # [2,3,6,7], target=7 -> [[2,2,3],[7]]
        ans = combination_sum([2, 3, 6, 7], 7)
        assert self._norm(ans) == self._norm([[2, 2, 3], [7]])

    def test_lc_example_2(self):
        # [2,3,5], target=8 -> [[2,2,2,2],[2,3,3],[3,5]]
        ans = combination_sum([2, 3, 5], 8)
        assert self._norm(ans) == self._norm([[2, 2, 2, 2], [2, 3, 3], [3, 5]])

    def test_lc_example_3(self):
        # [2], target=1 -> [] (凑不出)
        assert combination_sum([2], 1) == []

    def test_target_zero(self):
        # target=0 -> 唯一组合:空集
        assert combination_sum([2, 3], 0) == [[]]

    def test_unreachable(self):
        assert combination_sum([3, 6], 1) == []
        assert combination_sum([3, 6], 2) == []
        assert combination_sum([3, 6], 4) == []
        assert combination_sum([3, 6], 5) == []

    def test_reuse_allowed(self):
        # 同一元素可无限次用:用 [1] 凑 4 -> [[1,1,1,1]]
        ans = combination_sum([1], 4)
        assert self._norm(ans) == self._norm([[1, 1, 1, 1]])

    def test_all_combos_valid(self):
        candidates, target = [2, 3, 5], 8
        for combo in combination_sum(candidates, target):
            assert sum(combo) == target
            for x in combo:
                assert x in candidates


# ---------------------------------------------------------------------
# §40.5 买卖股票 max_profit (LC121)
# ---------------------------------------------------------------------
class TestMaxProfit:
    def test_lc_example_1(self):
        # [7,1,5,3,6,4] -> 5 (2 块买 6 块卖)
        assert max_profit([7, 1, 5, 3, 6, 4]) == 5

    def test_lc_example_2(self):
        # 一直跌,没法赚钱 -> 0
        assert max_profit([7, 6, 4, 3, 1]) == 0

    def test_empty(self):
        assert max_profit([]) == 0

    def test_single(self):
        assert max_profit([5]) == 0

    def test_two_profit(self):
        assert max_profit([1, 5]) == 4

    def test_two_no_profit(self):
        assert max_profit([5, 1]) == 0

    def test_monotonic_up(self):
        # 全程涨,最低点买、最高点卖
        assert max_profit([1, 2, 3, 4, 5]) == 4

    def test_valley_peak(self):
        # 经典 V 形:8 块买 11 块卖 = 3
        assert max_profit([3, 2, 6, 5, 0, 3]) == 4

    def test_never_negative(self):
        assert max_profit([5, 5, 5, 5]) == 0


# ---------------------------------------------------------------------
# §40.6 跳跃游戏 can_jump (LC55)
# ---------------------------------------------------------------------
class TestCanJump:
    def test_lc_example_true(self):
        # [2,3,1,1,4] -> True
        assert can_jump([2, 3, 1, 1, 4]) is True

    def test_lc_example_false(self):
        # [3,2,1,0,4] -> False (卡在 0)
        assert can_jump([3, 2, 1, 0, 4]) is False

    def test_single_zero(self):
        # [0]:已经在末尾,0 步可达 -> True
        assert can_jump([0]) is True

    def test_single_positive(self):
        assert can_jump([5]) is True

    def test_empty(self):
        # 空数组:已在末尾
        assert can_jump([]) is True

    def test_zeros_in_middle_passable(self):
        # [2,0,0]:0->1(跳 1)->2(跳 1)->末尾 -> True
        assert can_jump([2, 0, 0]) is True

    def test_zero_at_start_blocks(self):
        # [0,1]:第一步就必须跳 0 步,到不了 -> False(但 len=1 已特例)
        assert can_jump([0, 1]) is False

    def test_just_enough(self):
        # 每步刚好够
        assert can_jump([1, 1, 1, 1]) is True

    def test_big_first_jump(self):
        # 第一步就能跳到底
        assert can_jump([10, 0, 0, 0, 0, 0]) is True

    def test_blocked_far(self):
        # 中间有个 0 且之前的最远只能到这里
        assert can_jump([1, 0, 1, 0]) is False
