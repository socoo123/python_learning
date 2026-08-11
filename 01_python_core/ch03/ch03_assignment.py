"""
Ch03 作业:控制流、迭代器、生成器、推导式。

场景:你负责电商后台的「数据 + 监控」两条线——
白天给运营写商品文案、榜单、对接老 ERP(products.json,10 个商品);
晚上写日志巡检脚本和监控大盘统计(logs.json,20 行样本,
代表线上 GB 级日志流——所以流式处理是本章的灵魂)。

8 个函数,每个刚好砸在一个迭代知识点上。
在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch03/test_ch03_assignment.py -v

全绿 = 你掌握了 Ch03。

约定:
- products 是 list[dict],每个 dict 形如:
    {"id": 1, "name": "机械键盘", "category": "电脑外设",
     "price": 599.0, "stock": 120, "sku": "KB-001"}
- logs 是 list[str](或任何可迭代对象),每行形如:
    "2026-07-18 09:00:03 ERROR Failed to connect to redis at localhost:6379"
  (logs.json 共 20 行:INFO 10 条 / WARN 5 条 / ERROR 5 条)
"""
from collections.abc import Iterable


# ========== §3.1 列表推导式:过滤 + 变换 ==========


def cheap_product_names(products: list[dict], max_price: float = 200) -> list[str]:
    """
    【场景】运营要发一张「满 200 减 30」优惠券,先圈出价格【低于 200】
    的商品作为可用范围,要一份商品名清单(保持后台列表的原顺序)。

    【转换点】列表推导式。Java 要 stream().filter(...).map(...).toList();
    Python 一行 [表达式 for 变量 in 序列 if 条件],注意过滤 if 写在【最后】。

    任务:返回价格【严格小于】 max_price 的商品名列表。
         边界:价格恰好等于 max_price 不算(测试会查);空列表返回 []。
    示例(products.json 里 <200 的有 4 个:无线鼠标159、Python编程89、设计模式75.5、智能水杯199):
        cheap_product_names(products, max_price=200)
            -> ["无线鼠标", "Python编程:从入门到实践", "设计模式", "智能水杯"]
        cheap_product_names(products, max_price=100)
            -> ["Python编程:从入门到实践", "设计模式"]
        cheap_product_names([], max_price=200)   -> []

    提示:
        return [p["name"] for p in products if p["price"] < max_price]
    """
    # TODO: 一行列表推导式(过滤 if 在 for 后面)
    ...


# ========== §3.2 for-else:找遍了都没有 ==========


def find_first_error(logs: Iterable[str]) -> str | None:
    """
    【场景】监控巡检脚本:在日志流里找【第一条】含 ERROR 的行,交给告警系统;
    如果全部干净(一条 ERROR 都没有),返回 None 表示「本轮平安」。

    【转换点】for-else,Java 完全没有的语法:else 在循环【没有被中途
    return/break 打断】时执行——正好表达「找遍了都没找到」。
    Java 要 boolean found 标志位 + 循环后再判断,Python 把意图写进结构里。
    注意:空列表一次都不循环,也算「完整跑完」→ 直接进 else。

    任务:返回第一条含 "ERROR" 的完整日志行;没有则返回 None。
         logs 可能是 list,也可能是生成器(只能遍历一次)——for 都适用。
    示例(logs.json 第一条 ERROR 在第 4 行):
        find_first_error(logs)
            -> "2026-07-18 09:00:03 ERROR Failed to connect to redis at localhost:6379"
        find_first_error(["INFO ok", "WARN meh"])   -> None
        find_first_error([])                        -> None

    提示:
        for line in logs:
            if "ERROR" in line:
                return line      # 找到即返回,else 不会执行
        else:
            return None          # 循环完整跑完 → 一条 ERROR 都没有
    """
    # TODO: for + if return + else return None
    ...


# ========== §3.3 enumerate / zip:遍历两大神器 ==========


