"""
Ch05 作业测试。
运行: uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v

每题是一个「类工厂」函数:返回一个类。测试拿到类后做全套质检。
测试类之间互不依赖(每题自包含),可单独跑:pytest <本文件>::TestMakeXxxClass
断言期望值均已手工验算;products fixture 来自项目根 conftest.py。
"""
import pytest

from ch05_assignment import (
    make_product_class,
    make_order_class,
    make_inventory_class,
    make_price_list_class,
    make_money_class,
    make_discount_cart_class,
    make_checkout_class,
)


# ---------- §5.1 make_product_class:类基础 + @dataclass ----------
class TestMakeProductClass:
    def test_returns_a_class(self):
        # 拦「返回实例」或「返回字典」:必须是类本身
        Product = make_product_class()
        assert isinstance(Product, type)

    def test_positional_and_keyword_create(self):
        Product = make_product_class()
        p = Product("机械键盘", 599.0, 10)
        assert (p.name, p.price, p.stock) == ("机械键盘", 599.0, 10)
        p2 = Product(name="无线鼠标", price=159.0, stock=300)
        assert p2.name == "无线鼠标"

    def test_stock_defaults_to_zero(self):
        Product = make_product_class()
        assert Product("无线鼠标", 159.0).stock == 0

    def test_auto_eq(self):
        # @dataclass 自动生成 __eq__:同字段值即相等
        Product = make_product_class()
        assert Product("A", 1.0, 2) == Product("A", 1.0, 2)
        assert Product("A", 1.0) != Product("A", 2.0)

    def test_eq_with_other_type_is_false(self):
        Product = make_product_class()
        assert Product("A", 1.0) != "A"

    def test_auto_repr(self):
        # @dataclass 自动生成 __repr__(带 <locals> 前缀,断言关键片段)
        Product = make_product_class()
        r = repr(Product("机械键盘", 599.0, 10))
        assert "Product(" in r
        assert "name='机械键盘'" in r
        assert "599.0" in r

    def test_fields_mutable_by_default(self):
        # 默认不是 frozen:字段可以改
        Product = make_product_class()
        p = Product("A", 1.0, 1)
        p.stock = 5
        assert p.stock == 5

    def test_with_products_fixture(self, products):
        Product = make_product_class()
        first = products[0]  # {"name": "机械键盘", "price": 599.0, "stock": 120, ...}
        p = Product(first["name"], first["price"], first["stock"])
        assert (p.name, p.price, p.stock) == ("机械键盘", 599.0, 120)


# ---------- §5.2 make_order_class:__init__ + @property ----------
class TestMakeOrderClass:
    def test_empty_order_total_is_zero(self):
        Order = make_order_class()
        assert Order().total == 0

    def test_total_sums_price_times_qty(self):
        Order = make_order_class()
        o = Order()
        o.add_item("机械键盘", 599.0, 2)
        o.add_item("无线鼠标", 159.0)  # qty 默认 1
        assert o.total == 1357.0

    def test_total_is_rounded(self):
        # 0.1 × 3 = 0.30000000000000004 → round 后 0.3
        Order = make_order_class()
        o = Order()
        o.add_item("折扣小样", 0.1, 3)
        assert o.total == 0.3

    def test_total_is_read_only(self):
        # 没定义 setter → 赋值抛 AttributeError
        Order = make_order_class()
        o = Order()
        with pytest.raises(AttributeError):
            o.total = 999.0

    def test_total_recomputes_after_add(self):
        # 拦「第一次算完就缓存死」:total 必须每次现算
        Order = make_order_class()
        o = Order()
        o.add_item("A", 100.0)
        assert o.total == 100.0
        o.add_item("B", 50.0)
        assert o.total == 150.0

    def test_orders_are_independent(self):
        # 拦「_items 写成类属性」:两个订单不能串单(经典 Java 老手坑)
        Order = make_order_class()
        a, b = Order(), Order()
        a.add_item("A", 100.0)
        assert b.total == 0


