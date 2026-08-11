"""
Ch04 作业测试。
运行: uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v

测试用例按函数分组(class)。
products fixture 来自项目根 conftest.py(10 个商品,function 级隔离)。
断言期望值均已手工验算;spy 函数 / 独立闭包 / 串账检查用于防硬编码蒙对。
"""
import pytest

from ch04_assignment import (
    apply_discount,
    make_coupon,
    cart_total,
    build_response,
    count_calls,
    timer,
    retry,
    memoize,
)


# ---------- §4.1 apply_discount:函数是一等公民 ----------
class TestApplyDiscount:
    def test_lambda_half_off(self):
        assert apply_discount([100.0, 200.0], lambda p: p * 0.5) == [50.0, 100.0]

    def test_lambda_minus_20(self):
        assert apply_discount([100.0, 200.0], lambda p: max(p - 20, 0)) == [80.0, 180.0]

    def test_with_named_function(self):
        # 普通 def 函数和 lambda 一样能传——函数就是对象
        def minus_20(p):
            return max(p - 20, 0)
        assert apply_discount([599.0, 15.0], minus_20) == [579.0, 0]

    def test_every_price_passes_through_fn(self):
        # spy:拦住「不调 fn」或「只对部分元素应用」的实现
        seen = []

        def spy(p):
            seen.append(p)
            return p - 1
        assert apply_discount([10.0, 20.0, 30.0], spy) == [9.0, 19.0, 29.0]
        assert seen == [10.0, 20.0, 30.0]

    def test_returns_new_list_not_alias(self):
        # 拦住「直接 return prices」:必须返回新列表
        prices = [100.0, 200.0]
        result = apply_discount(prices, lambda p: p)
        assert result == prices
        assert result is not prices

    def test_empty_list(self):
        assert apply_discount([], lambda p: p * 0.5) == []

    def test_with_products_fixture(self, products):
        prices = [p["price"] for p in products]
        half = apply_discount(prices, lambda p: p * 0.5)
        assert half[0] == 299.5     # 机械键盘 599.0 半价
        assert len(half) == 10


# ---------- §4.2 make_coupon:闭包 ----------
class TestMakeCoupon:
    def test_full_reduction(self):
        coupon = make_coupon(200, 30)
        assert coupon(599.0) == 569.0

    def test_below_threshold_unchanged(self):
        coupon = make_coupon(200, 30)
        assert coupon(150.0) == 150.0

    def test_exact_threshold_reduced(self):
        # 拦住把 >= 写成 > 的实现:满 200 含 200
        coupon = make_coupon(200, 30)
        assert coupon(200.0) == 170.0

    def test_each_coupon_independent(self):
        # 每个闭包各记各的 threshold/off,互不干扰
        c1 = make_coupon(200, 30)
        c2 = make_coupon(500, 80)
        assert c1(600.0) == 570.0
        assert c2(600.0) == 520.0

    def test_returned_is_callable(self):
        # 拦住「return coupon()」:返回的必须是函数
        assert callable(make_coupon(100, 10))


# ---------- §4.3 cart_total:*args ----------
class TestCartTotal:
    def test_three_items(self):
        assert cart_total(599.0, 159.0, 75.5) == 833.5

    def test_no_args_returns_zero(self):
        assert cart_total() == 0

    def test_single_item(self):
        assert cart_total(199.0) == 199.0

    def test_unpack_list_at_call_site(self):
        # 调用处 * 打散:列表 → 一个个位置参数
        prices = [599.0, 159.0]
        assert cart_total(*prices) == 758.0

    def test_ints_and_floats_mixed(self):
        assert cart_total(1, 2.5, 3) == 6.5


# ---------- §4.3 build_response:**kwargs ----------
class TestBuildResponse:
    def test_wraps_data_with_meta(self):
        resp = build_response(["机械键盘", "无线鼠标"], total=10, page=1)
        assert resp == {"ok": True, "data": ["机械键盘", "无线鼠标"], "total": 10, "page": 1}

    def test_no_meta(self):
        assert build_response("pong") == {"ok": True, "data": "pong"}

    def test_meta_keys_spread_to_top_level(self):
        # 拦住「嵌套成 {"meta": {...}}」的实现:meta 必须展开铺平
        resp = build_response(None, sku="KB-001", cached=True)
        assert resp["sku"] == "KB-001"
        assert resp["cached"] is True
        assert "meta" not in resp

    def test_data_can_be_any_type(self, products):
        resp = build_response(products, total=len(products))
        assert resp["data"][0]["name"] == "机械键盘"
        assert resp["total"] == 10

    def test_each_call_returns_fresh_dict(self):
        r1 = build_response([], page=1)
        r2 = build_response([], page=2)
        assert r1 is not r2
        assert r1["page"] == 1 and r2["page"] == 2


