"""
Ch27 作业测试。运行:
    uv sync --extra devops
    uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v

psutil / socket / urllib 全部 monkeypatch,断言精确值,不依赖真机状态;
另保留少量真机冒烟测试(结构/范围),双保险。
"""
import json
import socket
import urllib.error
import urllib.request
from collections import namedtuple
from types import SimpleNamespace

import psutil
import pytest

import ch27_assignment as a
from ch27_assignment import (
    build_health_report,
    check_cpu,
    check_disk,
    check_memory,
    check_port,
    load_thresholds,
    run_inspection,
    send_webhook,
)

G = 1024 ** 3
# psutil.disk_usage 返回 namedtuple(total, used, free, percent),mock 用同构 namedtuple
FakeDiskUsage = namedtuple("FakeDiskUsage", "total used free percent")


# ---------- §27.2 load_thresholds ----------
class TestLoadThresholds:
    def test_empty_env_uses_defaults(self):
        assert load_thresholds({}) == {"disk": 80.0, "memory": 80.0, "cpu": 90.0}

    def test_disk_override(self):
        result = load_thresholds({"DISK_THRESHOLD": "95"})
        assert result["disk"] == 95.0
        assert result["memory"] == 80.0   # 未覆盖的保持默认
        assert result["cpu"] == 90.0

    def test_cpu_override_only(self):
        result = load_thresholds({"CPU_THRESHOLD": "98.5"})
        assert result["cpu"] == 98.5
        assert result["disk"] == 80.0

    def test_all_overrides(self):
        result = load_thresholds(
            {"DISK_THRESHOLD": "90", "MEMORY_THRESHOLD": "70", "CPU_THRESHOLD": "85"}
        )
        assert result == {"disk": 90.0, "memory": 70.0, "cpu": 85.0}

    def test_values_are_float(self):
        # 环境变量是 str,必须转 float;"95" -> 95.0
        result = load_thresholds({"DISK_THRESHOLD": "95"})
        assert isinstance(result["disk"], float)
        assert isinstance(result["memory"], float)

    def test_unrelated_env_ignored(self):
        result = load_thresholds({"HOME": "/root", "PATH": "/usr/bin", "DISK": "1"})
        assert result == {"disk": 80.0, "memory": 80.0, "cpu": 90.0}


# ---------- §27.3 check_disk ----------
class TestCheckDisk:
    def test_exact_dict_from_mock(self, monkeypatch):
        # mock psutil,断言精确计算:字节转 GB + ok 判断(硬编码返回值蒙不过)
        monkeypatch.setattr(
            psutil, "disk_usage",
            lambda path: FakeDiskUsage(total=200 * G, used=150 * G, free=50 * G, percent=75.0),
        )
        assert check_disk("/", threshold=80.0) == {
            "percent": 75.0, "free_gb": 50.0, "total_gb": 200.0, "ok": True,
        }

    def test_bytes_to_gb_rounding(self, monkeypatch):
        monkeypatch.setattr(
            psutil, "disk_usage",
            lambda path: FakeDiskUsage(total=3 * G, used=0, free=G // 3, percent=11.1),
        )
        result = check_disk("/")
        assert result["free_gb"] == 0.33      # 1/3 GB ≈ 0.3333... → round 0.33
        assert result["total_gb"] == 3.0

    def test_over_threshold_not_ok(self, monkeypatch):
        monkeypatch.setattr(
            psutil, "disk_usage",
            lambda path: FakeDiskUsage(total=G, used=0, free=0, percent=85.0),
        )
        assert check_disk("/", threshold=80.0)["ok"] is False

    def test_equal_threshold_not_ok(self, monkeypatch):
        # 边界:percent == threshold 算超标(严格小于),宁多告不漏告
        monkeypatch.setattr(
            psutil, "disk_usage",
            lambda path: FakeDiskUsage(total=G, used=0, free=0, percent=80.0),
        )
        assert check_disk("/", threshold=80.0)["ok"] is False

    def test_path_passed_through(self, monkeypatch):
        captured = {}
        def fake_disk_usage(path):
            captured["path"] = path
            return FakeDiskUsage(total=G, used=0, free=G, percent=1.0)
        monkeypatch.setattr(psutil, "disk_usage", fake_disk_usage)
        check_disk("/var/log")
        assert captured["path"] == "/var/log"

    def test_real_machine_smoke(self):
        # 真机冒烟:结构与范围(不断言具体值)
        result = check_disk("/")
        assert 0.0 <= result["percent"] <= 100.0
        assert result["total_gb"] > 0
        assert result["free_gb"] >= 0
        assert isinstance(result["ok"], bool)


# ---------- §27.3 check_memory ----------
class TestCheckMemory:
    def test_exact_dict_from_mock(self, monkeypatch):
        monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(percent=55.0))
        assert check_memory(threshold=80.0) == {"percent": 55.0, "ok": True}

    def test_over_threshold_not_ok(self, monkeypatch):
        monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(percent=91.5))
        assert check_memory(threshold=80.0)["ok"] is False

    def test_equal_threshold_not_ok(self, monkeypatch):
        monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(percent=80.0))
        assert check_memory(threshold=80.0)["ok"] is False

    def test_real_machine_smoke(self):
        result = check_memory()
        assert 0.0 <= result["percent"] <= 100.0
        assert isinstance(result["ok"], bool)


