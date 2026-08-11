"""
Ch12 作业测试。运行: uv run pytest 02_stdlib/ch12/test_ch12_assignment.py -v

caplog 是 pytest 内置 fixture:自动抓取测试期间产生的日志记录,
断言 "某条日志确实被记录/过滤" 全靠它(教程 §12.5 附注)。
"""
import logging
import logging.config

import pytest

from ch12_assignment import (
    DEFAULT_FMT,
    make_logger,
    add_console_handler,
    parse_level,
    log_event,
    get_config,
    read_env_file,
    load_config,
    build_logging_config,
    bootstrap,
)


# ---------- make_logger:具名 logger 与级别 ----------
class TestMakeLogger:
    def test_returns_logger(self):
        assert isinstance(make_logger("t12_basic"), logging.Logger)

    def test_default_level_info(self):
        assert make_logger("t12_default").level == logging.INFO

    def test_custom_level(self):
        assert make_logger("t12_debug", level=logging.DEBUG).level == logging.DEBUG

    def test_same_name_same_instance(self):
        # getLogger 单例:同名返回同一个对象,配置一次处处生效
        assert make_logger("t12_shared") is make_logger("t12_shared")

    def test_named_not_root(self):
        # 具名 logger 不是 root(业务代码不该用 root)
        assert make_logger("t12_named") is not logging.getLogger()


# ---------- add_console_handler:Handler + Formatter + 幂等 ----------
class TestAddConsoleHandler:
    def test_adds_stream_handler(self):
        logger = make_logger("t12_h_add")
        add_console_handler(logger)
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 1

    def test_returns_logger_for_chaining(self):
        logger = make_logger("t12_h_chain")
        assert add_console_handler(logger) is logger

    def test_idempotent_no_duplicate(self):
        # 防「日志打两遍」:重复调用不能重复挂 handler
        logger = make_logger("t12_h_idem")
        add_console_handler(logger)
        add_console_handler(logger)
        add_console_handler(logger)
        assert len(logger.handlers) == 1

    def test_formatter_applied(self):
        logger = make_logger("t12_h_fmt")
        add_console_handler(logger, fmt="%(levelname)s|%(message)s")
        record = logger.makeRecord("t12_h_fmt", logging.INFO, "app.py", 1, "order created", None, None)
        assert logger.handlers[0].formatter.format(record) == "INFO|order created"

    def test_default_fmt_is_chapter_standard(self):
        logger = make_logger("t12_h_deffmt")
        add_console_handler(logger)
        assert logger.handlers[0].formatter._fmt == DEFAULT_FMT


# ---------- parse_level:级别名 → 常量 ----------
class TestParseLevel:
    def test_common_levels(self):
        assert parse_level("debug") == logging.DEBUG
        assert parse_level("INFO") == logging.INFO
        assert parse_level("warning") == logging.WARNING
        assert parse_level("ERROR") == logging.ERROR

    def test_case_and_whitespace_tolerant(self):
        # 配置文件里的脏数据:" Info " 这种要写容错
        assert parse_level(" Info ") == logging.INFO
        assert parse_level("WaRnInG") == logging.WARNING

    def test_unknown_level_raises(self):
        # 宁抛勿吞:配置写错要在启动时炸出来
        with pytest.raises(ValueError):
            parse_level("VERBOSE")

    def test_error_message_lists_options(self):
        with pytest.raises(ValueError, match="DEBUG"):
            parse_level("VERBOSE")


