# Ch04 · 函数:一等公民、闭包、装饰器

> **预计**:1 天 ｜ **前置**:Ch03
> **目标**:理解函数在 Python 里是「一等公民」(可赋值、传参、返回),并掌握 **装饰器**——Python 最强大的特性之一,相当于 Java「注解 + AOP/拦截器」但内置在语言里、纯函数就能写。

> 📐 **本教程的契约**:下面每一节(§4.1–§4.6)都**精确对应**作业里的一道题。讲过的才考,考的必讲过。卡住时,按作业题号回查对应小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 把函数当**参数传、当返回值返**(高阶函数),理解 Python 函数就是对象
- 写出**闭包**(内层函数记住外层变量),理解它和 Java lambda 捕获的关系
- 用 `*args` / `**kwargs` 接收任意参数
- 写**装饰器**(基础版、带参数版、缓存版),用 `@functools.wraps` 保留元数据
- 解释 `@decorator` 语法糖背后的等价转换

**作业 ↔ 教程对应表**:

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `apply_twice` | §4.1 | 函数当参数(高阶函数) |
| `make_multiplier` | §4.2 | 闭包 |
| `sum_prices` | §4.3 | *args |
| `build_product` | §4.3 | **kwargs |
| `count_calls` | §4.4 | 装饰器基础 + functools.wraps |
| `retry` | §4.5 | 带参数的装饰器 |
| `memoize` | §4.6 | 缓存装饰器(综合) |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 看下面的差异,先猜 Python 怎么实现 | 本页 ① |
| ② 先动手 | 打开 `ch04_assignment.py`,**先试着写** | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"装饰器本质是什么、@糖怎么展开" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性**:先猜 ① → 写作业 → 装饰器题(§4.4–4.6)最容易卡,卡了就回对应 § 看那张「等价转换」图。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java 把函数当参数要写 `Function<Integer,Integer>`,Python 怎么传一个函数?
2. Java 要返回一个"记住外部变量"的函数,要用 lambda 捕获 effectively final 变量。Python 怎么做?
3. Java 可变参数 `Object... args` 只能有一种、且必须放最后。Python 能不能同时收"任意个位置参数 + 任意个关键字参数"?
4. Java 给方法加日志/计时,要靠 AOP 框架(Spring @Aspect)。Python 有没有语言内置的方式?
5. `@count_calls` 写在 `def` 上面,到底等价于什么?

> 猜完,带着验证心态进入正文。

---

## §4.1 函数是一等公民(对应:`apply_twice`)🟡

在 Python 里,**函数就是个对象**(Ch01 §1.5 讲过一切皆对象)。它能:
- 赋值给变量
- 当参数传给别的函数(**高阶函数**)
- 当返回值返回(§4.2 闭包)
- 放进容器

```java
// Java:函数不是一等公民,要包成函数式接口
int applyTwice(Function<Integer,Integer> f, int x) { return f.apply(f.apply(x)); }
applyTwice(x -> x + 3, 10);
```

```python
# Python:函数直接是对象,当参数传、当返回值都行
def apply_twice(func, x):       # func 是个函数对象
    return func(func(x))        # 直接调用

apply_twice(lambda x: x + 3, 10)   # 16
```

> 🟡 **Java 对比**:Java 的函数必须是「函数式接口的实例」(`Function`/`Consumer`/`Predicate`...),要类型签名。Python 函数没有这个包袱,任何函数都能直接传来传去。这让 Python 写高阶函数、回调、策略模式都极轻量。
>
> 调用一个函数对象:和 Java 一样用括号 `func(x)`;但**不带括号 `func` 是函数对象本身**(不调用)。Java 老手常误写 `apply_twice(func(), x)`(多加了括号,变成了调用结果)。

> ✅ 做 `apply_twice` 题:`return func(func(x))`。

---

## §4.2 闭包(对应:`make_multiplier`)🔴

**闭包 = 内层函数 + 它记住的外层变量**。

```python
def make_multiplier(factor):       # 外层函数
    def multiplier(x):             # 内层函数
        return x * factor          # ↑ 用到了外层的 factor
    return multiplier              # 返回内层函数(注意:不调用,不加括号)

triple = make_multiplier(3)        # triple 现在是个函数,且【记住了 factor=3】
triple(5)                          # 15
```

**关键理解**:`make_multiplier(3)` 执行完返回了,它的局部变量 `factor` 本该消亡——但 `multiplier` 这个内层函数**捕获**了它,只要 `triple` 还在,`factor=3` 就一直活着。这种「带着环境一起带走的函数」就是闭包。

> 🟡 **Java 对比**:就是 Java lambda 捕获外部变量:
> ```java
> Function<Integer,Integer> makeMultiplier(int factor) {
>     return x -> x * factor;   // 捕获 factor(必须 effectively final)
> }
> ```
> 区别:Java 要求被捕获变量 **effectively final**(不能再改);Python 闭包能读到外层变量,**想修改**要加 `nonlocal` 声明(本章不深究)。

### 坑:别加括号

