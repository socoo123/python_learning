# Python 全栈精通学习大纲（面向 15 年 Java 经验开发者）

> **学习者画像**：15 年 Java 后端经验，熟悉 OOP、并发、Web、API 设计。
> **目标**：一个月内彻底掌握 Python，核心覆盖 **Web 框架 / 运维脚本 / AI 框架 / LeetCode** 四大方向。
> **方法论**：对比 Java 快速过语法 → 实战驱动（web 调用 + mock json 解析 + pytest 验证）→「测试通过 = 掌握」。
> **进度估算**：共 40 章，约 30 天，每天 1–2 小时。

---

## 📐 学习方法论（重要，请先读）

每一章都遵循统一的**「五件套」**结构(命名规范):

```
ch{NN}/
├── tutorial.md               ← 教程正文(费曼五步骨架:地图/路径/预览猜/正文/费曼)
├── ch{NN}_assignment.py      ← 你的作业(函数签名已给,你填实现)
├── test_ch{NN}_assignment.py ← 测试用例(pytest,全绿 = 掌握)
├── review.md                 ← 本章记忆闪卡 + 复习日程
└── mock_data/*.json          ← 模拟数据(商品、API 返回值、日志等)
```

**工作流(费曼五步循环)**:
1. 你说「我要学第 N 章」→ 我生成该章五件套。
2. 你按 `tutorial.md` 的五步走:① 预览猜 → ② 先动手写 `ch{NN}_assignment.py` → ③ `pytest` 红绿 → ④ 费曼解释 → ⑤ 把 `review.md` 的卡标复习日期。
3. 全绿 + 费曼讲清 = 过关 → 下一章。每天开学习前先翻根 [`REVIEW.md`](./REVIEW.md) 的「今日复习」。

**作业设计的核心模式**（贯穿全程）：
> 「设计一个 web 调用逻辑，从 mock 的 json 中解析数据，处理后返回给前端」
> —— 你举的那个例子，会以不同难度出现在几乎每一章里。

---

## 🗓️ 总览：6 大模块 / 40 章

| 模块 | 章节 | 天数 | 核心产出 |
|------|------|------|----------|
| **M1 语言核心** | Ch01–Ch07 | 5–7 天 | Python 思维、数据结构、OOP、异步 |
| **M2 标准库 & 三方库** | Ch08–Ch12 | 4–5 天 | collections/itertools/正则/json/datetime |
| **M3 Web 框架 FastAPI** ⭐ | Ch13–Ch22 | 7–8 天 | 一个完整的 API 项目 |
| **M4 运维脚本** | Ch23–Ch27 | 4–5 天 | CLI 工具、批处理、监控脚本 |
| **M5 AI 框架** ⭐ | Ch28–Ch33 | 5–6 天 | LLM 调用 / RAG / Agent |
| **M6 LeetCode 实战** | Ch34–Ch40 | 5–6 天 | Pythonic 刷题技巧 |

⭐ = 你明确点名的核心方向。

---

# 模块一：Python 语言核心（Ch01–Ch07）

> 目标：建立 Python 思维，而不是「用 Java 的方式写 Python」。7 章快速过完语言本身。

---

## Ch01 · 环境工具链 & 从 Java 到 Python 的思维转换
**预计**：1 天 ｜ **前置**：无

**学习目标**：搭好开发环境，理解 Python 与 Java 的根本差异，避免写出「Java 风格的 Python」。

**核心知识点**（对比 Java）：
| 概念 | Java | Python |
|------|------|--------|
| 类型系统 | 静态强类型，编译期检查 | 动态强类型 + 可选类型注解（运行时不强制） |
| 一切皆对象 | 基本类型不是对象 | 真的一切皆对象（函数、类、模块都是） |
| 入口 | `public static void main` | `if __name__ == "__main__":` |
| 包管理 | Maven/Gradle | pip + venv（推荐 uv / poetry） |
| 编译 | javac → .class | 解释执行（.pyc 缓存） |

**工具链**：
- pyenv（多版本，你已装）｜ pip ｜ venv 虚拟环境 ｜ **uv**（现代极速，推荐）｜ pytest ｜ mypy（类型检查）｜ ruff（linter+formatter）

**实战案例**：用 `uv` 创建项目虚拟环境，装好 pytest，写第一个 `test_smoke.py` 跑通「绿条」。

**作业设想**：配置环境 + 写一个 `add(a, b)` 函数 + 3 个测试用例，全绿即过关（确认机制跑通）。

