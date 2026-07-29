# Ch01 · 环境工具链 & 从 Java 到 Python 的思维转换

> **预计**:1 天 ｜ **前置**:无
> **目标**:① 搭好开发环境,理解每个工具是干嘛的;② **换脑子**——理解 Python 与 Java 的根本差异,避免写出「用 Java 语法拼凑的 Python」。
> 你 15 年 Java 经验,语法扫一眼就会,真正要小心的是**思维差异**和**工具链生态**。

> 📐 **本教程的契约**:下面每一节(§1.1–§1.6)都**精确对应**作业里的一道题。讲过的才考,考的必讲过。卡住时,按作业题号回查对应小节即可,不用去翻外部文档。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 解释 Python 动态类型 + 类型注解的关系(为什么注解"不强制")
- 用元组解包一行交换变量、一行返回多值(告别临时变量)
- 用默认参数 + f-string + `join` 写出 Pythonic 的字符串拼接
- 用 truthiness 一句话判空,且知道它和 `None` 的陷阱
- 分清 `str()` 和 `repr()`(describe 题的核心)
- 用 `import` + 字典 + 列表推导式解析 mock JSON(工作流题的核心)
- 用 `venv` / `uv` 管理依赖,理解为什么 Python 需要虚拟环境(Java 不需要)
- 用 `pytest` 跑测试、读断言失败;用 `mypy` / `ruff` 做静态检查(模拟 Java 编译期)
- 避开 Java 老手最容易踩的 7 个坑

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `add` | §1.1 | 动态类型 + 类型注解 |
| `swap` | §1.2 | 元组打包/解包 |
| `greet` | §1.3 | 默认参数 + f-string + `join` + `*` |
| `first_or_default` | §1.4 | truthiness 真值表 |
| `describe` | §1.5 | 一切皆对象 + `repr` vs `str` |
| `load_product_names` | §1.6 | `import` + 字典 + 列表推导式 |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 看下面的差异,先猜 Python 怎么实现 | 本页 ① |
| ② 先动手 | 打开 `ch01_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"类型注解为何不强制""repr 和 str 差在哪" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别从头读到尾!先扫 ① 猜一猜 → 跳去 ② 写作业 → **哪题卡了,回对应 §查**(见上表)→ 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错没关系,错了记得更牢):
1. `def add(a: int, b: int)` 标了类型,调用 `add(1, "2")` 会怎样?(编译错?运行错?正常?)
2. Java 要临时变量才能交换两个值,Python 要几个变量?
3. `"ab" * 3` 在 Python 里等于什么?Java 里能这么写吗?
4. Java 要写 `if (items == null || items.isEmpty())`,Python 一句怎么写?
5. `print("hi")` 显示 `hi`,但为什么测试期望 describe 显示 `'hi'`(带引号)?
6. Java 的 `import` 是编译期声明,Python 的 `import` 是什么?

> 猜完,带着验证心态进入正文。

---

## §1.1 动态类型 + 可选类型注解(对应:`add`)🔴

Java 是**静态强类型**:编译期检查,类型错了编不过。

```java
// Java:类型错了,编译报错
int add(int a, int b) { return a + b; }
add(1, "2"); // ❌ 编译失败
```

Python 是**动态强类型**:运行时才确定类型。类型注解(`: int`)只是**给人和工具看的提示**,运行时**完全不强制**。

```python
# Python:注解是"建议",运行时不检查
def add(a: int, b: int) -> int:
    return a + b

