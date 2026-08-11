# Ch06 · 异常、上下文管理器、文件 IO

> **预计**:0.5–1 天 ｜ **前置**:Ch05
> **目标**:掌握 Python 的异常体系和 **`with` 语句**(= Java try-with-resources 的优雅版)。学会用「上下文管理器」自动管理资源(文件、连接、事务),无论是否异常都能正确清理。
> 本章主线:你是电商平台的值班工程师,要写一个**日志批处理脚本**——读 nginx 访问日志(`assets/mock_data/nginx_logs.txt`,13 行样本,含 2 行脏数据)→ 逐行解析(坏行跳过)→ 聚合成统计报告 → 写出报告文件 → 记录每阶段耗时 → 最后把结果批量「入库」(模拟事务:全部成功才 commit,否则 rollback)。

> 📐 **本教程的契约**:下面每一节(§6.1–§6.7)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 写**自定义异常**(继承 `Exception`),理解 Python 异常体系 vs Java 的 checked/unchecked
- 用 `try/except/else/finally` 四段式,说清 `else` 为什么存在、何时执行
- 用 `raise ... from e` 串异常链(= Java `throw new XxxException(msg, cause)`)
- 用 **`pathlib.Path`** 做文件 IO:`read_text` / `write_text` / `open()`(比 `os.path` 优雅)
- 写**类版上下文管理器**(`__enter__`/`__exit__`)——计时器、事务都靠它
- 写**生成器版上下文管理器**(`@contextmanager`)——一次性资源的更简写法
- 说清 `__exit__` 返回 `True`/`False` 的区别(吞异常 vs 传播)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `LogParseError` | §6.1 | 自定义异常(继承 Exception) |
| `parse_log_line` | §6.2 | try/except + EAFP + 自定义异常 |
| `parse_log_file` | §6.3 | pathlib 读文件 + for-else 逐行解析 |
| `build_summary` | §6.4 | raise from + try/except/else |
| `write_report` | §6.5 | with open() 写文件 |
| `Timer` | §6.6 | 类版上下文管理器(__enter__/__exit__) |
| `db_transaction` | §6.7 | @contextmanager + commit/rollback |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch06_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「with 做了什么、__exit__ 何时调、yield 切三段」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 有 `checked exception`(强制 try/catch 或 throws)。Python 有吗?
2. Java 的 `try/catch/finally`,Python 四段式里多出来的那个关键字是什么?
3. Java `try (Resource r = ...) { }`(try-with-resources)自动关资源。Python 用什么关键字?
4. Java 让一个类支持 try-with-resources 要 `implements AutoCloseable`。Python 要实现哪两个方法?
5. Java 抛业务异常带原始原因:`throw new BizException("msg", e)`。Python 用什么语法保留异常链?

> 猜完,带着验证心态进入正文。第 2 题的 `else` 和第 3 题的 `with` 是本章的灵魂。

---

## §6.1 异常体系 + 自定义异常(对应:`LogParseError`)🟡

### Python vs Java 异常体系

```
Python:                          Java:
BaseException                    Throwable
  ├── Exception                    ├── Error(不管)
  │   ├── ValueError               └── Exception
  │   ├── KeyError                     ├── IOException(checked,强制处理)
  │   ├── FileNotFoundError            └── RuntimeException(unchecked)
  │   └── ...
  ├── KeyboardInterrupt(Ctrl+C)
  └── SystemExit(sys.exit)
```

> 🟡 **关键差异**:Python **没有 checked exception**——所有异常都非受检,不强制 try/catch、不用在签名上声明。Java 老手的惯性「方法签名写 throws」在 Python 不存在。哲学:**异常该抛就抛,调用方决定要不要处理**。

### 常见内置异常对照表

| Python | 触发场景 | Java 类比 |
|--------|---------|-----------|
| `ValueError` | 值不合法(`int("abc")`) | `IllegalArgumentException` |
| `KeyError` | 字典键不存在(`d["x"]`) | `Map.get` 返回 null(不抛!) |
| `TypeError` | 类型操作错(`"a" + 1`) | `ClassCastException` |
| `FileNotFoundError` | 文件不存在 | `FileNotFoundException`(checked) |
| `ZeroDivisionError` | 除以零 | `ArithmeticException` |
| `IndexError` | 列表越界 | `IndexOutOfBoundsException` |

