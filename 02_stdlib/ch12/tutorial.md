# Ch12 · 现代工具链:logging / 配置 / 项目结构

> **预计**:0.5 天 ｜ **前置**:Ch01 ｜ **M2 收官**
> **目标**:把工程化基础打好——学会 `logging`(对比 Java logback)、用环境变量/`.env` 管配置、理解 `uv`+`pyproject.toml` 项目结构。为 M3 Web 框架铺路。

> 📐 **本教程的契约**:§12.2–§12.4 对应作业。§12.5(项目结构)是配置类知识,讲透但不出 pytest 题。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `make_logger` | §12.2 | logging.getLogger + setLevel |
| `log_event` | §12.2 | logger.log |
| `get_config` | §12.4 | os.environ 环境变量 |
| `read_env_file` | §12.4 | .env 文件解析 |

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## §12.1 为什么用 logging 不用 print

`print` 只能往屏幕输出,没法控制级别、没法写文件、没法分模块。`logging` 解决一切:

```python
import logging
logging.warning("磁盘空间不足")    # WARNING 级别
logging.info("任务完成")           # INFO(默认不显示,要配置)
```

> 🟡 **Java 对比**:= `org.slf4j.Logger` / logback。Python logging 是标准库内置,不用引三方包。

---

## §12.2 logging 四要素(对应:`make_logger`、`log_event`)🟡

理解这四个概念(和 logback 一一对应):

| 概念 | 作用 | Java 对应 |
|------|------|-----------|
| **Logger** | 记录器,代码里调它 | `Logger` |
| **Handler** | 输出到哪(控制台/文件) | `Appender` |
| **Formatter** | 输出格式 | `PatternLayout` |
| **Level** | 级别(DEBUG/INFO/WARNING/ERROR) | `Level` |

### 级别(从低到高)

```
DEBUG(10) < INFO(20) < WARNING(30) < ERROR(40) < CRITICAL(50)
```
设了某个级别,只输出**不低于**它的日志。生产通常设 INFO,调试设 DEBUG。

### 创建 logger

```python
import logging

logger = logging.getLogger("myapp")   # 按模块名命名(单例:同名返回同一个)
logger.setLevel(logging.INFO)         # 设级别
```

**关键特性**:
- `getLogger(name)` 同名返回**同一个** logger(单例)——所以跨模块用 `getLogger("myapp")` 拿到同一个,配置一次到处用。
- logger 有**层级**:`getLogger("myapp.db")` 是 `myapp` 的子 logger,继承父的配置。

### 记录日志

```python
logger.info("应用启动")             # 便捷方法
logger.warning("磁盘 80%")
logger.error("连接失败", exc_info=True)   # exc_info 记录异常栈
logger.log(logging.INFO, "消息")    # 通用方法(本节作业)
```

> 本节作业 `log_event` 用通用的 `logger.log(level, message)`,level 作为参数(可传 INFO/WARNING/...)。

> ✅ 做 `make_logger` 题:`logging.getLogger(name)` + `setLevel(level)`。
> 做 `log_event` 题:`logger.log(level, message)`。

---

## §12.3 logging 进阶:Handler / Formatter(了解)

默认 logger 只输出到控制台且格式简陋。生产要配置 Handler + Formatter:

```python
logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

# 控制台 handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# 文件 handler
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# 格式
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
console.setFormatter(fmt)
file_handler.setFormatter(fmt)

logger.addHandler(console)
logger.addHandler(file_handler)
```

正式项目通常把这段写进一个 `setup_logging()` 函数,或用 `logging.config.dictConfig`(配置文件,= logback.xml)。本章作业不要求,知道结构即可。

---

## §12.4 配置管理:环境变量 + .env(对应:`get_config`、`read_env_file`)🟡

**铁律**:API key、数据库密码、端口等**绝不通进代码**,走配置。最常见两种:

### ① 环境变量(`os.environ`)

```python
import os
db_password = os.environ.get("DB_PASSWORD", "默认值")   # 不存在返回默认
port = os.environ.get("PORT", "8000")
```

部署时 `DB_PASSWORD=xxx python app.py` 或 Docker/CI 注入。代码里只有 `getenv`,看不到明文密码。

> 🟡 **Java 对比**:= Spring 的 `${DB_PASSWORD}` 占位符 + 环境变量注入。Python 直接 `os.environ.get`。

### ② `.env` 文件(开发环境最方便)

`.env` 文件(项目根,记得 `.gitignore`):
```
DB_HOST=localhost
DB_PORT=5432
API_KEY=sk-xxxx
```