add(1, 2)     # ✅ 3
add(1, "2")   # ⚠️ 不报错地传进去,运行到 a+b 时才 TypeError: int + str
add("a", "b") # ⚠️ 也不报错,返回 "ab"(字符串也能 +)
```

> 🤯 **Java 老手震惊点**:类型注解不是约束,是文档。真正的约束靠 **mypy**(§1.8)在写代码时静态检查,模拟 Java 的编译期。运行时一律鸭子类型——"能 + 就行,不管你是啥"。
>
> **强类型**的"强"体现在:Python 不会像 JS 那样隐式 `1 + "2" = "12"`,它会直接抛 `TypeError`。

> ✅ 做 `add` 题:`return a + b` 即可,注解照抄。

---

## §1.2 元组与解包(对应:`swap`)🟡

### Python 怎么交换两个值

```java
// Java:必须借临时变量
int tmp = a; a = b; b = tmp;
```

```python
# Python:一行,无临时变量
a, b = b, a
```

**为什么不用临时变量?**——因为 Python 的赋值是「**先把右边整体求值,再解包给左边**」:
1. 右边 `b, a` 先求值,打包成一个**元组** `(b的值, a的值)`(此时 a/b 还是旧值,已固化进元组)
2. 再把这个元组**解包**到左边的 `a, b`

两步之间元组是中转,所以不会出现"先改 a 导致 b 也变错"的问题。Java 老手可以理解成:右边先存了一份快照。

### 元组(tuple)是什么

元组就是**不可变的列表**,用逗号定义,常用括号包裹:

```python
point = (3, 4)        # 一个元组
point = 3, 4          # 不加括号也是元组(逗号才是关键)
x, y = point          # 解包:x=3, y=4
```

> 🟡 Java 类比:Java 没有元组,要么用数组、要么写 `record`/POJO。Python 的元组是语言级内置,轻量到可以随手用。

### 函数返回"多个值"

Python 函数**只能返回一个值**,但元组让它**看起来**返回了多个:

```python
def swap(a, b):
    return b, a          # 实际返回的是元组 (b, a)

result = swap(1, 2)      # result == (2, 1)
x, y = swap(1, 2)        # 直接解包:x=2, y=1

# 另一个常见用法:一次返回多个有意义的结果
def min_max(nums):
    return min(nums), max(nums)
lo, hi = min_max([3, 1, 4, 1, 5])   # lo=1, hi=5
```

### 坑:解包数量必须匹配

```python
a, b = [1, 2, 3]        # ❌ ValueError: too many values to unpack
a, b, c = [1, 2]        # ❌ ValueError: not enough values to unpack

# 想收集多余的,用星号 *
a, *rest = [1, 2, 3]    # a=1, rest=[2, 3]
first, *middle, last = [1, 2, 3, 4]   # first=1, middle=[2,3], last=4
```

> ✅ 做 `swap` 题:`return b, a`。

---

## §1.3 默认参数 + f-string + 字符串操作(对应:`greet`)🟡

### 默认参数:Python 不要方法重载

```java
// Java:写 3 个 greet 重载
String greet(String name) { return greet(name, "Hello"); }
String greet(String name, String greeting) { return greeting + ", " + name + "!"; }
```

```python
# Python:一个函数,默认参数搞定
def greet(name: str, greeting: str = "Hello", times: int = 1) -> str:
    ...
```

调用时可以只传前面、跳着传:
```python
greet("Alice")                # 用默认 greeting="Hello", times=1
greet("Bob", "Hi")            # greeting="Hi"
greet("Carl", times=3)        # 关键字参数,跳过 greeting
```

**为什么**:默认参数把"可选性"内建进函数签名,一个签名表达 N 种调用形态。这是 Python 极常用的特性。

### f-string:告别 `String.format`

```python
name, price, count = "键盘", 599.0, 3
# Java: String.format("%s 总价 %.2f", name, price*count)
# Python:直接在字符串里写表达式
msg = f"{name} 总价 {price * count:.2f} 元"   # "键盘 总价 1797.00 元"

line = f"{greeting}, {name}!"   # "Hello, Alice!"
```

> f-string 前面那个 `f` 是开关。`{}` 里能放任意表达式,`:.2f` 是格式说明(保留 2 位小数)。

### 字符串/列表的 `*`(重复)和 `join`(拼接)

`greet` 题还要把一行问候**重复 times 次、用换行分隔**。需要两个工具:

```python
# 重复:用 *
"ab" * 3              # "ababab"     字符串重复
[line] * 3            # [line, line, line]   列表重复

