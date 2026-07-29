"""
Ch02 作业:数据结构实战(全部基于 products.json 商品数据)。

8 个函数覆盖 list / tuple / dict / set,并实践「可变默认参数陷阱」的正确写法。
在每处 TODO 写实现,然后:

    pytest 01_python_core/ch02/test_ch02_assignment.py -v

全绿 = 你掌握了 Ch02。

约定:products 是 list[dict],每个 dict 形如:
    {"id":1, "name":"机械键盘", "category":"电脑外设", "price":599.0, "stock":120, "sku":"KB-001"}
"""
# category_inventory_value 会用到 defaultdict;如果你不需要可以忽略这行
from collections import defaultdict


# ========== list:切片 + 排序 ==========


def get_top_products_by_price(products: list[dict], n: int = 3) -> list[str]:
    """
    【list + 切片 + 排序】返回价格最高的前 n 个商品名(降序)。
    若商品总数不足 n 个,返回全部。

    示例(products 共 10 个,最贵是"27寸4K显示器"2199):
        get_top_products_by_price(products, n=3)
            -> ["27寸4K显示器", "人体工学椅", "降噪耳机"]
        get_top_products_by_price(products, n=100)  -> 长度 10

    提示:
        sorted(products, key=lambda p: p["price"], reverse=True)  先排序
        再切片 [:n],再用列表推导取 name。
    """
    # TODO: 在这里写实现
    ...
    products.sort(key=lambda p: p["price"], reverse=True)
    return [p["name"] for p in products[:n]]

# ========== tuple:多返回值 ==========


def price_range(products: list[dict]) -> tuple[float, float]:
    """
    【tuple + 多返回值】返回 (最低价, 最高价)。
    假设 products 非空。

    示例:
        price_range(products) -> (75.5, 2199.0)

    提示:提取所有 price 到一个 list,再用 min() / max()。
        return (min(prices), max(prices))   # 返回两个值,实际是一个 tuple
    """
    # TODO: 在这里写实现
    prices = [p["price"] for p in products]
    return min(prices), max(prices)


# ========== dict:字典推导式 ==========


def build_price_map(products: list[dict]) -> dict[str, float]:
    """
    【dict 推导式】返回 name -> price 的映射。

    示例:
        m = build_price_map(products)
        m["机械键盘"]  -> 599.0

    提示(字典推导式,一行搞定,对比 Java stream toMap):
        {p["name"]: p["price"] for p in products}
    """
    # TODO: 在这里写实现
    return {p["name"] : p["price"] for p in products}


# ========== dict:setdefault 分组 ==========


def group_by_category(products: list[dict]) -> dict[str, list[dict]]:
    """
    【dict + setdefault】按 category 分组,返回 {类目: [商品, ...]}。

    示例(products 中"电脑外设"有 4 个):
        g = group_by_category(products)
        len(g["电脑外设"])  -> 4
        len(g["图书"])      -> 2

    提示(对比 Java map.computeIfAbsent):
        groups = {}
        for p in products:
            groups.setdefault(p["category"], []).append(p)
    """
    # TODO: 在这里写实现
    


# ========== dict:defaultdict 聚合 ==========


def category_inventory_value(products: list[dict]) -> dict[str, float]:
    """
    【defaultdict 聚合】计算每个类目的「库存货值」= sum(price * stock)。

    示例:
        v = category_inventory_value(products)
        v["生活用品"]  -> 47970.0   # 199*0(水杯缺货) + 1599*30(工学椅)
        v["电脑外设"]  -> 277715.0

    提示(顶部已 import defaultdict):
        value = defaultdict(float)
        for p in products:
            value[p["category"]] += p["price"] * p["stock"]
        return dict(value)
    """
    # TODO: 在这里写实现
    ...


# ========== set:推导式去重 ==========


def all_categories(products: list[dict]) -> set[str]:
    """
    【set 推导式】返回所有类目(自动去重)。

    示例:
        all_categories(products)
            -> {"电脑外设", "图书", "影音设备", "生活用品"}

    提示(集合推导式):
        {p["category"] for p in products}
    """
    # TODO: 在这里写实现
    ...


# ========== 综合 ==========


def find_cheapest_per_category(products: list[dict]) -> dict[str, str]:
    """
    【综合】返回每个类目里最便宜的商品名。
    可复用上面的 group_by_category。

    示例:
        find_cheapest_per_category(products)
            -> {"电脑外设": "无线鼠标", "图书": "设计模式",
                "影音设备": "蓝牙音箱", "生活用品": "智能水杯"}

    提示:
        for cat, ps in group_by_category(products).items():
            cheapest = min(ps, key=lambda p: p["price"])
            result[cat] = cheapest["name"]
    """
    # TODO: 在这里写实现
    ...


def filter_products(
    products: list[dict],
    min_price: float | None = None,
    category: str | None = None,
    in_stock_only: bool = False,
) -> list[dict]:
    """
    【综合 + 可变默认参数】这就是你举的例子:过滤商品 + 排序。

    过滤规则(全部可选,叠加):
      - min_price:    只保留 price >= min_price 的商品
      - category:     只保留该类目(精确匹配)
      - in_stock_only: 只保留 stock > 0 的商品
    过滤后按 price 升序排序,返回商品 dict 列表(保持完整 dict)。

    示例:
        filter_products(products, min_price=1000)
            -> [降噪耳机, 人体工学椅, 27寸4K显示器]   # 升序
        filter_products(products, category="图书")
            -> [设计模式, Python编程:从入门到实践]
        filter_products(products, in_stock_only=True)   # 长度 9(排除缺货水杯)

    ⚠️ 注意可变默认参数陷阱:
        默认值必须用 None(不可变),绝不能写 products: list = []。
        函数内部判断 None 再处理。

    提示:
        result = products
        if min_price is not None:
            result = [p for p in result if p["price"] >= min_price]
        ...同理处理 category 和 in_stock_only
        return sorted(result, key=lambda p: p["price"])
    """
    # TODO: 在这里写实现
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 01_python_core/ch02/ch02_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    prods = load_mock_json("products.json")
    print("top3:", get_top_products_by_price(prods, 3))
    print("range:", price_range(prods))
    print("categories:", all_categories(prods))
    print("cheapest/cat:", find_cheapest_per_category(prods))
    print("filter >=1000:", [p["name"] for p in filter_products(prods, min_price=1000)])
