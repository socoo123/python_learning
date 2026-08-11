"""
Ch12 作业:现代工具链 —— logging / 配置 / 项目结构。

场景:你是「订单服务」(order-service) 的后端负责人,服务明天上线。
现在代码里全是 print、配置写死在源码里。上线前完成工程化改造:
建具名 logger → 挂控制台格式化输出 → 级别按配置可调 → 结构化事件日志
→ 配置外置(环境变量 + .env)→ dictConfig 数据化 → 一键 bootstrap。

9 个任务,从单个 API 一路递进到大综合。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch12/test_ch12_assignment.py -v

全绿 = 你掌握了 Ch12 = M2 标准库毕业 🎓。

约定:
- 模块级常量 DEFAULT_FMT 是【脚手架】,全章统一的日志格式,直接用,不用改。
- 每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
  (提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import logging
import os
from pathlib import Path

# ========== 脚手架:全章统一的日志格式(§12.3 讲透,直接用)==========
# %(asctime)s 时间 | %(levelname)s 级别名 | %(name)s logger 名 | %(message)s 消息本体
DEFAULT_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


# ========== §12.2 Logger 与级别 ==========


def make_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    【具名 logger · §12.2】给订单服务的模块创建 logger 并设置级别。

    任务:按名字拿 logger(同名返回同一个,单例),设置级别,返回。
         订单服务按模块命名:"order.api"(接口层)、"order.db"(数据层)。

    示例:
        make_logger("order.api").level                    -> 20(默认 INFO)
        make_logger("order.db", logging.DEBUG).level      -> 10
        make_logger("order") is make_logger("order")      -> True(单例)

    提示:logging.getLogger(name) + logger.setLevel(level),两行。
         别用 logging.info(...) 快捷函数——那打的是 root logger(§12.2 的坑)。
    """
    # TODO: getLogger + setLevel + return
    ...


# ========== §12.3 Handler + Formatter ==========


def add_console_handler(logger: logging.Logger, fmt: str = DEFAULT_FMT) -> logging.Logger:
    """
    【Handler/Formatter · §12.3】给 logger 挂一个带格式的控制台 handler,幂等。

    任务:logger 已有 StreamHandler 就直接返回(防重复添加——addHandler 是追加,
         初始化跑两次日志会打两遍);没有才创建 StreamHandler + 设 Formatter + 挂上。
         返回 logger 本身(支持链式)。

    示例:
        logger = make_logger("order")
        add_console_handler(logger)
        add_console_handler(logger)     # 启动流程再调一次:安全跳过
        len(logger.handlers)            -> 1

    提示:any(isinstance(h, logging.StreamHandler) for h in logger.handlers) 查重。
         设格式:handler.setFormatter(logging.Formatter(fmt))。
    """
    # TODO: 查重 → StreamHandler + setFormatter + addHandler → return logger
    ...


# ========== §12.4 级别名 → 常量 ==========


def parse_level(name: str) -> int:
    """
    【级别名转换 · §12.4】把配置里的字符串级别名(如 "debug")转成 logging 常量。

    任务:大小写、首尾空白都容忍(" Info " 也行);未知名称抛 ValueError,
         报错信息里列出可选级别(配置错了要在启动时炸出来,宁抛勿吞)。

    示例:
        parse_level("debug")    -> 10
        parse_level(" Info ")   -> 20
        parse_level("VERBOSE")  -> 抛 ValueError(信息含可选级别)

    提示:logging.getLevelNamesMapping()(3.11+)返回 {"DEBUG": 10, "INFO": 20, ...}。
         name.strip().upper() 归一化后查表;别用私有 API logging._nameToLevel。
    """
    # TODO: getLevelNamesMapping 查表 + strip/upper 归一 + 未命中 raise ValueError
    ...


# ========== §12.5 logger.log + 结构化事件 ==========