# 拼接:用 str.join(分隔符)
"-".join(["a", "b", "c"])        # "a-b-c"
"\n".join(["x", "y", "z"])       # 三行:x / y / z
"".join(["a", "b", "c"])         # "abc"   分隔符为空就是纯拼接
```

> 🟡 Java 类比:`String.join("\n", list)`。Python 是 `分隔符.join(列表)`,**注意主语是分隔符不是列表**——Java 老手一开始常写反。

**为什么用 join 而不是 `+` 循环?**——join 是一次性分配内存,**O(n)**;而循环里每次 `s += line` 都会新建一个字符串,**O(n²)**。join 是 Pythonic 的标准做法。

### 组合起来:greet 的 Pythonic 写法

```python
def greet(name: str, greeting: str = "Hello", times: int = 1) -> str:
    line = f"{greeting}, {name}!"
    return "\n".join([line] * times)
```

一行 `[line] * times` 造出 n 份,`"\n".join` 用换行拼起来。

> ⚠️ **字符串里的换行**:写成 `"\n"`(一个反斜杠 + n)表示**换行符**;写成 `"\\n"`(两个反斜杠)表示**字面的反斜杠和字母 n**。这是上一版你踩过的坑——务必用单反斜杠。

> ✅ 做 `greet` 题:见上。

---

## §1.4 truthiness 真值表(对应:`first_or_default`)🟡

### Python 的 `if` 能直接判断任何对象

```java
// Java:必须显式判 null 和 empty
if (items == null || items.isEmpty()) return default;
return items.get(0);
```

```python
# Python:一句
if not items:
    return default
return items[0]
```

`if not items:` 一句同时覆盖了 **None、空列表、空串、空字典、0……**——因为 Python 给每个对象定义了"真假值"(truthiness)。

### 真值表(背下来)

| falsy(判定为假) | 其余都判定为真(truthy) |
|---|---|
| `None` | 非 None 的对象 |
| `False` | `True` |
| `0`、`0.0` | 任何非零数字 |
| `""` 空字符串 | 非空字符串 |
| `[]` 空列表 / `()` 空元组 | 非空容器 |
| `{}` 空字典 / `set()` 空集合 | 非空容器 |

**记忆口诀**:**空、零、假、None** 这四类是 falsy,其他全真。

**为什么这么设计?**——Python 哲学是"简单直接"。PEP 8 明确推荐:`if items:` 比 `if len(items) > 0:` 更 Pythonic。它把"有没有内容"这个极常见的判断压成一个词。

> ✅ 做 `first_or_default` 题:
> ```python
> def first_or_default(items: list, default=None):
>     if not items:
>         return default
>     return items[0]
> ```
> 或更 Pythonic 的三元表达式:`return items[0] if items else default`。

### 坑:`if x:` 会把 `0` 也判成假!

这是 truthiness 最危险的陷阱,Java 老手特别容易踩:

```python
count = 0
if count:          # ❌ False!因为 0 是 falsy
    print("有数量")  # 不会执行——但你的本意可能是"count 有值"

# 正确区分"没有值(None)"和"值为 0":
if count is not None:     # ✅ 这样 0 也能进
    print("count 有值")
```

**结论**:
- 想判断"是不是空/没有" → 用 `if not x:`
- 想判断"是不是 None" → 用 `if x is None:`(§1.10 坑2 会再强调)

---

## §1.5 一切皆对象 + `repr` vs `str`(对应:`describe`)🔴

这节是 `describe` 题的全部。请仔细读——上一版教程漏讲了,导致你卡在字符串那题。

### 差异:Python 没有基本类型

Java 区分**基本类型**(`int`/`double`/`boolean`)和**引用类型**(`Integer`/`String`),有装箱拆箱。
Python **没有基本类型**。整数、布尔值、甚至**函数、类、模块**,通通是对象。

```python
x = 42
print(x.bit_length())   # ✅ 6 —— int 也是对象,有方法

