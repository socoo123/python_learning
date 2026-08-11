"""
Ch06 作业测试。运行: uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v
"""
import pytest

from ch06_assignment import (
    LogParseError,
    parse_log_line,
    parse_log_file,
    build_summary,
    write_report,
    Timer,
    db_transaction,
)
from conftest import MOCK_DATA_DIR

NGINX_LOG = MOCK_DATA_DIR / "nginx_logs.txt"

GOOD_LINE = (
    '192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] '
    '"GET /api/products HTTP/1.1" 200 1234'
)


# ---------- LogParseError:自定义异常 ----------
class TestLogParseError:
    def test_is_exception_subclass(self):
        assert issubclass(LogParseError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(LogParseError):
            raise LogParseError("boom")

    def test_carries_message(self):
        try:
            raise LogParseError("无法解析: xxx")
        except LogParseError as e:
            assert "无法解析" in str(e)


# ---------- parse_log_line:EAFP + 自定义异常 ----------
class TestParseLogLine:
    def test_parses_good_line(self):
        assert parse_log_line(GOOD_LINE) == {"path": "/api/products", "status": 200}

    def test_parses_another_good_line(self):
        line = (
            '10.0.0.5 - - [10/Oct/2023:13:55:37 +0000] '
            '"POST /api/orders HTTP/1.1" 201 567'
        )
        assert parse_log_line(line) == {"path": "/api/orders", "status": 201}

    def test_malformed_raises_logparseerror(self):
        with pytest.raises(LogParseError):
            parse_log_line("this line is malformed and should be skipped")

    def test_garbage_line_raises(self):
        with pytest.raises(LogParseError):
            parse_log_line("another garbage line without any structure at all")

    def test_non_digit_status_raises(self):
        line = '1.2.3.4 - - [10/Oct/2023:13:55:36 +0000] "GET /x HTTP/1.1" abc 12'
        with pytest.raises(LogParseError):
            parse_log_line(line)

    def test_error_message_contains_line(self):
        bad = "totally broken"
        try:
            parse_log_line(bad)
        except LogParseError as e:
            assert bad in str(e)

    def test_preserves_cause(self):
        # raise ... from e 保留了原始 IndexError/ValueError
        try:
            parse_log_line("garbage")
        except LogParseError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, (IndexError, ValueError))


# ---------- parse_log_file:pathlib 读 + 单行容错 ----------
class TestParseLogFile:
    def test_parses_all_good_lines(self):
        entries, skipped = parse_log_file(NGINX_LOG)
        assert len(entries) == 11
        assert skipped == [4, 10]

    def test_entry_content(self):
        entries, _ = parse_log_file(NGINX_LOG)
        # 第 1 行
        assert entries[0] == {"path": "/api/products", "status": 200}
        # 第 3 行是 /api/orders/1 500(第 4 行是脏数据被跳过,不进 entries)
        assert entries[2] == {"path": "/api/orders/1", "status": 500}

    def test_accepts_str_path(self):
        entries, skipped = parse_log_file(str(NGINX_LOG))
        assert len(entries) == 11
        assert skipped == [4, 10]

    def test_skips_dont_stop_parsing(self):
        # 第 4 行坏了,但第 5 行及以后仍然被解析(11 条里包含 5-13 行的好数据)
        entries, skipped = parse_log_file(NGINX_LOG)
        paths = [e["path"] for e in entries]
        # 第 4 行脏数据之后,第 5 行 /admin 仍然被解析到
        assert "/admin" in paths
        # 最后一行 / 也被解析到
        assert "/" in paths

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.txt"
        empty.write_text("", encoding="utf-8")
        entries, skipped = parse_log_file(empty)
        assert entries == []
        assert skipped == []

    def test_all_bad_file(self, tmp_path):
        bad = tmp_path / "bad.txt"
        bad.write_text("garbage one\ngarbage two\n", encoding="utf-8")
        entries, skipped = parse_log_file(bad)
        assert entries == []
        assert skipped == [1, 2]

    def test_missing_file_raises(self, tmp_path):
        # 文件不存在时,底层 FileNotFoundError 会抛出来(本章不包装它)
        with pytest.raises(FileNotFoundError):
            parse_log_file(tmp_path / "nope.txt")


# ---------- build_summary:raise from + try/except/else ----------
class TestBuildSummary:
    def test_aggregates_nginx_log(self):
        entries, _ = parse_log_file(NGINX_LOG)
        summary = build_summary(entries)
        assert summary == {
            "total": 11,
            "by_status": {"2xx": 6, "5xx": 3, "4xx": 2},
        }

    def test_counts_by_bucket(self):
        entries = [
            {"path": "/a", "status": 200},
            {"path": "/b", "status": 201},
            {"path": "/c", "status": 404},
            {"path": "/d", "status": 500},
            {"path": "/e", "status": 502},
        ]
        summary = build_summary(entries)
        assert summary["total"] == 5
        assert summary["by_status"] == {"2xx": 2, "4xx": 1, "5xx": 2}

    def test_empty_entries(self):
        assert build_summary([]) == {"total": 0, "by_status": {}}

    def test_missing_status_raises(self):
        entries = [{"path": "/a"}]  # 缺 status 字段
        with pytest.raises(LogParseError):
            build_summary(entries)

    def test_missing_status_preserves_cause(self):
        entries = [{"path": "/a", "status": 200}, {"path": "/b"}]
        try:
            build_summary(entries)
        except LogParseError as e:
            # raise ... from e 保留了 KeyError
            assert isinstance(e.__cause__, KeyError)

    def test_error_message_contains_entry(self):
        bad_entry = {"path": "/broken"}
        try:
            build_summary([bad_entry])
        except LogParseError as e:
            assert "/broken" in str(e)


