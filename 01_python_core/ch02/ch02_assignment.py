"""
Ch02 作业:数据结构实战 —— 电商后台「商品数据中台」。

场景:你在给电商后台写一组商品数据服务函数——热销榜、价格区间、
价格速查表、类目分组、库存货值、类目列表、引流款分析、组合筛选器。
8 个函数,每个刚好砸在一个数据结构知识点上,全部跑在 products.json 上。

在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch02/test_ch02_assignment.py -v

全绿 = 你掌握了 Ch02。

约定:products 是 list[dict],每个 dict 形如:
    {"id": 1, "name": "机械键盘", "category": "电脑外设",
     "price": 599.0, "stock": 120, "sku": "KB-001"}
"""
from collections import defaultdict


# ========== §2.1 list:切片 + sorted ==========


def get_top_products_by_price(products: list[dict], n: int = 3) -> list[str]:
    """
    【场景】首页热销榜:展示价格最高的前 n 个商品名(降序),展位有限,n 默认 3。

    【转换点】切片 + sorted。Java 要 stream().sorted(comparing).limit(n);
    Python 排序后切片 [:n] 即可,且 n 超过总数不会报错(切片自动截断)。

    任务:返回价格最高的前 n 个商品的 name 列表,价格高的在前。
         商品总数不足 n 个时返回全部。n=0 时返回 []。
    示例(products.json 共 10 个商品):
        get_top_products_by_price(products, n=3)
            -> ["27寸4K显示器", "人体工学椅", "降噪耳机"]   # 2199 / 1599 / 1299
        get_top_products_by_price(products, n=100)   -> 返回全部 10 个
        get_top_products_by_price(products, n=0)     -> []
        get_top_products_by_price([], n=3)           -> []

    ⚠️ 不许修改传入的 products(调用方还要用!):
        用 sorted(...) 返回新列表,别用 products.sort() 原地排序。

    提示:
        top = sorted(products, key=lambda p: p["price"], reverse=True)[:n]
        return [p["name"] for p in top]
    """
    # TODO: 在这里写实现(两行:排序切片 + 推导式取名)
    ...


# ========== §2.2 tuple:多返回值 + 解包 ==========


def price_range(products: list[dict]) -> tuple[float, float]:
    """
    【场景】列表页筛选条要展示价格区间文案「全场 ¥75.5 ~ ¥2199」,
    需要后端一次返回 (最低价, 最高价) 两个值。

    【转换点】tuple 多返回值。Java 要造 record PriceRange(low, high);
    Python 直接 return a, b(返回一个 tuple),调用方用 low, high = ... 解包。

    任务:返回 (最低价, 最高价) 组成的 tuple。假设 products 非空。
    示例:
        price_range(products)                        -> (75.5, 2199.0)
        price_range([{"name": "水杯", "price": 199.0}])  -> (199.0, 199.0)
        low, high = price_range(products)            # 返回值可直接解包

    提示:
        prices = [p["price"] for p in products]
        return min(prices), max(prices)    # 逗号一写就是 tuple
    """
    # TODO: 在这里写实现(两行:取价 + 返回)
    ...


# ========== §2.3 dict:读取 + 字典推导式 ==========


def build_price_map(products: list[dict]) -> dict[str, float]:
    """
    【场景】前端商品价格速查表:拿到商品名就要 O(1) 查出价格,
    需要后端给一个 name -> price 的映射 dict。

    【转换点】字典推导式。Java 要 stream().collect(toMap(...));
    Python 一行 {k: v for ...}。同名商品时后出现的覆盖先出现的(测试会考)。

    任务:返回 {商品名: 价格} 的 dict。空列表返回 {}。
    示例:
        m = build_price_map(products)
        m["机械键盘"]   -> 599.0
        m["设计模式"]   -> 75.5
        build_price_map([])   -> {}

    提示(字典推导式,骨架 {键表达式: 值表达式 for 变量 in 可迭代对象}):
        {p["name"]: p["price"] for p in products}
    """
    # TODO: 在这里写实现(一行字典推导式)
    ...


# ========== §2.4 dict 分组与聚合:setdefault / defaultdict ==========


def group_by_category(products: list[dict]) -> dict[str, list[dict]]:
    """
    【场景】类目管理页:左侧类目树,右侧该类目下的商品列表,
    需要把商品按 category 归堆:{类目: [商品dict, ...]}。

    【转换点】分组套路。Java 要 groups.computeIfAbsent(k, x -> new ArrayList<>()).add(p);
    Python 用 setdefault:键不存在先放入 [] 再返回它,存在就直接返回已有列表。
    空 dict 上直接 groups[k].append(p) 会 KeyError——这是本题要避开的坑。

    任务:返回按 category 分组的 dict,值是保持原顺序的商品 dict 列表。
         空列表返回 {}。
    示例(products.json:电脑外设 4 个、图书 2 个、影音设备 2 个、生活用品 2 个):
        g = group_by_category(products)
        len(g["电脑外设"])   -> 4
        g["图书"][0]["name"] -> "Python编程:从入门到实践"   # 保持原顺序
        group_by_category([])   -> {}

    提示:
        groups = {}
        for p in products:
            groups.setdefault(p["category"], []).append(p)
        return groups
    """
    # TODO: 在这里写实现(空 dict + setdefault 循环)
    ...


