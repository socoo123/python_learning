"""
Ch07 作业测试。运行: uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v

注意:类型注解运行时不强制,真正的类型检查靠 mypy(见 tutorial §7.10)。
这里的测试验证【行为】+【运行时可检查的部分】(注解存在性、Protocol 的 isinstance、
Generic 的参数化能力)。
"""
import pytest

from ch07_assignment import (
    format_price,
    find_product,
    apply_discount,
    make_named_protocol,
    first_or_none,
    make_page_class,
    order_amount,
    extract_discount_rate,
    build_reconciliation_rows,
)


# ---------- §7.1 format_price:类型注解基础 ----------
class TestFormatPrice:
    def test_default_currency(self):
        assert format_price(599.0) == "¥599.00"

    def test_custom_currency(self):
        assert format_price(75.5, currency="$") == "$75.50"

    def test_zero_boundary(self):
        assert format_price(0) == "¥0.00"

    def test_rounds_to_two_decimals(self):
        # 第三位小数必须被格式化处理(拦住只做拼字符串的实现)
        assert format_price(75.556) == "¥75.56"

    def test_has_type_annotations(self):
        # 本章的核心任务就是补注解;注解运行时可查(存于 __annotations__)
        ann = format_price.__annotations__
        assert "amount" in ann
        assert "return" in ann


# ---------- §7.2 find_product:联合类型 dict | None ----------
class TestFindProduct:
    def test_found(self, products):
        p = find_product(products, "KB-001")
        assert p is not None
        assert p["name"] == "机械键盘"
        assert p["price"] == 599.0

    def test_found_another(self, products):
        p = find_product(products, "BK-005")
        assert p is not None
        assert p["name"] == "设计模式"

    def test_not_found_returns_none(self, products):
        assert find_product(products, "NOPE") is None

    def test_empty_list_returns_none(self):
        assert find_product([], "KB-001") is None

    def test_has_return_annotation(self):
        assert "return" in find_product.__annotations__


# ---------- §7.3 apply_discount:Callable 类型 ----------
class TestApplyDiscount:
    def test_lambda_strategy(self):
        assert apply_discount(599.0, lambda p: p * 0.8) == 479.2

    def test_subtract_strategy(self):
        assert apply_discount(599.0, lambda p: p - 50) == 549.0

    def test_named_function_strategy(self):
        def member_price(p):
            return p * 0.7

        assert apply_discount(599.0, member_price) == 419.3

    def test_result_rounded_to_two_decimals(self):
        # 100 * 0.333 = 33.300000000000004,必须 round 掉(拦住没 round 的实现)
        assert apply_discount(100, lambda p: p * 0.333) == 33.3

    def test_zero_amount(self):
        assert apply_discount(0, lambda p: p * 0.8) == 0.0

    def test_strategy_has_callable_annotation(self):
        assert "strategy" in apply_discount.__annotations__


# ---------- §7.4 make_named_protocol:Protocol ----------
class TestMakeNamedProtocol:
    def test_returns_a_class(self):
        Named = make_named_protocol()
        assert isinstance(Named, type)

    def test_is_actually_protocol(self):
        # 拦住「随便写个普通 class」的实现:Protocol 子类带有 _is_protocol 标记
        Named = make_named_protocol()
        assert getattr(Named, "_is_protocol", False) is True

    def test_runtime_isinstance_structural(self):
        # @runtime_checkable 让 isinstance 做运行时结构检查(没加会抛 TypeError)
        Named = make_named_protocol()

        class Cat:
            name = "Tom"

        class Rock:
            pass

        assert isinstance(Cat(), Named)       # 有 name → 结构化匹配
        assert not isinstance(Rock(), Named)  # 没 name → 不匹配

    def test_instance_attribute_also_matches(self):
        # 结构检查看的是「对象有没有 name」,类属性/实例属性都算
        Named = make_named_protocol()

        class Agent:
            def __init__(self, name):
                self.name = name

        assert isinstance(Agent("小芳"), Named)

    def test_usable_as_annotation(self):
        # Protocol 的真正用途:当注解用,鸭子传参
        Named = make_named_protocol()

        def get_name(obj: Named) -> str:
            return obj.name

        class Shop:
            name = "官方旗舰店"

        assert get_name(Shop()) == "官方旗舰店"


