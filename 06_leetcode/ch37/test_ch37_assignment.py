"""
Ch37 作业测试。运行: uv run pytest 06_leetcode/ch37/test_ch37_assignment.py -v
"""
import pytest

from ch37_assignment import (
    MinStack,
    daily_temperatures,
    is_valid_parens,
    trap,
)


# ---------- LC20 is_valid_parens ----------
class TestIsValidParens:
    def test_simple_pair(self):
        assert is_valid_parens("()") is True

    def test_multi_pairs(self):
        assert is_valid_parens("()[]{}") is True

    def test_nested(self):
        assert is_valid_parens("{[]}") is True

    def test_mismatch(self):
        assert is_valid_parens("(]") is False

    def test_cross_invalid(self):
        # ([)] —— 交叉,栈顺序不对
        assert is_valid_parens("([)]") is False

    def test_empty_is_valid(self):
        assert is_valid_parens("") is True

    def test_single_open_invalid(self):
        assert is_valid_parens("(") is False

    def test_single_close_invalid(self):
        assert is_valid_parens(")") is False

    def test_unclosed(self):
        assert is_valid_parens("(()") is False

    def test_deeply_nested(self):
        assert is_valid_parens("(((())))") is True

    def test_mixed_nested(self):
        assert is_valid_parens("([{}])") is True


# ---------- LC155 MinStack ----------
class TestMinStack:
    def test_leetcode_example(self):
        ms = MinStack()
        ms.push(-2)
        ms.push(0)
        ms.push(-3)
        assert ms.get_min() == -3
        ms.pop()
        assert ms.top() == 0
        assert ms.get_min() == -2

    def test_min_updates_after_pop(self):
        ms = MinStack()
        ms.push(5)
        ms.push(3)
        ms.push(4)
        assert ms.get_min() == 3
        ms.pop()  # 弹掉 4,min 还是 3
        assert ms.get_min() == 3
        ms.pop()  # 弹掉 3,min 回到 5
        assert ms.get_min() == 5

    def test_duplicate_min(self):
        # 多个相同最小值,弹一个 min 不应变
        ms = MinStack()
        ms.push(2)
        ms.push(2)
        ms.push(1)
        ms.push(1)
        assert ms.get_min() == 1
        ms.pop()
        assert ms.get_min() == 1
        ms.pop()
        assert ms.get_min() == 2

    def test_single_element(self):
        ms = MinStack()
        ms.push(42)
        assert ms.top() == 42
        assert ms.get_min() == 42

    def test_push_ascending(self):
        ms = MinStack()
        for v in [1, 2, 3, 4]:
            ms.push(v)
        assert ms.get_min() == 1
        assert ms.top() == 4

    def test_push_descending(self):
        ms = MinStack()
        for v in [4, 3, 2, 1]:
            ms.push(v)
        assert ms.get_min() == 1
        ms.pop()
        assert ms.get_min() == 2

    def test_negative_values(self):
        ms = MinStack()
        ms.push(-1)
        ms.push(-5)
        ms.push(-3)
        assert ms.get_min() == -5
        ms.pop()
        assert ms.get_min() == -5
        ms.pop()
        assert ms.get_min() == -1


# ---------- LC739 daily_temperatures ----------
class TestDailyTemperatures:
    def test_leetcode_example_1(self):
        assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]

    def test_leetcode_example_2(self):
        assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]

    def test_leetcode_example_3(self):
        assert daily_temperatures([30, 60, 90]) == [1, 1, 0]

    def test_single(self):
        assert daily_temperatures([30]) == [0]

    def test_empty(self):
        assert daily_temperatures([]) == []

    def test_descending_all_zero(self):
        # 递减,没人有更高温
        assert daily_temperatures([90, 80, 70, 60]) == [0, 0, 0, 0]

    def test_all_equal(self):
        assert daily_temperatures([50, 50, 50]) == [0, 0, 0]

    def test_plateau_then_higher(self):
        assert daily_temperatures([70, 70, 70, 80]) == [3, 2, 1, 0]


# ---------- LC42 trap ----------
class TestTrap:
    def test_leetcode_example_1(self):
        assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6

    def test_leetcode_example_2(self):
        assert trap([4, 2, 0, 3, 2, 5]) == 9

    def test_empty(self):
        assert trap([]) == 0

    def test_single(self):
        assert trap([1]) == 0

    def test_two_no_trap(self):
        assert trap([2, 1]) == 0
        assert trap([1, 2]) == 0

    def test_ascending_no_trap(self):
        # 单调上升,接不住水
        assert trap([1, 2, 3, 4, 5]) == 0

    def test_descending_no_trap(self):
        # 单调下降,接不住水
        assert trap([5, 4, 3, 2, 1]) == 0

    def test_valley(self):
        # 经典凹槽:两边高,中间凹。中间一列高 0,水位 min(3,3)-0 = 3
        assert trap([3, 0, 3]) == 3

    def test_all_zero(self):
        assert trap([0, 0, 0]) == 0

    def test_deep_valley(self):
        # 5 _ _ _ _ 5 -> 4 列每列水位 5
        assert trap([5, 0, 0, 0, 0, 5]) == 20
