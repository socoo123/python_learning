"""
Ch05 作业:OOP —— 魔术方法、继承、dataclass。

定义 Product(@dataclass)+ ShoppingCart(一整套魔术方法)+ DiscountedCart(继承)。
在每处 TODO 写实现,然后:

    uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v

全绿 = 你掌握了 Ch05。

每题顶部的【对应小节】指向 tutorial.md 里的讲解。卡住 → 回查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
from dataclasses import dataclass


# ========== §5.1 @dataclass ==========


# TODO: 给这个类加 @dataclass 装饰器,并定义三个字段(顺序很重要):
#     name: str
#     price: float
#     stock: int = 0      ← 有默认值的字段必须放最后
class Product:
    """商品。加 @dataclass 后会自动生成 __init__/__repr__/__eq__。"""
    ...


# ========== §5.2 魔术方法 + @property ==========


class ShoppingCart:
    """购物车。把下面这些魔术方法/属性补全,让对象支持:

        len(cart)               → 商品件数          __len__
        商品 or 名字 in cart     → 是否在车          __contains__
        for p in cart           → 遍历              __iter__
        cart.total              → 总价(像属性访问) @property
        cart1 + cart2           → 合并成【新】车     __add__
        repr(cart)              → 友好显示          __repr__
    """

    def __init__(self):
        # TODO: 初始化一个空列表 self._items(类型 list[Product])
        ...

    def add(self, product: Product, qty: int = 1) -> None:
        """添加商品 qty 件(默认1)。"""
        # TODO: 循环 qty 次,把 product append 进 self._items
        ...

    def __len__(self) -> int:
        """让 len(cart) 返回商品件数。"""
        # TODO: return len(self._items)
        ...

    def __contains__(self, item) -> bool:
        """让 `x in cart` 生效。item 可能是 Product 对象,也可能是名字字符串。"""
        # TODO: 若 isinstance(item, Product) → 判断 item 在不在 _items;
        #       否则当字符串处理 → any(p.name == item for p in self._items)
        ...

    def __iter__(self):
        """让 `for p in cart` 生效。返回 self._items 的迭代器。"""
        # TODO: return iter(self._items)
        ...

    @property
    def total(self) -> float:
        """总价。用 @property 让它像属性一样 cart.total 访问(不带括号)。"""
        # TODO: return sum(p.price for p in self._items)
        ...

    def __add__(self, other: "ShoppingCart") -> "ShoppingCart":
        """让 cart1 + cart2 返回一个【新的】ShoppingCart,商品是两边拼接。
        不要修改原来的两个 cart。"""
        # TODO: new = ShoppingCart(); new._items = self._items + other._items; return new
        ...

    def __repr__(self) -> str:
        """友好显示,例如 'ShoppingCart(2 items, ¥758.0)'。"""
        # TODO: f"ShoppingCart({len(self)} items, ¥{self.total})"
        ...


# ========== §5.3 继承 + super() ==========


class DiscountedCart(ShoppingCart):
    """打折购物车:继承 ShoppingCart,【覆盖】 total 这个 @property 实现打折,
    用 super() 复用父类的 total 计算。"""

    def __init__(self, discount: float = 0.1):
        # TODO: 先 super().__init__() 初始化父类的 _items;再存 self.discount = discount
        ...

    @property
    def total(self) -> float:
        """打折后的总价 = 父类 total × (1 - discount),保留两位小数。"""
        # TODO: original = super().total   ← 复用父类计算
        #       return round(original * (1 - self.discount), 2)
        ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch05/ch05_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    cart = ShoppingCart()
    cart.add(Product("机械键盘", 599.0), qty=2)
    cart.add(Product("无线鼠标", 159.0))
    print(repr(cart))
    print("total:", cart.total)
    print("键盘 in cart:", "机械键盘" in cart)
    dc = DiscountedCart(discount=0.1)
    dc.add(Product("机械键盘", 599.0))
    print("discounted total:", dc.total)