### 自定义异常:继承 `Exception` 就行

**真实场景**:日志解析器遇到格式不合法的行,不能返回 `null`(Java 习惯),要抛一个语义明确的 `LogParseError`,让上层决定「跳过」还是「中止」。

```python
class LogParseError(Exception):
    """日志行解析失败。"""     # 一行继承 + docstring,不需要写构造器
    pass

# 抛出去(message 直接传给 Exception 的 __init__)
raise LogParseError("无法解析: this line is malformed")
```

> 🟡 **Java 对比**:`class LogParseException extends Exception {}`。Python 连构造器都不用写——`Exception` 自带 `__init__(self, *args)`,`str(e)` 就能拿到 message。

❌ **错误写法**(Java 思维):

```python
class LogParseError(Exception):
    def __init__(self, message):        # 没必要!Exception 自带
        super().__init__(message)
        self.message = message
```

✅ **正确写法**:`class LogParseError(Exception): pass`(或只写 docstring)。

> ✅ 做 `LogParseError` 题:`class LogParseError(Exception):` + docstring,body 不需要任何代码(`pass` 或仅 docstring 均可)。

---

## §6.2 try/except + EAFP(对应:`parse_log_line`)🔴

### 四段式语法

```python
try:
    result = risky_operation()       # ① 可能出错的代码
except SpecificError as e:           # ② 捕获特定异常(= Java catch)
    handle(e)
else:
    use(result)                      # ③ try【没抛异常】才执行
finally:
    cleanup()                        # ④ 无论如何都执行(清理资源)
```

### 各段含义

| 段 | 何时执行 | 用途 |
|----|---------|------|
| `try` | 总是 | 放可能出错的代码 |
| `except XxxError` | try 抛了 XxxError | 处理异常(可写多个 except) |
| `else` | try **没抛**任何异常 | 放「成功后才做」的事 |
| `finally` | **无论如何**(异常/正常/return/break) | 清理资源(关文件、释放锁) |

> 🤯 **`else` 是 Java 没有的**。意义:把「成功后的逻辑」挪出 try 块,避免 try 块太大误捕自己代码的异常。

### EAFP vs LBYL:Python 的核心哲学 🔴

这是 Python 和 Java 思维的**根本差异**:

- **LBYL**(Look Before You Leap,Java 习惯):先检查再操作。
- **EAFP**(Easier to Ask Forgiveness than Permission,Python 习惯):直接操作,出错了再捕获。

**真实场景**:解析一行 nginx 日志,提取「请求路径」和「状态码」。

❌ **LBYL 写法**(Java 思维,啰嗦且容易漏判):

```python
def parse_log_line(line: str) -> dict:
    parts = line.split('"')
    if len(parts) >= 2:                    # 先检查有没有引号段
        request = parts[1].split()
        if len(request) >= 2:              # 再检查请求段能不能拆出 METHOD PATH
            tail = line.rsplit('"', 1)[-1].split()
            if len(tail) >= 2 and tail[0].isdigit():   # 再检查状态码是数字
                return {"path": request[1], "status": int(tail[0])}
    raise LogParseError(f"无法解析: {line}")
```

问题:检查项和真实解析逻辑脱节,日志格式一变就要改两处;`tail[0].isdigit()` 排除了负数等合法输入。

✅ **EAFP 写法**(Python 风格,直接解析、出错就抛):

```python
def parse_log_line(line: str) -> dict:
    try:
        request = line.split('"')[1]        # "GET /api/products HTTP/1.1"
        path = request.split()[1]           # "/api/products"
        status = int(line.rsplit('"', 1)[-1].split()[0])   # 200
    except (IndexError, ValueError) as e:
        raise LogParseError(f"无法解析: {line}") from e
    return {"path": path, "status": status}
```

好处:解析逻辑只有一份,任何一步失败(没引号→`IndexError`;状态码不是数字→`ValueError`)统一转成业务异常。**代码表达的是「我想做什么」,而不是「我怕什么」**。

### 捕获多个异常 + 顺序

```python
try:
    ...
except (KeyError, IndexError) as e:     # 多种异常一起捕,绑定到 e
    print(type(e).__name__, e)
except Exception:                        # 兜底,放最后
    print("未知错误")
```

> ⚠️ **顺序铁律**:从具体到一般。`except Exception` 放最前,后面的具体异常永远捕不到(Java 编译器会拦 unreachable catch,Python 不拦!)。

