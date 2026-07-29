"""
Ch01 作业:从 Java 到 Python 的思维转换热身。

每个函数对应一个【转换点】,即 Java 与 Python 的一个根本差异。
在每处 TODO 处写你的实现,然后:

    pytest 01_python_core/ch01/test_ch01_assignment.py -v

全绿 = 你掌握了 Ch01。

提示:函数的类型注解只是建议,先按注解理解题目,实现时可以用 Pythonic 的写法。
"""


# ========== Part A:思维转换热身 ==========


def add(a: int, b: int) -> int:
    """
    【转换点】动态类型 vs 静态类型。
    Java:  int add(int a, int b)
    Python:类型注解是"提示",运行时不强制。

    任务:返回 a + b。
    """
    return a + b


def swap(a, b):
    """
    【转换点】元组解包,Python 不需要临时变量。
    Java:  int tmp = a; a = b; b = tmp;
    Python: a, b = b, a   (一步搞定,元组打包/解包)

    任务:返回交换后的 (b, a)。即接收两个值,返回倒序的元组。
    示例:
        swap(1, 2)       -> (2, 1)
        swap("x", "y")   -> ("y", "x")
    """
    # TODO: 在这里写实现(提示:元组解包,一行搞定)
    return b, a


def greet(name: str, greeting: str = "Hello", times: int = 1) -> str:
    """
    【转换点】默认参数 + f-string,Python 不需要方法重载。
    Java 要写 3 个重载的 greet;Python 一个函数 + 默认参数搞定。

    任务:返回形如 "Hello, Alice!" 的问候,按 times 次重复,用换行 \\n 分隔。
    示例:
        greet("Alice")              -> "Hello, Alice!"
        greet("Bob", "Hi")          -> "Hi, Bob!"
        greet("Carl", times=3)      -> "Hello, Carl!\\nHello, Carl!\\nHello, Carl!"

    提示:f-string 写法  f"{greeting}, {name}!"
        多次重复可用:  "\\n".join([单行] * times)
    """
    # TODO: 在这里写实现
    
    line = f"{greeting}, {name}!"
    return "\n".join([line] * times)


def first_or_default(items: list, default=None):
    """
    【转换点】真理性(truthiness)判空。
    Java:  if (items == null || items.isEmpty()) return default;  return items.get(0);
    Python:if not items: 一句搞定(空列表/None/空串 都是 falsy)。

    任务:返回列表第一个元素;若列表为空,返回 default。
    示例:
        first_or_default([1, 2, 3])        -> 1
        first_or_default([], "empty")      -> "empty"
        first_or_default([])               -> None
        first_or_default([], default=99)   -> 99

    进阶(可选 Pythonic 写法):  items[0] if items else default
    """
    # TODO: 在这里写实现
    if not items:
        return default
    return items[0]


def describe(obj) -> str:
    """
    【转换点】一切皆对象。
    Java 区分基本类型和引用类型;Python 里 int/str/函数/类全是对象。

    任务:返回字符串  "<repr> is a <TypeName>"
    示例:
        describe(42)        -> "42 is a int"
        describe("hi")      -> "'hi' is a str"
        describe([1, 2])    -> "[1, 2] is a list"
        describe(3.14)      -> "3.14 is a float"

    提示:
        type(obj).__name__  -> 类型名字符串,如 "int"
        repr(obj)           -> 对象的"官方字符串表示"(42 -> "42", "hi" -> "'hi'")
    """
    # TODO: 在这里写实现
    t = type(obj).__name__
    return f"{repr(obj)} is a {t}"


# ========== Part B:工作流验证(用 mock 数据)==========


def load_product_names() -> list[str]:
    """
    【验证工作流】读取共享 mock 数据,返回所有商品名列表。

    这个函数验证三件事:
      1. 你会使用项目根目录 conftest.py 提供的 load_mock_json 工具
      2. mock 数据机制正常(products.json 里确实有 10 个商品)
      3. 你理解 list comprehension / 提取字段的思路

    任务:读取 assets/mock_data/products.json,提取每个商品的 name,
         返回名称列表(保持原始顺序)。

    提示:
        from conftest import load_mock_json
        data = load_mock_json("products.json")   # list[dict]
        # 每个 dict 形如 {"id":1, "name":"机械键盘", "price":599.0, ...}
        # 用列表推导式提取:  [p["name"] for p in data]
    """
    # TODO: 在这里写实现
    from conftest import load_mock_json
    data = load_mock_json("products.json")
    return [p["name"] for p in data]


# ---------------------------------------------------------------------
# 注意:下面这个块是"直接运行本文件看效果"的入口,不是测试。
# 测试请用 pytest。当你把上面的函数都实现好后,可以直接运行本文件:
#     python 01_python_core/ch01/ch01_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("add(1, 2) =", add(1, 2))
    print("swap(1, 2) =", swap(1, 2))
    print("greet('Alice', times=2) =", repr(greet("Alice", times=2)))
    print("first_or_default([], 'x') =", first_or_default([], "x"))
    print("describe(42) =", describe(42))
    print("load_product_names() =", load_product_names())