def indexed_summary(products: list[dict]) -> list[str]:
    """
    【场景】运营晨会的语音播报文案:给商品清单加上【从 1 开始】的序号,
    格式 "N. 商品名 (¥价格)",交给 TTS 念出来。

    【转换点】enumerate(seq, start)。Java 要 for (int i=0; i<n; i++) 手动
    维护下标;Python 用 enumerate 同时拿到序号和元素,start=1 让序号从 1 开始。
    别写 for i in range(len(products)) —— 那是 C/Java 遗风。

    任务:返回格式化字符串列表,序号从 1 开始;空列表返回 []。
    示例:
        indexed_summary(products)[0]   -> "1. 机械键盘 (¥599.0)"
        indexed_summary(products)[2]   -> "3. 27寸4K显示器 (¥2199.0)"
        indexed_summary([])            -> []

    提示:
        return [f"{i}. {p['name']} (¥{p['price']})" for i, p in enumerate(products, 1)]
    """
    # TODO: enumerate + 列表推导式 + f-string
    ...


def merge_product_lists(names: list[str], prices: list[float]) -> list[tuple[str, float]]:
    """
    【场景】对接公司老 ERP 系统:它的接口不返回 JSON 对象数组,而是返回两个
    【平行数组】——names[i] 和 prices[i] 是同一个商品。你要把它们合并成
    [(name, price), ...] 供新系统使用。

    【转换点】zip:把多个序列「拉链式」配对成元组,返回的是【迭代器】,
    要 list(...) 物化。Java 没有内置 zip,只能 for-i 按下标配对。
    ⚠️ zip 按【最短】的截断:names 3 个、prices 2 个 → 结果只有 2 对,
    多出来的悄悄丢掉,不报错(数据对不齐是常态,这个行为是特性也是坑)。

    任务:返回 [(name, price), ...];不等长按最短的截断(zip 自带语义,不用特判);
         任一为空返回 []。
    示例:
        merge_product_lists(["键盘", "鼠标"], [599.0, 159.0])
            -> [("键盘", 599.0), ("鼠标", 159.0)]
        merge_product_lists(["a", "b", "c"], [1.0, 2.0])
            -> [("a", 1.0), ("b", 2.0)]        # "c" 被截断丢弃
        merge_product_lists([], [])             -> []

    提示:
        return list(zip(names, prices))
    """
    # TODO: zip 配对 + list 物化
    ...


# ========== §3.4 解包与星号:first, *rest ==========


def champion_and_rest(names: list[str]) -> tuple[str | None, list[str]]:
    """
    【场景】热销榜 UI:第 1 名渲染成「冠军大卡」,其余名次小字列出。
    需要把商品名列表拆成 (第一名, 其余名字列表) 两个部分。

    【转换点】星号解包 first, *rest = names,Java 完全没有
    (最接近的是 get(0) + subList(1, n),还要拷贝)。
    隐藏卖点:【迭代器不能切片】(it[0] 直接 TypeError),但能星号解包——
    处理「只能遍历一次」的数据流时,这是唯一的拆分手段。
    ⚠️ 空序列解包会 ValueError,要先判空。

    任务:返回 (第一名, 其余列表);空列表返回 (None, []);只有 1 个返回 (它, [])。
    示例:
        champion_and_rest(["机械键盘", "无线鼠标", "27寸4K显示器"])
            -> ("机械键盘", ["无线鼠标", "27寸4K显示器"])
        champion_and_rest(["机械键盘"])   -> ("机械键盘", [])
        champion_and_rest([])             -> (None, [])

    提示:
        if not names:
            return None, []
        first, *rest = names
        return first, rest
    """
    # TODO: 判空 + 星号解包
    ...


# ========== §3.5 迭代器协议:只能走一次 ==========