❌ **永远别裸 `except:`**:

```python
try:
    do_something()
except:                  # ❌ 连 KeyboardInterrupt / SystemExit 都捕了
    pass
```

✅ 至少要 `except Exception:`(不捕 `BaseException`,保留 Ctrl+C 退出的能力)。

> ✅ 做 `parse_log_line` 题:EAFP 三段解析(引号段→path→status),`except (IndexError, ValueError)` 转成 `raise LogParseError(...) from e`。

---

## §6.3 pathlib 读文件 + for-else 逐行解析(对应:`parse_log_file`)🟡

### `pathlib.Path`:现代文件 API

`pathlib` 是面向对象的路径/文件库,**取代老式 `os.path`**。

```python
from pathlib import Path

p = Path("assets") / "mock_data" / "nginx_logs.txt"   # / 运算符拼路径!
p.exists()                          # True/False
p.read_text(encoding="utf-8")       # 一行读完整个文件(自动关闭)
p.write_text("hello", encoding="utf-8")   # 一行写入(覆盖)
p.parent      # 父目录 Path
p.name        # 文件名 "nginx_logs.txt"
p.suffix      # 后缀 ".txt"
list(Path(".").glob("*.json"))      # 匹配文件
```

> 🟡 **Java 对比**:`Path.of(...)` + `Files.readString(p)`。Python 的 `Path("a") / "b"` 用运算符重载拼路径,比 Java 的 `p.resolve("b")` 直观。

### 读文本文件的两种姿势

**一次性读全**(小文件,简单):

```python
text = Path("nginx_logs.txt").read_text(encoding="utf-8")
lines = text.splitlines()           # 按行拆成 list[str]
```

**逐行迭代**(大文件,省内存——GB 级日志必须这么读):

```python
with Path("nginx_logs.txt").open(encoding="utf-8") as f:
    for line in f:                  # f 是迭代器,一次一行,不加载整个文件
        process(line.rstrip("\n"))
```

> 🔴 **`for line in f` 是惰性迭代**,内存只占一行的空间。Java 的 `Files.readAllLines` 会把 10GB 全读进内存 OOM;Python 的 `read_text` 同理,**大文件必须用 `with open() + for`**。

### 组合:读文件 + 逐行解析 + 跳过坏行

**真实场景**:日志批处理——读取文件,用上一节的 `parse_log_line` 逐行解析,坏行记一笔然后跳过,不能让 1 行脏数据搞挂整个批处理。

```python
def parse_log_file(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    entries, skipped = [], []
    for i, line in enumerate(lines, 1):          # enumerate 拿行号(从 1 开始)
        try:
            entries.append(parse_log_line(line))
        except LogParseError:
            skipped.append(i)                    # 坏行行号记下来,最后告警用
    return entries, skipped
```

> 🟡 **「坏行跳过」是批处理经典模式**:不能因为第 4 行是脏数据,后面 9 行好数据都不处理。逐行 `try/except` 把失败隔离在单行内。

❌ **错误写法**(把整个 for 包在一个 try 里):

```python
try:
    for line in lines:
        entries.append(parse_log_line(line))
except LogParseError:
    pass                        # ❌ 第 4 行一坏,后面 9 行全丢了
```

✅ **正确写法**:`try` 放在 `for` **里面**,粒度是单行。

> ✅ 做 `parse_log_file` 题:`Path(path).read_text().splitlines()` → `for i, line in enumerate(lines, 1)` → 单行 `try/except LogParseError` → 返回 `(entries, skipped)`。

---

## §6.4 raise from + try/except/else(对应:`build_summary`)🟡

### `raise ... from e`:保留异常链

**真实场景**:解析完日志条目,要按「状态码段位」(2xx/3xx/4xx/5xx)聚合。如果某条 entry 缺 `status` 字段(上游 bug),你要抛一个业务异常 `LogParseError`,但**必须保留原始的 `KeyError`**,否则排查时根本不知道是哪条 entry、哪个字段出问题。

```python
try:
    bucket = f"{entry['status'] // 100}xx"
except KeyError as e:
    raise LogParseError(f"entry 缺 status 字段: {entry}") from e
    #                                                     ↑ from e 把原始异常挂到 __cause__
```