# ---------- §27.3 check_cpu ----------
class TestCheckCpu:
    def test_exact_dict_and_interval(self, monkeypatch):
        captured = {}
        def fake_cpu_percent(interval=None):
            captured["interval"] = interval
            return 42.0
        monkeypatch.setattr(psutil, "cpu_percent", fake_cpu_percent)
        assert check_cpu(threshold=80.0) == {"percent": 42.0, "ok": True}
        assert captured["interval"] == 0.1   # 必须传 interval 采样,否则首次恒 0.0

    def test_over_threshold_not_ok(self, monkeypatch):
        monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 95.0)
        assert check_cpu(threshold=90.0)["ok"] is False

    def test_equal_threshold_not_ok(self, monkeypatch):
        monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 90.0)
        assert check_cpu(threshold=90.0)["ok"] is False

    def test_custom_interval_passed(self, monkeypatch):
        captured = {}
        def fake_cpu_percent(interval=None):
            captured["interval"] = interval
            return 1.0
        monkeypatch.setattr(psutil, "cpu_percent", fake_cpu_percent)
        check_cpu(interval=0.5)
        assert captured["interval"] == 0.5

    def test_real_machine_smoke(self):
        result = check_cpu()
        assert 0.0 <= result["percent"] <= 100.0
        assert isinstance(result["ok"], bool)


# ---------- §27.4 check_port ----------
class _FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestCheckPort:
    def test_open_port(self, monkeypatch):
        captured = {}
        def fake_create_connection(address, timeout=None):
            captured["address"] = address
            captured["timeout"] = timeout
            return _FakeConn()
        monkeypatch.setattr(socket, "create_connection", fake_create_connection)
        assert check_port("db.internal", 5432, timeout=1.5) == {
            "host": "db.internal", "port": 5432, "ok": True,
        }
        assert captured["address"] == ("db.internal", 5432)
        assert captured["timeout"] == 1.5   # timeout 必须透传,防挂死

    def test_default_timeout_2s(self, monkeypatch):
        captured = {}
        def fake_create_connection(address, timeout=None):
            captured["timeout"] = timeout
            return _FakeConn()
        monkeypatch.setattr(socket, "create_connection", fake_create_connection)
        check_port("db.internal", 5432)
        assert captured["timeout"] == 2.0

    def test_connection_refused(self, monkeypatch):
        def fake_create_connection(address, timeout=None):
            raise ConnectionRefusedError("refused")
        monkeypatch.setattr(socket, "create_connection", fake_create_connection)
        assert check_port("db.internal", 5432) == {
            "host": "db.internal", "port": 5432, "ok": False,
        }

    def test_timeout_returns_false(self, monkeypatch):
        def fake_create_connection(address, timeout=None):
            raise socket.timeout("timed out")
        monkeypatch.setattr(socket, "create_connection", fake_create_connection)
        assert check_port("db.internal", 5432)["ok"] is False

    def test_dns_failure_returns_false(self, monkeypatch):
        def fake_create_connection(address, timeout=None):
            raise socket.gaierror("name or service not known")
        monkeypatch.setattr(socket, "create_connection", fake_create_connection)
        assert check_port("no.such.host", 5432)["ok"] is False

    def test_real_closed_port(self):
        # 真机:环回地址 1 号端口几乎必然关闭,拒连即刻返回(不挂起)
        assert check_port("127.0.0.1", 1, timeout=1.0)["ok"] is False


# ---------- §27.5 build_health_report ----------
class TestBuildHealthReport:
    def test_all_ok(self):
        report = build_health_report({"disk": {"ok": True}, "memory": {"ok": True}})
        assert report["overall_ok"] is True

    def test_one_not_ok(self):
        report = build_health_report({"disk": {"ok": True}, "memory": {"ok": False}})
        assert report["overall_ok"] is False

    def test_none_ok(self):
        report = build_health_report({"disk": {"ok": False}, "cpu": {"ok": False}})
        assert report["overall_ok"] is False

    def test_empty_is_healthy(self):
        # 空检查视为健康:all([]) == True(vacuous truth)
        assert build_health_report({}) == {"overall_ok": True, "checks": {}}

    def test_missing_ok_key_counts_unhealthy(self):
        # 脏数据缺 ok 键按 False 处理,而不是 KeyError 崩掉
        report = build_health_report({"disk": {"percent": 50}})
        assert report["overall_ok"] is False

    def test_checks_preserved(self):
        checks = {"disk": {"percent": 50, "ok": True}}
        report = build_health_report(checks)
        assert report["checks"] == checks