---

## Ch02 · 数据结构：list / tuple / dict / set
**预计**：1 天 ｜ **前置**：Ch01

**学习目标**：掌握 Python 四大内置容器，对应 Java 的 `ArrayList` / `不可变List` / `HashMap` / `HashSet`，并学会 Pythonic 用法。

**核心知识点**：
- `list`：可变序列 → 切片 `a[1:3]`、`a[::-1]`、列表方法、对比 `ArrayList`
- `tuple`：不可变 → 解包 `x, y = point`、多返回值、`namedtuple`
- `dict`：哈希表 → `.get()`、`.items()`、字典推导、3.7+ 有序
- `set` / `frozenset`：集合运算（交集并集差集），去重 O(1)
- ⚡ **可变默认参数陷阱**（Java 没有）：`def f(x=[])` 的坑

**实战案例**：从 `mock_data/products.json`（10 个商品）解析，按类目分组，统计每类总价。

**作业设想**：实现 `filter_products(products, min_price, category)` → 返回过滤+排序后的商品名+价格列表。测试用例覆盖：空列表、价格边界、类目不存在、排序稳定性。

---

## Ch03 · 控制流、迭代器、生成器、推导式
**预计**：1 天 ｜ **前置**：Ch02

**学习目标**：掌握 Python 特有的控制流（`for-else`）和强大的迭代机制——这是 Python 效率的核心。

**核心知识点**：
- `for-else` / `while-else`（Java 没有，面试常考）
- 推导式：`[x*2 for x in xs if x>0]`、字典/集合推导式（替代 Java 的 stream）
- 迭代器协议 `__iter__` / `__next__`（对比 Java `Iterator`）
- **生成器** `yield`：惰性求值，省内存，对比 Java 的 `Stream` / 反应式
- `enumerate` / `zip` / `map` / `filter`
- 解包与星号：`a, *rest = xs`、`f(*args, **kwargs)`

**实战案例**：用生成器逐行读取大日志文件（GB 级），流式过滤 ERROR，而不是一次 `read()` 进内存。

**作业设想**：实现 `top_n_products(product_iter, n)`，输入是生成器（模拟从 mock json 流式读取），返回价格前 N 的商品。测试：大数据量（10w 条）、N 超过总数、重复价格。

---

## Ch04 · 函数：一等公民、闭包、装饰器
**预计**：1 天 ｜ **前置**：Ch03

**学习目标**：理解函数在 Python 中是「一等公民」，掌握装饰器——Python 最强大的特性之一（Java 注解的进阶版）。

**核心知识点**：
- 函数是对象：可赋值、传参、返回（对比 Java 的函数式接口/lambda 限制）
- `*args` / `**kwargs`（对比 Java 可变参数）
- **闭包**（对比 Java lambda 捕获 effectively final）
- **装饰器** `@decorator`：日志、计时、缓存、权限（= Java AOP/拦截器）
- `functools.wraps`、带参数的装饰器、类装饰器
- `lambda`（对比 Java lambda，但 Python 里不建议滥用）

**实战案例**：写 `@timer` 和 `@retry(times=3)` 装饰器，给 API 调用函数加超时重试逻辑。

**作业设想**：实现 `@cached` 装饰器（自己手写，不用 `lru_cache`），缓存函数返回值。测试：相同入参只调一次、不同入参独立、缓存命中计数正确。

---

## Ch05 · OOP：魔术方法、继承、dataclass
**预计**：1 天 ｜ **前置**：Ch04

**学习目标**：理解 Python 的 OOP 与 Java 的本质区别——没有重载、有多继承、靠「魔术方法」实现运算符重载。

**核心知识点**：
| Java 概念 | Python 对应 |
|-----------|-------------|
| 构造器 `new` | `__init__`（不是 `__new__`） |
| `toString` | `__repr__` / `__str__` |
| `equals`/`hashCode` | `__eq__` / `__hash__` |
| 运算符重载（Java 没有） | `__lt__` `__add__` 等 |
| interface | duck typing / `Protocol`（Ch07） |
| 单继承 + interface | **多继承 + MRO**（C3 线性化） |
| `@Data` Lombok | **`@dataclass`**（标准库自带！） |
| getter/setter | `@property` |

- `@dataclass`：自动生成 `__init__`/`__repr__`/`__eq__`（Java 老手最爱）
- `@property`：受控属性访问
- `super()` 调用父类
- 魔术方法 `__len__` `__getitem__` `__contains__`（让自定义类支持 `len()`/`in`/`[]`）