# ---------- log_event:结构化事件日志 ----------
class TestLogEvent:
    def test_event_with_fields(self, caplog):
        caplog.set_level(logging.DEBUG)
        logger = make_logger("t12_ev_fields")
        log_event(logger, logging.INFO, "order_created", order_id=123, amount=99.9)
        assert "event=order_created order_id=123 amount=99.9" in caplog.text

    def test_level_is_a_parameter(self, caplog):
        caplog.set_level(logging.DEBUG)
        logger = make_logger("t12_ev_level")
        log_event(logger, logging.WARNING, "payment_slow", order_id=123, elapsed_ms=2300)
        assert caplog.records[0].levelno == logging.WARNING
        assert caplog.records[0].getMessage() == "event=payment_slow order_id=123 elapsed_ms=2300"

    def test_no_fields_no_trailing_space(self, caplog):
        caplog.set_level(logging.DEBUG)
        logger = make_logger("t12_ev_plain")
        log_event(logger, logging.INFO, "app_started")
        assert caplog.records[0].getMessage() == "event=app_started"

    def test_filtered_by_logger_level(self, caplog):
        # logger 级别 INFO(默认),DEBUG 事件在 logger 这一层就被过滤
        caplog.set_level(logging.DEBUG)  # root 放开,隔离变量:只看 logger 自身级别
        logger = make_logger("t12_ev_filter")  # 默认 INFO
        log_event(logger, logging.DEBUG, "cache_hit", key="hot:products")
        assert "cache_hit" not in caplog.text


# ---------- get_config:环境变量 ----------
class TestGetConfig:
    def test_reads_existing_env(self, monkeypatch):
        monkeypatch.setenv("CH12_DB_DSN", "postgres://u:p@db:5432/orders")
        assert get_config("CH12_DB_DSN") == "postgres://u:p@db:5432/orders"

    def test_default_when_missing(self):
        assert get_config("CH12_NOT_SET_X", "sqlite:///orders.db") == "sqlite:///orders.db"

    def test_default_is_none(self):
        assert get_config("CH12_NOT_SET_X") is None

    def test_empty_string_is_a_value(self, monkeypatch):
        # 显式设空 ≠ 没设。or 写法会把 "" 吞成 default,这条专拦它
        monkeypatch.setenv("CH12_EMPTY", "")
        assert get_config("CH12_EMPTY", "fallback") == ""


