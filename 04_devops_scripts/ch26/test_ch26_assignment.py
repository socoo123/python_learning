"""
Ch26 作业测试。运行: uv run pytest 04_devops_scripts/ch26/test_ch26_assignment.py -v
"""
import pytest

from ch26_assignment import (
    build_alert_message,
    count_5xx_per_minute,
    extract_ts_status,
    find_spike_minutes,
    schedule_job,
)


# ---------- extract_ts_status ----------
class TestExtractTsStatus:
    def test_normal_line(self):
        line = "2026-07-24T10:00:01 500 GET /api/orders"
        assert extract_ts_status(line) == ("2026-07-24T10:00", 500)

    def test_truncates_to_minute(self):
        # 同一分钟内不同秒,分钟相同
        a = extract_ts_status("2026-07-24T10:00:01 200 GET /")
        b = extract_ts_status("2026-07-24T10:00:59 200 GET /")
        assert a[0] == b[0] == "2026-07-24T10:00"

    def test_status_is_int(self):
        result = extract_ts_status("2026-07-24T10:00:01 404 GET /x")
        assert result[1] == 404
        assert isinstance(result[1], int)

    def test_malformed_returns_none(self):
        assert extract_ts_status("乱七八糟的行") is None

    def test_empty_line(self):
        assert extract_ts_status("") is None

    def test_partial_no_status(self):
        # 有时间戳没状态码
        assert extract_ts_status("2026-07-24T10:00:01 GET /x") is None

    def test_returns_tuple_or_none(self):
        result = extract_ts_status("2026-07-24T10:00:01 200 GET /")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------- count_5xx_per_minute ----------
class TestCount5xxPerMinute:
    def test_real_server_logs(self):
        from conftest import load_mock_json

        lines = load_mock_json("server_logs.json")
        # 10:00 有 5 个 5xx(500/500/503/500/502),10:01 有 1 个(500)
        assert count_5xx_per_minute(lines) == {
            "2026-07-24T10:00": 5,
            "2026-07-24T10:01": 1,
        }

    def test_excludes_non_5xx(self):
        lines = [
            "2026-07-24T10:00:01 200 GET /",    # 2xx 不算
            "2026-07-24T10:00:02 404 GET /x",   # 4xx 不算
            "2026-07-24T10:00:03 500 GET /y",   # 5xx 算
        ]
        assert count_5xx_per_minute(lines) == {"2026-07-24T10:00": 1}

    def test_skips_malformed(self):
        lines = [
            "2026-07-24T10:00:01 500 GET /",
            "malformed line",
            "2026-07-24T10:00:02 501 GET /",
        ]
        assert count_5xx_per_minute(lines) == {"2026-07-24T10:00": 2}

    def test_empty(self):
        assert count_5xx_per_minute([]) == {}

    def test_boundary_499_and_599(self):
        # 5xx 是 500~599;499 和 600 不算
        lines = [
            "2026-07-24T10:00:01 499 GET /",
            "2026-07-24T10:00:02 599 GET /",
            "2026-07-24T10:00:03 500 GET /",
        ]
        assert count_5xx_per_minute(lines) == {
            "2026-07-24T10:00": 2   # 499 不算,599 和 500 算
        }


# ---------- find_spike_minutes ----------
class TestFindSpikeMinutes:
    def test_threshold_3(self):
        counts = {"10:00": 5, "10:01": 1, "10:02": 3}
        assert find_spike_minutes(counts, threshold=3) == ["10:00", "10:02"]

    def test_threshold_1(self):
        counts = {"10:00": 5, "10:01": 1}
        assert find_spike_minutes(counts, threshold=1) == ["10:00", "10:01"]

    def test_no_spike(self):
        counts = {"10:00": 1, "10:01": 2}
        assert find_spike_minutes(counts, threshold=5) == []

    def test_result_sorted(self):
        counts = {"10:05": 9, "10:00": 8, "10:10": 7}
        result = find_spike_minutes(counts, threshold=1)
        assert result == sorted(result)   # 按分钟字符串排序

    def test_empty(self):
        assert find_spike_minutes({}, threshold=1) == []


# ---------- build_alert_message ----------
class TestBuildAlertMessage:
    def test_basic_fields(self):
        msg = build_alert_message("2026-07-24T10:00", 5, 3)
        assert msg["minute"] == "2026-07-24T10:00"
        assert msg["count"] == 5
        assert msg["threshold"] == 3

    def test_warning_severity(self):
        msg = build_alert_message("10:00", 5, 3)   # 5 < 3*2=6
        assert msg["severity"] == "warning"

    def test_critical_severity(self):
        msg = build_alert_message("10:00", 6, 3)   # 6 >= 3*2
        assert msg["severity"] == "critical"

    def test_message_contains_info(self):
        msg = build_alert_message("2026-07-24T10:00", 5, 3)
        assert "2026-07-24T10:00" in msg["message"]
        assert "5" in msg["message"]
        assert "3" in msg["message"]

    def test_returns_dict(self):
        assert isinstance(build_alert_message("m", 1, 1), dict)


# ---------- schedule_job ----------
class TestScheduleJob:
    def setup_method(self):
        import schedule
        schedule.clear()   # 每个测试前清空全局任务表,隔离

    def teardown_method(self):
        import schedule
        schedule.clear()

    def test_returns_job(self):
        import schedule
        job = schedule_job(lambda: None, every_minutes=10)
        assert isinstance(job, schedule.Job)

    def test_interval_correct(self):
        job = schedule_job(lambda: None, every_minutes=30)
        assert job.interval == 30

    def test_unit_is_minutes(self):
        job = schedule_job(lambda: None, every_minutes=5)
        assert job.unit == "minutes"

    def test_job_registered(self):
        import schedule
        schedule_job(lambda: None, every_minutes=10)
        assert len(schedule.get_jobs()) == 1

    def test_one_minute(self):
        # every_minutes=1 也要正常工作(.minutes 复数兼容 1)
        job = schedule_job(lambda: None, every_minutes=1)
        assert job.interval == 1
        assert job.unit == "minutes"
