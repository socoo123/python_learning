"""
Ch07 作业:类型注解与 Pythonic 风格。

本章特殊:类型注解运行时不强制(真正的检查靠 mypy)。所以本题你要【补全类型注解】
+ 写实现。测试会检查行为,也会检查注解是否存在(__annotations__)。

    uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v

全绿 = 你掌握了 Ch07。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from typing import Callable, Protocol, runtime_checkable


# ========== §7.1 类型注解基础 ==========


# TODO: 给参数和返回值加类型注解,并实现。
#   注解:price: float, currency: str = "¥",返回 -> str
#   实现:f"{currency}{price:.2f}"(保留两位小数)
def format_price(price, currency="¥"):
    """返回形如 "¥59.50" 的价格字符串。"""
    ...


# ========== §7.2 联合类型(dict | None)==========


# TODO: 返回类型标注为 dict | None;实现:遍历按 sku 查找,找到返回 dict,找不到返回 None。
def find_product(products, sku):
    """按 sku 查商品;找不到返回 None。"""
    ...


# ========== §7.3 Callable(函数类型注解)==========


# TODO: 给 func 标注 Callable[[int], int](意思是:接收 int、返回 int 的函数)。
#       实现:return func(x)
def apply_operation(func, x):
    """调用 func(x) 并返回结果。"""
    ...


# ========== §7.4 Protocol(结构化类型)==========


# TODO: ① 给类加 @runtime_checkable 装饰器(让 Protocol 能用 isinstance)
#       ② 在类体里声明属性 name: str(只写类型,不写值——这是接口声明)
class Named(Protocol):
    """任何【有 name 属性】的对象都自动算 Named(不用显式继承,= 鸭子类型的接口)。"""
    ...


# TODO: 给 obj 标注类型 Named;实现:return obj.name
def get_name(obj):
    """返回 obj.name。只要 obj 有 .name 就能用。"""
    ...


# ========== §7.5 EAFP 风格 ==========


# TODO: 用 EAFP 风格实现(请求宽恕比许可容易):
#       try: return d[key]
#       except KeyError: return default
#   (对比 LBYL:if key in d: return d[key] else return default —— EAFP 更 Pythonic)
def safe_get(d, key, default=None):
    """安全取字典键,不存在返回 default。用 try/except,不要用 if key in d。"""
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch07/ch07_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(format_price(59.5))
    print(format_price(99, currency="$"))
    print(apply_operation(lambda x: x * 2, 5))

    class Cat:
        name = "Tom"
    print(get_name(Cat()))
    print("Cat is Named?", isinstance(Cat(), Named))

    print(safe_get({"a": 1}, "a"))
    print(safe_get({"a": 1}, "b"))
