"""
Ch27 作业测试。运行: uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v
"""
import json
import urllib.error
import urllib.request

import pytest

from ch27_assignment import (
    build_health_report,
    check_disk,
    check_memory,
    load_thresholds,
    send_webhook,
)


# ---------- load_thresholds ----------
class TestLoadThresholds:
    def test_empty_env_uses_defaults(self):
        result = load_thresholds({})
        assert result == {"disk": 80.0, "memory": 80.0, "cpu": 90.0}

    def test_disk_override(self):
        result = load_thresholds({"DISK_THRESHOLD": "95"})
        assert result["disk"] == 95.0
        assert result["memory"] == 80.0   # 未覆盖

    def test_partial_override(self):
        result = load_thresholds({"MEMORY_THRESHOLD": "75"})
        assert result["memory"] == 75.0
        assert result["disk"] == 80.0
        assert result["cpu"] == 90.0

    def test_all_overrides(self):
        result = load_thresholds(
            {"DISK_THRESHOLD": "90", "MEMORY_THRESHOLD": "70", "CPU_THRESHOLD": "85"}
        )
        assert result == {"disk": 90.0, "memory": 70.0, "cpu": 85.0}

    def test_values_are_float(self):
        result = load_thresholds({"DISK_THRESHOLD": "95"})
        assert isinstance(result["disk"], float)   # "95" → 95.0

    def test_unrelated_env_ignored(self):
        result = load_thresholds({"HOME": "/root", "PATH": "/usr/bin"})
        assert result == {"disk": 80.0, "memory": 80.0, "cpu": 90.0}


# ---------- check_disk ----------
class TestCheckDisk:
    def test_returns_dict_with_keys(self):
        result = check_disk("/")
        for key in ("percent", "free_gb", "total_gb", "ok"):
            assert key in result

    def test_percent_in_range(self):
        result = check_disk("/")
        assert 0.0 <= result["percent"] <= 100.0

    def test_ok_is_bool(self):
        assert isinstance(check_disk("/")["ok"], bool)

    def test_high_threshold_means_ok(self):
        # 阈值设 200,任何机器的 percent 都 < 200 → ok True
        result = check_disk("/", threshold=200.0)
        assert result["ok"] is True

    def test_zero_threshold_means_not_ok(self):
        # 阈值设 0,percent>=0 永远不 < 0 → ok False
        result = check_disk("/", threshold=0.0)
        assert result["ok"] is False

    def test_works_with_tmp(self, tmp_path):
        result = check_disk(str(tmp_path))
        assert result["total_gb"] > 0

    def test_gb_values_positive(self):
        result = check_disk("/")
        assert result["total_gb"] > 0
        assert result["free_gb"] >= 0


# ---------- check_memory ----------
class TestCheckMemory:
    def test_returns_dict_with_keys(self):
        result = check_memory()
        assert "percent" in result
        assert "ok" in result

    def test_percent_in_range(self):
        result = check_memory()
        assert 0.0 <= result["percent"] <= 100.0

    def test_ok_is_bool(self):
        assert isinstance(check_memory()["ok"], bool)

    def test_high_threshold_ok(self):
        assert check_memory(threshold=200.0)["ok"] is True

    def test_zero_threshold_not_ok(self):
        assert check_memory(threshold=0.0)["ok"] is False


# ---------- build_health_report ----------
class TestBuildHealthReport:
    def test_all_ok(self):
        checks = {"disk": {"ok": True}, "memory": {"ok": True}}
        report = build_health_report(checks)
        assert report["overall_ok"] is True

    def test_one_not_ok(self):
        checks = {"disk": {"ok": True}, "memory": {"ok": False}}
        report = build_health_report(checks)
        assert report["overall_ok"] is False

    def test_none_ok(self):
        checks = {"disk": {"ok": False}, "memory": {"ok": False}}
        report = build_health_report(checks)
        assert report["overall_ok"] is False

    def test_empty_is_healthy(self):
        # 空检查视为健康(vacuous truth)
        report = build_health_report({})
        assert report["overall_ok"] is True

    def test_checks_preserved(self):
        checks = {"disk": {"percent": 50, "ok": True}}
        report = build_health_report(checks)
        assert report["checks"] == checks


# ---------- send_webhook ----------
class _FakeResp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestSendWebhook:
    def test_success_returns_true(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["req"] = req
            captured["timeout"] = timeout
            return _FakeResp(200)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"alert": "disk"}) is True

    def test_posts_json(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["req"] = req
            return _FakeResp(200)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        send_webhook("https://hook.example/x", {"a": 1})
        # 方法是 POST,body 是 JSON 编码的 payload
        assert captured["req"].get_method() == "POST"
        assert json.loads(captured["req"].data) == {"a": 1}

    def test_content_type_header(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["req"] = req
            return _FakeResp(200)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        send_webhook("https://hook.example/x", {"a": 1})
        assert captured["req"].headers.get("Content-type") == "application/json"

    def test_non_2xx_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, timeout: _FakeResp(500)
        )
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_network_error_returns_false(self, monkeypatch):
        def fake_urlopen(req, timeout):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_any_exception_returns_false(self, monkeypatch):
        def fake_urlopen(req, timeout):
            raise TimeoutError("timed out")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert send_webhook("https://hook.example/x", {"a": 1}) is False

    def test_never_raises(self, monkeypatch):
        # 不管底层怎么崩,send_webhook 都不该抛
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, timeout: (_ for _ in ()).throw(RuntimeError())
        )
        result = send_webhook("https://hook.example/x", {"a": 1})
        assert isinstance(result, bool)