**实战案例**：用 `@dataclass` 建模「商品」「订单」，实现 `Order` 支持 `+` 合并、`len()` 返回商品数、可迭代。

**作业设想**：实现一个 `ShoppingCart` 类，支持添加/删除商品、`@property` 计算总价、`__contains__` 支持 `if product in cart`、`__iter__` 支持遍历。测试用例验证所有魔术方法。

---

## Ch06 · 异常、上下文管理器、文件 IO
**预计**：0.5 天 ｜ **前置**：Ch05

**学习目标**：掌握 Python 的资源管理方式 `with`（= Java try-with-resources 的优雅版）。

**核心知识点**：
- 异常体系：`BaseException` ← `Exception`（对比 Java `Throwable` ← `Exception`）
- `try/except/else/finally`（对比 Java `try/catch/finally`，注意没有 checked exception）
- 自定义异常（继承 `Exception`）
- **`with` 语句 + 上下文管理器**：`__enter__` / `__exit__`（= Java try-with-resources / AutoCloseable）
- `contextlib.contextmanager`：用生成器写上下文管理器
- 文件 IO：`open()`、`pathlib.Path`（替代 `os.path`）

**实战案例**：封装一个「数据库连接」上下文管理器，自动 commit/rollback；用 `pathlib` 批量读取 mock json 文件。

**作业设想**：实现 `@contextmanager` 装饰的 `timer()` 上下文，记录代码块耗时；实现 `safe_read_json(path)` 在文件不存在时抛自定义 `DataLoadError`。测试覆盖正常/异常路径。

---

## Ch07 · 类型注解与 Pythonic 风格
**预计**：0.5 天 ｜ **前置**：Ch05

**学习目标**：给 Python 加上「准静态类型」，让你从 Java 过来更舒服；学会写地道的 Python 代码。

**核心知识点**：
- 类型注解：`def f(x: int) -> str:`（运行时不强制，靠 mypy 检查）
- `typing`：`List[int]` `Dict[str, Product]` `Optional[X]` `Union[A, B]`、3.10+ 用 `X | Y`
- `Callable`、`TypeVar`、`Generic`（对比 Java 泛型）
- **`Protocol`**：结构化类型 = Java interface 但鸭子类型版
- `TypedDict`：字典的强类型
- **mypy** 静态检查（模拟编译期）
- Pythonic 风格：`The Zen of Python`（`import this`）、EAFP（请求宽恕比许可容易）vs Java 的 LBYL

**实战案例**：把前几章的作业代码加上完整类型注解，跑 `mypy` 零报错。

**作业设想**：给定一个无类型注解的「订单处理」模块，补全所有类型注解 + 定义 `Protocol`，使 mypy 严格模式通过。

---

# 模块二：标准库 & 常用三方库（Ch08–Ch12）

> 目标：Python「自带电池（batteries included）」。掌握这些库，日常效率起飞。

---

## Ch08 · collections：Counter / defaultdict / deque / namedtuple
**预计**：0.5 天 ｜ **前置**：M1

**核心知识点**（对比 Java）：
- `Counter`：计数器，`collections.Counter("aabbb")`（Java 要手写 Map 循环）
- `defaultdict`：带默认值的 dict（告别 `KeyError`）
- `deque`：双端队列 O(1) popleft（对比 Java `ArrayDeque`）
- `namedtuple` / `typing.NamedTuple`：轻量不可变对象（对比 Java record）
- `ChainMap` `OrderedDict`（3.7+ dict 有序后用得少）

**实战案例**：用 `Counter` 统计日志中 IP 访问频率，找 Top10（运维场景预热）。

**作业设想**：`analyze_access_log(logs: list[str]) -> dict`，返回「状态码分布」「最频繁 IP」「请求路径 Top5」，全用 collections 实现。

---

## Ch09 · itertools + functools：函数式利器
**预计**：0.5 天 ｜ **前置**：Ch08

**核心知识点**：
- `itertools.chain` `groupby` `combinations` `permutations` `product` `islice`（对比 Java Stream 但更强大）
- `functools.reduce`（= Java stream `.reduce`）
- **`functools.lru_cache`**：自动记忆化（刷题神器）
- `functools.partial`：偏函数（= Java Currying 替代）

**实战案例**：用 `groupby` 按日期分组订单；用 `lru_cache` 优化递归斐波那契。