= Java 的 `throw new BizException("msg", e)`。打印堆栈时能看到完整链条:

```
KeyError: 'status'

The above exception was the direct cause of the following exception:
LogParseError: entry 缺 status 字段: {'path': '/api/products'}
```

❌ **错误写法**(丢失原因):

```python
except KeyError:
    raise LogParseError(f"entry 缺 status: {entry}")     # ❌ 没 from e,__cause__ 丢了
```

✅ **正确写法**:`raise LogParseError(...) from e`。

### `else` 段的实战:聚合统计

`else` 在 try **没抛异常**时执行。聚合场景里,把「可能失败的字段提取」放 try,「成功后的累加」放 else,意图更清晰:

```python
def build_summary(entries):
    total, by_status = 0, {}
    for e in entries:
        try:
            bucket = f"{e['status'] // 100}xx"
        except KeyError as ex:
            raise LogParseError(f"entry 缺 status 字段: {e}") from ex
        else:
            total += 1                        # 只有 status 提取成功才走到这
            by_status[bucket] = by_status.get(bucket, 0) + 1
    return {"total": total, "by_status": by_status}
```

> 🟡 **`dict.get(key, 0)` 是聚合套路**:key 不存在返回默认值 0,等价 Java `map.getOrDefault(key, 0)`。

> ✅ 做 `build_summary` 题:遍历 entries,`try` 提取 `status` 算 bucket、`except KeyError` → `raise LogParseError from e`、`else` 累加 `total` 和 `by_status`。

---

## §6.5 with open() 写文件(对应:`write_report`)🔴

### 为什么必须用 `with`?

**问题**:文件/连接/锁用完必须关,手动关容易忘(尤其异常时)。

❌ **手动关的坑**(异常时漏关):

```python
f = open("report.txt", "w", encoding="utf-8")
f.write(report)              # 如果这行抛异常(磁盘满/编码错)...
f.close()                    # ...这行就执行不到,f 泄漏!
```

✅ **`with` 自动关**(无论是否异常):

```python
with open("report.txt", "w", encoding="utf-8") as f:
    f.write(report)
# 出了 with 块,f 自动关闭(哪怕 write 抛了异常)
```

> 🟡 **Java 对比**:`with` = `try (Resource r = ...) { }`(try-with-resources)。`open()` 返回的文件对象实现了「上下文管理器协议」,with 块结束自动调清理。

### 写文本文件的完整姿势

**真实场景**:把统计结果写成人类可读的报告文件。

```python
from pathlib import Path

def write_report(summary: dict, path) -> None:
    lines = [f"total: {summary['total']}"]
    for bucket, count in summary["by_status"].items():
        lines.append(f"{bucket}: {count}")
    report = "\n".join(lines) + "\n"          # 末尾补换行,符合 POSIX 习惯

    p = Path(path)
    with p.open("w", encoding="utf-8") as f:   # "w" = 覆盖写;"a" = 追加
        f.write(report)
    # f 已自动关闭
```

**三个细节**:

1. **`encoding="utf-8"` 必须显式写**:Windows 默认 GBK,不写会在中文环境乱码。
2. **`"w"` 模式会清空原文件**:想追加用 `"a"`。
3. **`Path.open()` vs 内置 `open()`**:完全等价,`p.open(...)` 更面向对象。

> 🟡 **简便写法**:小文件也可以 `p.write_text(report, encoding="utf-8")` 一行搞定(内部就是 `with open`)。作业里用 `with` 是为了练协议,实战中两者都可以。

> ✅ 做 `write_report` 题:拼报告字符串 → `Path(path)` → `with p.open("w", encoding="utf-8") as f:` → `f.write(report)`。

---

## §6.6 类版上下文管理器(对应:`Timer`)🔴

### `with` 背后的协议:`__enter__` / `__exit__`

上一节你用 `with open(...)` 享受了自动关闭。这一节自己造一个——**任何类只要实现 `__enter__` 和 `__exit__` 两个方法,就能被 `with` 使用**(= Java `implements AutoCloseable`)。

**真实场景**:批处理脚本要统计「读文件花了多久、解析花了多久、写报告花了多久」,打点到监控系统。造一个 `Timer` 上下文管理器。