print(type(42))         # <class 'int'>   ← 注意这是个类型对象,不是字符串
print(type("hi"))       # <class 'str'>
```

### 拿到"类型名字符串":`type(obj).__name__`

`type(42)` 返回的是**类型对象** `<class 'int'>`,不是字符串 `"int"`。要拿到干净的名字,取它的 `__name__` 属性:

```python
type(42).__name__       # "int"
type("hi").__name__     # "str"
type([1,2]).__name__    # "list"
type(3.14).__name__     # "float"
```

> 🟡 为什么有两层?——因为 Python 里**类也是对象**。`int` 是一个"类的对象",它自己是 `type` 类的实例(`type(type(42))` 是 `<class 'type'>`)。`__name__` 是这个类对象的名字属性。Java 里 `Integer.class.getSimpleName()` 类似。

### `str()` vs `repr()`:describe 题的核心

Python 有**两个**把对象转字符串的函数,Java 老手要特别留意(Java 的 `toString()` 只有一个):

```python
str(obj)    # 给【人】看:友好、简洁的显示
repr(obj)   # 给【程序】看:无歧义,尽量能被 eval 重建回来
```

**对比表**(这是 describe 题的答案表):

| 对象 `obj` | `str(obj)` | `repr(obj)` |
|---|---|---|
| `42` | `"42"` | `"42"` |
| `3.14` | `"3.14"` | `"3.14"` |
| `"hi"` | `hi`(**无引号**) | `'hi'`(**有引号**) |
| `[1, 2]` | `"[1, 2]"` | `"[1, 2]"` |

**关键区别就在字符串这一行**:数字和列表,`str` 和 `repr` 长一样;但**字符串**,`str` 去掉引号(给人看),`repr` 保留引号(给程序看)。

**为什么 `repr` 要给字符串加引号?**——因为 `repr` 的设计目标是"**无歧义地标识一个对象的类型和值,最好能直接 eval 重建**":
```python
eval(repr("hi"))   # == "hi"   ✅ 能重建
eval(repr(42))     # == 42     ✅
eval(str("hi"))    # eval("hi") → 去找名为 hi 的变量 → NameError(除非恰好有这个变量)
```
加引号让你一眼区分"这是字符串值 `hi`"还是"这是变量名 `hi`"。这就是 describe 题为什么期望 `'hi' is a str` 带引号——它要的是**无歧义表示**。

> 🟡 Java 类比:`str(obj)` ≈ `obj.toString()`(给人看);`repr(obj)` 没有完美对应,最接近的是"调试器/日志里能区分类型的表示"。Java 的 `toString` 一般只有一个,Python 分 `__str__`/`__repr__` 两个钩子。

### 什么时候看到的是 str,什么时候是 repr?

- `print(obj)` → 用 **str**
- 在 REPL / 交互式环境里直接敲 `obj` 回车 → 用 **repr**
- f-string `f"{obj}"` → 用 **str**(describe 题踩坑点!)

```python
print("hi")        # 显示:  hi       (str, 无引号)
# REPL 里敲:
>>> "hi"
'hi'               # 显示带引号(repr)
>>> 42
42
```

所以 `describe` 题里,直接写 `f"{obj}"` 对字符串得到的是 `hi`(无引号),**过不了**测试。要换成 `f"{repr(obj)}"` 才能得到 `'hi'`。

> ✅ 做 `describe` 题:
> ```python
> def describe(obj) -> str:
>     return f"{repr(obj)} is a {type(obj).__name__}"
> ```
> 验证:`describe(42)`→`42 is a int`、`describe("hi")`→`'hi' is a str`、`describe([1,2])`→`[1, 2] is a list`、`describe(3.14)`→`3.14 is a float`。全对。

---

## §1.6 `import` + 字典 + 列表推导式(对应:`load_product_names`)🔴

这节是工作流题的全部,上一版完全没讲,这是补上的。

### `import`:Python 的导入语句

```python
from conftest import load_mock_json   # 从 conftest 模块导入一个函数
import json                            # 导入整个 json 模块,用 json.loads()
from assets.mock_data import products  # 从子包导入
```

**与 Java 的根本区别**:
- Java 的 `import com.foo.Bar;` 是**编译期声明**,只是告诉编译器 `Bar` 在哪,运行时不存在。
- Python 的 `import` 是**运行时执行的语句**——它真的会去找到那个 `.py` 文件(一个 `.py` 文件 = 一个模块),**执行它**,然后把里面的名字绑到当前作用域。

> 🟡 Java 类比:更接近 Java 的 `Class.forName()` 动态加载,而不是编译期 import。模块 = 一个 `.py` 文件;包(package)= 一个含 `__init__.py` 的目录。

**项目里的 conftest 是什么**:`conftest.py` 是 pytest 的约定文件,放在项目根目录,里面的函数所有测试都能直接 `from conftest import xxx` 用。我们的 `load_mock_json(name)` 就定义在那(读 `assets/mock_data/` 下的 JSON 文件)。

### 字典(dict):JSON 解析后的结果

JSON 对象在 Python 里就是 **dict**(字典),类似 Java 的 `Map<String, Object>`,但语法原生、用得极频繁:

```python
p = {"id": 1, "name": "键盘", "price": 599.0, "stock": 10}