# ---------- §5.3 make_inventory_class:__len__ / __contains__ / __iter__ ----------
class TestMakeInventoryClass:
    def _inv(self):
        Inventory = make_inventory_class()
        return Inventory({"KB-001": 120, "MS-002": 300, "MN-003": 45})

    def test_len_counts_skus(self):
        assert len(self._inv()) == 3

    def test_len_empty(self):
        Inventory = make_inventory_class()
        assert len(Inventory({})) == 0

    def test_contains_hit_and_miss(self):
        inv = self._inv()
        assert "KB-001" in inv
        assert "XX-000" not in inv

    def test_iter_yields_skus_in_insertion_order(self):
        assert list(self._inv()) == ["KB-001", "MS-002", "MN-003"]

    def test_for_loop_works(self):
        seen = []
        for sku in self._inv():
            seen.append(sku)
        assert seen == ["KB-001", "MS-002", "MN-003"]

    def test_constructor_copies_dict(self):
        # 防御性拷贝:构造后改原字典,不应影响 inv(拦「直接持有引用」)
        Inventory = make_inventory_class()
        stock = {"KB-001": 120}
        inv = Inventory(stock)
        stock["HACK-999"] = 1
        assert len(inv) == 1


# ---------- §5.3 make_price_list_class:__getitem__ ----------
class TestMakePriceListClass:
    def test_getitem_returns_price(self):
        PriceList = make_price_list_class()
        pl = PriceList({"KB-001": 599.0, "MS-002": 159.0})
        assert pl["KB-001"] == 599.0
        assert pl["MS-002"] == 159.0

    def test_brackets_trigger_getitem(self):
        # 拦「只定义了普通方法 get」:必须用 [] 语法触发 __getitem__
        PriceList = make_price_list_class()
        pl = PriceList({"A": 1.0})
        assert pl["A"] == 1.0

    def test_missing_sku_raises_keyerror(self):
        PriceList = make_price_list_class()
        pl = PriceList({"KB-001": 599.0})
        with pytest.raises(KeyError):
            _ = pl["NOPE"]

    def test_with_products_fixture(self, products):
        # 真实数据:用 products.json 建价目表
        PriceList = make_price_list_class()
        pl = PriceList({p["sku"]: p["price"] for p in products})
        assert pl["BK-005"] == 75.5
        assert pl["CH-010"] == 1599.0
        with pytest.raises(KeyError):
            _ = pl["XX-000"]


# ---------- §5.4 make_money_class:__add__ / __eq__ / __hash__ / __repr__ ----------
class TestMakeMoneyClass:
    def test_add_returns_new_money(self):
        Money = make_money_class()
        a, b = Money(100.0), Money(50.0)
        c = a + b
        assert c.amount == 150.0
        assert isinstance(c, Money)

    def test_add_does_not_mutate_operands(self):
        # 拦「self.amount += other.amount; return self」:运算不能改原对象
        Money = make_money_class()
        a, b = Money(100.0), Money(50.0)
        c = a + b
        assert a.amount == 100.0
        assert b.amount == 50.0
        assert c is not a and c is not b

    def test_eq_same_amount(self):
        Money = make_money_class()
        assert Money(12.5) == Money(12.5)
        assert Money(12.5) != Money(12.6)

    def test_eq_with_other_types_is_false(self):
        # 不认识的类型 → NotImplemented → 整体结果为 False(不能抛异常)
        Money = make_money_class()
        assert Money(1.0) != 1.0
        assert Money(1.0) != "1.0"

    def test_hashable_and_dedup_in_set(self):
        # 定义 __eq__ 后 __hash__ 变 None → 不手写 __hash__ 这里直接 TypeError
        Money = make_money_class()
        s = {Money(10.0), Money(10.0), Money(20.0)}
        assert len(s) == 2

    def test_usable_as_dict_key_for_aggregation(self):
        # 「按金额聚合计数」:同金额必须命中同一个 key
        Money = make_money_class()
        agg = {Money(10.0): 1}
        agg[Money(10.0)] += 1
        assert agg[Money(10.0)] == 2

    def test_add_with_non_money_raises_typeerror(self):
        # 返回 NotImplemented → Python 试反向也不行 → TypeError
        # (先确认 Money 可用,再验证 TypeError;否则骨架 None(1.0) 也会误抛 TypeError)
        Money = make_money_class()
        assert (Money(1.0) + Money(2.0)).amount == 3.0
        with pytest.raises(TypeError):
            _ = Money(1.0) + 5

    def test_repr_format(self):
        Money = make_money_class()
        assert repr(Money(12.5)) == "Money(12.50)"
        assert repr(Money(100.0)) == "Money(100.00)"


