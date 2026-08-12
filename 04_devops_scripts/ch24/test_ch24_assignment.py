"""
Ch24 作业测试。运行: uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v
"""
import subprocess
import sys

import psutil
import pytest

from ch24_assignment import (
    bytes_to_gb,
    check_thresholds,
    disk_free_gb,
    health_report,
    memory_usage_percent,
    ping_host,
    run_command,
    run_command_safely,
)


# ---------- run_command ----------
class TestRunCommand:
    def test_returns_completed_process(self):
        r = run_command([sys.executable, "--version"])
        assert isinstance(r, subprocess.CompletedProcess)

    def test_stdout_captured_as_text(self):
        # text=True → stdout 是 str 不是 bytes
        r = run_command([sys.executable, "-c", "print('hello')"])
        assert r.stdout == "hello\n"
        assert isinstance(r.stdout, str)

    def test_returncode_zero_on_success(self):
        r = run_command([sys.executable, "-c", "pass"])
        assert r.returncode == 0

    def test_nonzero_returncode_propagates(self):
        # run 默认 check=False:非 0 退出码不抛异常,只是 returncode != 0
        r = run_command([sys.executable, "-c", "import sys; sys.exit(3)"])
        assert r.returncode == 3

    def test_stderr_captured(self):
        r = run_command(
            [sys.executable, "-c", "import sys; print('boom', file=sys.stderr)"]
        )
        assert r.stderr == "boom\n"

    def test_timeout_raises(self):
        # 子进程睡 5 秒,timeout 0.2 秒必触发;本题不 catch,原样抛出
        with pytest.raises(subprocess.TimeoutExpired):
            run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)


