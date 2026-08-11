"""
Ch01 作业:从 Java 到 Python 的思维转换(电商后台场景)。

场景:你在给一个电商后台写一组工具函数——算订单金额、解析 SKU、
生成价格标签、找补货商品、写审计日志、做盘点汇总。
8 个函数,每个刚好落在一个 Java → Python 的【转换点】上。

在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch01/test_ch01_assignment.py -v

全绿 = 你掌握了 Ch01。

约定:products 是 list[dict],每个 dict 形如:
    {"id": 1, "name": "机械键盘", "category": "电脑外设",
     "price": 599.0, "stock": 120, "sku": "KB-001"}
"""


# ========== §1.1 动态类型 + 类型注解 ==========


def calc_line_total(price: float, quantity: int) -> float:
    """
    【场景】订单中心:计算一个订单行的金额(单价 × 数量)。

    【转换点】动态类型。Java 里 `double calc(double price, int qty)` 类型错了编译就挂;
    Python 的注解 `: float` 只是提示,运行时不强制——传 int 也能算(动态强类型)。

    任务:返回 price * quantity。
    示例:
        calc_line_total(599.0, 2)     -> 1198.0
        calc_line_total(89, 3)        -> 267      (int 单价也能算,注解不强制)
        calc_line_total(599.0, 0)     -> 0.0
    """
    # TODO: 在这里写实现(一行)
    ...


# ========== §1.2 元组与解包 ==========


def parse_sku(sku: str) -> tuple[str, int]:
    """
    【场景】仓储系统:SKU 编码规则是 "类目前缀-序号",如 "KB-001" 表示键盘类目第 1 号。
    现在要把 SKU 拆成 (前缀, 序号) 两部分,序号转成 int(去掉前导零,方便排序比较)。

    【转换点】元组打包/解包。Java 要返回两个值得造 record/Pair;Python 返回元组即可。
    而 `a, b = 右边` 的解包赋值,让你一行接住两个值。

    任务:把 sku 按 "-" 拆开,返回 (前缀字符串, 序号 int)。
    示例:
        parse_sku("KB-001")   -> ("KB", 1)
        parse_sku("BK-005")   -> ("BK", 5)

    提示:
        sku.split("-")        -> ["KB", "001"]  (split 返回 list)
        prefix, num = ...     解包:一行把 list 两项分别赋给两个变量
        int("001")            -> 1              (int() 自动去前导零)
    """
    # TODO: 在这里写实现(两行:解包 + 返回)
    ...


# ========== §1.3 默认参数 + f-string + join + 推导式 ==========


def format_price_tag(name: str, price: float, currency: str = "¥") -> str:
    """
    【场景】运营后台:生成商品价格标签文案,默认人民币,可切换美元。

    【转换点】默认参数。Java 要为「可选货币符号」写两个重载方法;
    Python 一个函数 + 默认参数搞定,调用方可以只传前两个、或用关键字跳着传。

    任务:返回 "名称 货币符号价格(保留 2 位小数)"。
    示例:
        format_price_tag("机械键盘", 599.0)               -> "机械键盘 ¥599.00"
        format_price_tag("无线鼠标", 159.0, currency="$") -> "无线鼠标 $159.00"
        format_price_tag("设计模式", 75.5)                -> "设计模式 ¥75.50"

    提示(f-string 格式说明,价格两位小数):
        f"{name} {currency}{price:.2f}"
    """
    # TODO: 在这里写实现(一行 f-string)
    ...


def render_price_list(products: list[dict], currency: str = "¥") -> str:
    """
    【场景】对账导出:把商品列表渲染成多行文本,每行一个价格标签,行之间用换行分隔。
    直接复用上面的 format_price_tag。

    【转换点】`分隔符.join(列表)` + 列表推导式。
    Java 是 String.join("\\n", list);Python 主语是分隔符(别写反)。
    列表推导式对应 Java 的 stream().map().collect()。

    任务:对每个商品调用 format_price_tag(name, price, currency),
         把所有行用 "\\n" 拼成一个大字符串返回。空列表返回空串 ""。
    示例:
        render_price_list([{"name": "无线鼠标", "price": 159.0},
                           {"name": "设计模式", "price": 75.5}])
            -> "无线鼠标 ¥159.00\\n设计模式 ¥75.50"   (\\n 是换行符)
        render_price_list([])                          -> ""

    提示:
        lines = [format_price_tag(p["name"], p["price"], currency) for p in products]
        return "\\n".join(lines)
    """
    # TODO: 在这里写实现(提示:推导式 + join)
    ...


# ========== §1.4 truthiness 真值表 ==========