**作业设想**：实现「订单按月份分组统计」，要求用 `itertools.groupby` + `lru_cache` 缓存「商品详情查询」。测试验证缓存命中。

---

## Ch10 · 正则表达式与字符串处理
**预计**：0.5 天 ｜ **前置**：M1

**核心知识点**：
- `re` 模块：`match` / `search` / `findall` / `sub` / `split`（对比 Java `Pattern`/`Matcher`）
- 分组与命名分组 `(?P<name>...)`
- `re.compile` 预编译
- f-string 高级用法：对齐、精度、日期格式化
- `str` 方法链 vs 正则的选择

**实战案例**：从 nginx 日志行中用正则提取 method/path/status/IP。

**作业设想**：`parse_log_line(line: str) -> dict | None`，正则解析，非法行返回 None。测试覆盖多种日志格式 + 异常输入。

---

## Ch11 · 数据交换：json / csv / datetime
**预计**：0.5 天 ｜ **前置**：Ch02

**核心知识点**：
- `json`：`load`/`loads`/`dump`/`dumps`，处理 datetime（默认不支持，要 encoder）
- `csv`：读写 CSV
- **`datetime`**：`datetime` / `date` / `timedelta` / 时区 `timezone`（对比 Java `java.time`，注意时区坑）
- `pydantic` 预告：JSON ↔ 对象的现代方式（M3 重点）
- 序列化陷阱：自定义对象不能直接 `json.dumps`

**实战案例**：把商品列表 + 时间戳序列化成 json，再反序列化回 `@dataclass`。

**作业设想**：实现自定义 `JSONEncoder` 处理 `datetime` 和 `dataclass`；实现 `load_products_with_expiry(path)` 解析带过期时间的商品 json。

---

## Ch12 · 现代工具链：uv / logging / 项目结构
**预计**：0.5 天 ｜ **前置**：Ch01

**核心知识点**：
- **uv**：现代包管理（替代 pip+venv+pip-tools，Rust 写的超快）
- **logging**：`getLogger`、handler、formatter、配置文件（对比 Java logback/slf4j）
- 项目结构规范：`src` layout、`pyproject.toml`（替代 `pom.xml`）
- `__init__.py`、相对/绝对导入
- `.env` 环境变量管理（`python-dotenv`）

**实战案例**：把前面所有作业组织成一个标准 Python 项目，配 `pyproject.toml` + logging。

**作业设想**：给项目加 `pyproject.toml`，配置 logging 写入文件，跑通 `uv run pytest`。

---

# 模块三：Web 框架 FastAPI ⭐（Ch13–Ch22）

> 目标：用一周时间，从零搭一个**带数据库、认证、测试、异步**的完整 RESTful API 服务。
> **为什么选 FastAPI 而不是 Django/Flask**：① 类型注解原生支持（Java 老手友好）；② 异步原生；③ 自动生成 OpenAPI 文档；④ 2024+ 新项目首选；⑤ 性能接近 Node/Go。Flask/Django 会在 Ch22 简介对比。

---

## Ch13 · HTTP 客户端：requests / httpx 调用 API
**预计**：0.5 天 ｜ **前置**：M1

**学习目标**：先学会「调」API，再学「写」API。

**核心知识点**：
- `requests`：`get/post/put/delete`、params、json body、headers、timeout、session（对比 Java HttpClient/OkHttp）
- `httpx`：现代版，支持同步+异步（推荐）
- 状态码处理、异常处理、重试
- 流式响应、文件上传/下载

**实战案例**：调用一个 mock 的商品 API（用 `assets/mock_data/products.json` 起一个本地服务），聚合数据。

**作业设想**：实现 `fetch_and_aggregate(base_url, category)`，调用 mock API 拉取商品，按价格排序，处理超时和 404。测试用 mock server。

---

## Ch14 · FastAPI 入门：第一个 API + Pydantic 模型
**预计**：1 天 ｜ **前置**：Ch13

**学习目标**：理解 FastAPI 的核心理念——「类型注解驱动一切」。

**核心知识点**：
- 创建 app、定义路由、`@app.get/post`
- **Pydantic** `BaseModel`：请求/响应模型（= Java DTO + 自动校验，老手秒懂）
- 自动参数校验、自动 JSON 序列化、自动 OpenAPI 文档（`/docs`）
- 对比 Spring Boot `@RestController` + `@RequestBody`