# ---------- §5.5 make_discount_cart_class:继承 + super() ----------
class TestMakeDiscountCartClass:
    def test_returns_real_subclass_of_cart(self):
        # 拦「定义了一个和 Cart 无关的类」:必须真的继承函数内的 Cart
        DC = make_discount_cart_class()
        assert isinstance(DC, type)
        assert DC.__mro__[1].__name__ == "Cart"

    def test_discounted_total(self):
        DC = make_discount_cart_class()
        c = DC(discount=0.2)
        c.add("机械键盘", 599.0)
        c.add("无线鼠标", 159.0)
        # 758.0 × 0.8 = 606.4
        assert c.total == 606.4

    def test_default_discount(self):
        # discount 默认 0.1(9 折)
        DC = make_discount_cart_class()
        c = DC()
        c.add("A", 100.0)
        assert c.total == 90.0

    def test_inherits_add_from_parent(self):
        # add 是父类继承来的;打折只影响 total,不影响加商品
        DC = make_discount_cart_class()
        c = DC(0.5)
        c.add("A", 100.0)
        assert c.total == 50.0

    def test_zero_discount_equals_parent_total(self):
        DC = make_discount_cart_class()
        c = DC(discount=0)
        c.add("A", 100.0)
        c.add("B", 59.9)
        assert c.total == 159.9


# ---------- §5.6 make_checkout_class:综合 ----------
class TestMakeCheckoutClass:
    def _checkout(self):
        Checkout = make_checkout_class()
        c = Checkout()
        c.add("机械键盘", 599.0, 2)
        c.add("无线鼠标", 159.0)
        return c

    def test_len_counts_total_qty(self):
        # 总件数 = Σ qty = 2 + 1(不是明细条数 2!)
        assert len(self._checkout()) == 3

    def test_len_empty(self):
        Checkout = make_checkout_class()
        assert len(Checkout()) == 0

    def test_contains_by_name(self):
        c = self._checkout()
        assert "机械键盘" in c
        assert "降噪耳机" not in c

    def test_iter_yields_item_dicts(self):
        names = [i["name"] for i in self._checkout()]
        assert names == ["机械键盘", "无线鼠标"]

    def test_total_property(self):
        assert self._checkout().total == 1357.0
        Checkout = make_checkout_class()
        assert Checkout().total == 0

    def test_add_merges_into_new_checkout(self):
        Checkout = make_checkout_class()
        a = Checkout()
        a.add("A", 100.0)
        b = Checkout()
        b.add("B", 50.0, 2)
        merged = a + b
        assert len(merged) == 3
        assert merged.total == 200.0
        assert merged is not a and merged is not b

    def test_add_does_not_mutate_originals(self):
        Checkout = make_checkout_class()
        a = Checkout()
        a.add("A", 100.0)
        b = Checkout()
        b.add("B", 50.0, 2)
        _ = a + b
        assert len(a) == 1
        assert len(b) == 2

    def test_repr_format(self):
        assert repr(self._checkout()) == "Checkout(2 种商品, 共 3 件, ¥1357.0)"

    def test_repr_empty(self):
        Checkout = make_checkout_class()
        assert repr(Checkout()) == "Checkout(0 种商品, 共 0 件, ¥0)"