# ---------- write_report:with open() 写文件 ----------
class TestWriteReport:
    def test_writes_expected_content(self, tmp_path):
        summary = {"total": 11, "by_status": {"2xx": 6, "5xx": 3, "4xx": 2}}
        out = tmp_path / "report.txt"
        write_report(summary, out)
        content = out.read_text(encoding="utf-8")
        assert content == "total: 11\n2xx: 6\n5xx: 3\n4xx: 2\n"

    def test_writes_single_bucket(self, tmp_path):
        summary = {"total": 3, "by_status": {"2xx": 3}}
        out = tmp_path / "r.txt"
        write_report(summary, out)
        assert out.read_text(encoding="utf-8") == "total: 3\n2xx: 3\n"

    def test_writes_empty_summary(self, tmp_path):
        summary = {"total": 0, "by_status": {}}
        out = tmp_path / "r.txt"
        write_report(summary, out)
        assert out.read_text(encoding="utf-8") == "total: 0\n"

    def test_overwrites_existing_file(self, tmp_path):
        out = tmp_path / "r.txt"
        out.write_text("old content that should be gone", encoding="utf-8")
        write_report({"total": 1, "by_status": {"2xx": 1}}, out)
        assert "old content" not in out.read_text(encoding="utf-8")

    def test_file_closed_after_write(self, tmp_path):
        # 验证 with 确实关了文件:Windows 上不关文件会导致后续写失败
        summary = {"total": 1, "by_status": {"2xx": 1}}
        out = tmp_path / "r.txt"
        write_report(summary, out)
        # 能再次打开并写入,说明上次已正确关闭
        write_report({"total": 2, "by_status": {"2xx": 2}}, out)
        assert "total: 2" in out.read_text(encoding="utf-8")


# ---------- Timer:类版上下文管理器 ----------
class TestTimer:
    def test_enter_returns_self(self):
        t = Timer()
        with t as ctx:
            assert ctx is t

    def test_elapsed_set_after_block(self):
        t = Timer()
        with t:
            pass
        assert hasattr(t, "elapsed")
        assert t.elapsed >= 0

    def test_elapsed_not_set_before_enter(self):
        t = Timer()
        assert not hasattr(t, "elapsed")

    def test_measures_real_time(self):
        import time
        t = Timer()
        with t:
            time.sleep(0.05)
        # 睡 50ms,测出来的耗时至少要有 40ms(留点余量)
        assert t.elapsed >= 0.04

    def test_exit_called_on_exception(self):
        # with 块里抛异常,__exit__ 仍然要执行并算出 elapsed
        t = Timer()
        with pytest.raises(RuntimeError):
            with t:
                raise RuntimeError("boom")
        assert hasattr(t, "elapsed")

    def test_does_not_swallow_exception(self):
        # return False:异常必须向外传播,不能被吞
        t = Timer()
        with pytest.raises(ValueError):
            with t:
                raise ValueError("must propagate")


# ---------- db_transaction:@contextmanager 事务 ----------
class TestDbTransaction:
    def _fresh_db(self):
        return {"committed": [], "pending": [], "rolled_back": False}

    def test_commit_on_success(self):
        db = self._fresh_db()
        with db_transaction(db) as tx:
            tx["pending"].append({"total": 11})
        assert db["committed"] == [{"total": 11}]
        assert db["pending"] == []

    def test_commit_multiple_records(self):
        db = self._fresh_db()
        with db_transaction(db) as tx:
            tx["pending"].append({"a": 1})
            tx["pending"].append({"b": 2})
        assert db["committed"] == [{"a": 1}, {"b": 2}]

    def test_yields_db(self):
        db = self._fresh_db()
        with db_transaction(db) as tx:
            assert tx is db

    def test_rollback_on_exception(self):
        db = self._fresh_db()
        with pytest.raises(RuntimeError):
            with db_transaction(db) as tx:
                tx["pending"].append({"total": 11})
                raise RuntimeError("DB 挂了")
        assert db["rolled_back"] is True
        assert db["committed"] == []          # 半截数据不能进 committed
        assert db["pending"] == []

    def test_pending_cleared_after_commit(self):
        db = self._fresh_db()
        with db_transaction(db) as tx:
            tx["pending"].append({"x": 1})
        assert db["pending"] == []

    def test_pending_cleared_after_rollback(self):
        db = self._fresh_db()
        with pytest.raises(RuntimeError):
            with db_transaction(db) as tx:
                tx["pending"].append({"x": 1})
                raise RuntimeError("boom")
        assert db["pending"] == []

    def test_exception_propagates(self):
        # except 里 raise 了,异常必须能被外面捕到,不能被吞
        db = self._fresh_db()
        with pytest.raises(ValueError):
            with db_transaction(db):
                raise ValueError("must propagate")

    def test_sequential_transactions(self):
        # 两次连续事务:第一次 commit,第二次 rollback,互不影响
        db = self._fresh_db()
        with db_transaction(db) as tx:
            tx["pending"].append({"batch": 1})
        assert db["committed"] == [{"batch": 1}]

        with pytest.raises(RuntimeError):
            with db_transaction(db) as tx:
                tx["pending"].append({"batch": 2})
                raise RuntimeError("second fails")
        assert db["committed"] == [{"batch": 1}]   # 第一次的还在
        assert db["rolled_back"] is True
