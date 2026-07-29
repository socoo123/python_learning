# Ch06 · 异常、上下文管理器、文件 IO

> **预计**:0.5–1 天 ｜ **前置**:Ch05
> **目标**:掌握 Python 的异常体系和 **`with` 语句**(= Java try-with-resources 的优雅版)。学会用「上下文管理器」自动管理资源(文件、连接、锁),无论是否异常都能正确清理。

> 📐 **本教程的契约**:下面每一节(§6.1–§6.5)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按任务名回查对应小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 理解 Python 异常体系,写**自定义异常**(= Java 自定义 exception)
- 用 `try/except/else/finally` 四段式(比 Java 多一个 `else`)
- 用 `raise ... from e` 串接异常链(= Java exception cause)
- 用 **`pathlib`** 做文件 IO(比 `os.path` 优雅得多)
- 写**上下文管理器**:类版(`__enter__`/`__exit__`)+ 生成器版(`@contextmanager`)

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `DataLoadError` | §6.1 | 自定义异常(继承 Exception) |
| `safe_divide` | §6.2 | try/except/else |
| `read_config` | §6.3 | pathlib + raise from |
| `Timer` | §6.4 | 类版上下文管理器(__enter__/__exit__) |
| `managed_resource` | §6.5 | @contextmanager 生成器版 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 先猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch06_assignment.py`,先试着写 | assignment |
| ③ 提取+反馈 | 写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 讲清"with 到底做了什么、__exit__ 何时被调" | 本页 ④ |
| ⑤ 存闪卡 | 标 [`review.md`](./review.md) 复习日期 | review.md |

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java 有 `checked exception`(强制 try/catch 或 throws)。Python 有吗?
2. Java 的 `try/catch/finally`,Python 对应的四个关键字里,哪个是 Java 没有的?
3. Java `try (Resource r = ...) { }`(try-with-resources)自动关闭资源。Python 用什么关键字?
4. Java 让一个类支持 try-with-resources 要 `implements AutoCloseable`。Python 要实现哪两个方法?
5. Java 读文件 `Files.readString(path)`。Python 现代的、面向对象的路径 API 叫什么?

> 猜完,带着验证心态进入正文。

---

## §6.1 异常体系 + 自定义异常(对应:`DataLoadError`)🟡

### 异常体系对比

```
Python:                       Java:
BaseException                 Throwable
  ├── Exception                 ├── Exception(checked + unchecked)
  │   ├── ValueError            │   ├── IOException(checked)
  │   ├── KeyError              │   └── RuntimeException(unchecked)
  │   ├── FileNotFoundError
  │   └── ...
  ├── KeyboardInterrupt
  └── SystemExit
```

> 🟡 **关键差异**:Python **没有 checked exception**——所有异常都是非受检的,不强制你 try/catch 或声明。Java 老手会觉得"少了约束",但也少了样板代码。Python 的哲学:异常该抛就抛,调用方决定要不要处理。

### 常见内置异常

| Python | 触发场景 | Java 类比 |
|--------|---------|-----------|
| `ValueError` | 值不合法(`int("abc")`) | `IllegalArgumentException` |
| `KeyError` | 字典键不存在 | (Map.get 返回 null,不抛) |
| `TypeError` | 类型操作错(`"a"+1`) | `ClassCastException` |
| `FileNotFoundError` | 文件不存在 | `FileNotFoundException` |
| `ZeroDivisionError` | 除以零 | `ArithmeticException` |
| `IndexError` | 列表越界 | `IndexOutOfBoundsException` |

### 自定义异常:继承 `Exception`

```python
class DataLoadError(Exception):
    """数据加载失败。"""      # 就这么简单,继承 Exception 即可
    pass

raise DataLoadError("配置文件不存在")     # 直接 raise
```

> 🟡 **Java 对比**:`class DataLoadError extends Exception {}`。Python 不需要写构造器——`Exception` 自带 `__init__(self, *args)`,message 直接传。一行继承就够。

> ✅ 做 `DataLoadError` 题:让类继承 `Exception`(`class DataLoadError(Exception):`)。body 用 `pass` 或只写 docstring。

---

## §6.2 try/except/else/finally(对应:`safe_divide`)🟡

四段式(比 Java 多一个 `else`):

```python
try:
    result = a / b              # ① 可能出错的代码
except ZeroDivisionError:       # ② 捕获特定异常(= Java catch)
    return None
else:
    return result               # ③ try 没抛异常【才】执行
finally:
    print("无论如何都执行")      # ④ 总是执行(清理用)
