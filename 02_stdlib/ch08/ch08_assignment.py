"""
Ch08 作业:collections —— Counter / defaultdict / deque / namedtuple。

5 个任务围绕「访问日志分析」(运维场景预热)。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v

全绿 = 你掌握了 Ch08。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)

约定:logs 是 list[dict],每个 dict 形如
    {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}
mock 数据在 assets/mock_data/access_logs.json(20 条访问记录)。
"""
from collections import Counter, defaultdict, deque, namedtuple


# ========== §8.1 Counter ==========


def count_by_status(logs: list[dict]) -> Counter:
    """
    【Counter · §8.1】统计每个 HTTP 状态码出现次数,返回 Counter 对象。

    示例(access_logs.json 里 200 出现 13 次):
        count_by_status(logs)[200]  -> 13
        count_by_status(logs)[999]  -> 0   (不存在的键返回 0,不抛 KeyError)

    思路:Counter 接受任意【可迭代对象】,自动数每个元素出现几次。
         Counter(log["status"] for log in logs) —— 生成器产出所有 status,Counter 数。
    """
    # TODO: Counter(生成器表达式)
    ...


# ========== §8.2 Counter.most_common ==========


def top_ips(logs: list[dict], n: int = 3) -> list[tuple[str, int]]:
    """
    【Counter.most_common · §8.2】访问最频繁的前 n 个 IP,返回 [(ip, 次数), ...] 降序。

    示例:
        top_ips(logs, 1)   -> [("192.168.1.1", 5)]
        top_ips(logs, 2)[1] -> ("10.0.0.5", 3)

    思路:先 Counter(log["ip"] for log in logs),再调 .most_common(n)
         返回前 n 个 (元素, 次数) 元组,按次数降序。
    """
    # TODO: Counter(...).most_common(n)
    ...


# ========== §8.3 defaultdict(分组)==========


def group_by_status(logs: list[dict]) -> dict[int, list[dict]]:
    """
    【defaultdict · §8.3】按 status 分组,返回 {状态码: [日志, ...]}。

    示例:
        g = group_by_status(logs)
        len(g[200])  -> 13
        len(g[500])  -> 3

    思路:defaultdict(list) 造一个「键不存在时自动建空 list」的字典:
        groups = defaultdict(list)
        for log in logs:
            groups[log["status"]].append(log)   # 不存在的 status 会自动先建 []
        return dict(groups)   # 转回普通 dict(可选,便于测试/打印)
    """
    # TODO: defaultdict(list) + 遍历 append
    ...


# ========== §8.4 deque(双端队列 + maxlen)==========


def recent_paths(logs: list[dict], n: int = 5) -> list[str]:
    """
    【deque · §8.4】返回【最近 n 条】日志的 path。用 deque(maxlen=n) 自动只留最后 n 个。

    示例:
        recent_paths(logs, 3)  -> ["/api/products", "/", "/api/products"]  (最后3条的path)

    思路:deque(maxlen=n) 是个【定长】双端队列——满了再 append,最旧的自动被挤掉。
        recent = deque(maxlen=n)
        for log in logs:
            recent.append(log["path"])
        return list(recent)   # 遍历完后,deque 里恰好是最新的 n 个
    """
    # TODO: deque(maxlen=n) + 遍历 append + list()
    ...


# ========== §8.5 namedtuple ==========


# TODO: 用 namedtuple 定义一个 AccessLog 命名元组,字段顺序:ip, method, path, status
#   骨架:AccessLog = namedtuple("AccessLog", ["ip", "method", "path", "status"])
AccessLog = None   # ← 把这行换成 namedtuple(...) 定义


def to_namedtuple(d: dict) -> AccessLog:
    """
    【namedtuple · §8.5】把日志 dict 转成 AccessLog 命名元组。

    示例:
        log = to_namedtuple({"ip":"1.2.3.4","method":"GET","path":"/","status":200})
        log.ip      -> "1.2.3.4"   (按字段名访问,比 d["ip"] 可读)
        log.status  -> 200

    思路:用 ** 把字典【解包】成关键字参数:AccessLog(**d)。
         要求 d 的键和 namedtuple 字段名一致。
    """
    # TODO: AccessLog(**d)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch08/ch08_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    logs = load_mock_json("access_logs.json")
    print("status counts:", dict(count_by_status(logs)))
    print("top3 ips:", top_ips(logs, 3))
    print("recent 3 paths:", recent_paths(logs, 3))
    print("as namedtuple:", to_namedtuple(logs[0]))
