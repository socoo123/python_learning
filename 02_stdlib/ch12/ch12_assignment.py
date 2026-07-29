"""
Ch12 作业:现代工具链 —— logging / 配置 / .env。

4 个任务。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch12/test_ch12_assignment.py -v

全绿 = 你掌握了 Ch12 = M2 标准库毕业 🎓。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import logging
import os
from pathlib import Path


# ========== §12.2 logging ==========


def make_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    【logging · §12.2】创建并配置一个 logger(设置日志级别)。

    示例:
        logger = make_logger("myapp")
        logger.level  -> logging.INFO(20)

    思路:logging.getLogger(name) 获取(或创建)logger;logger.setLevel(level)。
         同名多次 getLogger 返回同一个(logger 是单例)。
    """
    # TODO: getLogger + setLevel + return
    ...


def log_event(logger: logging.Logger, message: str, level: int = logging.INFO) -> None:
    """
    【logging · §12.2】用 logger 记录一条日志(默认 INFO 级别)。

    示例:
        log_event(logger, "应用启动")

    思路:logger.log(level, message)。level 可传 logging.WARNING / ERROR 等。
    """
    # TODO: logger.log(level, message)
    ...


# ========== §12.4 配置:环境变量 ==========


def get_config(key: str, default=None):
    """
    【环境变量 · §12.4】从环境变量读配置;不存在返回 default。

    示例:
        get_config("PORT", "8000")   # 有 PORT 环境变量用之,否则 "8000"

    思路:os.environ.get(key, default)。
         生产配置(API key、数据库密码)绝不通进代码,走环境变量。
    """
    # TODO: os.environ.get(key, default)
    ...


# ========== §12.4 配置:.env 文件解析 ==========


def read_env_file(path) -> dict:
    """
    【.env · §12.4】解析简单的 .env 文件(KEY=VALUE),返回 dict。
    规则:跳过空行和 # 注释;VALUE 支持包含 = 号(只切第一个 =)。

    示例文件内容:
        DB_HOST=localhost
        DB_PORT=5432
        # 这是注释
        API_KEY=abc=def

    思路:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            跳过空行和 # 开头
            if "=" in line: key, value = line.split("=", 1); config[key.strip()] = value.strip()
    """
    # TODO: 逐行解析,跳过注释/空行,split("=", 1)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    logger = make_logger("demo")
    log_event(logger, "应用启动")
    print("PORT from env:", get_config("PORT", "8000"))