p["name"]              # 取值:"键盘"
p["price"]             # 599.0
p.get("stock", 0)      # 安全取值:有就返回,没有返回默认 0(不会抛错)
p["color"]             # ❌ KeyError:键不存在会抛异常
```

> 🟡 Java 类比:`Map<String, Object>` + `map.get("name")`。但 Python dict 是一等公民,`{}` 直接写,取值用方括号。

### 列表推导式(list comprehension):Pythonic 的核心

要"从一堆商品里提取所有 name",Java 用 Stream,Python 用**列表推导式**:

```java
// Java Stream
List<String> names = products.stream()
    .map(p -> p.getName())
    .collect(Collectors.toList());
```

```python
# Python 列表推导式
[p["name"] for p in products]                          # 提取每个的 name
[p["name"] for p in products if p["price"] > 100]      # 带过滤
[f"{p['name']}-{p['price']}" for p in products]        # 带变换
```

语法骨架:`[表达式 for 变量 in 可迭代对象 if 条件]`——读作"**对每个 p,算出表达式,收集成列表**"。

**为什么用推导式**:它是声明式的、紧凑的,Python 社区极推崇(PEP 8 / PEP 20 "简单胜于复杂")。等价的传统写法是 for + append:

```python
names = []
for p in products:
    names.append(p["name"])
# 上面这 3 行 == [p["name"] for p in products]  这 1 行
```

> ⚠️ 推导式别写太长、别嵌套太深(超过两层可读性变差),那时就老老实实写 for 循环。

### 组合起来:load_product_names

```python
def load_product_names() -> list[str]:
    from conftest import load_mock_json          # 1. 导入工具
    data = load_mock_json("products.json")       # 2. 读 JSON → list[dict]
    return [p["name"] for p in data]             # 3. 列表推导式提取 name