**实战案例**：写一个 `GET /products` 返回 mock 商品列表，`POST /products` 创建商品（带校验）。

**作业设想**：实现一个「商品管理 API」：定义 `ProductCreate` / `Product` 模型（价格>0、名称非空、SKU 格式校验），实现增删改查。测试用 `TestClient`。

---

## Ch15 · 路由、路径/查询参数、请求体
**预计**：0.5 天 ｜ **前置**：Ch14

**核心知识点**：
- 路径参数 `/{id}`、查询参数 `?limit=10&category=book`
- 参数校验：`Query`、`Path`、`Field`
- 请求体嵌套模型
- `Form`、`File` 上传
- 路由分组 `APIRouter`（= Spring 的 `@RequestMapping` 前缀）

**实战案例**：商品列表 API 加上分页、筛选、排序参数。

**作业设想**：实现 `GET /products` 支持分页（page/size）、筛选（category/min_price/max_price）、排序（sort_by/order），全用类型注解 + 校验。

---

## Ch16 · 依赖注入系统
**预计**：1 天 ｜ **前置**：Ch15

**学习目标**：理解 FastAPI 的 DI（这是它最强大的设计之一，对比 Spring DI）。

**核心知识点**：
- `Depends()`：依赖注入（= Spring `@Autowired`）
- 函数依赖、类依赖、嵌套依赖
- `yield` 依赖（= 上下文管理器，如数据库 session）
- 全局依赖、路由级依赖
- 用 DI 实现认证、配置注入、DB session

**实战案例**：用 DI 注入「数据库 session」和「当前登录用户」。

**作业设想**：实现 `get_db_session()`（yield 依赖）+ `get_current_user()`（从 header 解析 token），注入到订单 API。

---

## Ch17 · 中间件、CORS、异常处理
**预计**：0.5 天 ｜ **前置**：Ch16

**核心知识点**：
- 中间件（= Java Servlet Filter / Spring Interceptor）
- CORS 配置
- 全局异常处理器 `@app.exception_handler`
- 自定义业务异常 → HTTP 响应映射
- 请求日志中间件、耗时统计

**实战案例**：加请求日志中间件 + 全局异常处理 + CORS。

**作业设想**：实现「业务异常 → 统一错误响应格式」，自定义 `NotFoundError`/`ValidationException`/`PermissionError`，全局处理。

---

## Ch18 · 异步编程：async / await + 异步数据库
**预计**：1 天 ｜ **前置**：Ch16 ｜ **重点**

**学习目标**：这是 Python 和 Java 最大差异之一（Java 21 虚拟线程才追上）。掌握协程。

**核心知识点**：
- `async def` / `await`、事件循环 `asyncio`
- 对比 Java：CompletionStage / Reactor / 虚拟线程
- 异步 IO：`httpx.AsyncClient`、异步数据库驱动
- `asyncio.gather` 并发、`asyncio.create_task`
- 同步 vs 异步的取舍（CPU 密集别用 async）
- **FastAPI 中混用同步/异步路由的正确姿势**

**实战案例**：把商品 API 改成异步，用 `httpx` 并发调用 3 个外部服务聚合数据。

**作业设想**：实现 `aggregate_product_info(product_id)`，并发调用「价格服务」「库存服务」「评论服务」3 个 mock 异步 API，3 秒内返回聚合结果。

---

## Ch19 · 数据库 ORM：SQLAlchemy
**预计**：1 天 ｜ **前置**：Ch16

**学习目标**：用 SQLAlchemy 2.0 操作数据库（对比 Mybatis/JPA/Hibernate）。

**核心知识点**：
- SQLAlchemy 2.0 Core + ORM（现代写法）
- 模型定义、关系（一对多/多对多）
- Session、查询、过滤、分页
- 异步 SQLAlchemy `AsyncSession`
- Alembic 数据库迁移（= Java Flyway/Liquibase）
- SQLite（开发）→ PostgreSQL（生产）

**实战案例**：商品 + 订单两张表，关联查询。

**作业设想**：建 `products`/`orders`/`users` 三表，实现带分页的复杂查询（用户订单含商品详情）。用 Alembic 写一个迁移。

---

## Ch20 · 测试 API：TestClient + pytest fixtures
**预计**：0.5 天 ｜ **前置**：Ch19

**学习目标**：给 API 写测试，养成 TDD 习惯（Java 老手不陌生）。