```

### 各段含义

| 段 | 何时执行 | 用途 |
|----|---------|------|
| `try` | 总是 | 放可能出错的代码 |
| `except XxxError` | try 抛了 XxxError | 处理异常(可写多个 except) |
| `else` | try **没抛**任何异常 | 放"成功后才做"的事(和 for-else 一样,是个"nobreak"语义) |
| `finally` | **无论如何**(异常/正常/return/break) | 清理资源(关文件、释放锁) |

> 🤯 **`else` 是 Java 没有的**。它存在的意义:把"成功后的逻辑"挪出 try 块,避免误捕自己代码的异常。本节作业 `safe_divide` 就用它:除法放 try,成功 return 放 else。

### 捕获多个异常

```python
try:
    ...
except (KeyError, IndexError) as e:    # 同时捕获多种,绑到变量 e
    print(type(e).__name__, e)
except Exception:                        # 兜底(放最后)
    print("未知错误")
```

> ⚠️ **永远从具体到一般**:先 `except FileNotFoundError`,再 `except Exception`。反过来写,具体那个永远捕不到(Java 老手懂的——unreachable catch)。

### 重新抛出 + 异常链:`raise ... from e`

```python
try:
    text = Path(path).read_text()
except FileNotFoundError as e:
    raise DataLoadError(f"配置不存在: {path}") from e
    #                                       ↑ from e 把原始异常挂到 __cause__,保留全链路
```

= Java 的 `throw new XxxException("...", e)`(把原异常当 cause)。调试时能看到完整调用链。

> ✅ 做 `safe_divide` 题:见上面四段式(else 返回 result)。

---

## §6.3 pathlib 文件 IO(对应:`read_config`)🟡

`pathlib` 是 Python 现代的路径/文件 API,**面向对象**,比老式的 `os.path` 优雅得多。

```python
from pathlib import Path

p = Path("assets") / "mock_data" / "products.json"   # / 运算符拼接路径!(运算符重载)
p = Path("products.json")

p.exists()              # True/False
p.read_text(encoding="utf-8")      # 一行读完文件(自动关闭)
p.write_text("hello")              # 一行写入
p.read_bytes()                     # 读字节
p.parent / p.name / p.suffix       # 父目录 / 文件名 / 后缀
list(Path(".").glob("*.json"))     # 匹配文件
```

> 🟡 **Java 对比**:`Path` + `Files.readString(p)` 几乎一一对应。Python 的 `Path / "x"` 用运算符重载拼路径,比 Java 的 `p.resolve("x")` 直观。

### 读 JSON 文件的完整模式

```python
import json
from pathlib import Path

def read_config(path):
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise DataLoadError(f"配置不存在: {path}") from e
    return json.loads(text)        # json.loads 把字符串解析成 Python 对象
```

> ✅ 做 `read_config` 题:见上。关键是 `Path(path).read_text()` + `except FileNotFoundError` + `raise ... from e` + `json.loads`。

---

## §6.4 with 语句 + 类版上下文管理器(对应:`Timer`)🔴

这是本章核心。**问题**:文件/连接/锁用完必须关闭,但手动关容易忘(尤其异常时)。Java 用 try-with-resources 解决,Python 用 `with`。

### `with` 的效果

```python
# 手动关:异常时容易漏关
f = open("x.txt")
try:
    data = f.read()
finally:
    f.close()

# with:自动关(无论是否异常)
with open("x.txt") as f:
    data = f.read()
# 出了 with 块,f 自动关闭
```

> 🟡 **Java 对比**:`with` = `try (Resource r = ...) { }`(try-with-resources)。`open()` 返回的文件对象实现了「上下文管理器协议」,with 会自动在块结束时清理。

### 怎么让自己的类支持 `with`?实现两个方法

```python
class Timer:
    def __enter__(self):
        # 进入 with 块时调用(= 获取资源)。返回值赋给 as 后面的变量
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 退出 with 块时调用(= 释放资源),无论是否异常
        # 三个参数:异常类型/异常值/traceback(没异常时都是 None)
        self.elapsed = time.time() - self.start
        return False        # 返回 True=吞掉异常, False/None=让异常继续抛

# 用法
with Timer() as t:       # __enter__ 被调,返回值赋给 t
    ...do something...