# ---------- §7.5 first_or_none:TypeVar 泛型函数 ----------
class TestFirstOrNone:
    def test_strings(self):
        assert first_or_none(["CP-009", "MN-003"]) == "CP-009"

    def test_ints(self):
        assert first_or_none([599, 159]) == 599

    def test_empty_returns_none(self):
        assert first_or_none([]) is None

    def test_falsy_first_element_returned_as_is(self):
        # 拦住 `return items[0] or None` 这类假值翻车实现
        assert first_or_none([0, False]) == 0

    def test_has_generic_annotations(self):
        ann = first_or_none.__annotations__
        assert "items" in ann
        assert "return" in ann


# ---------- §7.6 make_page_class:Generic 泛型类 ----------
class TestMakePageClass:
    def test_returns_a_class(self):
        Page = make_page_class()
        assert isinstance(Page, type)

    def test_fields_and_page_count(self):
        Page = make_page_class()
        p = Page(items=["a", "b"], total=7, page=2)
        assert p.items == ["a", "b"]
        assert p.total == 7
        assert p.page == 2
        assert p.page_count(3) == 3  # 7 条每页 3 条 → 3 页(ceil)

    def test_page_count_exact_division(self):
        # 拦住 `total // size + 1` 的偷懒实现(整除时多算一页)
        Page = make_page_class()
        assert Page(items=[], total=6).page_count(3) == 2

    def test_page_defaults_to_one(self):
        Page = make_page_class()
        assert Page(items=[], total=0).page == 1

    def test_zero_total_zero_pages(self):
        Page = make_page_class()
        assert Page(items=[], total=0).page_count(5) == 0

    def test_subscriptable_generic(self):
        # 拦住「忘写 (Generic[T])」:普通类 Page[str] 会抛 TypeError
        Page = make_page_class()
        p = Page[str](items=["x"], total=1)
        assert p.items == ["x"]


# ---------- §7.7 order_amount:TypedDict ----------
class TestOrderAmount:
    def test_basic(self):
        order = {"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5}
        assert order_amount(order) == 119.0

    def test_rounding(self):
        # 3 * 19.9 = 59.699999...,必须 round 成 59.7
        order = {"id": "A002", "sku": "BK-005", "qty": 3, "unit_price": 19.9}
        assert order_amount(order) == 59.7

    def test_zero_qty(self):
        order = {"id": "A003", "sku": "X", "qty": 0, "unit_price": 999.0}
        assert order_amount(order) == 0.0

    def test_has_order_annotation(self):
        assert "order" in order_amount.__annotations__


# ---------- §7.8 extract_discount_rate:EAFP ----------
class TestExtractDiscountRate:
    def test_normal_rate(self):
        assert extract_discount_rate({"promo": {"rate": 0.15}}) == 0.15

    def test_numeric_string_rate(self):
        # float() 兼容数字字符串(营销系统常把数字存成字符串)
        assert extract_discount_rate({"promo": {"rate": "0.2"}}) == 0.2

    def test_missing_promo_key(self):
        assert extract_discount_rate({}) == 0.0

    def test_promo_is_none(self):
        # None["rate"] 是 TypeError,不是 KeyError——EAFP 要捕全
        assert extract_discount_rate({"promo": None}) == 0.0

    def test_rate_key_missing(self):
        assert extract_discount_rate({"promo": {}}) == 0.0

    def test_rate_not_a_number(self):
        assert extract_discount_rate({"promo": {"rate": "abc"}}) == 0.0

    def test_has_payload_annotation(self):
        assert "payload" in extract_discount_rate.__annotations__


# ---------- §7.9 build_reconciliation_rows:综合流水线 ----------
class TestBuildReconciliationRows:
    ORDERS = [
        {"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5},
        {"id": "A002", "sku": "BK-005", "qty": 1, "unit_price": 75.5},
    ]

    def test_with_discount_strategy(self):
        rows = build_reconciliation_rows(self.ORDERS, lambda a: a * 0.9)
        assert rows == ["A001: ¥107.10", "A002: ¥67.95"]

    def test_with_identity_strategy(self):
        rows = build_reconciliation_rows(self.ORDERS, lambda a: a)
        assert rows == ["A001: ¥119.00", "A002: ¥75.50"]

    def test_empty_orders(self):
        assert build_reconciliation_rows([], lambda a: a * 0.9) == []

    def test_has_annotations(self):
        ann = build_reconciliation_rows.__annotations__
        assert "orders" in ann
        assert "strategy" in ann
        assert "return" in ann