def log_event(logger: logging.Logger, level: int, event: str, **fields) -> None:
    """
    【结构化日志 · §12.5】记一条 key=value 结构化事件日志(ELK/Loki 可切字段)。

    任务:消息格式 "event=<事件名> k1=v1 k2=v2"(fields 按传入顺序拼,空格连接);
         没有 fields 时消息就是 "event=<事件名>" 本身,不多尾巴空格。
         用 logger.log(level, message)——级别是参数,不是写死的方法名。

    示例:
        log_event(logger, logging.INFO, "order_created", order_id=123, amount=99.9)
            记录文本: event=order_created order_id=123 amount=99.9
        log_event(logger, logging.WARNING, "payment_slow", order_id=123, elapsed_ms=2300)
            记录文本: event=payment_slow order_id=123 elapsed_ms=2300
        log_event(logger, logging.INFO, "app_started")
            记录文本: event=app_started

    提示:" ".join(f"{k}={v}" for k, v in fields.items()) 拼字段;
         fields 为空时跳过拼接(想一下怎么用一个表达式处理)。
    """
    # TODO: 拼 event=xxx + k=v 字段串 → logger.log(level, message)
    ...


# ========== §12.6 配置:环境变量 ==========


def get_config(key: str, default: str | None = None) -> str | None:
    """
    【环境变量 · §12.6】从环境变量读配置;不存在时返回 default。

    任务:读 key 对应的环境变量,没设置返回 default。
         注意:设了空字符串是有意的配置,要返回 "" 而不是 default(别用 or!)。

    示例(假设环境变量 ORDER_DB_DSN 未设置):
        get_config("ORDER_DB_DSN", "sqlite:///orders.db")   -> "sqlite:///orders.db"
        get_config("ORDER_DB_DSN")                          -> None
        # 若 ORDER_DB_DSN="" (显式设空):  -> ""(不是默认值)

    提示:os.environ.get(key, default) 一行。os.environ[key] 方括号取值
         缺失时抛 KeyError,读配置一律用 .get。
    """
    # TODO: os.environ.get(key, default)
    ...


# ========== §12.7 配置:.env 文件解析 ==========


def read_env_file(path) -> dict[str, str]:
    """
    【.env 解析 · §12.7】手写解析 .env 文件,返回配置 dict(值全是字符串)。

    规则(5 条,dotenv 事实标准):
      ① 空行、# 注释行跳过
      ② 可选 "export " 前缀去掉(docker-compose 风格)
      ③ 只切第一个 "="(值里可含 =)
      ④ 键值两侧 strip 空白
      ⑤ 值的成对引号('...' 或 "...")去掉

    示例文件内容:
        # 订单服务本地配置
        DB_HOST=localhost
        DB_PORT=5432
        export APP_PORT=8000
        API_KEY="abc=def"

    返回:{"DB_HOST": "localhost", "DB_PORT": "5432", "APP_PORT": "8000", "API_KEY": "abc=def"}
         (注意 DB_PORT 是字符串 "5432" 不是 int;没有 = 的行跳过)

    提示:for line in Path(path).read_text(encoding="utf-8").splitlines(): 逐行处理;
         key, value = line.split("=", 1);引号判断 value[0] == value[-1] 且是引号字符。
    """
    # TODO: 逐行解析:跳注释/空行 → 去 export → split("=", 1) → strip → 去引号
    ...


# ========== §12.8 12-Factor 合并:环境变量覆盖 .env ==========


def load_config(path, environ: dict | None = None) -> dict[str, str]:
    """
    【配置合并 · §12.8】读 .env 文件,再让环境变量覆盖同名键,返回最终配置。

    任务:.env 提供「本地默认值」;environ(None 时用 os.environ)里的同名键覆盖之。
         【只覆盖文件里已有的键】——别把 environ 里几百个系统变量倒进来:
         配置的形状由文件定义,值由环境覆盖(12-Factor / Spring 同理)。

    示例(.env 内容 "APP_PORT=8000\nDB_HOST=localhost\n"):
        load_config(path, environ={})                        -> {"APP_PORT": "8000", "DB_HOST": "localhost"}
        load_config(path, environ={"APP_PORT": "9000"})      -> {"APP_PORT": "9000", "DB_HOST": "localhost"}
        load_config(path, environ={"UNRELATED": "x"})        -> {"APP_PORT": "8000", "DB_HOST": "localhost"}
                                                              (无关环境变量不进配置)

    提示:.env 解析逻辑同 read_env_file,内联写一遍(web 端每题独立可测,
         不能调用其他作业函数);然后 for key in list(config): if key in environ: 覆盖。
    """
    # TODO: 内联 .env 解析 → 环境变量覆盖已有键
    ...