- 生产用 `python-dotenv` 库自动加载:`load_dotenv()` 后,`.env` 里的键进入 `os.environ`,然后照常用 `os.environ.get`。
- 本章作业 `read_env_file` 让你**手写解析**(理解原理,不依赖三方库)。

> ✅ 做 `get_config` 题:`os.environ.get(key, default)`。
> 做 `read_env_file` 题:逐行读,跳过空行/`#`注释,`split("=", 1)` 拆键值。

---

## §12.5 项目结构:uv + pyproject.toml(配置类,讲透不出题)🔴

这是 M3 前必须理解的工程化基础。

### pyproject.toml = pom.xml

本项目的 `pyproject.toml` 已经是标准结构(你看一眼):

```toml
[project]
name = "python-learning"
dependencies = ["pytest>=8.0", ...]          # 基础依赖

[project.optional-dependencies]               # 可选依赖组
web = ["fastapi>=0.110", "uvicorn", ...]      # 学到 Web 章节再装
ai = ["anthropic", "openai", ...]

[tool.pytest.ini_options]
testpaths = ["01_python_core", "02_stdlib", ...]   # pytest 测试目录
```

> 🟡 **Java 对比**:= `pom.xml`。`dependencies` = `<dependencies>`,`optional-dependencies` = Maven profiles(按需装)。`[tool.xxx]` 段是各工具配置(pytest/mypy/ruff),= Maven plugins。

### uv:现代包管理(本项目在用)

你前面一直在用的 `uv run pytest` 就是 uv。核心命令:

```bash
uv venv                    # 建虚拟环境
uv add fastapi             # 装包并写进 pyproject(= mvn install + 改 pom)
uv add --dev pytest        # 装到 dev 组
uv sync                    # 按 pyproject + uv.lock 同步装全依赖
uv run pytest              # 在项目环境里跑命令(自动激活虚拟环境)
```

> uv 的 `uv.lock` 锁定精确版本(= Maven 的锁版本),保证不同机器装出相同环境。

### 标准项目布局(M3 会用到)

```
myproject/
├── pyproject.toml         # 项目配置(= pom.xml)
├── uv.lock                # 依赖锁
├── src/myproject/         # 源码(src layout,推荐)
│   ├── __init__.py
│   └── main.py
├── tests/                 # 测试
└── .env                   # 本地配置(gitignore)
```

本项目是「学习项目」,布局是按章节分目录(`01_python_core/` 等)。正式项目通常用上面的 `src` layout。M3 会演示。

---

## §12.6 Java 老手常踩的坑 ⚠️

1. **`print` 调试 vs logging**:正式代码用 logging,print 只用于临时调试。print 没法关级别、没法写文件。
2. **logger 是单例**:`getLogger("x")` 多次调用返回同一个,配置一处生效。别 `Logger()` 构造(不存在)。
3. **密码别进代码**:用环境变量/`.env`,且 `.env` 加进 `.gitignore`。
4. **`.env` 不进 git**:里面是密钥,泄露了就完了。本项目 `.gitignore` 已含。
5. **level 过滤是「不低于」**:设了 INFO,DEBUG 不显示。调试时临时改 DEBUG。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `make_logger` | logging.getLogger + setLevel | 🟢 |
| `log_event` | logger.log | 🟢 |
| `get_config` | os.environ 环境变量 | 🟢 |
| `read_env_file` | .env 解析 | 🟡 |

```bash
uv run pytest 02_stdlib/ch12/test_ch12_assignment.py -v
```

全绿 = 掌握 Ch12 = **M2 标准库毕业** 🎓。

---

## ✅ 自测

- [ ] 能说清 logging 的 logger/handler/formatter/level 四要素(§12.2)
- [ ] 知道为什么配置要走环境变量/`.env` 而非写死在代码(§12.4)
- [ ] 理解 pyproject.toml 和 uv.lock 的作用(§12.5)
- [ ] 4 个作业全绿

## 🎓 费曼挑战

1. 「logging 的四要素各对应 Java logback 的什么?为什么别用 print?」— 重读 §12.1/§12.2
2. 「为什么 API key 要走环境变量/`.env` 而不是写进代码?`.env` 为什么不进 git?」— 重读 §12.4

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:M2 毕业,进入 M3

恭喜!Ch08–Ch12 完成,Python **标准库**核心你已掌握(collections/itertools/正则/json/datetime/logging)。

下一站 **M3 Web 框架 FastAPI**(Ch13–22):从「调 API」到「写 API」,搭一个带数据库、认证、测试的完整 RESTful 服务。这是你最初点名的核心方向之一。

> 建议进 M3 前,先把 M1(Ch02–07)+ M2(Ch08–12)的费曼挑战和闪卡过一遍——语言和标准库的基础现在成体系了,M3 会大量用到。