```python
return multiplier      # ✅ 返回函数对象本身
return multiplier()    # ❌ 立刻调用它(还没传 x,会报错)
```

> ✅ 做 `make_multiplier` 题:定义内层 `multiplier(x): return x*factor`,返回它。

---

## §4.3 *args / **kwargs(对应:`sum_prices`、`build_product`)🟡

Python 函数能接收**任意数量**的参数,分两组:

| 写法 | 收集什么 | 函数内是什么类型 |
|------|---------|-----------------|
| `*args` | 多余的【位置参数】 | 元组 `tuple` |
| `**kwargs` | 多余的【关键字参数】 | 字典 `dict` |

```python
def sum_prices(*prices):       # 调用 sum_prices(599, 129) → prices=(599,129)
    return sum(prices)

def build_product(name, **fields):   # 调用 build_product("键", price=599) → fields={"price":599}
    return {"name": name, **fields}
```

### `**fields` 解包进字典字面量

`build_product` 的返回值 `{"name": name, **fields}` 里,`**fields` 把字典**展开**铺进新字典:
```python
fields = {"price": 599.0, "stock": 120}
{"name": "键盘", **fields}   # {"name": "键盘", "price": 599.0, "stock": 120}
```

### 完整参数顺序(背下来)

```python
def f(pos, /, normal, *args, kw_only, **kwargs):
    ...
#  位置only  普通参数   可变位置  关键字only   可变关键字
```
日常用 `def f(a, b, *args, **kwargs)` 就够。

> 🟡 **Java 对比**:Java 可变参数只有 `Object... args`(本质数组),且只能有一种、必须放最后。Python 把「位置可变」和「关键字可变」分成 `*args`/`**kwargs` 两组,灵活得多。这正是 FastAPI(Ch14+)能自动解析查询参数的基础。

### `*` 解包(调用时)

```python
def add(a, b, c): return a+b+c
nums = [1, 2, 3]
add(*nums)          # 等价 add(1, 2, 3)   —— * 把列表拆开成位置参数
add(**{"a":1,"b":2,"c":3})   # ** 把字典拆成关键字参数
```

> ✅ 做 `sum_prices`:`return sum(prices)`(prices 是元组)。
> 做 `build_product`:`return {"name": name, **fields}`。

---

## §4.4 装饰器基础(对应:`count_calls`)🔴

这是本章核心。**装饰器本质就是一个「接收函数、返回新函数」的函数**。先别管 `@`,先看手动版本:

### 手动版本:把函数"包"一下

```python
def greet(name):
    return f"hi {name}"

# 我想统计 greet 被调几次,但【不想改 greet 的源码】
def count_calls(func):
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)
    wrapper.call_count = 0
    return wrapper

greet = count_calls(greet)    # ✨ 用【包装后的新函数】替换原 greet
greet("a")                    # call_count 变 1
greet.call_count              # 1
```

`count_calls` 接收 `greet`,返回一个新的 `wrapper`(它在调真函数前后做了计数)。最后一行 `greet = count_calls(greet)` 把名字重新指向包装版。**原函数没动,行为却被增强了**——这就是 AOP 的思想。

### `@` 语法糖:上面的简写

```python
@count_calls
def greet(name):
    return f"hi {name}"
```
**完全等价于**:
```python
def greet(name):
    return f"hi {name}"
greet = count_calls(greet)      # ← @ 就是这一句的简写!
```

> 🤯 **记住这张等价关系,装饰器就懂了一半**:`@deco` 贴在 `def f` 上 = `f = deco(f)`。装饰器在函数【定义时】执行一次,把 f 替换成包装版。

### 为什么用 `*args, **kwargs`

wrapper 要能接住**原函数任意签名**的调用,所以用 `*args, **kwargs` 全收下,再原样传给 `func(*args, **kwargs)`。这是装饰器 wrapper 的标准签名。

### `@functools.wraps(func)`:别忘了

不加它,装饰后的函数 `__name__` 会变成 `"wrapper"`,丢了原来的身份(影响调试、反射)。
```python
import functools

def count_calls(func):
    @functools.wraps(func)      # ← 把 func 的 __name__/__doc__ 拷贝给 wrapper
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)
    wrapper.call_count = 0
    return wrapper
```
**装饰器 wrapper 上永远要加 `@functools.wraps(原函数)`**——这是铁律(作业里有 test 检查 `__name__`)。

> 🟡 **Java 对比**:Java 的注解(`@Override`/`@Transactional`)本身只是元数据,**靠 Spring/Hibernate 等框架在运行时反射处理**。Python 装饰器是**语言层面的变换**,不依赖框架,一个普通函数就能实现 AOP。

> ✅ 做 `count_calls` 题:见上(注意初始化 `wrapper.call_count = 0` 后再 return)。

---

## §4.5 带参数的装饰器(对应:`retry`)🔴

`@retry(times=3)` ——装饰器自己带参数。这需要**三层嵌套**:

```python
def retry(times):              # 第1层:接收参数 times,返回真正的装饰器
    def decorator(func):       # 第2层:接收被装饰函数,返回 wrapper
        @functools.wraps(func)
        def wrapper(*args, **kwargs):   # 第3层:实际替换原函数
            last_exc = None
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
            raise last_exc
        return wrapper
    return decorator
```

### 为什么是三层?——再看等价转换

```python
@retry(times=3)
def f(): ...
# 等价于:
def f(): ...
f = retry(times=3)(f)
#       └─────┬────┘ └┬┘
#       先调用得到 decorator,再用 decorator 包 f
```
`retry(times=3)` 必须返回一个**装饰器**(就是 `decorator`),这个装饰器再接收 `f`。所以多了一层。

> **记忆口诀**:普通装饰器两层(`deco(func)→wrapper`);带参装饰器三层(`factory(args)→decorator(func)→wrapper`)。

### 为什么要重试这种东西?

API 调用、网络请求、DB 操作会偶发失败——自动重试是生产代码常见需求。你刚写的 `retry` 就是个微型版 Spring Retry / Resilience4j。

> ✅ 做 `retry` 题:见上三层结构。注意 `raise last_exc`(循环结束都失败才抛)。

---

## §4.6 缓存装饰器(对应:`memoize`)🟡

把 §4.2 闭包 + §4.4 装饰器合起来:**闭包持有一个 cache 字典**。

```python
def memoize(func):
    cache = {}                          # 闭包变量,每次装饰独立一份

    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:           # args 是元组,可作字典键
            wrapper.miss_count += 1
            cache[args] = func(*args)   # 没命中才算
        return cache[args]

    wrapper.miss_count = 0
    return wrapper

@memoize
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)
```

**为什么 cache 在闭包里?**——每个被装饰的函数要有自己独立的缓存,闭包变量正好"跟着函数走"。这是闭包的经典应用。

> 🟡 **实战**:Python 标准库 `functools.lru_cache` 就是更完善的版本(带容量上限、线程安全)。Ch09 会讲。本题要求**手写**不用它。

> ✅ 做 `memoize` 题:见上。`args` 天然是元组(可哈希),直接当键。

---

## §4.7 lambda 补充(本章了解)

Ch02 讲过 `lambda 参数: 表达式`。本章 `apply_twice` 的 test 里用了 lambda。记住:
- lambda 只能写**一个表达式**,不能写语句(不能赋值、不能 for)。
- 复杂逻辑用 `def`,别滥用 lambda(可读性差)。

---

## §4.8 Java 老手常踩的坑 ⚠️

1. **调用 vs 引用**:`func` 是函数对象,`func()` 是调用它。传参/返回时别多加括号。
2. **忘了 `@functools.wraps`**:装饰后 `__name__` 变 `wrapper`,调试和反射会乱。每个 wrapper 都要加。
3. **wrapper 签名**:永远用 `def wrapper(*args, **kwargs)`,别写死参数,否则原函数签名一变就崩。
4. **带参装饰器少一层**:写两层会得到"装饰器对象"而非"包装后的函数"。记住三层套路。
5. **闭包改外层变量要 `nonlocal`**:只读不用,想 `count += 1` 这种重新绑定,必须 `nonlocal count`(本题用属性 `wrapper.call_count` 规避了这点)。

---

## 📝 本章作业

打开 **`ch04_assignment.py`**,6 个函数。每题顶部标了【对应小节】。

| 函数 | 知识点 | 难度 |
|------|--------|------|
| `apply_twice` | 高阶函数 | 🟢 |
| `make_multiplier` | 闭包 | 🟡 |
| `sum_prices` / `build_product` | *args / **kwargs | 🟢 |
| `count_calls` | 装饰器基础 | 🟡 |
| `retry` | 带参装饰器 | 🔴 |
| `memoize` | 缓存装饰器(综合) | 🟡 |

```bash
uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v
```
全绿 = 掌握 Ch04。装饰器题卡了 → 回 §4.4 看那张「等价转换」。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说出「`@deco` 贴在 def 上,等价于哪一句赋值」(§4.4)
- [ ] 能解释闭包为什么能让 `factor` 在外层函数返回后还活着(§4.2)
- [ ] 知道带参装饰器为什么是三层、每层 return 什么(§4.5)
- [ ] 知道为什么 wrapper 必须用 `*args, **kwargs` + `@functools.wraps`(§4.4)
- [ ] 6 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「装饰器到底是什么?`@count_calls` 这一行等价于什么?」— 卡壳重读 §4.4
2. 「为什么带参数的装饰器要写三层?每层各 return 什么?」— 卡壳重读 §4.5
3. 「闭包为什么能记住外层已经返回的变量?和 Java lambda 捕获什么区别?」— 卡壳重读 §4.2

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch04 掌握后,进 **Ch05 · OOP:魔术方法、继承、dataclass**——理解 Python OOP 和 Java 的本质区别(没有重载、有多继承、靠魔术方法重载运算符),你会手写一个支持 `+`/`len()`/`in` 的 `ShoppingCart`。