# ========== §12.9 dictConfig:配置字典 ==========


def build_logging_config(level: int = logging.INFO, log_file: str | None = None) -> dict:
    """
    【dictConfig · §12.9】生成 logging.config.dictConfig 可用的配置字典。

    任务:返回四件套 dict——version 固定 1;formatters 含名为 "standard" 的格式
         (格式串用 DEFAULT_FMT);handlers 必有 "console"(class logging.StreamHandler);
         log_file 非 None 时再加 "file"(class logging.FileHandler,带 filename);
         root 挂对应 handlers 列表、级别为 level。所有 handler 的 level 也用 level。

    示例:
        cfg = build_logging_config()
        cfg["version"]                       -> 1
        cfg["root"]                          -> {"level": 20, "handlers": ["console"]}
        cfg = build_logging_config(level=logging.DEBUG, log_file="logs/order.log")
        cfg["handlers"]["file"]["filename"]  -> "logs/order.log"
        cfg["root"]["handlers"]              -> ["console", "file"]

    提示:结构照 §12.9;file handler 的 key 是 "class"/"filename"/"formatter"/"level"。
         测试会把你返回的 dict 真喂给 logging.config.dictConfig——结构非法当场报错。
    """
    # TODO: version / formatters / handlers / root 四件套;log_file 非 None 才加 file
    ...


# ========== §12.10 综合:bootstrap 启动序列 ==========


def bootstrap(env_path, environ: dict | None = None) -> logging.Logger:
    """
    【综合 · §12.10】服务启动序列:读配置 → 定级别 → 建 logger → 挂 handler → 记启动事件。

    任务(五步,全是你练过的):
      ① 读 .env 文件(解析规则同 §12.7,内联写)
      ② environ(None 时用 os.environ)覆盖文件里已有的键(§12.8)
      ③ LOG_LEVEL 键(缺省 "INFO")转 logging 常量(§12.4)
      ④ 建具名 logger "order",设级别;没有 StreamHandler 才挂一个
        (格式用 DEFAULT_FMT,幂等,§12.2/§12.3)
      ⑤ 用 logger.info 记一条启动事件:
         f"event=app_started port={config.get('APP_PORT', '8000')}"
         (固定 INFO 级别,交 logger 自身级别过滤——LOG_LEVEL=warning 时这条不该出现)
      返回 logger。

    示例(.env 内容 "LOG_LEVEL=debug\nAPP_PORT=9000\n",environ={}):
        logger = bootstrap(path, environ={})
        logger.level                     -> 10
        # 控制台输出:... [INFO] order: event=app_started port=9000
        # 若 environ={"LOG_LEVEL": "warning"}:logger.level -> 30,启动事件被过滤

    提示:按 ①→⑤ 顺序;每步都对应前面某题的逻辑,但【全部内联】——
         web 端单题运行时其他函数还是骨架,调用它们会失败(§12.10 有解释)。
    """
    # TODO: 读配置 → 覆盖 → 级别 → logger+handler → logger.info 启动事件 → return
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch12/ch12_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    # 造一份临时 .env 演示 bootstrap 全链路
    env_file = Path(tempfile.mkdtemp()) / ".env"
    env_file.write_text(
        "# 订单服务本地配置\nLOG_LEVEL=debug\nAPP_PORT=9000\nDB_HOST=localhost\n",
        encoding="utf-8",
    )

    logger = bootstrap(env_file)  # 应看到一行带格式的启动日志
    print("logger 级别:", logger.level, "(10=DEBUG)")
    print("handler 数:", len(logger.handlers))

    log_event(logger, logging.INFO, "order_created", order_id=123, amount=99.9)
    print("级别转换:", parse_level("warning"))
    print("配置读取:", get_config("HOME", "/tmp"))
    print("合并配置:", load_config(env_file, environ={"APP_PORT": "7000"}))
    cfg = build_logging_config(level=logging.DEBUG, log_file="logs/order.log")
    print("dictConfig root:", cfg["root"])