def category_inventory_value(products: list[dict]) -> dict[str, float]:
    """
    【场景】财务报表:每个类目压在库存里的货值 = Σ(该类的 单价 × 库存),
    缺货(stock=0)的商品贡献 0。

    【转换点】defaultdict 聚合。defaultdict(float) 缺键自动给 0.0,
    直接 += 累加,不用先判断键是否存在(对比 Java map.merge(k, v, Double::sum))。

    任务:返回 {类目: 库存货值} 的普通 dict(用 dict(...) 转换,
         避免调用方误触发 defaultdict 的自动造键)。空列表返回 {}。
    示例:
        v = category_inventory_value(products)
        v["电脑外设"]   -> 277715.0   # 599*120 + 159*300 + 2199*45 + 269*220
        v["生活用品"]   -> 47970.0    # 199*0(水杯缺货) + 1599*30(工学椅)
        category_inventory_value([])   -> {}

    提示(文件顶部已 import defaultdict):
        value = defaultdict(float)
        for p in products:
            value[p["category"]] += p["price"] * p["stock"]
        return dict(value)
    """
    # TODO: 在这里写实现(defaultdict(float) + 循环 +=)
    ...


# ========== §2.5 set:推导式去重 ==========


def all_categories(products: list[dict]) -> set[str]:
    """
    【场景】筛选器面板要渲染「类目」下拉选项:从所有商品里抽出 category,
    自动去重(10 个商品只有 4 个类目)。

    【转换点】集合推导式。和列表推导式同构,外层换 {} 就自动去重。
    Java 要 stream().map(...).collect(toSet())。

    任务:返回所有商品类目的 set。空列表返回空 set。
    示例:
        all_categories(products)
            -> {"电脑外设", "图书", "影音设备", "生活用品"}
        all_categories([])   -> set()

    提示(注意返回值是 set,不是 list):
        {p["category"] for p in products}
    """
    # TODO: 在这里写实现(一行集合推导式)
    ...


# ========== §2.6 min + key:综合 ==========


def find_cheapest_per_category(products: list[dict]) -> dict[str, str]:
    """
    【场景】运营做「引流款」分析:每个类目挑出最便宜的商品用于广告投放,
    返回 {类目: 商品名}。

    【转换点】min(xs, key=...) 返回的是整个元素(商品 dict),不是最小值本身;
    并列最低价时返回【先出现】的那个。综合题 = 复用 group_by_category + min。

    任务:返回每个类目中最便宜商品的名字。空列表返回 {}。
    示例:
        find_cheapest_per_category(products)
            -> {"电脑外设": "无线鼠标", "图书": "设计模式",
                "影音设备": "蓝牙音箱", "生活用品": "智能水杯"}
        find_cheapest_per_category([])   -> {}

    提示(复用你上面写的 group_by_category,别重写分组):
        for cat, ps in group_by_category(products).items():
            result[cat] = min(ps, key=lambda p: p["price"])["name"]
    """
    # TODO: 在这里写实现(分组 + min(key=...) 循环)
    ...


# ========== §2.7 可变默认参数陷阱 + 组合过滤 ==========


def filter_products(
    products: list[dict],
    min_price: float | None = None,
    category: str | None = None,
    in_stock_only: bool = False,
) -> list[dict]:
    """
    【场景】商品列表页的筛选器:价格下限、类目、只看有货,三个条件都可传可不传,
    可叠加。这就是大纲里「filter_products 过滤+排序」的完整版。

    【转换点】可变默认参数陷阱:默认参数在函数定义时只求值一次,
    默认值是可变对象会被所有调用共享——所以签名里默认值只写 None / False
    这类不可变对象,需要可变容器一律函数体内现造。
    另外:判可选参数要用 is not None(min_price=0 是 falsy,if min_price: 会漏判)。

    任务:按顺序叠加过滤条件(全部可选):
           - min_price:    只保留 price >= min_price(含边界)
           - category:     只保留该类目(精确匹配)
           - in_stock_only: 只保留 stock > 0
         最后按 price 升序排序,返回商品 dict 列表(保持完整 dict)。
         不许修改传入的 products 列表(用 sorted,不用 .sort())。
    示例:
        filter_products(products, min_price=1000)
            -> [降噪耳机(1299), 人体工学椅(1599), 27寸4K显示器(2199)]   # 升序
        filter_products(products, category="图书")
            -> [设计模式(75.5), Python编程:从入门到实践(89)]
        filter_products(products, in_stock_only=True)   -> 9 个(排除缺货水杯)
        filter_products(products, category="食品")      -> []
        filter_products([])                             -> []

    提示:
        result = products
        if min_price is not None:
            result = [p for p in result if p["price"] >= min_price]
        ... 同理叠加 category 和 in_stock_only ...
        return sorted(result, key=lambda p: p["price"])
    """
    # TODO: 在这里写实现(三段可选过滤 + sorted 升序)
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
    print("price_map 机械键盘:", build_price_map(prods)["机械键盘"])
    print("group counts:", {k: len(v) for k, v in group_by_category(prods).items()})
    print("inventory 电脑外设:", category_inventory_value(prods)["电脑外设"])
    print("categories:", all_categories(prods))
    print("cheapest/cat:", find_cheapest_per_category(prods))
    print("filter >=1000:", [p["name"] for p in filter_products(prods, min_price=1000)])