```

三步:导入 → 读数据(JSON 数组变成 list[dict])→ 推导式提取字段。

> ✅ 做 `load_product_names` 题:见上。

---

## §1.7 工具链全景(对比 Java 生态)

| 用途 | Java | Python | 说明 |
|------|------|--------|------|
| 多版本管理 | SDKMAN / 手动 | **pyenv** ✅(你已装) | 管理 Python 解释器版本 |
| 依赖管理 | Maven / Gradle | **pip** + 虚拟环境 | pip 类似 Maven,但没有内置锁文件 |
| 项目隔离 | Maven 自动隔离 | **venv** / **uv** ⚠️(关键差异) | **Java 不需要虚拟环境,Python 必须!** |
| 现代一体化 | — | **uv** ⭐(推荐,你已装) | Rust 写的,极速,= Maven+venv+pip-tools |
| 构建/打包 | jar / `mvn package` | `pyproject.toml` + `pip install -e .` | 类似 pom.xml |
| 测试 | JUnit | **pytest** | 本课程核心 |
| 类型检查 | 编译器(自带) | **mypy** | 模拟编译期类型检查 |
| Lint/Format | Checkstyle / Spotless | **ruff** ⭐ | 一个工具替代 flake8+black+isort |
| 依赖锁文件 | `pom.xml` 锁版本 | `uv.lock` / `requirements.txt` | 锁定版本 |

### 为什么 Python 必须用虚拟环境(Java 不用)?

🟡 **关键差异**:Java 依赖通过 Maven/Gradle 按**项目**隔离(`~/.m2/repository` 缓存,但每个项目 classpath 独立),全局只有一个 `java`。

Python 默认是**全局共享 site-packages**:你在项目 A 装了 `requests==2.31`,项目 B 装 `requests==2.28`,后者会**覆盖**前者,全局炸了。

所以每个 Python 项目都要建**虚拟环境**(一个独立的 site-packages 文件夹),依赖装在里面,互不干扰。

### 实操命令(在你的环境里跑一遍)

你当前项目已经建好了 `.venv`(Python 3.14)。下面验证你**会**这些命令:

```bash
cd /Users/zy/ai_learn/python_learning

# ---------- 虚拟环境(venv,标准库自带)----------
source .venv/bin/activate        # 激活(命令行前会出现 (.venv) )
which python                     # 应指向 ./.venv/bin/python,不是系统 python
deactivate                       # 退出虚拟环境

# ---------- 现代一体化:uv(强烈推荐,本课程统一用它)----------
uv venv                          # 建虚拟环境(替代 python -m venv .venv)
uv pip install pytest            # 装(比 pip 快 10-100 倍)
uv run pytest                    # 在项目虚拟环境里跑命令(自动激活,不用 source)
```

> 💡 本课程从 Ch01 起就统一用 `uv run pytest`,不用再手动 `source activate`。

---

## §1.8 pytest 工作流(本课程核心机制)

> 你 15 年经验肯定用过 JUnit。pytest 比 JUnit 更简洁——不用写 class,不用 `@Test`,函数名以 `test_` 开头就是测试。

### 跑测试的命令

```bash
uv run pytest                                    # 跑所有测试(pyproject.toml 配的 testpaths)
uv run pytest 01_python_core/ch01/ -v            # 只跑本章
uv run pytest -k "swap"                          # 只跑名字含 "swap" 的测试
uv run pytest --lf                               # 只跑上次失败的(--last-failed)
uv run pytest -v                                 # -v 详细模式,看每个测试名
```

### 读断言失败(pytest 的杀手锏)

pytest 的 `assert` 比 JUnit 的 `assertEquals` 智能,失败时直接显示两边值:

```python
def test_add():
    assert add(1, 2) == 4   # 故意写错
```

失败输出会显示:
```
>       assert add(1, 2) == 4
E       assert 3 == 4
```
一眼看出左边是 3、右边期望 4。

### 静态检查:模拟 Java 编译期

```bash
uv run mypy 01_python_core/ch01/ch01_assignment.py   # 类型检查,模拟编译期
uv run ruff check 01_python_core/ch01/               # 语法/风格 lint
```

配 IDE 插件后(mypy + ruff),能获得接近 Java 的实时红线反馈——这是 Python 弥补"没有编译期"的方式。

---

## §1.9 第一个 Python 程序 & `if __name__ == "__main__":`

Java 程序入口是 `public static void main(String[] args)`。Python 没有强制入口,但有个**惯用法**:

```python
# hello.py
def greet(name: str) -> str:
    return f"Hello, {name}!"

# 这块代码:直接 `python hello.py` 运行时执行;被 `import hello` 时不执行
if __name__ == "__main__":
    print(greet("World"))