```python
import time

class Timer:
    def __enter__(self):
        # 进入 with 块时调用(= 获取资源)。返回值赋给 as 后面的变量
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 退出 with 块时调用(= 释放资源),无论是否异常
        # 三个参数:异常类型 / 异常值 / traceback;没异常时都是 None
        self.elapsed = time.time() - self.start
        return False        # False=不吞异常, True=吞掉(慎用)
```

**用法**:

```python
with Timer() as t:          # ① __enter__ 被调,返回值(self)赋给 t
    data = parse_log_file("nginx_logs.txt")     # ② with 块干活
# ③ __exit__ 被调(哪怕 parse_log_file 抛异常也会调),算出 t.elapsed
print(f"解析耗时: {t.elapsed:.3f}s")
```

### 执行时序图

```
with Timer() as t:        ──►  t.__enter__()   → return self 绑定给 t
    <body>                ──►  执行 with 块
    (正常结束 or 抛异常)   ──►  t.__exit__(exc_type, exc_val, exc_tb)
                                 ├─ 无异常:三个参数都是 None
                                 ├─ 有异常:参数是异常信息
                                 └─ return False → 异常继续抛
                                    return True  → 异常被吞掉!
```

**记住三条**:

- `__enter__` 进入时调,`return` 的值 = `as` 拿到的对象。
- `__exit__` 退出时调(**异常也调**),负责清理。
- `__exit__` 返回 `False` = 不吞异常(**99% 情况**);返回 `True` = 「我处理了,别向上抛」。

❌ **错误写法**(吞异常不自知):

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    self.elapsed = time.time() - self.start
    return True             # ❌ with 块里的异常被悄悄吞了,排查时怀疑人生
```

✅ **正确写法**:`return False`(或不 return,默认 None 也是 False 语义)。

> 🟡 **Java 对比**:Java 只有一个 `close()`;Python 分「进入 + 退出」两步,`__enter__` 可以返回值(比如打开的连接对象),更灵活。

> ✅ 做 `Timer` 题:`__enter__` 记 `self.start = time.time()` 并 `return self`;`__exit__` 算 `self.elapsed = time.time() - self.start` 并 `return False`。

---

## §6.7 @contextmanager 生成器版(对应:`db_transaction`)🔴

类版要写两个方法+一个类,一次性场景有点啰嗦。Python 提供**生成器 + `@contextmanager` 装饰器**,一个函数就能造上下文管理器(Ch03 生成器 + Ch04 装饰器的合体)。

### 套路:yield 把函数切成三段

```python
from contextlib import contextmanager

@contextmanager
def db_transaction(db: dict):
    # 【yield 之前】= __enter__:进入 with 时执行
    db["pending"] = []
    try:
        yield db                       # yield 的值 = as 拿到的对象;这里暂停,执行 with 块
        # 【yield 之后(没异常)】= __exit__ 的「成功路径」
        db["committed"].extend(db["pending"])
    except Exception:
        # 【yield 处复苏抛异常】= __exit__ 的「异常路径」
        db["rolled_back"] = True
        raise                          # 重新抛,让调用方知道失败了
    finally:
        # 【无论如何】= __exit__ 的「清理」
        db["pending"] = []
```

### 三段对照表

| 位置 | 等价于 | 何时执行 |
|------|--------|---------|
| `yield` 之前 | `__enter__` | 进入 with 块 |
| `yield` 的值 | `__enter__` 的返回值 | `as` 拿到的对象 |
| `yield` 之后(正常) | `__exit__` 无异常分支 | with 块正常结束 |
| `except`(在 yield 处复苏) | `__exit__` 异常分支 | with 块抛异常 |
| `finally` | `__exit__` 的清理 | **无论如何** |

> 🤯 **with 块抛异常时发生了什么**:异常被「注入」到生成器的 `yield` 处,生成器在 `yield` 那一行抛同一个异常。所以 `try/except/finally` 必须包住 `yield`,才能分别处理「成功 commit」「失败 rollback」「清理」。

### 真实场景:模拟数据库事务

批处理最后一步:把解析出的 11 条日志统计「入库」。事务语义:**全部成功才 commit,任何一条失败整个 rollback**,不能留半截数据。

```python
db = {"committed": [], "pending": [], "rolled_back": False}

# 成功路径
with db_transaction(db) as tx:
    tx["pending"].append({"total": 11})
    tx["pending"].append({"by_status": {"2xx": 6}})
# with 块没异常 → commit:committed 里有 2 条,pending 清空