# ---------- §4.4 count_calls:装饰器基础 ----------
class TestCountCalls:
    def test_counts_calls(self):
        @count_calls
        def query_price(sku):
            return 599.0
        query_price("KB-001"); query_price("MS-002"); query_price("KB-001")
        assert query_price.call_count == 3

    def test_preserves_return_value(self):
        @count_calls
        def add(a, b):
            return a + b
        assert add(1, 2) == 3
        assert add.call_count == 1

    def test_wraps_preserves_name_and_doc(self):
        @count_calls
        def query_stock(sku):
            """查库存"""
            return 120
        # functools.wraps 让 wrapper 冒充原函数
        assert query_stock.__name__ == "query_stock"
        assert query_stock.__doc__ == "查库存"

    def test_starts_at_zero(self):
        @count_calls
        def f():
            return 1
        assert f.call_count == 0

    def test_each_decorated_function_independent(self):
        # 两个被装饰函数各有独立计数器(函数属性挂在各自 wrapper 上)
        @count_calls
        def f():
            return 1

        @count_calls
        def g():
            return 2
        f(); f(); g()
        assert f.call_count == 2
        assert g.call_count == 1


# ---------- §4.4 timer:装饰器记录耗时 ----------
class TestTimer:
    def test_preserves_return_value(self):
        @timer
        def query_stock(sku):
            return 120
        assert query_stock("KB-001") == 120

    def test_records_one_entry_per_call(self):
        @timer
        def f(x):
            return x
        assert f.records == []      # 初始空列表
        f(1); f(2)
        assert len(f.records) == 2

    def test_records_are_non_negative_floats(self):
        @timer
        def f():
            return 1
        f(); f(); f()
        assert all(isinstance(r, float) and r >= 0 for r in f.records)

    def test_works_with_args_and_kwargs(self):
        # wrapper 通用签名:位置参数 + 关键字参数都要能转发
        @timer
        def greet(name, punct="!"):
            return f"hi {name}{punct}"
        assert greet("键盘", punct="。") == "hi 键盘。"
        assert len(greet.records) == 1

    def test_wraps_preserves_name(self):
        @timer
        def slow_query():
            return "done"
        assert slow_query.__name__ == "slow_query"


# ---------- §4.5 retry:带参数的装饰器 ----------
class TestRetry:
    def test_succeeds_first_try(self):
        calls = []

        @retry(times=3)
        def pay(order_id):
            calls.append(order_id)
            return "paid"
        assert pay("A001") == "paid"
        assert calls == ["A001"]            # 一次成功,绝不多试

    def test_retries_then_succeeds(self):
        calls = []

        @retry(times=3)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("网关抖动")
            return "paid"
        assert flaky() == "paid"
        assert len(calls) == 3

    def test_all_attempts_fail_raises_last(self):
        calls = []

        @retry(times=2)
        def always_fail():
            calls.append(1)
            raise RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            always_fail()
        assert len(calls) == 2              # 恰好 times 次,不多不少

    def test_raises_last_exception_when_different(self):
        # 拦住「抛第一次异常」的实现:必须抛【最后一次】
        attempts = []

        @retry(times=2)
        def fail_differently():
            attempts.append(1)
            if len(attempts) == 1:
                raise ValueError("第一次")
            raise RuntimeError("最后一次")
        with pytest.raises(RuntimeError, match="最后一次"):
            fail_differently()

    def test_retries_reset_between_calls(self):
        # 每次调用独立计数:上一次失败不影响下一次
        state = {"fail": True}

        @retry(times=2)
        def sometimes():
            if state["fail"]:
                state["fail"] = False
                raise ValueError("x")
            return "ok"
        assert sometimes() == "ok"      # 第一次调用:失败 1 次后成功
        assert sometimes() == "ok"      # 第二次调用:直接成功

    def test_wraps_preserves_name(self):
        @retry(times=3)
        def call_gateway():
            return "ok"
        assert call_gateway.__name__ == "call_gateway"


# ---------- §4.6 memoize:缓存装饰器 ----------
class TestMemoize:
    def test_caches_repeated_call(self):
        evals = {"n": 0}

        @memoize
        def get_exchange_rate(currency):
            evals["n"] += 1
            return 7.2
        assert get_exchange_rate("USD") == 7.2
        assert get_exchange_rate("USD") == 7.2
        assert evals["n"] == 1              # 函数体只执行过一次

    def test_different_args_independent(self):
        evals = {"n": 0}

        @memoize
        def rate(currency):
            evals["n"] += 1
            return {"USD": 7.2, "JPY": 0.05}[currency]
        rate("USD"); rate("JPY"); rate("USD")
        assert evals["n"] == 2              # USD 第二次命中缓存

    def test_miss_count_attribute(self):
        @memoize
        def f(x):
            return x * 2
        f(1); f(1); f(2)
        assert f.miss_count == 2            # 1 和 2 各 miss 一次

    def test_separate_functions_have_separate_caches(self):
        # 拦住「cache 放模块全局」的实现:每个被装饰函数一本独立缓存
        @memoize
        def f(x):
            return x + 1

        @memoize
        def g(x):
            return x * 10
        f(1); g(1)
        assert f.miss_count == 1
        assert g.miss_count == 1
        # 串账的话 g(1) 会错误命中 f 的缓存返回 2
        assert f(1) == 2 and g(1) == 10

    def test_wraps_preserves_name(self):
        @memoize
        def get_exchange_rate(currency):
            """查汇率"""
            return 7.2
        assert get_exchange_rate.__name__ == "get_exchange_rate"
