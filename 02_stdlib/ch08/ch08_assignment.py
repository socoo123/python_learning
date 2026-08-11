"""
Ch08 作业:collections —— Counter / defaultdict / deque / namedtuple。

场景:你是电商平台的值班运维,要基于访问日志写一份「访问日报」:
状态码分布 → Top IP → 和昨日对比恶化指标 → 按状态码分组排查 →
各接口独立访客数(UV) → 最近 N 条请求 → 最新错误栈 → 结构化日志记录 → 汇总。

9 个任务围绕 assets/mock_data/access_logs.json(20 条访问记录)展开。
在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v

全绿 = 你掌握了 Ch08。

约定:
- logs 是 list[dict],每个 dict 形如
    {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}
- AccessLog(§8.8 的 namedtuple)已作为【脚手架】给出,不用改;
  你的任务是练 to_namedtuple 的转换与使用。
- 每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
  (提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
from collections import Counter, defaultdict, deque, namedtuple


# ========== §8.1 Counter:创建与计数 ==========


def count_by_status(logs: list[dict]) -> Counter:
    """
    【Counter · §8.1】统计每个 HTTP 状态码出现次数,返回 Counter 对象(日报第一段)。

    示例(access_logs.json 的 20 条记录):
        count_by_status(logs)        -> Counter({200: 13, 201: 2, 500: 3, 404: 1, 401: 1})
        count_by_status(logs)[200]   -> 13
        count_by_status(logs)[999]   -> 0   (缺键返回 0,不抛 KeyError)
        count_by_status([])          -> Counter()

    提示:Counter 接受任意【可迭代对象】,自动数每个元素出现几次。
         用生成器表达式产出所有 status,交给 Counter 数。不要转 dict,直接返回 Counter。
    """
    # TODO: Counter(生成器表达式)
    ...


# ========== §8.2 Counter.most_common:Top-N ==========


def top_ips(logs: list[dict], n: int = 3) -> list[tuple[str, int]]:
    """
    【Counter.most_common · §8.2】访问最频繁的前 n 个 IP,返回 [(ip, 次数), ...] 降序。

    示例:
        top_ips(logs, 1)    -> [("192.168.1.1", 5)]
        top_ips(logs, 3)    -> [("192.168.1.1", 5), ("10.0.0.5", 3), ("172.16.0.3", 2)]
        top_ips(logs, 0)    -> []
        top_ips(logs, 100)  -> 全部 8 个 IP(most_common 自动处理,不用特判)

    提示:先 Counter(log["ip"] for log in logs),再调 .most_common(n)。
         次数相同的 IP 按【首次出现顺序】排(172.16.0.3 第 9 条首次登场,领先其他 2 次 IP)。
    """
    # TODO: Counter(...).most_common(n)
    ...


# ========== §8.3 Counter 算术:加减 ==========


def status_diff(today: Counter, yesterday: Counter) -> Counter:
    """
    【Counter 减法 · §8.3】对比「今日 vs 昨日同时段」状态码分布,找出【恶化】的指标。

    示例:
        status_diff(Counter({200: 13, 500: 3, 404: 1}),
                    Counter({200: 10, 500: 1, 404: 5}))
            -> Counter({200: 3, 500: 2})
            # 404 从 5 降到 1(好转),差集里【没有】404 这个键——减法丢弃 ≤0 的键
        status_diff(Counter({200: 5}), Counter({200: 9}))   -> Counter()  (全线好转,空)

    提示:就是一行 today - yesterday。关键不是写出来,而是理解:
         结果里出现的每个键都是「变多了」的指标(该告警的);好转的键直接消失。
    """
    # TODO: 一个减号
    ...


# ========== §8.4 defaultdict(list):分组 ==========


def group_by_status(logs: list[dict]) -> dict[int, list[dict]]:
    """
    【defaultdict(list) · §8.4】按 status 分组,返回普通 dict {状态码: [日志, ...]}。

    示例:
        g = group_by_status(logs)
        len(g[200])   -> 13
        len(g[500])   -> 3    (值班排查:所有 500 的具体是哪几条)
        sorted(g.keys())  -> [200, 201, 401, 404, 500]
        group_by_status([]) -> {}

    提示:groups = defaultdict(list),遍历 logs 往 groups[log["status"]] 里 append。
         缺键时会自动调用 list() 建空 list——注意传的是【工厂 list】不是【实例 []】。
         最后 dict(groups) 转回普通 dict(防止下游误触自动建键 + 便于 JSON 序列化)。
    """
    # TODO: defaultdict(list) + 遍历 append + dict() 转换
    ...


# ========== §8.5 defaultdict(set):UV 去重计数 ==========


def unique_ips_by_path(logs: list[dict]) -> dict[str, int]:
    """
    【defaultdict(set) · §8.5】统计每个接口的独立访客数(UV),返回 {路径: 不同 IP 数}。

    PV(访问量)会骗人:/api/products 被访问 9 次,但背后是几个不同的人?

    示例:
        uv = unique_ips_by_path(logs)
        uv["/api/products"]   -> 7   (9 次访问来自 7 个不同 IP,192.168.1.1 一人刷 3 次)
        uv["/login"]          -> 1
        len(uv)               -> 7   (共 7 个不同路径)
        unique_ips_by_path([]) -> {}

    提示:defaultdict(set) 收集 {路径: {IP 集合}},set 自动去重;
         收集用 uv[log["path"]].add(log["ip"])(set 是 add 不是 append!);
         最后字典推导式 {path: len(ips) for ...} 把集合换成计数。
    """
    # TODO: defaultdict(set) 收集 → {path: len(ips)} 字典推导式
    ...


# ========== §8.6 deque(maxlen):滚动窗口 ==========


def recent_paths(logs: list[dict], n: int = 5) -> list[str]:
    """
    【deque(maxlen) · §8.6】返回【最近 n 条】日志的 path(时间正序),监控大盘滚动窗口。

    示例:
        recent_paths(logs, 3)   -> ["/api/products", "/", "/api/products"]  (第18~20条)
        recent_paths(logs)      -> ["/login", "/api/products", "/api/products", "/", "/api/products"]
        recent_paths(logs, 100) -> 20 个元素(数据不足 n 时保留全部,不报错)
        recent_paths(logs, 0)   -> []
        recent_paths([], 5)     -> []

    提示:recent = deque(maxlen=n),遍历 append(log["path"])。
         满了再 append 时最旧的自动被挤掉——窗口逻辑被 maxlen 吃掉,不用手写 if。
         最后 list(recent) 转成 list 返回。
    """
    # TODO: deque(maxlen=n) + 遍历 append + list()
    ...


# ========== §8.7 deque 双端操作:appendleft ==========


def recent_errors(logs: list[dict], n: int = 3) -> list[dict]:
    """
    【appendleft · §8.7】返回最近 n 条【错误请求】(status >= 400),【最新的在前】。

    监控错误栈语义:最新的错误排最上。从左边压栈,满了挤掉右端(最旧的)。

    示例(日志里共 5 条错误:第 8/11/15/17/18 条):
        recent_errors(logs, 3) 的 path  -> ["/api/products", "/api/products", "/login"]
        recent_errors(logs, 3)[0]["ip"] -> "198.51.100.2"   (第 18 条,最新)
        recent_errors(logs, 10)         -> 全部 5 条,最新在前
        recent_errors([], 3)            -> []

    提示:errors = deque(maxlen=n);遍历时 status >= 400 的 appendleft 进栈。
         appendleft = 进左挤右(时间倒序);别用 append(那是进右挤左,顺序就反了)。
    """
    # TODO: deque(maxlen=n) + status >= 400 时 appendleft + list()
    ...


# ========== §8.8 namedtuple ==========

# 【脚手架】AccessLog 定义已给出(= Java record 的一行版),不用改。
# 本节考点在 tutorial §8.8:读懂这行定义 + 练下面的 ** 解包转换。
AccessLog = namedtuple("AccessLog", ["ip", "method", "path", "status"])


def to_namedtuple(d: dict) -> AccessLog:
    """
    【namedtuple · §8.8】把日志 dict 转成 AccessLog 命名元组(字段名访问,比 d["ip"] 可读)。

    示例:
        log = to_namedtuple({"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200})
        log.ip      -> "1.2.3.4"
        log.status  -> 200
        log[0]      -> "1.2.3.4"   (本质还是 tuple,索引也行)
        log == ("1.2.3.4", "GET", "/", 200)  -> True

        to_namedtuple(logs[0]).path  -> "/api/products"   (mock 第一条)

    提示:用 ** 把 dict【解包】成关键字参数:AccessLog(**d)。
         要求 d 的键和字段名一致(access_logs.json 的记录正好满足)。
         namedtuple 不可变:想「改」用 log._replace(status=299) 返回新实例。
    """
    # TODO: AccessLog(**d)
    ...


# ========== §8.9 综合:组装访问日报 ==========


def build_daily_report(logs: list[dict]) -> dict:
    """
    【综合 · §8.9】一次算出完整访问日报。这是 §8.1–§8.7 的大合奏——四大件各管一段。

    返回 dict 的 schema(键名固定,测试逐个验):
        "total":         日志总条数
        "status_counts": {状态码: 次数} 普通 dict        ← Counter(§8.1)
        "top_ips":       前 3 个 [(ip, 次数)]            ← most_common(§8.2)
        "path_uv":       {路径: 独立 IP 数}              ← defaultdict(set)(§8.5)
        "latest_paths":  最近 5 条 path,时间正序         ← deque(maxlen)(§8.6)
        "latest_errors": 最近 3 条错误日志 dict,最新在前 ← appendleft(§8.7)

    示例(access_logs.json 的真实结果):
        r = build_daily_report(logs)
        r["total"]          -> 20
        r["status_counts"]  -> {200: 13, 201: 2, 500: 3, 404: 1, 401: 1}
        r["top_ips"]        -> [("192.168.1.1", 5), ("10.0.0.5", 3), ("172.16.0.3", 2)]
        r["path_uv"]["/api/products"] -> 7
        r["latest_paths"]   -> ["/login", "/api/products", "/api/products", "/", "/api/products"]
        [e["ip"] for e in r["latest_errors"]] -> ["198.51.100.2", "198.51.100.2", "203.0.113.5"]
        build_daily_report([])  -> {"total": 0, "status_counts": {}, "top_ips": [],
                                   "path_uv": {}, "latest_paths": [], "latest_errors": []}

    提示:每个键对应你前面写过的一段逻辑,这里【内联】实现(别调前面的函数,
         保持本题自包含)。空列表不用特判——四大件对空输入天然返回空。
    """
    # TODO: Counter × 2 + defaultdict(set) + deque × 2,组装 6 键 dict
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch08/ch08_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    logs = load_mock_json("access_logs.json")

    report = build_daily_report(logs)
    print("===== 访问日报 =====")
    for key, value in report.items():
        print(f"{key}: {value}")

    yesterday = Counter({200: 10, 500: 1, 404: 5})
    print("\n对比昨日,恶化的状态码:", dict(status_diff(count_by_status(logs), yesterday)))

    print("\n第一条日志结构化:", to_namedtuple(logs[0]))
