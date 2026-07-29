"""
Ch12 作业测试。运行: uv run pytest 02_stdlib/ch12/test_ch12_assignment.py -v
"""
import logging

import pytest

from ch12_assignment import make_logger, log_event, get_config, read_env_file


# ---------- make_logger:logging ----------
class TestMakeLogger:
    def test_returns_logger(self):
        assert isinstance(make_logger("t_basic"), logging.Logger)

    def test_default_level_info(self):
        logger = make_logger("t_default")
        assert logger.level == logging.INFO

    def test_custom_level(self):
        logger = make_logger("t_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_same_name_returns_same_logger(self):
        # getLogger 同名返回同一个实例(单例)
        a = make_logger("t_shared")
        b = make_logger("t_shared")
        assert a is b


# ---------- log_event:logging 记录 ----------
class TestLogEvent:
    def test_logs_info(self, caplog):
        caplog.set_level(logging.INFO)
        logger = make_logger("t_log_info")
        log_event(logger, "hello world")
        assert "hello world" in caplog.text

    def test_logs_at_given_level(self, caplog):
        caplog.set_level(logging.WARNING)
        logger = make_logger("t_log_warn")
        log_event(logger, "something wrong", level=logging.WARNING)
        assert "something wrong" in caplog.text
        # 记录确实是 WARNING 级别
        assert any(r.levelno == logging.WARNING for r in caplog.records)


# ---------- get_config:环境变量 ----------
class TestGetConfig:
    def test_reads_existing_env(self, monkeypatch):
        monkeypatch.setenv("CH12_TEST_KEY", "abc123")
        assert get_config("CH12_TEST_KEY") == "abc123"

    def test_default_when_missing(self):
        assert get_config("CH12_NOPE_NOT_SET", "fallback") == "fallback"

    def test_default_none(self):
        assert get_config("CH12_NOPE_NOT_SET") is None


# ---------- read_env_file:.env 解析 ----------
class TestReadEnvFile:
    def test_parses_key_value(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret", encoding="utf-8")
        cfg = read_env_file(f)
        assert cfg == {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}

    def test_skips_comments_and_blanks(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("# a comment\n\n   \nA=1", encoding="utf-8")
        assert read_env_file(f) == {"A": "1"}

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("KEY = value ", encoding="utf-8")
        assert read_env_file(f) == {"KEY": "value"}

    def test_value_can_contain_equals(self, tmp_path):
        # 只切第一个 =,所以 value 里的 = 保留
        f = tmp_path / ".env"
        f.write_text("URL=host=db;user=admin", encoding="utf-8")
        assert read_env_file(f)["URL"] == "host=db;user=admin"

    def test_values_are_strings(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("PORT=8000\nDEBUG=true", encoding="utf-8")
        cfg = read_env_file(f)
        assert cfg["PORT"] == "8000"   # 字符串,不是 int
        assert cfg["DEBUG"] == "true"  # 字符串,不是 bool
