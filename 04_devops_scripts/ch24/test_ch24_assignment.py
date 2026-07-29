"""
Ch24 作业测试。运行: uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v
"""
import subprocess
import sys

import pytest

from ch24_assignment import (
    disk_free_gb,
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
        # text=True → stdout 是 str
        r = run_command([sys.executable, "-c", "print('hello')"])
        assert r.stdout == "hello\n"
        assert isinstance(r.stdout, str)

    def test_returncode_zero_on_success(self):
        r = run_command([sys.executable, "-c", "pass"])
        assert r.returncode == 0

    def test_nonzero_returncode_on_failure(self):
        r = run_command([sys.executable, "-c", "import sys; sys.exit(3)"])
        assert r.returncode == 3

    def test_stderr_captured(self):
        r = run_command(
            [sys.executable, "-c", "import sys; print('boom', file=sys.stderr)"]
        )
        assert r.stderr == "boom\n"

    def test_timeout_raises(self):
        # 子进程睡 5 秒,timeout 0.5 秒必触发
        with pytest.raises(subprocess.TimeoutExpired):
            run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.5)


# ---------- run_command_safely ----------
class TestRunCommandSafely:
    def test_success(self):
        ok, out = run_command_safely([sys.executable, "-c", "print('ok')"])
        assert ok is True
        assert "ok" in out

    def test_command_not_found(self):
        ok, out = run_command_safely(["这种命令肯定不存在_xyz_123"])
        assert ok is False
        assert isinstance(out, str)  # 有错误信息
        assert len(out) > 0

    def test_nonzero_exit_is_failure(self):
        ok, out = run_command_safely(
            [sys.executable, "-c", "import sys; print('errline', file=sys.stderr); sys.exit(1)"]
        )
        assert ok is False
        assert "errline" in out  # 失败时 stderr 也带回

    def test_never_raises(self):
        # 不管什么命令都不抛异常
        ok, out = run_command_safely(["又一个不存在的命令_xyz"])
        assert isinstance(ok, bool)
        assert isinstance(out, str)

    def test_returns_tuple(self):
        result = run_command_safely([sys.executable, "--version"])
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------- ping_host ----------
class TestPingHost:
    def test_localhost_reachable(self):
        # 127.0.0.1 永远通(macOS/Linux/Windows 都是)
        assert ping_host("127.0.0.1") is True

    def test_returns_bool(self):
        assert isinstance(ping_host("127.0.0.1"), bool)

    def test_invalid_host_returns_false(self):
        # .invalid 是 RFC2606 保留域名,DNS 查询立即失败 → ping 快速返回非 0
        assert ping_host("definitely-not-real.invalid") is False

    def test_never_raises(self):
        # 即使 ping 命令有问题,也不该抛异常
        result = ping_host("127.0.0.1")
        assert isinstance(result, bool)


# ---------- memory_usage_percent ----------
class TestMemoryUsagePercent:
    def test_returns_float(self):
        assert isinstance(memory_usage_percent(), float)

    def test_in_valid_range(self):
        pct = memory_usage_percent()
        assert 0.0 <= pct <= 100.0


# ---------- disk_free_gb ----------
class TestDiskFreeGb:
    def test_returns_float(self):
        assert isinstance(disk_free_gb("/"), float)

    def test_non_negative(self):
        assert disk_free_gb("/") >= 0.0

    def test_works_with_tmp(self, tmp_path):
        # tmp_path 所在分区也得能查
        free = disk_free_gb(str(tmp_path))
        assert isinstance(free, float)
        assert free >= 0.0
