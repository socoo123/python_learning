"""
Ch05 作业测试。运行: uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v
"""
from ch05_assignment import Product, ShoppingCart, DiscountedCart


# ---------- Product:@dataclass ----------
class TestProductDataclass:
    def test_create_full(self):
        p = Product(name="键盘", price=599.0, stock=10)
        assert p.name == "键盘"
        assert p.price == 599.0
        assert p.stock == 10

    def test_default_stock_is_zero(self):
        # stock 有默认值,可不传
        p = Product("鼠标", 159.0)
        assert p.stock == 0

    def test_auto_equality(self):
        # @dataclass 自动生成 __eq__:同字段值即相等
        assert Product("a", 1.0, 2) == Product("a", 1.0, 2)
        assert Product("a", 1.0) != Product("a", 2.0)

    def test_auto_repr_contains_name(self):
        # @dataclass 自动生成 __repr__
        assert "键盘" in repr(Product("键盘", 599.0, 10))


# ---------- ShoppingCart:__len__ ----------
class TestShoppingCartLen:
    def test_empty_is_zero(self):
        assert len(ShoppingCart()) == 0

    def test_add_one(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0))
        assert len(cart) == 1

    def test_add_with_qty(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0), qty=3)
        assert len(cart) == 3


# ---------- ShoppingCart:__contains__ ----------
class TestShoppingCartContains:
    def test_contains_product_object(self):
        cart = ShoppingCart()
        kb = Product("键盘", 599.0)
        cart.add(kb)
        assert kb in cart

    def test_not_contains(self):
        cart = ShoppingCart()
        assert Product("nope", 1.0) not in cart

    def test_contains_by_name_string(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0))
        assert "键盘" in cart
        assert "鼠标" not in cart


# ---------- ShoppingCart:__iter__ ----------
class TestShoppingCartIter:
    def test_iterate_yields_products(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0))
        cart.add(Product("鼠标", 159.0))
        names = [p.name for p in cart]
        assert names == ["键盘", "鼠标"]

    def test_iter_empty(self):
        assert list(ShoppingCart()) == []


# ---------- ShoppingCart:@property total ----------
class TestShoppingCartTotal:
    def test_sums_prices(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0))
        cart.add(Product("鼠标", 159.0))
        assert cart.total == 758.0

    def test_total_counts_duplicates(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0), qty=2)
        assert cart.total == 1198.0

    def test_empty_total_is_zero(self):
        assert ShoppingCart().total == 0.0

    def test_total_is_read_only(self):
        # @property 不带 setter → 只读,赋值应报错
        cart = ShoppingCart()
        import pytest
        with pytest.raises(AttributeError):
            cart.total = 100.0


# ---------- ShoppingCart:__add__ ----------
class TestShoppingCartAdd:
    def test_merge_two_carts(self):
        c1 = ShoppingCart(); c1.add(Product("键盘", 599.0))
        c2 = ShoppingCart(); c2.add(Product("鼠标", 159.0))
        merged = c1 + c2
        assert len(merged) == 2
        assert merged.total == 758.0

    def test_originals_not_mutated(self):
        c1 = ShoppingCart(); c1.add(Product("键盘", 599.0))
        c2 = ShoppingCart()
        _ = c1 + c2
        assert len(c1) == 1   # 原 cart 未被改动

    def test_merged_is_new_instance(self):
        c1 = ShoppingCart(); c1.add(Product("键盘", 599.0))
        c2 = ShoppingCart(); c2.add(Product("鼠标", 159.0))
        merged = c1 + c2
        assert merged is not c1 and merged is not c2


# ---------- ShoppingCart:__repr__ ----------
class TestShoppingCartRepr:
    def test_repr_mentions_count_and_total(self):
        cart = ShoppingCart()
        cart.add(Product("键盘", 599.0))
        r = repr(cart)
        assert "1" in r       # 件数
        assert "599" in r     # 总价


# ---------- DiscountedCart:继承 + super() ----------
class TestDiscountedCart:
    def test_discounted_total(self):
        cart = DiscountedCart(discount=0.1)
        cart.add(Product("键盘", 599.0))
        # 599 * 0.9 = 539.1
        assert cart.total == 539.1

    def test_inherits_add_and_len(self):
        # 子类自动拥有父类的 add / __len__
        cart = DiscountedCart()
        cart.add(Product("键盘", 599.0), qty=2)
        assert len(cart) == 2

    def test_inherits_contains(self):
        cart = DiscountedCart()
        cart.add(Product("键盘", 599.0))
        assert "键盘" in cart

    def test_default_discount(self):
        # discount 默认 0.1
        cart = DiscountedCart()
        cart.add(Product("X", 100.0))
        assert cart.total == 90.0