# ---------- read_env_file:.env 手写解析 ----------
class TestReadEnvFile:
    def test_basic_parse(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("DB_HOST=localhost\nDB_PORT=5432\n", encoding="utf-8")
        assert read_env_file(f) == {"DB_HOST": "localhost", "DB_PORT": "5432"}

    def test_skips_comments_and_blanks(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("# 订单服务配置\n\n   \nDB_HOST=localhost\n", encoding="utf-8")
        assert read_env_file(f) == {"DB_HOST": "localhost"}

    def test_export_prefix(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("export APP_PORT=8000\n", encoding="utf-8")
        assert read_env_file(f) == {"APP_PORT": "8000"}

    def test_quoted_value_unwrapped(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text('API_KEY="abc=def"\n', encoding="utf-8")
        assert read_env_file(f) == {"API_KEY": "abc=def"}

    def test_value_can_contain_equals(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("DB_URL=postgres://u:p@h:5432/db?opt=1\n", encoding="utf-8")
        assert read_env_file(f) == {"DB_URL": "postgres://u:p@h:5432/db?opt=1"}

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("  DB_HOST  =  localhost  \n", encoding="utf-8")
        assert read_env_file(f) == {"DB_HOST": "localhost"}

    def test_line_without_equals_skipped(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("JUST_A_FLAG\nA=1\n", encoding="utf-8")
        assert read_env_file(f) == {"A": "1"}

    def test_values_are_strings(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("DB_PORT=5432\nDEBUG=true\n", encoding="utf-8")
        cfg = read_env_file(f)
        assert cfg["DB_PORT"] == "5432"   # 字符串,不是 int
        assert cfg["DEBUG"] == "true"     # 字符串,不是 bool


# ---------- load_config:12-Factor 合并 ----------
ENV_SAMPLE = "APP_PORT=8000\nDB_HOST=localhost\nLOG_LEVEL=info\n"


class TestLoadConfig:
    def _write(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text(ENV_SAMPLE, encoding="utf-8")
        return f

    def test_file_values_when_env_silent(self, tmp_path):
        cfg = load_config(self._write(tmp_path), environ={})
        assert cfg == {"APP_PORT": "8000", "DB_HOST": "localhost", "LOG_LEVEL": "info"}

    def test_env_overrides_file(self, tmp_path):
        # 部署环境注入 APP_PORT=9000,压过 .env 的 8000;未覆盖的键保持文件值
        cfg = load_config(self._write(tmp_path), environ={"APP_PORT": "9000"})
        assert cfg["APP_PORT"] == "9000"
        assert cfg["DB_HOST"] == "localhost"

    def test_unrelated_env_keys_ignored(self, tmp_path):
        # 配置的形状由文件定义:文件没有的键,环境变量里有也不收
        cfg = load_config(self._write(tmp_path), environ={"CH12_UNRELATED_XYZ": "1"})
        assert "CH12_UNRELATED_XYZ" not in cfg
        assert len(cfg) == 3

    def test_defaults_to_os_environ(self, tmp_path, monkeypatch):
        # environ 不传时读真实环境变量(测试里用 monkeypatch 注入)
        monkeypatch.setenv("LOG_LEVEL", "debug")
        cfg = load_config(self._write(tmp_path))
        assert cfg["LOG_LEVEL"] == "debug"


# ---------- build_logging_config:dictConfig 字典 ----------
class TestBuildLoggingConfig:
    def test_version_and_formatter(self):
        cfg = build_logging_config()
        assert cfg["version"] == 1
        assert cfg["formatters"]["standard"]["format"] == DEFAULT_FMT

    def test_console_only_by_default(self):
        cfg = build_logging_config()
        assert set(cfg["handlers"]) == {"console"}
        assert cfg["handlers"]["console"]["class"] == "logging.StreamHandler"
        assert cfg["handlers"]["console"]["level"] == logging.INFO
        assert cfg["root"] == {"level": logging.INFO, "handlers": ["console"]}

    def test_file_handler_added(self):
        cfg = build_logging_config(level=logging.DEBUG, log_file="logs/order.log")
        assert cfg["handlers"]["file"]["class"] == "logging.FileHandler"
        assert cfg["handlers"]["file"]["filename"] == "logs/order.log"
        assert cfg["handlers"]["file"]["level"] == logging.DEBUG
        assert cfg["root"]["handlers"] == ["console", "file"]
        assert cfg["root"]["level"] == logging.DEBUG

    def test_no_file_handler_when_none(self):
        cfg = build_logging_config(log_file=None)
        assert "file" not in cfg["handlers"]
        assert cfg["root"]["handlers"] == ["console"]

    def test_config_accepted_by_dictconfig(self):
        # 结构非法(dict 缺 version、引用了不存在的 formatter 等)在这里直接抛
        logging.config.dictConfig(build_logging_config())
        root = logging.getLogger()
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)


# ---------- bootstrap:综合启动序列 ----------
class TestBootstrap:
    def _write(self, tmp_path, content):
        f = tmp_path / ".env"
        f.write_text(content, encoding="utf-8")
        return f

    def test_full_start_sequence(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        env = self._write(tmp_path, "LOG_LEVEL=info\nAPP_PORT=8000\n")
        logger = bootstrap(env, environ={})
        assert logger.name == "order"
        assert logger.level == logging.INFO
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 1
        assert "event=app_started port=8000" in caplog.text

    def test_env_overrides_log_level(self, tmp_path):
        env = self._write(tmp_path, "LOG_LEVEL=info\nAPP_PORT=8000\n")
        logger = bootstrap(env, environ={"LOG_LEVEL": "warning"})
        assert logger.level == logging.WARNING

    def test_debug_level_from_file(self, tmp_path):
        env = self._write(tmp_path, "LOG_LEVEL=debug\nAPP_PORT=9000\n")
        logger = bootstrap(env, environ={})
        assert logger.level == logging.DEBUG

    def test_startup_event_filtered_at_warning(self, tmp_path, caplog):
        # LOG_LEVEL=warning 时,INFO 级别的启动事件被 logger 自身过滤
        caplog.set_level(logging.DEBUG)  # root 放开,只看 logger 级别
        env = self._write(tmp_path, "LOG_LEVEL=warning\nAPP_PORT=8000\n")
        bootstrap(env, environ={})
        assert "app_started" not in caplog.text

    def test_idempotent_handlers_across_calls(self, tmp_path):
        # 反复 bootstrap(测试/预热场景),handler 不重复
        env = self._write(tmp_path, "LOG_LEVEL=info\nAPP_PORT=8000\n")
        bootstrap(env, environ={})
        logger = bootstrap(env, environ={})
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 1
