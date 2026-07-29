"""
Ch03 作业:控制流、迭代器、生成器、推导式。

6 个函数覆盖 Python 效率核心:推导式、enumerate/zip、for-else、生成器、迭代器消费。
在每处 TODO 写实现,然后:

    uv run pytest 01_python_core/ch03/test_ch03_assignment.py -v

全绿 = 你掌握了 Ch03。

每题顶部的【对应小节】指向 tutorial.md 里的讲解。卡住 → 回查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
from collections.abc import Iterable


# ========== §3.1 列表推导式(带条件)==========


def cheap_product_names(products: list[dict], max_price: float = 200) -> list[str]:
    """
    【列表推导式 · §3.1】返回价格 < max_price 的商品名列表(保持原顺序)。

    示例(products 里 <200 的有 4 个:无线鼠标159、Python编程89、设计模式75.5、智能水杯199):
        cheap_product_names(products, max_price=200)
            -> ["无线鼠标", "Python编程:从入门到实践", "设计模式", "智能水杯"]
        cheap_product_names(products, max_price=100)
            -> ["Python编程:从入门到实践", "设计模式"]

    思路:列表推导式 = `[表达式 for 变量 in 序列 if 条件]`。这里表达式取 name,条件判价格。
    """
    # TODO: 一行列表推导式
    ...


# ========== §3.3 enumerate / zip ==========


def indexed_summary(products: list[dict]) -> list[str]:
    """
    【enumerate · §3.3】返回带【从1开始的序号】的摘要列表,格式 "N. 商品名 (¥价格)"。

    示例:
        indexed_summary(products)[0]  -> "1. 机械键盘 (¥599.0)"
        indexed_summary(products)[2]  -> "3. 27寸4K显示器 (¥2199.0)"

    思路:用 enumerate 遍历拿到 (序号, 商品);序号要【从1开始】(给 enumerate 第二个参数)。
         再配合列表推导式 + f-string 拼出字符串。
    """
    # TODO: enumerate + 列表推导式 + f-string
    ...


def names_and_prices_zipped(products: list[dict]) -> list[tuple[str, float]]:
    """
    【zip · §3.3】返回 [(name, price), ...],用 zip 把"名字列表"和"价格列表"并行配对。

    示例:
        names_and_prices_zipped(products)[0]  -> ("机械键盘", 599.0)
        names_and_prices_zipped(products)[4]  -> ("设计模式", 75.5)

    思路:先用两个列表推导式分别抽出 names 和 prices(两个等长列表),
         再 zip(names, prices) 配对,最后用 list(...) 转成列表(zip 返回的是迭代器)。
    """
    # TODO: 抽两个列表 → zip → list
    ...


# ========== §3.2 for-else ==========


def is_prime(n: int) -> bool:
    """
    【for-else · §3.2】判断 n 是否为素数(n < 2 返回 False)。

    示例:
        is_prime(2)  -> True
        is_prime(7)  -> True
        is_prime(8)  -> False   (8 % 2 == 0)
        is_prime(1)  -> False
        is_prime(97) -> True

    思路(关键是 for-else 的语义——循环【没被中途 return 跳出】时才执行 else):
      1. n < 2 直接 return False
      2. for i in range(2, n):一旦发现 n % i == 0(找到因子),立即 return False(跳出)
      3. for 循环正常跑完(一个因子都没找到)→ 走 else 分支 → return True
    """
    # TODO: for-else 结构
    ...


# ========== §3.4 生成器 yield ==========


def iter_error_lines(lines: Iterable[str]):
    """
    【生成器 yield · §3.4】逐个【惰性产出】含 "ERROR" 的日志行。
    用 yield(不是 return),让它成为生成器——能流式处理 GB 级日志而不爆内存。

    示例(logs.json 里共 5 条 ERROR):
        list(iter_error_lines(logs))  -> 长度 5,且每条都含 "ERROR"

    思路:for 遍历 lines;if 当前行含 "ERROR",就 `yield line`(产出这一行,下次 next 继续)。
         注意:函数体里只要出现 yield,这个函数就自动变成生成器函数,调用它返回生成器对象。
    """
    # TODO: for + if + yield
    ...


# ========== §3.5 迭代器消费(综合)==========


def top_n_by_price(product_iter: Iterable[dict], n: int = 3) -> list[str]:
    """
    【消费迭代器 · §3.5】输入是一个【只能遍历一次】的迭代器/生成器
    (模拟"从大文件或网络流式读取商品")。消费它,返回价格最高的前 n 个商品名(降序)。

    示例:
        top_n_by_price(iter(products), n=3)
            -> ["27寸4K显示器", "人体工学椅", "降噪耳机"]
        top_n_by_price(iter(products), n=100)  -> 长度 10(不足 n 返回全部)

    思路:迭代器用完即弃,先用 list(product_iter) 把它【一次性物化】成列表;
         然后按 price 降序排(参考 Ch02 的 sorted + key=lambda + reverse=True),切片 [:n],取 name。
    """
    # TODO: list() 物化 → sorted 降序 → 切片 → 取 name
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch03/ch03_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    prods = load_mock_json("products.json")
    logs = load_mock_json("logs.json")
    print("cheap<200:", cheap_product_names(prods, 200))
    print("indexed[0]:", indexed_summary(prods)[0])
    print("zipped[0]:", names_and_prices_zipped(prods)[0])
    print("is_prime(7):", is_prime(7), "is_prime(8):", is_prime(8))
    print("error count:", len(list(iter_error_lines(logs))))
    print("top3:", top_n_by_price(iter(prods), 3))