**核心知识点**：
- `TestClient`（基于 httpx）：不用起服务直接测
- pytest fixtures：依赖注入式测试准备（= JUnit `@BeforeEach` 升级版）
- 测试数据库（内存 SQLite，隔离）
- 覆盖率 `pytest-cov`
- 参数化测试 `@pytest.mark.parametrize`
- mock 外部依赖

**实战案例**：给前几章的 API 补全覆盖率 90%+ 的测试。

**作业设想**：用 fixture 准备测试数据，参数化测试商品 API 的各种边界（含权限、校验、分页）。

---

## Ch21 · 认证与授权：JWT + OAuth2
**预计**：1 天 ｜ **前置**：Ch16

**核心知识点**：
- JWT 原理、`python-jose` / `pyjwt`
- OAuth2 Password Flow（FastAPI 内置支持）
- 密码哈希 `passlib`（bcrypt）
- RBAC 角色权限
- 对比 Spring Security

**实战案例**：实现登录 → 发 JWT → 受保护接口验 token。

**作业设想**：完整实现「注册/登录/刷新 token/受保护资源」流程，测试覆盖 token 过期、篡改、权限不足。

---

## Ch22 · 部署：uvicorn / gunicorn / Docker + 框架对比
**预计**：0.5 天 ｜ **前置**：Ch20

**核心知识点**：
- ASGI：uvicorn（单进程异步）、gunicorn + uvicorn worker（生产多进程）
- Dockerfile 最佳实践（多阶段构建）
- 配置管理：环境变量、`pydantic-settings`
- **FastAPI vs Flask vs Django 对比**（你点的「最出名的框架」全覆盖）：
  - Flask：轻量经典，同步为主，生态老牌
  - Django：全家桶（admin/orm/auth 全自带），= Spring 全家桶
  - FastAPI：现代异步，类型驱动，新项目首选
- 何时选哪个

**作业设想**：把整个商品 API 项目 Docker 化，`docker-compose` 起 app + postgres，跑通端到端。

---

# 模块四：运维脚本（Ch23–Ch27）

> 目标：发挥 Python 作为「胶水语言 + 运维利器」的优势——这正是 Python 相对 Java 的舒适区。

---

## Ch23 · 文件系统批量操作
**预计**：0.5 天 ｜ **前置**：M2

**核心知识点**：
- `pathlib`：现代路径 API（比 `os.path` 优雅百倍）
- `shutil`：复制/移动/删除目录
- `glob` / `rglob`：文件匹配
- 递归遍历、批量重命名

**实战案例**：扫描 `mock_data/` 下所有 json，统计每个文件大小，归档超过阈值的。

**作业设想**：实现「日志归档脚本」：按日期分目录、压缩旧日志、清理 30 天前的。测试用临时目录。

---

## Ch24 · 进程与子进程管理
**预计**：0.5 天 ｜ **前置**：Ch23

**核心知识点**：
- `subprocess`：执行外部命令（对比 Java `ProcessBuilder`）
- `subprocess.run` / `Popen`、管道、超时、返回码
- `psutil`：进程/内存/CPU 监控（跨平台）
- 守护进程、信号处理

**实战案例**：写一个脚本监控某进程内存，超阈值告警。

**作业设想**：实现「服务健康检查脚本」：批量 ping 一组服务，记录响应时间，导出报告。

---

## Ch25 · CLI 工具开发：Typer + Rich
**预计**：1 天 ｜ **前置**：M2

**学习目标**：写漂亮的命令行工具（对比 Java Picocli）。

**核心知识点**：
- **Typer**：基于类型注解的 CLI（FastAPI 同作者，老手秒懂）
- **Rich**：终端美化（表格、进度条、颜色、markdown）
- 子命令、参数、选项、自动 `--help`
- `click` 对比（Typer 底层）

**实战案例**：写一个 `mytool process <file> --format json` 的 CLI。

**作业设想**：把 Ch08 的日志分析器改造成 CLI：`loganalyzer analyze access.log --top 10 --format table`，Rich 输出彩色表格。

---

## Ch26 · 定时任务与日志分析
**预计**：0.5 天 ｜ **前置**：Ch25

**核心知识点**：
- `schedule` 库：进程内定时
- 系统级：cron / systemd timer（部署视角）
- 大日志文件流式处理、正则提取、聚合
- 输出到文件/ES/邮件

**实战案例**：每小时分析 nginx access.log，找出错误率突增的 5 分钟窗口。

