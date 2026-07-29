"""
Ch07 作业测试。运行: uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v

注意:类型注解运行时不强制,真正的类型检查靠 mypy(见 tutorial §7.6)。
这里的测试验证【行为】+【运行时可检查的部分】(注解存在性、Protocol 的 isinstance)。
"""
import pytest

from ch07_assignment import (
    format_price,
    find_product,
    apply_operation,
    Named,
    get_name,
    safe_get,
)


# ---------- format_price:类型注解基础 ----------
class TestFormatPrice:
    def test_basic_default_currency(self):
        assert format_price(59.5) == "¥59.50"

    def test_custom_currency(self):
        assert format_price(10, currency="$") == "$10.00"

    def test_zero(self):
        assert format_price(0) == "¥0.00"

    def test_has_type_annotations(self):
        # 类型注解运行时可查(存于 __annotations__)
        ann = format_price.__annotations__
        assert "price" in ann
        assert "return" in ann


# ---------- find_product:联合类型 dict | None ----------
class TestFindProduct:
    def test_found(self, products):
        p = find_product(products, "KB-001")
        assert p["name"] == "机械键盘"

    def test_not_found_returns_none(self, products):
        assert find_product(products, "NOPE") is None

    def test_has_return_annotation(self):
        ann = find_product.__annotations__
        assert "return" in ann


# ---------- apply_operation:Callable 类型 ----------
class TestApplyOperation:
    def test_with_lambda(self):
        assert apply_operation(lambda x: x * 2, 5) == 10

    def test_with_named_function(self):
        assert apply_operation(abs, -7) == 7

    def test_func_has_callable_annotation(self):
        ann = apply_operation.__annotations__
        assert "func" in ann


# ---------- Named Protocol:结构化类型 ----------
class TestNamedProtocol:
    def test_get_name_works(self):
        class Cat:
            name = "Tom"
        assert get_name(Cat()) == "Tom"

    def test_runtime_isinstance_satisfied(self):
        # @runtime_checkable 让 Protocol 能用 isinstance 运行时检查
        class Dog:
            name = "Rex"

        class Rock:
            pass

        assert isinstance(Dog(), Named)      # 有 name 属性 → 是 Named
        assert not isinstance(Rock(), Named)  # 没有 name 属性 → 不是

    def test_works_with_instance_attribute(self):
        class Item:
            def __init__(self, n):
                self.name = n
        assert isinstance(Item("x"), Named)
        assert get_name(Item("x")) == "x"

    def test_protocol_is_a_class(self):
        # Protocol 本身是个类(可继承的结构化接口)
        assert isinstance(Named, type)


# ---------- safe_get:EAFP 风格 ----------
class TestSafeGetEAFP:
    def test_existing_key(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_missing_returns_none(self):
        assert safe_get({"a": 1}, "b") is None

    def test_missing_returns_custom_default(self):
        assert safe_get({"a": 1}, "b", default=99) == 99

    def test_value_can_be_falsy(self):
        # EAFP 的好处:值是 0/""/False 时也能正确返回(不依赖 truthiness)
        assert safe_get({"a": 0, "b": ""}, "a") == 0
        assert safe_get({"a": 0, "b": ""}, "b") == ""
