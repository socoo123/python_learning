"""
Ch26 作业测试。运行: uv run pytest 04_devops_scripts/ch26/test_ch26_assignment.py -v
"""
import pytest

from ch26_assignment import (
    alert_on_spikes,
    build_alert_message,
    count_5xx_per_minute,
    extract_ts_status,
    find_spike_minutes,
    format_report,
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
        # 有时间戳没状态码 -> None
        assert extract_ts_status("2026-07-24T10:00:01 GET /x") is None

    def test_target_in_middle_uses_search(self):
        # 状态码在行中间也能命中(search);若误用 match 取行首会失败
        assert extract_ts_status("2026-07-24T23:59:59 503 POST /pay") == ("2026-07-24T23:59", 503)


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
        # 5xx 是 500~599;499 和 600 不算(链式比较 500 <= s < 600)
        lines = [
            "2026-07-24T10:00:01 499 GET /",   # 不算
            "2026-07-24T10:00:02 599 GET /",   # 算
            "2026-07-24T10:00:03 600 GET /",   # 不算(已出 5xx 区间)
            "2026-07-24T10:00:04 500 GET /",   # 算
        ]
        assert count_5xx_per_minute(lines) == {"2026-07-24T10:00": 2}


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
        # 乱序插入,结果仍按分钟字符串升序
        counts = {"10:10": 7, "10:00": 8, "10:05": 9}
        assert find_spike_minutes(counts, threshold=1) == ["10:00", "10:05", "10:10"]

    def test_threshold_boundary_inclusive(self):
        # 等于阈值也要告(>=),不是 >
        counts = {"10:00": 3}
        assert find_spike_minutes(counts, threshold=3) == ["10:00"]

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

    def test_critical_boundary(self):
        # 恰好 2 倍阈值算 critical
        assert build_alert_message("m", 10, 5)["severity"] == "critical"
        assert build_alert_message("m", 9, 5)["severity"] == "warning"

    def test_message_exact(self):
        # 精确断言 message,拦住乱拼/漏字段的实现
        msg = build_alert_message("2026-07-24T10:00", 5, 3)
        assert msg["message"] == "2026-07-24T10:00 5xx 错误数 5 超过阈值 3"

    def test_returns_dict(self):
        assert isinstance(build_alert_message("m", 1, 1), dict)


# ---------- alert_on_spikes(综合:复用前 4 个函数) ----------
class TestAlertOnSpikes:
    def test_real_server_logs_threshold_3(self):
        from conftest import load_mock_json

        lines = load_mock_json("server_logs.json")
        alerts = alert_on_spikes(lines, threshold=3)
        # 只有 10:00 达标(5>=3);10:01 只 1 个不超标
        assert len(alerts) == 1
        assert alerts[0]["minute"] == "2026-07-24T10:00"
        assert alerts[0]["count"] == 5
        assert alerts[0]["severity"] == "warning"   # 5 < 3*2

    def test_real_server_logs_threshold_1(self):
        from conftest import load_mock_json

        lines = load_mock_json("server_logs.json")
        alerts = alert_on_spikes(lines, threshold=1)
        assert [a["minute"] for a in alerts] == ["2026-07-24T10:00", "2026-07-24T10:01"]
        assert [a["count"] for a in alerts] == [5, 1]

    def test_alerts_carry_count(self):
        # 关键:alert 里的 count 要回查 counts,不能瞎填
        lines = ["2026-07-24T10:00:0%d 500 GET /" % i for i in range(4)]
        alerts = alert_on_spikes(lines, threshold=2)
        assert alerts[0]["count"] == 4

    def test_no_spike_returns_empty(self):
        lines = ["2026-07-24T10:00:01 200 GET /"] * 10   # 全是 2xx
        assert alert_on_spikes(lines, threshold=1) == []

    def test_all_malformed(self):
        assert alert_on_spikes(["脏数据", "还是脏数据"], threshold=1) == []

    def test_empty_lines(self):
        assert alert_on_spikes([], threshold=3) == []


# ---------- format_report ----------
class TestFormatReport:
    def test_empty_alerts(self):
        assert format_report([]) == "✅ 系统正常:无 5xx 超阈值告警"

    def test_single_alert_exact(self):
        alerts = [
            {"minute": "2026-07-24T10:00", "count": 5, "threshold": 3,
             "severity": "warning", "message": "..."},
        ]
        assert format_report(alerts) == (
            "🚨 5xx 告警报告(共 1 条)\n"
            "[warning] 2026-07-24T10:00 5xx=5 (阈值 3)"
        )

    def test_multiple_alerts_order_and_lines(self):
        alerts = [
            {"minute": "10:00", "count": 5, "threshold": 3, "severity": "warning", "message": ""},
            {"minute": "10:05", "count": 9, "threshold": 3, "severity": "critical", "message": ""},
        ]
        report = format_report(alerts)
        rows = report.split("\n")
        assert rows[0] == "🚨 5xx 告警报告(共 2 条)"
        assert rows[1] == "[warning] 10:00 5xx=5 (阈值 3)"
        assert rows[2] == "[critical] 10:05 5xx=9 (阈值 3)"

    def test_returns_str(self):
        assert isinstance(format_report([]), str)

    def test_integrates_with_pipeline(self):
        # 与 alert_on_spikes 串联:数据 → 表现
        from conftest import load_mock_json

        lines = load_mock_json("server_logs.json")
        report = format_report(alert_on_spikes(lines, threshold=3))
        assert report.startswith("🚨 5xx 告警报告(共 1 条)")
        assert "[warning] 2026-07-24T10:00 5xx=5 (阈值 3)" in report


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