def first_in_stock_name(products: list[dict]) -> str | None:
    """
    【场景】推荐位:首页"猜你喜欢"要展示第一个有货的商品名;全缺货(或列表为空)就不展示。

    【转换点】truthiness。Java 要写 `if (list == null || list.isEmpty())`;
    Python 里 空列表/0/None/"" 都是 falsy,`if not x:` 一句判空。
    本题里 `if p["stock"]:` 利用「0 是 falsy」刚好表达「有库存」。

    任务:返回第一个 stock > 0 的商品的 name;一个都没有(或列表为空)返回 None。
    示例:
        first_in_stock_name([{"name": "智能水杯", "stock": 0},
                             {"name": "机械键盘", "stock": 120}])   -> "机械键盘"
        first_in_stock_name([{"name": "智能水杯", "stock": 0}])     -> None
        first_in_stock_name([])                                     -> None

    提示:
        for p in products:
            if p["stock"]:        # 0 是 falsy,自动跳过缺货
                return p["name"]
        return None               # 循环没 return,说明全缺货/空列表
    """
    # TODO: 在这里写实现
    ...


# ========== §1.5 一切皆对象 + repr vs str ==========


def debug_repr(value) -> str:
    """
    【场景】排查线上 bug:审计日志里要打印变量值,且必须【无歧义】——
    字符串要带引号(区分值 "hi" 和名字 hi),还要附上类型名。

    【转换点】一切皆对象 + repr vs str。Java 只有 toString() 一个钩子;
    Python 分两个:str() 给人看(字符串不带引号),repr() 给程序看(字符串带引号)。
    类型名用 type(value).__name__ 取(类似 Java 的 obj.getClass().getSimpleName())。

    任务:返回 "<repr> (<类型名>)"。
    示例:
        debug_repr(42)      -> "42 (int)"
        debug_repr("hi")    -> "'hi' (str)"     注意引号!
        debug_repr([1, 2])  -> "[1, 2] (list)"
        debug_repr(3.14)    -> "3.14 (float)"

    提示:
        f"{repr(value)} ({type(value).__name__})"
    """
    # TODO: 在这里写实现(一行)
    ...


# ========== §1.6 import + dict + 推导式(带过滤)+ sum/min/max ==========


def load_out_of_stock_skus() -> list[str]:
    """
    【场景】补货工单:从共享 mock 数据里读出所有商品,挑出缺货(stock == 0)的,
    返回它们的 sku 列表,交给采购系统。

    【转换点】import 机制 + dict 取值 + 带过滤的列表推导式。
    Java 的 import 是编译期声明;Python 的 import 是运行时执行的语句。
    带 if 的推导式 = Java stream 的 filter + map 合体。

    任务:用 conftest 提供的 load_mock_json 读 "products.json",
         返回缺货商品的 sku 列表(保持原顺序)。
    示例(products.json 里只有 "智能水杯" stock 为 0):
        load_out_of_stock_skus()   -> ["CP-009"]

    提示:
        from conftest import load_mock_json
        data = load_mock_json("products.json")        # list[dict]
        return [p["sku"] for p in data if p["stock"] == 0]
    """
    # TODO: 在这里写实现
    ...


def inventory_summary(products: list[dict]) -> dict:
    """
    【场景】盘点报表:给管理层一个总览 dict——多少种商品、价格区间、总货值。

    【转换点】综合:len() + min()/max()/sum() 配合生成表达式 + dict 字面量。
    Java 要 Stream 的 min/max/summingDouble + Collectors;Python 内置函数一行一个。

    任务:返回 dict,4 个键:
        "count":       商品种数(len)
        "min_price":   最低价(min)
        "max_price":   最高价(max)
        "total_value": 总货值 = sum(每个商品 price * stock)
    假设 products 非空。
    示例(products.json 全量 10 个商品):
        inventory_summary(products)
            -> {"count": 10, "min_price": 75.5, "max_price": 2199.0, "total_value": 549055.0}

    提示(括号版推导式叫生成表达式,直接喂给 min/max/sum,省一个临时列表):
        min(p["price"] for p in products)
        sum(p["price"] * p["stock"] for p in products)
    """
    # TODO: 在这里写实现(一个 dict 字面量,4 个键)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 01_python_core/ch01/ch01_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    prods = load_mock_json("products.json")
    print("calc_line_total(599.0, 2) =", calc_line_total(599.0, 2))
    print("parse_sku('KB-001') =", parse_sku("KB-001"))
    print("format_price_tag('机械键盘', 599.0) =", format_price_tag("机械键盘", 599.0))
    print("render_price_list(prods[:2]) =", repr(render_price_list(prods[:2])))
    print("first_in_stock_name(prods) =", first_in_stock_name(prods))
    print("debug_repr('hi') =", debug_repr("hi"))
    print("load_out_of_stock_skus() =", load_out_of_stock_skus())
    print("inventory_summary(prods) =", inventory_summary(prods))