**作业设想**：实现「日志报警器」：解析日志、按分钟统计 5xx、超阈值生成报警 json。

---

## Ch27 · 配置管理与系统监控
**预计**：0.5 天 ｜ **前置**：Ch24

**核心知识点**：
- 配置：`pydantic-settings`（环境变量+json+优先级，对比 Spring `@ConfigurationProperties`）
- 系统信息：磁盘、CPU、网络（`psutil`/`shutil.disk_usage`）
- 推送告警：webhook（钉钉/飞书/Slack）

**实战案例**：写一个磁盘水位监控，超 80% 飞书告警。

**作业设想**：实现「系统巡检脚本」：检查磁盘/CPU/内存/关键端口，生成健康报告，异常时 webhook 告警。

---

# 模块五：AI 框架 ⭐（Ch28–Ch33）

> 目标：掌握调用 LLM、Prompt 工程、RAG、Agent 开发——当前最热的 Python 应用领域。
> 基于真实可用的 Claude / OpenAI API（具体看你有哪些 key）。

---

## Ch28 · LLM SDK 调用：OpenAI / Anthropic
**预计**：1 天 ｜ **前置**：M3

**核心知识点**：
- `anthropic` SDK / `openai` SDK：消息、流式、多轮对话
- API key 管理（`.env`，绝不硬编码）
- token 计费、上下文窗口、速率限制
- 对比直接 HTTP 调用 vs SDK

**实战案例**：写一个「商品描述生成器」，输入商品信息，调 LLM 生成营销文案。

**作业设想**：实现 `generate_product_description(product, tone)`，带错误重试、超时、token 统计。测试用 mock client。

---

## Ch29 · Prompt 工程与结构化输出
**预计**：0.5 天 ｜ **前置**：Ch28

**核心知识点**：
- Prompt 设计模式：few-shot、CoT、role prompting
- **结构化输出**：用 Pydantic 定义输出 schema，强制 LLM 返回 JSON（`response_format` / tool use）
- 对比手写正则解析 vs 结构化输出
- Prompt 模板管理（Jinja2）

**实战案例**：让 LLM 从「用户评论」中抽取 `{sentiment, pros, cons, score}`，强类型返回。

**作业设想**：实现 `analyze_review(text) -> ReviewAnalysis`（Pydantic 模型），测试解析准确率。

---

## Ch30 · LangChain 基础
**预计**：1 天 ｜ **前置**：Ch29

**核心知识点**：
- LangChain 核心抽象：LLM / ChatModel / Prompt / Chain / Output Parser
- LCEL（LangChain Expression Language）：`prompt | model | parser`
- Memory：对话记忆
- 对比 LangChain vs 直接用 SDK（何时用何时不用的工程判断）

**实战案例**：用 LangChain 重写 Ch28 的商品描述生成器，加对话记忆。

**作业设想**：实现「商品客服问答机器人」，基于商品 json 回答用户问题，带 3 轮记忆。

---

## Ch31 · RAG 实战：向量数据库 + 检索增强
**预计**：1 天 ｜ **前置**：Ch30 ｜ **重点**

**核心知识点**：
- RAG 原理：embedding → 向量库检索 → 拼接上下文 → LLM 回答
- Embedding 模型（OpenAI / 本地 `sentence-transformers`）
- **向量数据库**：Chroma（本地，推荐入门）/ pgvector / FAISS
- 文档切分策略、重排序
- 对比「微调 vs RAG」

**实战案例**：把 100 个商品描述建索引，实现「自然语言搜商品」。

**作业设想**：实现 `ProductSearchRAG`： ingest 商品 json → 用户提问 → 检索 top3 → LLM 总结回答。

---

## Ch32 · Agent 开发：Tool Use / Function Calling
**预计**：1 天 ｜ **前置**：Ch31 ｜ **前沿**

**核心知识点**：
- Tool use / function calling 原理：LLM 决定调哪个工具
- 定义工具 schema（Pydantic）
- ReAct 循环：思考 → 调工具 → 观察 → 再思考
- 对比「单轮调用 vs Agent 循环」
- Claude Code / 各类 Agent 框架简介

**实战案例**：实现「订单查询 Agent」：用户自然语言问「我上个月的订单」，Agent 自动调用查询工具。

**作业设想**：实现一个多工具 Agent：能查商品、查订单、查库存，根据用户问题自主决策。

---

## Ch33 · 用 FastAPI 封装 AI 服务
**预计**：0.5 天 ｜ **前置**：Ch18, Ch28