```

> 🟡 `__name__` 是每个模块的内置变量。直接运行时它等于 `"__main__"`;被 import 时等于模块名(如 `"hello"`)。这个判断让你同一个文件既能当脚本跑,又能被当库 import——Java 要做到这个得拆两个类。
>
> 🟢 记不住没关系,先当成 Python 的 `public static void main` 就行。

---

## §1.10 Java 老手 7 大常见坑 ⚠️

### 坑 1:混用 Tab 和空格 → `IndentationError`
编辑器设"插入 4 空格",`ruff` 会帮你查。

### 坑 2:`is` vs `==`(Java `==` 的对应物要小心)
Java `==` 比较引用,`equals` 比较值。Python:
- `==` 比较**值**(= Java `equals`)
- `is` 比较**身份/内存地址**(= Java `==` 引用相等)

```python
a, b = [1,2], [1,2]
a == b   # True(值相等)
a is b   # False(不同对象)
# 判 None 用 is:  if x is None   ✅   不要 if x == None
```

### 坑 3:`None` 不是 `null`,判空要区分场景
Python 用 `None`(首字母大写的单例对象)。
- 想"判断是否为 None" → `if x is None:`
- 想"判断是否为空/没有内容" → `if not x:`(见 §1.4 truthiness,注意 0 也是 falsy)

### 坑 4:`True`/`False` 首字母大写,且是 `1`/`0` 的别名
```python
True + True   # = 2!  (bool 是 int 子类)
```

### 坑 5:没有 `++`/`--`,没有 `i++`
用 `i += 1`。

### 坑 6:可变默认参数(Ch02 详讲,先记住)
```python
def f(items=[]):      # ❌ 危险!默认值在函数定义时只创建一次,所有调用共享
    items.append(1)
    return items
def f(items=None):    # ✅ 正确写法
    if items is None:
        items = []
```

### 坑 7:没有传统 `switch`,但有 `match/case`(3.10+,Ch07 讲)
```python
match status:
    case 200: print("OK")
    case 404: print("Not Found")
    case _:   print("Unknown")
```

---

## 📝 本章作业

打开 **`ch01_assignment.py`**,6 个函数。每个函数顶部注释标了【转换点】,对应正文某节(见开头「作业 ↔ 教程对应表」)。

**完成方式**:
```bash
uv run pytest 01_python_core/ch01/test_ch01_assignment.py -v
```
全绿 = 你掌握了 Ch01。**哪题卡住 → 回对应 § 查**(`describe`卡→§1.5,`load_product_names`卡→§1.6)。

---

## ✅ 自测:你真的掌握了吗?

- [x] 能解释「为什么 Python 需要虚拟环境而 Java 不需要」(§1.7)
- [x] 能说清 `str()` 和 `repr()` 的区别,以及为什么字符串的 repr 带引号(§1.5)
- [x] 能背 truthiness 真值表,知道 `if not 0` 会进分支的陷阱(§1.4)
- [x] 能用列表推导式提取字段(§1.6)
- [x] 知道判 `None` 要用 `is None` 而不是 `== None`(§1.10 坑2)
- [x] 6 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 费曼技巧:用大白话把概念讲给一个「Java 同事」听。**讲不清的地方 = 你还没真懂**,回去重读对应小节。可口头讲(通勤/洗澡),不必写下来。

任选一题,讲清楚(1-2 分钟):
1. 「为什么 Python 的类型注解不强制,而 Java 的类型是硬约束?」— 卡壳重读 §1.1
2. 「`str()` 和 `repr()` 到底差在哪?为什么字符串的 repr 要带引号?」— 卡壳重读 §1.5
3. 「为什么 `if not x:` 在 x=0 时也会进分支?怎么避免?」— 卡壳重读 §1.4

✅ 自检:不查资料、不堆术语,能说清「为什么」吗?说不清 → 重读。

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完把复习日期标上(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch01 掌握后,进 **Ch02 · 数据结构(list/tuple/dict/set)**——正式进入 Python 数据处理,作业就是你举的那个例子(从 mock json 解析商品、过滤、排序)。