# 失败路径
with db_transaction(db) as tx:
    tx["pending"].append({"total": 11})
    raise RuntimeError("DB 连接断开")     # 模拟中途挂了
# with 块抛异常 → rollback:rolled_back=True,pending 清空,committed 不变
```

> 🟡 **Java 对比**:Java 要 `Connection conn = ...; try { ...; conn.commit(); } catch { conn.rollback(); } finally { conn.close(); }`,或者靠 Spring `@Transactional` AOP。Python 一个 10 行生成器函数就封装了同样的语义,且能 `with` 复用到任何地方。

### 类版 vs 生成器版,怎么选?

- **类版**:状态复杂、要多个方法、同一对象反复进 with → 写类(如数据库连接池)。
- **生成器版**:一次性、逻辑就是「进入做 A / 退出做 B」 → 写函数(计时、事务、临时改配置)。**实战中生成器版更常用**。

> ✅ 做 `db_transaction` 题:加 `@contextmanager` 装饰器(从 `contextlib` 导入);`yield` 前初始化 `pending`,`yield db`;正常结束 `committed.extend(pending)`;`except Exception` 设 `rolled_back=True` 并 `raise`;`finally` 清空 `pending`。

---

## §6.8 Java 老手常踩的坑 ⚠️

1. **没有 checked exception**:别指望编译器提醒你 try/catch,重要调用自己想清楚异常路径。
2. **except 顺序**:从具体到一般,`except Exception` 永远放最后(Python 不拦 unreachable catch)。
3. **别裸 `except:`**:会捕 `KeyboardInterrupt`/`SystemExit`,用 `except Exception:`。
4. **`__exit__` 返回 `True` 吞异常**:99% 情况返回 `False`/不 return。吞异常要非常确定自己在干嘛。
5. **生成器版忘包 try/finally**:with 块抛异常时清理代码会漏执行。
6. **读大文件用 `read_text`**:GB 级日志直接 OOM,用 `with open() + for line in f` 逐行。
7. **`open()` 不写 `encoding="utf-8"`**:Windows 默认 GBK,中文环境乱码。
8. **字符串拼路径**:`path + "/" + file` 是 Java 思维,用 `Path("a") / "b"`。

---

## 📝 本章作业

打开 **`ch06_assignment.py`**,7 个任务,一条主线串起来:读日志 → 解析 → 聚合 → 写报告 → 计时 → 入库。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `LogParseError` | 自定义异常 | 🟢 |
| `parse_log_line` | try/except + EAFP | 🟡 |
| `parse_log_file` | pathlib 读 + 单行容错 | 🟡 |
| `build_summary` | raise from + else | 🟡 |
| `write_report` | with open() 写文件 | 🟡 |
| `Timer` | 类版上下文管理器 | 🔴 |
| `db_transaction` | @contextmanager 事务 | 🔴 |

```bash
uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v
```

全绿 = 掌握 Ch06。`with` 相关卡了 → 回 §6.5/§6.6/§6.7。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「with 语句做了什么?`__enter__`/`__exit__` 何时被调?」(§6.5/§6.6)
- [ ] 能解释 try/except/else/finally 各段何时执行,`else` 为什么存在(§6.2/§6.4)
- [ ] 知道 `raise ... from e` 的作用,不用它会丢什么(§6.4)
- [ ] 能说清 EAFP vs LBYL 的区别,为什么 Python 推荐 EAFP(§6.2)
- [ ] 能说清 `@contextmanager` 版「yield 切三段」的套路,`except` 在何时触发(§6.7)
- [ ] 7 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「with 语句到底做了什么?它和 Java try-with-resources 怎么对应?`__exit__` 返回 True 会怎样?」— 卡壳重读 §6.5/§6.6
2. 「@contextmanager 版为什么用 yield?yield 前后各对应什么?with 块抛异常时生成器里发生什么?」— 卡壳重读 §6.7
3. 「try/except/else/finally 的 else 何时执行?为什么 Python 有而 Java 没有?」— 卡壳重读 §6.2/§6.4

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch06 掌握后,进 **Ch07 · 类型注解与 Pythonic 风格**——M1 最后一章。给 Python 加上「准静态类型」(mypy),让你从 Java 过来更舒服;并学会最地道的 Python 写法(EAFP 已在本章抢先体验、Protocol、The Zen of Python)。
