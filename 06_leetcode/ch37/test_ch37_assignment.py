"""
Ch37 作业测试。运行: uv run pytest 06_leetcode/ch37/test_ch37_assignment.py -v
"""

from ch37_assignment import (
    daily_temperatures,
    eval_rpn,
    is_valid_parens,
    make_min_stack_class,
    make_my_queue_class,
    remove_adjacent_duplicates,
    trap,
)


# ---------- §37.2 LC20 is_valid_parens ----------
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
        # 拦「忘查栈空」:走完栈非空必须 False
        assert is_valid_parens("(()") is False

    def test_deeply_nested(self):
        assert is_valid_parens("(((())))") is True

    def test_mixed_nested(self):
        assert is_valid_parens("([{}])") is True


# ---------- §37.3 LC1047 remove_adjacent_duplicates ----------
class TestRemoveAdjacentDuplicates:
    def test_leetcode_example_1(self):
        # abbaca -> (删 bb) aaca -> (删 aa) ca
        assert remove_adjacent_duplicates("abbaca") == "ca"

    def test_leetcode_example_2(self):
        assert remove_adjacent_duplicates("azxxzy") == "ay"

    def test_empty(self):
        assert remove_adjacent_duplicates("") == ""

    def test_single_char(self):
        assert remove_adjacent_duplicates("a") == "a"

    def test_no_duplicates(self):
        assert remove_adjacent_duplicates("abcba") == "abcba"

    def test_all_cancel_out(self):
        # 连续两对:aabb -> 全消
        assert remove_adjacent_duplicates("aabb") == ""

    def test_cascade(self):
        # 拦「只消一轮不再查」:删 bb 后 aa 成新邻居,还要再消
        assert remove_adjacent_duplicates("abba") == ""

    def test_prefix_leftover(self):
        assert remove_adjacent_duplicates("aab") == "b"


# ---------- §37.4 LC150 eval_rpn ----------
class TestEvalRpn:
    def test_leetcode_example_1(self):
        assert eval_rpn(["2", "1", "+", "3", "*"]) == 9

    def test_leetcode_example_2(self):
        assert eval_rpn(["4", "13", "5", "/", "+"]) == 6

    def test_leetcode_example_3(self):
        tokens = ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]
        assert eval_rpn(tokens) == 22

    def test_single_number(self):
        assert eval_rpn(["18"]) == 0 + 18

    def test_division_truncates_toward_zero(self):
        # 拦「a // b」:6 / -132 = -0.045,向零取整 = 0;向下取整 = -1
        assert eval_rpn(["6", "-132", "/"]) == 0

    def test_negative_division_negative_result(self):
        # -7 / 2 = -3.5,向零 = -3(向下会是 -4)
        assert eval_rpn(["-7", "2", "/"]) == -3

    def test_subtraction_operand_order(self):
        # 拦「左右操作数搞反」:3 - 4 = -1,不是 4 - 3
        assert eval_rpn(["3", "4", "-"]) == -1

    def test_division_operand_order(self):
        # 12 / 4 = 3,不是 4 / 12
        assert eval_rpn(["12", "4", "/"]) == 3

    def test_negative_intermediate(self):
        # (2 - 5) * 3 = -9
        assert eval_rpn(["2", "5", "-", "3", "*"]) == -9


# ---------- §37.5 LC155 make_min_stack_class ----------
class TestMakeMinStackClass:
    def test_leetcode_example(self):
        MinStack = make_min_stack_class()
        ms = MinStack()
        ms.push(-2)
        ms.push(0)
        ms.push(-3)
        assert ms.get_min() == -3
        ms.pop()
        assert ms.top() == 0
        assert ms.get_min() == -2

    def test_min_updates_after_pop(self):
        # 拦「辅助栈不同步弹」:弹掉最小值后 min 要回退
        MinStack = make_min_stack_class()
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
        MinStack = make_min_stack_class()
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
        MinStack = make_min_stack_class()
        ms = MinStack()
        ms.push(42)
        assert ms.top() == 42
        assert ms.get_min() == 42

    def test_push_ascending(self):
        MinStack = make_min_stack_class()
        ms = MinStack()
        for v in [1, 2, 3, 4]:
            ms.push(v)
        assert ms.get_min() == 1
        assert ms.top() == 4

    def test_push_descending(self):
        MinStack = make_min_stack_class()
        ms = MinStack()
        for v in [4, 3, 2, 1]:
            ms.push(v)
        assert ms.get_min() == 1
        ms.pop()
        assert ms.get_min() == 2

    def test_negative_values(self):
        MinStack = make_min_stack_class()
        ms = MinStack()
        ms.push(-1)
        ms.push(-5)
        ms.push(-3)
        assert ms.get_min() == -5
        ms.pop()
        assert ms.get_min() == -5
        ms.pop()
        assert ms.get_min() == -1

    def test_factory_returns_fresh_classes(self):
        # 每次调用返回独立的类,互不影响
        MinStack1 = make_min_stack_class()
        MinStack2 = make_min_stack_class()
        a, b = MinStack1(), MinStack2()
        a.push(1)
        assert b.stack == [] and b.mins == []


# ---------- §37.6 LC232 make_my_queue_class ----------
class TestMakeMyQueueClass:
    def test_leetcode_example(self):
        MyQueue = make_my_queue_class()
        q = MyQueue()
        q.push(1)
        q.push(2)
        assert q.peek() == 1
        assert q.pop() == 1
        assert q.empty() is False

    def test_fifo_order(self):
        # 拦「当成栈用(LIFO)」:必须 1,2,3,4,5 顺序出
        MyQueue = make_my_queue_class()
        q = MyQueue()
        for v in [1, 2, 3, 4, 5]:
            q.push(v)
        assert [q.pop() for _ in range(5)] == [1, 2, 3, 4, 5]
        assert q.empty() is True

    def test_interleaved_push_pop(self):
        # 拦「每次 pop 都重新倒栈」:pop 后再 push,顺序不能乱
        MyQueue = make_my_queue_class()
        q = MyQueue()
        q.push(1)
        q.push(2)
        q.push(3)
        assert q.pop() == 1   # 倒栈发生在这
        q.push(4)
        assert q.pop() == 2   # out 不空,不倒;若乱倒会弹出 4
        assert q.pop() == 3
        assert q.pop() == 4
        assert q.empty() is True

    def test_single_element(self):
        MyQueue = make_my_queue_class()
        q = MyQueue()
        q.push(7)
        assert q.empty() is False
        assert q.peek() == 7
        assert q.pop() == 7
        assert q.empty() is True

    def test_peek_does_not_remove(self):
        MyQueue = make_my_queue_class()
        q = MyQueue()
        q.push(1)
        q.push(2)
        assert q.peek() == 1
        assert q.peek() == 1   # 再看还是 1,没被删
        assert q.pop() == 1
        assert q.peek() == 2


# ---------- §37.7 LC739 daily_temperatures ----------
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
        # 相等不算「更高」,全 0(拦 >= 弹出的错误实现)
        assert daily_temperatures([50, 50, 50]) == [0, 0, 0]

    def test_plateau_then_higher(self):
        assert daily_temperatures([70, 70, 70, 80]) == [3, 2, 1, 0]


# ---------- §37.8 LC42 trap ----------
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
