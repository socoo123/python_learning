"""
Ch08 作业测试。运行: uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v
"""
from collections import Counter

import pytest

from ch08_assignment import (
    count_by_status,
    top_ips,
    group_by_status,
    recent_paths,
    AccessLog,
    to_namedtuple,
)
from conftest import load_mock_json


@pytest.fixture
def access_logs():
    return load_mock_json("access_logs.json")


# ---------- count_by_status:Counter ----------
class TestCountByStatus:
    def test_returns_counter(self, access_logs):
        assert isinstance(count_by_status(access_logs), Counter)

    def test_status_200(self, access_logs):
        assert count_by_status(access_logs)[200] == 13

    def test_status_500(self, access_logs):
        assert count_by_status(access_logs)[500] == 3

    def test_missing_key_returns_zero(self, access_logs):
        # Counter 对不存在的键返回 0(不抛 KeyError)—— 这是它比普通 dict 好的地方
        assert count_by_status(access_logs)[999] == 0


# ---------- top_ips:Counter.most_common ----------
class TestTopIps:
    def test_top1(self, access_logs):
        assert top_ips(access_logs, 1) == [("192.168.1.1", 5)]

    def test_top2(self, access_logs):
        result = top_ips(access_logs, 2)
        assert result[0] == ("192.168.1.1", 5)
        assert result[1] == ("10.0.0.5", 3)

    def test_returns_list_of_2tuples(self, access_logs):
        result = top_ips(access_logs, 3)
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)

    def test_default_n(self, access_logs):
        assert len(top_ips(access_logs)) == 3


# ---------- group_by_status:defaultdict ----------
class TestGroupByStatus:
    def test_group_sizes(self, access_logs):
        g = group_by_status(access_logs)
        assert len(g[200]) == 13
        assert len(g[500]) == 3
        assert len(g[404]) == 1

    def test_keys_are_all_status_codes(self, access_logs):
        g = group_by_status(access_logs)
        assert set(g.keys()) == {200, 201, 401, 404, 500}

    def test_no_logs_lost(self, access_logs):
        g = group_by_status(access_logs)
        assert sum(len(v) for v in g.values()) == 20


# ---------- recent_paths:deque(maxlen) ----------
class TestRecentPaths:
    def test_last_three(self, access_logs):
        # 最后 3 条日志的 path(条 18/19/20)
        result = recent_paths(access_logs, 3)
        assert result == ["/api/products", "/", "/api/products"]

    def test_default_n_is_5(self, access_logs):
        assert len(recent_paths(access_logs)) == 5

    def test_n_more_than_total(self, access_logs):
        # deque(maxlen=100) 超过数据量时,保留全部(不报错)
        assert len(recent_paths(access_logs, 100)) == 20

    def test_preserves_order(self, access_logs):
        # deque 是 FIFO,保留最后 n 个的原始顺序
        result = recent_paths(access_logs, 2)
        # 最后两条:条 19(/) 和 条 20(/api/products)
        assert result == ["/", "/api/products"]


# ---------- AccessLog namedtuple ----------
class TestAccessLogNamedTuple:
    def test_field_access_by_name(self):
        log = AccessLog(ip="1.2.3.4", method="GET", path="/", status=200)
        assert log.ip == "1.2.3.4"
        assert log.status == 200

    def test_to_namedtuple(self):
        d = {"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200}
        log = to_namedtuple(d)
        assert log.path == "/"
        assert isinstance(log, AccessLog)

    def test_immutable(self):
        log = AccessLog("1.2.3.4", "GET", "/", 200)
        with pytest.raises(AttributeError):
            log.ip = "changed"      # namedtuple 不可变,改字段会抛错

    def test_index_access(self):
        log = AccessLog("1.2.3.4", "GET", "/", 200)
        assert log[0] == "1.2.3.4"   # 也支持索引访问(它是 tuple 子类)
