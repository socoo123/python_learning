"""
Ch04 作业测试。运行: uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v
"""
import pytest

from ch04_assignment import (
    apply_twice,
    make_multiplier,
    sum_prices,
    build_product,
    count_calls,
    retry,
    memoize,
)


# ---------- apply_twice:函数是一等公民 ----------
class TestApplyTwice:
    def test_add_three_twice(self):
        # (10 + 3) + 3 = 16
        assert apply_twice(lambda x: x + 3, 10) == 16

    def test_square_twice(self):
        # square(square(2)) = square(4) = 16
        assert apply_twice(lambda x: x * x, 2) == 16

    def test_with_named_function(self):
        def negate(n):
            return -n
        # negate(negate(5)) = negate(-5) = 5
        assert apply_twice(negate, 5) == 5


# ---------- make_multiplier:闭包 ----------
class TestMakeMultiplier:
    def test_triple(self):
        triple = make_multiplier(3)
        assert triple(5) == 15

    def test_doubler(self):
        doubler = make_multiplier(2)
        assert doubler(10) == 20

    def test_each_closure_independent(self):
        # 两次调用造出独立的闭包,各记各的 factor
        assert make_multiplier(4)(2) == 8
        assert make_multiplier(10)(3) == 30

    def test_returned_is_callable(self):
        assert callable(make_multiplier(1))


# ---------- sum_prices:*args ----------
class TestSumPrices:
    def test_no_args_returns_zero(self):
        assert sum_prices() == 0

    def test_three_prices(self):
        assert sum_prices(599.0, 129.0, 99.0) == 827.0

    def test_single(self):
        assert sum_prices(42) == 42


# ---------- build_product:**kwargs ----------
class TestBuildProduct:
    def test_with_fields(self):
        p = build_product("机械键盘", price=599.0, stock=120)
        assert p == {"name": "机械键盘", "price": 599.0, "stock": 120}

    def test_only_name(self):
        assert build_product("鼠标") == {"name": "鼠标"}

    def test_arbitrary_kwargs(self):
        p = build_product("X", category="电脑外设", sku="X-001", stock=10)
        assert p["category"] == "电脑外设"
        assert p["sku"] == "X-001"


# ---------- count_calls:装饰器基础 ----------
class TestCountCalls:
    def test_counts_three(self):
        @count_calls
        def greet(name):
            return f"hi {name}"
        greet("a"); greet("b"); greet("c")
        assert greet.call_count == 3

    def test_preserves_return_value(self):
        @count_calls
        def add(a, b):
            return a + b
        assert add(1, 2) == 3
        assert add.call_count == 1

    def test_wraps_preserves_name(self):
        @count_calls
        def my_func(x):
            """my doc"""
            return x
        # functools.wraps 让 wrapper 冒充原函数
        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "my doc"

    def test_starts_at_zero(self):
        @count_calls
        def f():
            return 1
        assert f.call_count == 0


# ---------- retry:带参数的装饰器 ----------
class TestRetry:
    def test_succeeds_first_try(self):
        calls = []

        @retry(times=3)
        def f():
            calls.append(1)
            return "ok"
        assert f() == "ok"
        assert len(calls) == 1

    def test_retries_then_succeeds(self):
        calls = []

        @retry(times=3)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("transient")
            return "ok"
        assert flaky() == "ok"
        assert len(calls) == 3

    def test_all_attempts_fail_raises_last(self):
        calls = []

        @retry(times=2)
        def always_fail():
            calls.append(1)
            raise RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            always_fail()
        assert len(calls) == 2


# ---------- memoize:缓存装饰器 ----------
class TestMemoize:
    def test_caches_repeated_call(self):
        evals = {"n": 0}

        @memoize
        def slow_square(x):
            evals["n"] += 1
            return x * x
        assert slow_square(4) == 16
        assert slow_square(4) == 16   # 第二次走缓存
        assert evals["n"] == 1         # 函数体只执行过一次

    def test_different_args_independent(self):
        evals = {"n": 0}

        @memoize
        def f(x):
            evals["n"] += 1
            return x
        f(1); f(2); f(1)
        assert evals["n"] == 2   # f(1) 第二次命中缓存

    def test_miss_count_attribute(self):
        @memoize
        def f(x):
            return x * 2
        f(1); f(1); f(2)
        assert f.miss_count == 2   # 1 和 2 各 miss 一次

    def test_wraps_preserves_name(self):
        @memoize
        def fib(n):
            return n
        assert fib.__name__ == "fib"
