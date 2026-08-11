"""
Ch08 作业测试。运行: uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v

每个函数一个 TestXxx 类(命名 = Test + 函数名 PascalCase,web 端按类名单跑)。
覆盖:正常 case ≥ 2 + 边界 case(空输入 / n=0 / n 超总量 / 缺键)≥ 1,
另配「手工小数据」用例防止对着 mock 数据硬编码。
"""
from collections import Counter

import pytest

from ch08_assignment import (
    AccessLog,
    build_daily_report,
    count_by_status,
    group_by_status,
    recent_errors,
    recent_paths,
    status_diff,
    to_namedtuple,
    top_ips,
    unique_ips_by_path,
)
from conftest import load_mock_json


@pytest.fixture
def access_logs():
    return load_mock_json("access_logs.json")


# ---------- count_by_status:Counter 创建与计数 ----------
class TestCountByStatus:
    def test_returns_counter(self, access_logs):
        assert isinstance(count_by_status(access_logs), Counter)

    def test_counts_match(self, access_logs):
        c = count_by_status(access_logs)
        assert c[200] == 13
        assert c[500] == 3
        assert c[201] == 2
        assert c[404] == 1
        assert c[401] == 1

    def test_total_preserved(self, access_logs):
        assert sum(count_by_status(access_logs).values()) == 20

    def test_missing_key_returns_zero(self, access_logs):
        # 缺键返 0 是 Counter 相对普通 dict 的核心特性
        assert count_by_status(access_logs)[999] == 0

    def test_empty_logs(self):
        assert count_by_status([]) == Counter()

    def test_handmade_logs(self):
        # 手工小数据,防止对着 mock 答案硬编码
        logs = [{"status": 200}, {"status": 200}, {"status": 503}]
        c = count_by_status(logs)
        assert c[200] == 2
        assert c[503] == 1


# ---------- top_ips:Counter.most_common ----------
class TestTopIps:
    def test_top1(self, access_logs):
        assert top_ips(access_logs, 1) == [("192.168.1.1", 5)]

    def test_top3_exact_with_tie(self, access_logs):
        # 6 个 IP 并列 2 次,172.16.0.3 首次出现最早(第 9 条)排最前
        assert top_ips(access_logs, 3) == [
            ("192.168.1.1", 5),
            ("10.0.0.5", 3),
            ("172.16.0.3", 2),
        ]

    def test_returns_list_of_2tuples(self, access_logs):
        assert all(isinstance(t, tuple) and len(t) == 2 for t in top_ips(access_logs, 3))

    def test_n_zero(self, access_logs):
        assert top_ips(access_logs, 0) == []

    def test_n_over_total(self, access_logs):
        assert len(top_ips(access_logs, 100)) == 8

    def test_empty_logs(self):
        assert top_ips([], 3) == []

    def test_handmade_logs(self):
        logs = [{"ip": "9.9.9.9"}, {"ip": "1.1.1.1"}, {"ip": "9.9.9.9"}]
        assert top_ips(logs, 2) == [("9.9.9.9", 2), ("1.1.1.1", 1)]


# ---------- status_diff:Counter 减法 ----------
class TestStatusDiff:
    def test_regression_found(self, access_logs):
        today = count_by_status(access_logs)
        yesterday = Counter({200: 10, 500: 1, 404: 5})
        diff = status_diff(today, yesterday)
        assert diff[200] == 3    # 13 - 10
        assert diff[500] == 2    # 3 - 1,恶化,该告警
        assert diff[201] == 2    # 昨天没有,今天新增

    def test_improved_keys_dropped(self, access_logs):
        # 404 从 5 降到 1(好转)——减法结果里键直接消失,不是 0 也不是负数
        today = count_by_status(access_logs)
        diff = status_diff(today, Counter({200: 10, 500: 1, 404: 5}))
        assert 404 not in diff
        assert diff[404] == 0   # 但缺键返 0,读取依然安全

    def test_all_improved_gives_empty(self):
        diff = status_diff(Counter({200: 5}), Counter({200: 9}))
        assert isinstance(diff, Counter)
        assert len(diff) == 0

    def test_both_empty(self):
        assert status_diff(Counter(), Counter()) == Counter()