def top_n_by_price(product_iter: Iterable[dict], n: int = 3) -> list[str]:
    """
    【场景】商品数据从网络/文件【流式】读取,到你手上是个只能遍历一次的
    迭代器。运营要看「价格 Top N」榜单——但迭代器没有 len()、不能切片、
    不能排序,唯一办法是先物化成列表。

    【转换点】迭代器的一次性:list(it) 把游标从头拉到尾,收集成列表
    (迭代器随之耗尽,再 list 就是 [])。物化后它就是普通列表,
    可以 sorted、切片、反复遍历——放弃惰性,换随机访问。

    任务:消费 product_iter,返回价格最高的前 n 个商品名(降序);
         不足 n 个返回全部;空迭代器返回 []。
    示例(products.json):
        top_n_by_price(iter(products), n=3)
            -> ["27寸4K显示器", "人体工学椅", "降噪耳机"]   # 2199 / 1599 / 1299
        top_n_by_price(iter(products), n=100)   -> 全部 10 个
        top_n_by_price(iter([]))                -> []

    提示:
        products = list(product_iter)      # 物化(迭代器耗尽)
        top = sorted(products, key=lambda p: p["price"], reverse=True)[:n]
        return [p["name"] for p in top]
    """
    # TODO: list() 物化 → sorted 降序 → 切片 → 取 name
    ...


# ========== §3.6 生成器 yield:可暂停的机器 ==========


def iter_error_lines(lines: Iterable[str]):
    """
    【场景】线上日志 GB 级,绝不能 readlines() 全读进内存。写一个【惰性】
    过滤器:逐个产出含 "ERROR" 的行,调用方要一条给一条,内存里始终只有一行。

    【转换点】yield——函数体里只要出现 yield,函数就变成【生成器函数】:
    调用它不执行函数体,只返回一台「可暂停的机器」(生成器对象);
    每次 next() 运转到下一个 yield,产出值并冻结现场。
    写成 return 就完了:return 会结束函数,只能交出第一条。

    任务:产出(不是返回!)所有含 "ERROR" 的行;没有则一条都不产出。
    示例(logs.json 共 5 条 ERROR):
        list(iter_error_lines(logs))   -> 长度 5,每条都含 "ERROR"
        list(iter_error_lines(["INFO ok"]))   -> []

    提示:
        for line in lines:
            if "ERROR" in line:
                yield line        # 产出并暂停,下次 next 从这里继续
    """
    # TODO: for + if + yield(不是 return!)
    ...


# ========== §3.7 生成器表达式:推导式的惰性版 ==========


def count_error_logs(lines: Iterable[str], keyword: str = "ERROR") -> int:
    """
    【场景】监控大盘要展示「过去 1 小时各级别日志条数」。日志是流式读出来的,
    只需要【计数】,行本身用完就扔——别把 1000 万行物化成列表再数。

    【转换点】生成器表达式 sum(1 for ...):列表推导式的 [] 换成 (),
    就变成惰性生成器,边遍历边计数,内存恒定。sum() 直接消费它。
    对比:sum([1 for ...]) 会先把一堆 1 物化成列表再求和,白白占内存。
    (函数调用的括号里,生成器表达式的 () 可以省略,这是官方许可的简写。)

    任务:统计含 keyword 的行数;keyword 默认 "ERROR";空输入返回 0。
    示例(logs.json:ERROR 5 条、WARN 5 条、INFO 10 条):
        count_error_logs(logs)                  -> 5
        count_error_logs(logs, keyword="WARN")  -> 5
        count_error_logs(logs, keyword="INFO")  -> 10
        count_error_logs([])                    -> 0

    提示:
        return sum(1 for line in lines if keyword in line)
        (也可以复用你上面写的生成器:sum(1 for _ in iter_error_lines(lines)))
    """
    # TODO: sum + 生成器表达式(圆括号,不是方括号!)
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
    print("first error:", find_first_error(logs))
    print("indexed[0]:", indexed_summary(prods)[0])
    print("merged[0]:", merge_product_lists(["键盘", "鼠标"], [599.0, 159.0])[0])
    print("champion:", champion_and_rest(["27寸4K显示器", "人体工学椅", "降噪耳机"]))
    print("top3:", top_n_by_price(iter(prods), 3))
    print("error lines:", len(list(iter_error_lines(logs))))
    print("count ERROR/WARN/INFO:",
          count_error_logs(logs), count_error_logs(logs, "WARN"), count_error_logs(logs, "INFO"))