**学习目标**：把 AI 能力变成生产级 API（综合实战）。

**核心知识点**：
- LLM API 的特殊点：流式响应（SSE）、长耗时、限流
- SSE 流式返回（`StreamingResponse`）
- 异步并发调 LLM、队列削峰（Celery/ARQ 预告）
- 成本控制、缓存

**实战案例**：把 Ch31 的 RAG 包装成 `/chat` 流式 API。

**作业设想**：实现 `POST /api/chat`（SSE 流式），后端调 RAG，带并发限流和测试。

---

# 模块六：LeetCode 实战（Ch34–Ch40）

> 目标：用 **Pythonic** 方式刷题——很多题在 Python 里 3 行搞定，Java 要 15 行。
> 每章选 3–5 道高频题，给 Python 解法 + 测试，对比 Java 思路。

---

## Ch34 · Python 刷题利器总览
**预计**：0.5 天 ｜ **前置**：M1, M2

**核心知识点**（为什么 Python 刷题爽）：
- `Counter` / `defaultdict` 哈希表一行初始化
- `heapq`（最小堆）、`deque` 双端队列
- `bisect` 二分查找
- `sorted` + `key=lambda`、`itertools`
- 切片、解包、星号表达式
- `@lru_cache` 记忆化搜索一行搞定
- `float('inf')`、`math.inf`

**实战案例**：用 5 个经典技巧秒杀 5 道题。

**作业设想**：给定 5 道题，要求用 Pythonic 写法（禁止转成 Java 风格），测试通过。

---

## Ch35 · 双指针 / 滑动窗口
**作业设想**：LeetCode 3（无重复字符最长子串）、11（盛水容器）、76（最小覆盖子串）、15（三数之和）。

---

## Ch36 · 哈希表 / 前缀和
**作业设想**：LeetCode 1（两数之和）、49（字母异位词分组）、560（和为 K 的子数组）、128（最长连续序列）。

---

## Ch37 · 栈 / 队列 / 单调栈
**作业设想**：LeetCode 20（有效括号）、155（最小栈）、739（每日温度）、42（接雨水）。

---

## Ch38 · 二叉树 / DFS / BFS
**作业设想**：LeetCode 104（最大深度）、226（翻转）、98（验证 BST）、102（层序遍历）、236（最近公共祖先）。

---

## Ch39 · 动态规划
**作业设想**：LeetCode 70（爬楼梯）、322（零钱兑换）、300（最长递增子序列）、1143（最长公共子序列）、72（编辑距离）—— 用 `@lru_cache` 优雅实现。

---

## Ch40 · 回溯 / 贪心 + 综合
**作业设想**：LeetCode 46/47（全排列）、78（子集）、39（组合总和）、121（买卖股票）、55（跳跃游戏）。

---

# 📊 学习路径建议

## 推荐节奏（30 天）

```
第 1 周   ▶ M1 语言核心 (Ch01–07)        —— 打地基，对 Java 降维打击
第 2 周   ▶ M2 标准库 + M3 前半 (Ch08–17) —— 进 Web 框架
第 3 周   ▶ M3 后半 + M4 (Ch18–27)       —— 异步、DB、运维
第 4 周   ▶ M5 AI + M6 LeetCode (Ch28–40)—— 综合实战
```

## 给 Java 老手的「快速通道」标记

每章正文里我会用这些标记帮你跳读：
- 🟢 **Java 老手秒懂**：和 Java 几乎一样，扫一眼即可
- 🟡 **注意差异**：名字像但行为不同（如 `dict` 不是 `HashMap` 那么简单）
- 🔴 **Python 特有**：Java 完全没有的概念（如装饰器、生成器、with）—— **重点学**

## 如何开始

1. 告诉我「**我要学 Ch01**」（或任何章节）
2. 我生成该章五件套:`tutorial.md` 教程 + `ch{NN}_assignment.py` 作业 + 测试 + `review.md` 闪卡 + mock 数据
3. 你读教程、写作业、跑测试，全绿后进入下一章
4. 随时可以让我「**讲得更细**」「**加更多练习**」「**对比 Spring/Mybatis 的某用法**」

---

> 这份大纲是活文档，学习过程中你觉得哪块多/少、深/浅，随时告诉我调整。
> **现在，告诉我你想从哪一章开始？** 建议 **Ch01**（先把环境和工具链搭顺，后面才不卡）。