# ---------- group_by_status:defaultdict(list) ----------
class TestGroupByStatus:
    def test_group_sizes(self, access_logs):
        g = group_by_status(access_logs)
        assert len(g[200]) == 13
        assert len(g[500]) == 3
        assert len(g[404]) == 1
        assert len(g[201]) == 2

    def test_keys_are_all_status_codes(self, access_logs):
        assert set(group_by_status(access_logs).keys()) == {200, 201, 401, 404, 500}

    def test_no_logs_lost(self, access_logs):
        assert sum(len(v) for v in group_by_status(access_logs).values()) == 20

    def test_returns_plain_dict(self, access_logs):
        # 必须 dict(groups) 转回普通 dict,防下游误触自动建键
        assert type(group_by_status(access_logs)) is dict

    def test_group_content(self, access_logs):
        g = group_by_status(access_logs)
        assert all(log["status"] == 500 for log in g[500])

    def test_empty_logs(self):
        assert group_by_status([]) == {}

    def test_handmade_logs(self):
        logs = [{"status": 200, "ip": "a"}, {"status": 404, "ip": "b"}, {"status": 200, "ip": "c"}]
        g = group_by_status(logs)
        assert [log["ip"] for log in g[200]] == ["a", "c"]
        assert len(g[404]) == 1


# ---------- unique_ips_by_path:defaultdict(set) ----------
class TestUniqueIpsByPath:
    def test_products_uv(self, access_logs):
        # 9 次访问 / 7 个不同 IP(192.168.1.1 一人刷 3 次只算 1)
        assert unique_ips_by_path(access_logs)["/api/products"] == 7

    def test_single_visitor_paths(self, access_logs):
        uv = unique_ips_by_path(access_logs)
        assert uv["/login"] == 1
        assert uv["/admin"] == 1
        assert uv["/api/orders/1"] == 1

    def test_all_paths_present(self, access_logs):
        uv = unique_ips_by_path(access_logs)
        assert len(uv) == 7
        assert uv["/"] == 2
        assert uv["/api/orders"] == 2

    def test_empty_logs(self):
        assert unique_ips_by_path([]) == {}

    def test_handmade_dedup(self):
        logs = [
            {"path": "/a", "ip": "1.1.1.1"},
            {"path": "/a", "ip": "1.1.1.1"},   # 同 IP 重复,只算一次
            {"path": "/a", "ip": "2.2.2.2"},
            {"path": "/b", "ip": "1.1.1.1"},   # 同 IP 访问不同路径,各算各的
        ]
        assert unique_ips_by_path(logs) == {"/a": 2, "/b": 1}


# ---------- recent_paths:deque(maxlen) ----------
class TestRecentPaths:
    def test_last_three(self, access_logs):
        assert recent_paths(access_logs, 3) == ["/api/products", "/", "/api/products"]

    def test_default_n_is_5(self, access_logs):
        assert recent_paths(access_logs) == [
            "/login", "/api/products", "/api/products", "/", "/api/products",
        ]

    def test_n_more_than_total(self, access_logs):
        # 数据不足 n 时保留全部,不报错
        assert len(recent_paths(access_logs, 100)) == 20

    def test_n_zero(self, access_logs):
        assert recent_paths(access_logs, 0) == []

    def test_empty_logs(self):
        assert recent_paths([], 5) == []

    def test_preserves_order(self, access_logs):
        # deque 是正序滚动:最后两条是第 19 条(/)和第 20 条(/api/products)
        assert recent_paths(access_logs, 2) == ["/", "/api/products"]