# ---------- §27.6 send_webhook ----------
class _FakeResp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestSendWebhook:
    def test_success_returns_true(self, monkeypatch):
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, timeout=None: _FakeResp(200)
        )
        assert send_webhook("https://hook.example/x", {"alert": "disk"}) is True

    def test_posts_json_with_header_and_url(self, monkeypatch):
        captured = {}
        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            captured["timeout"] = timeout
            return _FakeResp(200)
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        send_webhook("https://hook.example/x", {"a": 1}, timeout=3.0)
        req = captured["req"]
        assert req.full_url == "https://hook.example/x"      # url 透传
        assert req.get_method() == "POST"                    # 是 POST 不是 GET
        assert json.loads(req.data) == {"a": 1}              # body 是 JSON 编码的 payload
        assert req.headers.get("Content-type") == "application/json"
        assert captured["timeout"] == 3.0                    # timeout 透传

    def test_non_2xx_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, timeout=None: _FakeResp(500)
        )
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_network_error_returns_false(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_timeout_error_returns_false(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            raise TimeoutError("timed out")
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_never_raises(self, monkeypatch):
        # 不管底层怎么崩,send_webhook 都不该抛(EAFP 底线)
        def fake_urlopen(req, timeout=None):
            raise RuntimeError("boom")
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"a": 1}) is False


# ---------- §27.7 run_inspection(综合:monkeypatch 各零件,只测编排)----------
def _ok(percent=10.0):
    return {"percent": percent, "ok": True}


@pytest.fixture
def healthy_parts(monkeypatch):
    """把三项检查全换成健康的假实现,send_webhook 换成记录仪。"""
    monkeypatch.setattr(a, "check_disk", lambda path, threshold: _ok())
    monkeypatch.setattr(a, "check_memory", lambda threshold: _ok())
    monkeypatch.setattr(a, "check_cpu", lambda threshold, interval=0.1: _ok())
    calls = []
    monkeypatch.setattr(
        a, "send_webhook", lambda url, payload, timeout=5.0: calls.append((url, payload)) or True
    )
    return calls


class TestRunInspection:
    def test_healthy_skips_webhook(self, healthy_parts):
        result = run_inspection({}, webhook_url="https://hook.example/x")
        assert result["report"]["overall_ok"] is True
        assert result["webhook_sent"] is None     # 健康不推
        assert healthy_parts == []                # send_webhook 根本没被调

    def test_report_contains_three_checks(self, healthy_parts):
        result = run_inspection({})
        assert set(result["report"]["checks"]) == {"disk", "memory", "cpu"}

    def test_unhealthy_pushes_report(self, healthy_parts, monkeypatch):
        monkeypatch.setattr(a, "check_disk", lambda path, threshold: {"percent": 99.0, "ok": False})
        result = run_inspection({}, webhook_url="https://hook.example/x")
        assert result["report"]["overall_ok"] is False
        assert result["webhook_sent"] is True
        # 推出去的 payload 就是健康报告本身
        url, payload = healthy_parts[0]
        assert url == "https://hook.example/x"
        assert payload["overall_ok"] is False
        assert payload["checks"]["disk"]["percent"] == 99.0

    def test_unhealthy_without_url_not_pushed(self, healthy_parts, monkeypatch):
        monkeypatch.setattr(a, "check_memory", lambda threshold: {"percent": 99.0, "ok": False})
        result = run_inspection({})               # 没配 webhook_url
        assert result["report"]["overall_ok"] is False
        assert result["webhook_sent"] is None
        assert healthy_parts == []

    def test_webhook_failure_reflected(self, healthy_parts, monkeypatch):
        monkeypatch.setattr(a, "check_cpu", lambda threshold, interval=0.1: {"percent": 99.0, "ok": False})
        monkeypatch.setattr(a, "send_webhook", lambda url, payload, timeout=5.0: False)
        result = run_inspection({}, webhook_url="https://hook.example/x")
        assert result["webhook_sent"] is False    # 推了但失败,三态之 False

    def test_env_thresholds_flow_to_checks(self, healthy_parts, monkeypatch):
        # env 覆盖的阈值必须真的传到各检查函数(拦硬编码)
        seen = {}
        def fake_disk(path, threshold):
            seen["disk"] = threshold
            return _ok()
        def fake_mem(threshold):
            seen["memory"] = threshold
            return _ok()
        monkeypatch.setattr(a, "check_disk", fake_disk)
        monkeypatch.setattr(a, "check_memory", fake_mem)
        run_inspection({"DISK_THRESHOLD": "66.5", "MEMORY_THRESHOLD": "77"})
        assert seen["disk"] == 66.5
        assert seen["memory"] == 77.0