# ---------- run_command_safely ----------
class TestRunCommandSafely:
    def test_success_returns_true_and_stdout(self):
        ok, out = run_command_safely([sys.executable, "-c", "print('ok')"])
        assert ok is True
        assert out == "ok"  # strip 过,不带末尾换行

    def test_command_not_found(self):
        ok, out = run_command_safely(["这种命令肯定不存在_xyz_123"])
        assert ok is False
        assert "这种命令肯定不存在_xyz_123" in out  # 错误信息里带命令名

    def test_nonzero_exit_brings_back_stderr(self):
        ok, out = run_command_safely(
            [sys.executable, "-c", "import sys; print('errline', file=sys.stderr); sys.exit(1)"]
        )
        assert ok is False
        assert "errline" in out  # 失败时 stderr 也带回(排查靠它)

    def test_timeout_never_raises(self):
        # 睡 5 秒 + timeout 0.2 必超时;安全封装要吞掉异常返回 (False, 提示)
        ok, out = run_command_safely(
            [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2
        )
        assert ok is False
        assert isinstance(out, str) and len(out) > 0

    def test_returns_two_tuple(self):
        result = run_command_safely([sys.executable, "--version"])
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


# ---------- ping_host ----------
class TestPingHost:
    def test_localhost_reachable(self):
        # 127.0.0.1 本机回环,各平台都通
        assert ping_host("127.0.0.1") is True

    def test_invalid_host_returns_false(self):
        # .invalid 是 RFC2606 保留域名,DNS 立即失败 → ping 秒回非 0
        assert ping_host("definitely-not-real.invalid") is False

    def test_returns_bool_not_truthy(self):
        # 拦住「直接返回 CompletedProcess / returncode」的实现
        assert isinstance(ping_host("127.0.0.1"), bool)

    def test_never_raises(self):
        # 异常兜底:任何结果都应该是 bool,绝不抛给调用方
        assert isinstance(ping_host("definitely-not-real.invalid", timeout=0.5), bool)


# ---------- bytes_to_gb ----------
class TestBytesToGb:
    def test_one_gib(self):
        assert bytes_to_gb(1073741824) == 1.0  # 1024³

    def test_five_gib(self):
        assert bytes_to_gb(5368709120) == 5.0

    def test_zero(self):
        assert bytes_to_gb(0) == 0.0

    def test_fractional(self):
        # 1.5 GiB;同时拦住「用 1000³」的实现(那会得 1.610612736)
        assert bytes_to_gb(1610612736) == pytest.approx(1.5)

    def test_returns_float(self):
        assert isinstance(bytes_to_gb(1024), float)


# ---------- memory_usage_percent ----------
class TestMemoryUsagePercent:
    def test_returns_float(self):
        assert isinstance(memory_usage_percent(), float)

    def test_in_valid_range(self):
        pct = memory_usage_percent()
        assert 0.0 <= pct <= 100.0

    def test_matches_psutil(self):
        # 与 psutil 直读一致(同一时刻采样,容差 5 个百分点防波动)
        assert memory_usage_percent() == pytest.approx(
            psutil.virtual_memory().percent, abs=5.0
        )


# ---------- disk_free_gb ----------
class TestDiskFreeGb:
    def test_returns_float(self):
        assert isinstance(disk_free_gb("/"), float)

    def test_non_negative(self):
        assert disk_free_gb("/") >= 0.0

    def test_is_gb_not_bytes(self):
        # 拦住「忘除 1024³」的实现:返回值应与 psutil 换算结果同量级(容差 10%)
        expected = psutil.disk_usage("/").free / (1024**3)
        assert disk_free_gb("/") == pytest.approx(expected, rel=0.1)

    def test_works_with_tmp_path(self, tmp_path):
        free = disk_free_gb(str(tmp_path))
        assert isinstance(free, float)
        assert free >= 0.0


# ---------- check_thresholds ----------
class TestCheckThresholds:
    def test_max_exceeded_alerts(self):
        alerts = check_thresholds({"memory_percent": 87.5}, {"memory_percent_max": 80.0})
        assert alerts == ["memory_percent=87.5 超过上限 80.0"]

    def test_min_below_alerts(self):
        alerts = check_thresholds({"disk_free_gb": 12.0}, {"disk_free_gb_min": 20.0})
        assert alerts == ["disk_free_gb=12.0 低于下限 20.0"]

    def test_within_limits_no_alert(self):
        alerts = check_thresholds(
            {"memory_percent": 50.0, "disk_free_gb": 100.0},
            {"memory_percent_max": 80.0, "disk_free_gb_min": 20.0},
        )
        assert alerts == []

    def test_equal_to_limit_no_alert(self):
        # 严格 > / <:等于阈值不告警
        alerts = check_thresholds({"memory_percent": 80.0}, {"memory_percent_max": 80.0})
        assert alerts == []

    def test_missing_metric_skipped(self):
        # metrics 缺 key:跳过,不报错不告警
        assert check_thresholds({}, {"memory_percent_max": 80.0}) == []

    def test_multiple_alerts_in_limits_order(self):
        # dict 保插入序,告警按 limits 的 key 顺序产出
        alerts = check_thresholds(
            {"memory_percent": 87.5, "disk_free_gb": 12.0},
            {"memory_percent_max": 80.0, "disk_free_gb_min": 20.0},
        )
        assert alerts == [
            "memory_percent=87.5 超过上限 80.0",
            "disk_free_gb=12.0 低于下限 20.0",
        ]

    def test_empty_limits(self):
        assert check_thresholds({"memory_percent": 99.0}, {}) == []


# ---------- health_report(综合) ----------
class TestHealthReport:
    def test_report_structure(self):
        report = health_report(["127.0.0.1"])
        assert set(report.keys()) == {
            "hosts", "up_count", "total", "memory_percent", "disk_free_gb", "alerts",
        }

    def test_hosts_mapping(self):
        report = health_report(["127.0.0.1", "definitely-not-real.invalid"])
        assert report["hosts"] == {
            "127.0.0.1": True,
            "definitely-not-real.invalid": False,
        }
        assert report["up_count"] == 1
        assert report["total"] == 2

    def test_metrics_present_and_sane(self):
        report = health_report([])
        assert isinstance(report["memory_percent"], float)
        assert 0.0 <= report["memory_percent"] <= 100.0
        assert isinstance(report["disk_free_gb"], float)
        assert report["disk_free_gb"] >= 0.0

    def test_alerts_triggered_deterministically(self):
        # 上限 -1:内存使用率必然 >= 0 > -1 → 必告警,拦住「alerts 硬编码 []」
        report = health_report([], {"memory_percent_max": -1.0})
        assert len(report["alerts"]) == 1
        assert "memory_percent" in report["alerts"][0]

    def test_alerts_silenced_deterministically(self):
        # 上限 101:内存使用率必然 <= 100 < 101 → 必不告警,拦住「无脑告警」
        report = health_report([], {"memory_percent_max": 101.0})
        assert report["alerts"] == []

    def test_no_limits_means_no_alerts(self):
        report = health_report([])
        assert report["alerts"] == []

    def test_empty_hosts(self):
        report = health_report([])
        assert report["hosts"] == {}
        assert report["up_count"] == 0
        assert report["total"] == 0