# ---------- recent_errors:appendleft 双端 ----------
class TestRecentErrors:
    def test_last_three_newest_first(self, access_logs):
        result = recent_errors(access_logs, 3)
        assert [e["path"] for e in result] == ["/api/products", "/api/products", "/login"]

    def test_newest_is_last_log_error(self, access_logs):
        # 最新的错误是第 18 条(198.51.100.2 的 500)
        result = recent_errors(access_logs, 3)
        assert result[0]["ip"] == "198.51.100.2"
        assert result[0]["status"] == 500

    def test_n_over_error_count(self, access_logs):
        # 只有 5 条错误,n=10 返回全部 5 条,最新在前
        result = recent_errors(access_logs, 10)
        assert len(result) == 5
        assert [e["path"] for e in result] == [
            "/api/products", "/api/products", "/login", "/admin", "/api/orders/1",
        ]

    def test_no_errors(self):
        logs = [{"status": 200}, {"status": 201}]
        assert recent_errors(logs, 3) == []

    def test_empty_logs(self):
        assert recent_errors([], 3) == []


# ---------- to_namedtuple:namedtuple 转换(AccessLog 为脚手架) ----------
class TestToNamedtuple:
    def test_field_access_by_name(self):
        log = to_namedtuple({"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200})
        assert log.ip == "1.2.3.4"
        assert log.status == 200

    def test_real_log(self, access_logs):
        log = to_namedtuple(access_logs[0])
        assert isinstance(log, AccessLog)
        assert log.path == "/api/products"
        assert log.method == "GET"

    def test_index_and_tuple_equality(self):
        log = to_namedtuple({"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200})
        assert log[0] == "1.2.3.4"                       # 本质是 tuple,索引也行
        assert log == ("1.2.3.4", "GET", "/", 200)       # 和等值 tuple 相等

    def test_immutable(self):
        log = to_namedtuple({"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200})
        assert isinstance(log, AccessLog)   # 先确保转换成功,再验不可变
        with pytest.raises(AttributeError):
            log.ip = "8.8.8.8"      # 不可变;要「改」用 log._replace(ip=...)

    def test_hashable_as_dict_key(self):
        d = {"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200}
        # 不可变 → 可哈希:相同内容的两条日志在 set 里去重
        pair = {to_namedtuple(d), to_namedtuple(dict(d))}
        assert all(isinstance(x, AccessLog) for x in pair)   # 先确保转换成功
        assert len(pair) == 1


# ---------- build_daily_report:综合 ----------
class TestBuildDailyReport:
    def test_total(self, access_logs):
        assert build_daily_report(access_logs)["total"] == 20

    def test_status_counts(self, access_logs):
        assert build_daily_report(access_logs)["status_counts"] == {
            200: 13, 201: 2, 500: 3, 404: 1, 401: 1,
        }

    def test_top_ips(self, access_logs):
        assert build_daily_report(access_logs)["top_ips"] == [
            ("192.168.1.1", 5), ("10.0.0.5", 3), ("172.16.0.3", 2),
        ]

    def test_path_uv(self, access_logs):
        report = build_daily_report(access_logs)
        assert report["path_uv"]["/api/products"] == 7
        assert report["path_uv"]["/login"] == 1
        assert len(report["path_uv"]) == 7

    def test_latest_paths(self, access_logs):
        assert build_daily_report(access_logs)["latest_paths"] == [
            "/login", "/api/products", "/api/products", "/", "/api/products",
        ]

    def test_latest_errors_newest_first(self, access_logs):
        errors = build_daily_report(access_logs)["latest_errors"]
        assert [e["ip"] for e in errors] == ["198.51.100.2", "198.51.100.2", "203.0.113.5"]

    def test_empty_logs(self):
        assert build_daily_report([]) == {
            "total": 0,
            "status_counts": {},
            "top_ips": [],
            "path_uv": {},
            "latest_paths": [],
            "latest_errors": [],
        }
