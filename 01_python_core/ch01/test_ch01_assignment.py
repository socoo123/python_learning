"""
Ch01 作业测试。
运行: pytest 01_python_core/ch01/test_ch01_assignment.py -v

测试用例按函数分组(class)。你写完 ch01_assignment.py 后,这里应该全绿。
"""
from ch01_assignment import (
    add,
    swap,
    greet,
    first_or_default,
    describe,
    load_product_names,
)


# ---------- add:动态类型 + 类型注解 ----------
class TestAdd:
    def test_basic(self):
        assert add(1, 2) == 3

    def test_negative(self):
        assert add(-5, 3) == -2

    def test_zero(self):
        assert add(0, 0) == 0

    def test_large_number(self):
        # Python 整数无溢出(对比 Java int 会溢出)
        assert add(10**18, 10**18) == 2 * 10**18


# ---------- swap:元组解包 ----------
class TestSwap:
    def test_ints(self):
        assert swap(1, 2) == (2, 1)

    def test_strings(self):
        assert swap("a", "b") == ("b", "a")

    def test_returns_tuple(self):
        assert isinstance(swap(1, 2), tuple)


# ---------- greet:默认参数 + f-string ----------
class TestGreet:
    def test_default_greeting(self):
        assert greet("Alice") == "Hello, Alice!"

    def test_custom_greeting_positional(self):
        assert greet("Bob", "Hi") == "Hi, Bob!"

    def test_times_repeat_newline_separated(self):
        assert greet("Carl", times=3) == "Hello, Carl!\nHello, Carl!\nHello, Carl!"

    def test_times_one(self):
        assert greet("Dan", times=1) == "Hello, Dan!"


# ---------- first_or_default:truthiness 判空 ----------
class TestFirstOrDefault:
    def test_normal(self):
        assert first_or_default([1, 2, 3]) == 1

    def test_empty_with_default(self):
        assert first_or_default([], "empty") == "empty"

    def test_empty_no_default_returns_none(self):
        # 注意 None 要用 is 判断
        assert first_or_default([]) is None

    def test_empty_keyword_default(self):
        assert first_or_default([], default=99) == 99


# ---------- describe:一切皆对象 ----------
class TestDescribe:
    def test_int(self):
        assert describe(42) == "42 is a int"

    def test_str(self):
        # repr("hi") 带引号
        assert describe("hi") == "'hi' is a str"

    def test_list(self):
        assert describe([1, 2]) == "[1, 2] is a list"

    def test_float(self):
        assert describe(3.14) == "3.14 is a float"


# ---------- load_product_names:工作流验证 ----------
class TestLoadProductNames:
    def test_returns_list_of_10(self):
        names = load_product_names()
        assert isinstance(names, list)
        assert len(names) == 10

    def test_first_name(self):
        assert load_product_names()[0] == "机械键盘"

    def test_all_are_strings(self):
        names = load_product_names()
        assert all(isinstance(n, str) for n in names)

    def test_contains_expected_product(self):
        assert "人体工学椅" in load_product_names()