# __exit__ 被调,t.elapsed 现在可用
print(t.elapsed)
```

**记住**:
- `__enter__` 进入时调,`return` 的值 = `as` 拿到的对象。
- `__exit__` 退出时调(异常也调),负责清理。
- `__exit__` 返回 `False` = 不吞异常(99% 情况)。

> 🟡 **Java 对比**:= `implements AutoCloseable`,实现 `close()`。但 Python 的 `__enter__`/`__exit__` 分两步(进入+退出),Java 只有一个 `close()`。Python 更灵活。

> ✅ 做 `Timer` 题:`__enter__` 记 `self.start=time.time()` 返回 self;`__exit__` 算 `self.elapsed` 返回 False。

---

## §6.5 @contextmanager 生成器版(对应:`managed_resource`)🔴

类版要写两个方法,有点啰嗦。Python 提供了更简洁的方式:用**生成器 + `@contextmanager`** 装饰器写上下文管理器(Ch04 装饰器 + Ch03 生成器的合体)。

### 套路:yield 把函数切成三段

```python
from contextlib import contextmanager

@contextmanager
def managed_resource(state, name):
    # 【yield 之前】= __enter__:进入 with 时执行
    state["active"] = name
    try:
        yield state        # yield 的值 = as 拿到的对象;这里暂停,执行 with 块
        # 【yield 之后】= __exit__:with 块结束后执行
    finally:
        state["active"] = None    # 放 finally,保证异常也清理

# 用法(和类版完全一样)
with managed_resource(state, "db") as s:
    assert s["active"] == "db"
assert state["active"] is None
```

### 三段对照

| 位置 | 等价于 | 何时执行 |
|------|--------|---------|
| `yield` 之前 | `__enter__` | 进入 with 块 |
| `yield` 的值 | `__enter__` 的返回值 | as 拿到的对象 |
| `yield` 之后(放 finally) | `__exit__` | 退出 with 块(异常也执行) |

> 🤯 **为什么要包 try/finally**:with 块里抛异常时,生成器会在 `yield` 处复苏并抛异常。用 `try/finally` 保证清理代码一定执行(否则异常时 yield 之后的代码可能漏跑)。这是生成器版的关键套路。

> 🟡 **Java 对比**:Java 没有等价物——要 try-with-resources 必须 `implements AutoCloseable`。Python 用一个生成器函数就能搞定,这正是「装饰器 + 生成器」组合的威力。

### 什么时候用哪个?

- **类版**:状态复杂、需要多个方法、复用同一个对象 → 写类。
- **生成器版**:一次性、简单(开关、计时、临时状态)→ 写函数。实战中生成器版更常用。

> ✅ 做 `managed_resource` 题:加 `@contextmanager` 装饰器(从 contextlib 导入),按上面三段套路写。

---

## §6.6 Java 老手常踩的坑 ⚠️

1. **没有 checked exception**:别指望编译器提醒你 try/catch。重要的调用自己想清楚异常路径。
2. **except 顺序**:从具体到一般,`except Exception` 永远放最后。
3. **别裸 `except:`**:`except:`(不带类型)会捕一切(含 `KeyboardInterrupt`),几乎总是错的。用 `except Exception:`。
4. **`__exit__` 返回 True 会吞异常**:99% 情况返回 False/None。返回 True 是"我处理了,别向上抛",慎用。
5. **生成器版忘加 try/finally**:with 块抛异常时清理代码会漏执行。
6. **`pathlib` 比 `os.path` 好**:新代码用 `Path`,字符串拼路径(`path + "/" + file`)是 Java 思维,用 `Path("a") / "b"`。

---

## 📝 本章作业

打开 **`ch06_assignment.py`**,5 个任务。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `DataLoadError` | 自定义异常 | 🟢 |
| `safe_divide` | try/except/else | 🟢 |
| `read_config` | pathlib + raise from | 🟡 |
| `Timer` | 类版上下文管理器 | 🟡 |
| `managed_resource` | @contextmanager 生成器版 | 🔴 |

```bash
uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v
```
全绿 = 掌握 Ch06。with 相关卡了 → 回 §6.4/§6.5。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「with 语句做了什么?__enter__/__exit__ 何时被调?」(§6.4)
- [ ] 能解释 try/except/else/finally 各段何时执行,else 为什么存在(§6.2)
- [ ] 知道 `raise ... from e` 的作用(§6.3)
- [ ] 能说清 @contextmanager 版的「yield 切三段」套路(§6.5)
- [ ] 5 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「with 语句到底做了什么?它和 Java try-with-resources 怎么对应?」— 卡壳重读 §6.4
2. 「@contextmanager 版为什么用 yield?yield 前后各对应什么?」— 卡壳重读 §6.5
3. 「try/except/else/finally 的 else 何时执行?Java 为什么没有?」— 卡壳重读 §6.2

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch06 掌握后,进 **Ch07 · 类型注解与 Pythonic 风格**——M1 最后一章。给 Python 加上「准静态类型」(mypy),让你从 Java 过来更舒服;并学会最地道的 Python 写法(EAFP、Protocol、The Zen of Python)。
