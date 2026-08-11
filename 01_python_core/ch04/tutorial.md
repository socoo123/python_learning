# Ch04 · 函数:一等公民、闭包、装饰器

> **预计**:1 天 ｜ **前置**:Ch03
> **目标**:理解函数在 Python 里是「一等公民」(可赋值、传参、返回),并掌握 **装饰器**——Python 最强大的特性之一,相当于 Java 的「注解 + AOP/拦截器」,但内置在语言里、一个普通函数就能写出来。
> 本章主线:你在电商后台负责「营销 + 稳定性」两条工具线——上午给运营做促销工具(批量试算折扣、发券工厂、购物车合计、统一 API 响应体);下午给服务加稳定性埋点(调用计数、耗时统计、失败重试、结果缓存)。这些工具不靠任何框架,全靠「函数本身」写出来。

> 📐 **本教程的契约**:下面每一节(§4.1–§4.6)都**精确对应**作业里的题。讲过的才考,考的必讲过。卡住时,按对应表回查小节即可。

---

## 🗺️ 本章地图(元学习 · 原则一)

学完这章,你将能够:
- 把函数当**参数传、当返回值返、放进容器**,说清 `fn` 和 `fn()` 的天差地别
- 写**闭包**(内层函数记住外层变量),说出它和 Java lambda 捕获 effectively final 的异同
- 用 `*args` / `**kwargs` 接收任意参数,并能在调用处用 `*` / `**` 打散列表/字典
- 写**装饰器**(基础版、带参数版),默出 `@deco` 的等价赋值,wrapper 永远带 `@functools.wraps`
- 手写**缓存装饰器**(闭包持有 cache 字典),理解标准库 `lru_cache` 为什么只是它的完善版

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `apply_discount` | §4.1 | 函数当参数(高阶函数) |
| `make_coupon` | §4.2 | 闭包 |
| `cart_total` | §4.3 | *args |
| `build_response` | §4.3 | **kwargs |
| `count_calls` | §4.4 | 装饰器基础 + functools.wraps |
| `timer` | §4.4 | 装饰器记录耗时 |
| `retry` | §4.5 | 带参数的装饰器 |
| `memoize` | §4.6 | 缓存装饰器(综合) |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch04_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"装饰器本质是什么、@糖怎么展开" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。装饰器题(§4.4–4.6)最容易卡,卡住先默写那句等价转换。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 把行为当参数传,要 `Function<Double,Double>` 这类接口包装。Python 想把「打半价」这个算法传给一个试算函数,你猜怎么写?
2. Java lambda 捕获外部变量必须 effectively final。Python 想让「满 200 减 30」这张券**记住**自己的门槛和减额,怎么造?
3. Java 可变参数 `Object... args` 只有一种、必须放最后。Python 能不能同时收「任意个位置参数 + 任意个关键字参数」?
4. Java 给方法加计数/计时,靠 Spring AOP 框架。Python 不写框架、不改原函数源码,怎么给任意函数包一层?
5. `@retry(times=3)` 写在 `def` 上面,你猜它等价于哪一句赋值?

> 猜完,带着验证心态进入正文。第 4、5 题的答案在 §4.4/§4.5,是本章的灵魂。

---

## §4.1 函数是一等公民(对应:`apply_discount`)🟡

在 Python 里,**函数就是个对象**(Ch01 讲过一切皆对象)。它能:赋值给变量、当参数传给别的函数(**高阶函数**)、当返回值返回(§4.2)、放进容器。

### Java 对照:函数式接口的包袱

```java
// Java:算法要包成函数式接口的实例才能传
List<Double> applyDiscount(List<Double> prices, Function<Double,Double> rule) {
    return prices.stream().map(rule).toList();
}
applyDiscount(prices, p -> p * 0.5);
```

```python
# Python:函数直接当参数传,不需要任何接口包装
def apply_discount(prices, discount_fn):     # discount_fn 是个函数对象
    return [discount_fn(p) for p in prices]

apply_discount([100.0, 200.0], lambda p: p * 0.5)   # [50.0, 100.0]
```

> 🟡 **Java 对比**:Java 的「函数」必须是 `Function`/`Consumer`/`Predicate` 等接口的实例,带类型签名;Python 函数没有这个包袱——**任何 def 出来的函数、lambda、甚至内置函数**都能直接传来传去。策略模式、回调在 Python 里轻量到几乎没有存在感。

### 真实场景:运营促销试算(就是作业)

大促前,运营想拿同一份商品价格试两种算法——「全场半价」和「每单减 20(最低 0)」:

```python
def half_off(p):
    return p * 0.5

apply_discount([599.0, 159.0, 75.5], half_off)
# [299.5, 79.5, 37.75]

apply_discount([599.0, 159.0, 75.5], lambda p: max(p - 20, 0))
# [579.0, 139.0, 55.5]
```

换算法 = 换一个函数参数,`apply_discount` 本身一行不用改。这就是「把行为当数据传」。

### ⚠️ 头号坑:带不带括号,天差地别 🔴

```python
apply_discount(prices, half_off)     # ✅ 传的是函数【对象本身】
apply_discount(prices, half_off())   # ❌ TypeError:先调用了它(还没给价格),
                                     #    传进去的是调用结果,不是函数
```

`fn` 是函数对象,`fn()` 是调用它拿返回值。**传参/返回时永远不带括号**。Java 里方法引用 `this::halfOff` 和调用 `this.halfOff()` 的区别,一模一样。

### 函数还能放进容器(了解)

```python
strategies = {"half_off": half_off, "minus_20": lambda p: max(p - 20, 0)}
apply_discount(prices, strategies["half_off"])   # 按名字从 dict 取函数
```

策略表、命令分发、Flask/FastAPI 的路由注册表,本质都是「容器里放函数」。

### lambda 速记(Ch02 见过,这里复习)

- `lambda p: p * 0.5` = 匿名单行函数,**只能写一个表达式**,不能写语句(不能赋值、不能 for)。
- 复杂逻辑老实 `def`,别堆 lambda(可读性差)。本章 lambda 只用来一行算价。

> ✅ **做 `apply_discount` 题**:`return [discount_fn(p) for p in prices]`——记住:`discount_fn` 不带括号是「传它」,带括号才是「调它」,这里要调。

---

## §4.2 闭包(对应:`make_coupon`)🔴

**闭包 = 内层函数 + 它记住的外层变量**。

### 真实场景:发券工厂(就是作业)

运营后台要发两种券:满 200 减 30、满 500 减 80。每种券逻辑一样,只是门槛/减额不同——写一个**工厂函数**批量「印券」:

```python
def make_coupon(threshold, off):        # 外层:印券机,收下这张券的参数
    def coupon(price):                  # 内层:券本身,结算时用
        return price - off if price >= threshold else price
    return coupon                       # 返回券(函数),注意【不调用、不加括号】

coupon_200_30 = make_coupon(200, 30)    # 印一张「满200减30」券
coupon_200_30(599.0)                    # 569.0  (满门槛 → 减)
coupon_200_30(150.0)                    # 150.0  (不够门槛 → 原价)
coupon_200_30(200.0)                    # 170.0  (满门槛含等于)

make_coupon(500, 80)(600.0)             # 520.0  每张券各记各的参数
```

### Java 对照:lambda 捕获

```java
// Java 等价:被捕获的变量必须 effectively final
Function<Double,Double> makeCoupon(double threshold, double off) {
    return price -> price >= threshold ? price - off : price;
}
```

> 🟡 **异同**:两边都是「函数带走了定义时的环境」。Java 要求被捕获变量 effectively final(不能再改);Python 闭包**能读**外层变量,想**改**(重新绑定)要加 `nonlocal` 声明——本章作业不需要改,了解即可。

### 关键理解:变量「延寿」了

`make_coupon(200, 30)` 执行完返回,局部变量 `threshold`/`off` 本该消亡——但内层函数 `coupon` **捕获**了它们,只要这张券还在用,`threshold=200` 就一直活着。**每次调用工厂,造出一个独立闭包**,各记各的,互不干扰——这正是 §4.6 缓存装饰器的地基。

### ⚠️ 坑 1:返回时别加括号

```python
return coupon      # ✅ 返回函数对象(这张券)
return coupon()    # ❌ 立刻调用它——price 还没传,TypeError
```

### ⚠️ 坑 2:循环里印券,闭包共享同一个循环变量(了解)

```python
coupons = [lambda price, t=t: price - t for t in [10, 20, 30]]
```

闭包对循环变量是**晚点绑定**(late binding):不加 `t=t` 的话,三个 lambda 共享同一个 `t`,循环结束后全是 30。默认参数 `t=t` 把当期值「拍下来」。本章作业不在循环里造闭包,见到能认出即可。

> ✅ **做 `make_coupon` 题**:内层 `def coupon(price)` + 门槛判断(`>=`,含等于,测试会查 200 整这个边界)+ `return coupon`(不加括号!)。

---

## §4.3 *args / **kwargs(对应:`cart_total`、`build_response`)🟡

Python 函数能接收**任意数量**的参数,分两组:

| 写法 | 收集什么 | 函数内是什么类型 |
|------|---------|-----------------|
| `*args` | 多余的【位置参数】 | 元组 `tuple` |
| `**kwargs` | 多余的【关键字参数】 | 字典 `dict` |

```java
// Java 对照:只有一种可变参数,本质是数组,且必须放最后
double cartTotal(double... prices) { ... }
```

### 场景一:购物车合计(*args,就是作业)

结算页购物车有几件商品不确定,让函数「来几件收几件」:

```python
def cart_total(*prices):        # 调用 cart_total(599.0, 159.0, 75.5)
    return sum(prices)          # 函数内 prices = (599.0, 159.0, 75.5) 元组

cart_total()                    # 0      一件没有 → 空元组 → sum=0
cart_total(199.0)               # 199.0
cart_total(599.0, 159.0, 75.5)  # 833.5
```

### ⚠️ 坑:手上有列表,直接传会整个塞进第一个位置 🔴

```python
prices = [599.0, 159.0, 75.5]
cart_total(prices)      # ❌ prices 变成 ([599.0, 159.0, 75.5],)——元组里套了个列表!
                        #    sum() 直接 TypeError
cart_total(*prices)     # ✅ 调用处 * 把列表【打散】成一个个位置参数 → 833.5
```

> 🟡 **Java 老手注意**:Java 的 varargs 可以直接传数组(`cartTotal(arr)` 合法),Python 的 `*args` **不行**——列表必须 `*prices` 打散。这是两种可变参数观的根本差异,作业测试会专门验证 `cart_total(*[...])` 的用法。

### 场景二:统一 API 响应体(**kwargs,就是作业)

后端约定:所有接口返回 `{"ok": True, "data": ...}`,再带分页等元信息。元信息字段不确定,用 `**kwargs` 全收:

```python
def build_response(data, **meta):
    return {"ok": True, "data": data, **meta}   # **meta 把字典【解包】铺进字面量

build_response(["机械键盘", "无线鼠标"], total=10, page=1)
# {"ok": True, "data": ["机械键盘", "无线鼠标"], "total": 10, "page": 1}

build_response("pong")          # {"ok": True, "data": "pong"}   meta 为空也合法
```

`**` 解包进字典字面量,就是 Ch02 学的字典合并语法:

```python
meta = {"total": 10, "page": 1}
{"ok": True, **meta}            # {"ok": True, "total": 10, "page": 1}
```

### 完整参数顺序(背骨架)

```python
def f(pos, /, normal, *args, kw_only, **kwargs): ...
#     位置only  普通参数  可变位置  关键字only  可变关键字
```

日常写 `def f(a, b, *args, **kwargs)` 就够。这正是 FastAPI(Ch14+)自动解析查询参数、以及 §4.4 装饰器 wrapper 通用签名的语法地基。

> ✅ **做 `cart_total` 题**:`return sum(prices)`(prices 已是元组,**别再加 \***)。
> ✅ **做 `build_response` 题**:`return {"ok": True, "data": data, **meta}`——meta 要【展开】铺平,不能嵌套成 `{"meta": {...}}`。

---

## §4.4 装饰器基础(对应:`count_calls`、`timer`)🔴

本章核心。**装饰器 = 「接收函数、返回新函数」的函数**。先忘掉 `@`,看手动版本。

### 手动版本:给函数包一层,不改源码

下午的任务:给「价格查询」函数加调用计数,但**不能改它的源码**(别处还在引用)。

```python
def query_price(sku):
    return 599.0

def count_calls(func):                  # 接收一个函数
    def wrapper(*args, **kwargs):       # 包出来的新函数
        wrapper.call_count += 1         # 增强逻辑:计数
        return func(*args, **kwargs)    # 原样转发,拿到真返回值
    wrapper.call_count = 0              # 计数器挂在函数对象上(函数也是对象!)
    return wrapper                      # 返回新函数

query_price = count_calls(query_price)  # ✨ 用包装版替换原函数
query_price("KB-001"); query_price("MS-002")
query_price.call_count                  # 2
```

`count_calls` 收下原函数,返回增强版;最后那行赋值把名字指向包装版。**原函数源码一行没动,行为却被增强了**——这就是 AOP 的思想,纯函数实现。

### `@` 语法糖:上面那句赋值的简写

```python
@count_calls
def query_price(sku):
    return 599.0
```

**完全等价于**:

```python
def query_price(sku):
    return 599.0
query_price = count_calls(query_price)      # ← @ 就是这一句的简写!
```

> 🤯 **记住这张等价关系,装饰器就懂了一半**:`@deco` 贴在 `def f` 上 = `f = deco(f)`。装饰在函数【定义时】执行一次,从此 `f` 这个名字指向包装版。预览猜第 4 题的答案就是它。

### 为什么 wrapper 用 `*args, **kwargs`

包装版要能接住**原函数任意签名**的调用(它不知道自己会包谁),所以 `*args, **kwargs` 全收下,再原样 `func(*args, **kwargs)` 转发——§4.3 刚学的可变参数,在这里是标配。

### `@functools.wraps(func)`:铁律,永远要加 🔴

不加它,装饰后的函数 `__name__` 变成 `"wrapper"`,`__doc__` 也丢了——调试、日志、反射(FastAPI 就靠函数元数据)全乱套:

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

**写装饰器 wrapper,永远先加 `@functools.wraps(func)`**——作业测试会检查 `__name__`。

### 第二个例子:`timer` 记录耗时(就是作业)

同一张骨架,增强逻辑换成「计时」:排查慢接口时给函数包一层,把每次耗时(秒)追加到 `wrapper.records`:

```python
import time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()     # 高精度计时器,专测间隔
        result = func(*args, **kwargs)  # 先存结果
        wrapper.records.append(time.perf_counter() - start)
        return result                   # 原样返回,调用方无感
    wrapper.records = []                # 每次装饰独立一份记录表
    return wrapper

@timer
def query_stock(sku):
    return 120

query_stock("KB-001")                   # 120(返回值不变)
query_stock("MS-002")
len(query_stock.records)                # 2 —— 每次调用一条耗时,单位秒
```

> 🔑 **模式提炼**:计数和计时是同一张骨架——「前:做点事(或记下起点)→ 调真函数 → 后:做点事 → 原样返回」。以后见到任何装饰器,先找「前/后各做了什么」。

> 🟡 **Java 对比**:Java 的 `@Transactional`/`@Cacheable` 注解本身只是元数据,靠 Spring 运行时代理(反射 + 字节码增强)才生效。Python 装饰器是**语言层面的函数变换**,不依赖任何框架——你刚写的 20 行,就是一个微型 Spring AOP。

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 三个典型错误:wrapper 写死参数 / 忘 wraps / 忘初始化属性
def count_calls(func):
    def wrapper(name):              # 包一个两参函数立刻 TypeError
        return func(name)
    return wrapper

# ✅ 标准骨架(建议背下来)
def count_calls(func):
    @functools.wraps(func)          # 保元数据
    def wrapper(*args, **kwargs):   # 通用签名
        wrapper.call_count += 1
        return func(*args, **kwargs)
    wrapper.call_count = 0          # 初始化属性再返回
    return wrapper
```

> ✅ **做 `count_calls` 题**:照标准骨架写,`wrapper.call_count = 0` 初始化别漏。
> ✅ **做 `timer` 题**:同骨架,增强逻辑换成 `perf_counter()` 前后差,append 到 `wrapper.records`(初始化为 `[]`)。

---

## §4.5 带参数的装饰器(对应:`retry`)🔴

`@retry(times=3)`——装饰器自己带参数。这要**三层嵌套**,先背口诀:

> **普通装饰器两层**(`deco(func) → wrapper`);**带参装饰器三层**(`factory(args) → decorator(func) → wrapper`)。

### 真实场景:支付网关抖动,自动重试(就是作业)

调第三方支付网关,网络偶发抖动抛异常。希望:失败自动重试,最多试 3 次;3 次都失败,把**最后一次**异常抛出来交给告警。

```python
def retry(times):                           # 第1层:收参数 times,返回【真正的装饰器】
    def decorator(func):                    # 第2层:收被装饰函数,返回 wrapper
        @functools.wraps(func)
        def wrapper(*args, **kwargs):       # 第3层:实际替换原函数的家伙
            last_exc = None
            for _ in range(times):          # 最多尝试 times 次
                try:
                    return func(*args, **kwargs)   # 成功 → 立刻返回,绝不再试
                except Exception as e:
                    last_exc = e            # 记下异常,进入下一次尝试
            raise last_exc                  # 循环走完 = 全失败 → 抛最后一次异常
        return wrapper
    return decorator

@retry(times=3)
def call_payment_gateway(order_id): ...
```

### 为什么是三层?——再看等价转换(预览猜第 5 题答案)

```python
@retry(times=3)
def f(): ...

# 等价于:
def f(): ...
f = retry(times=3)(f)
#    └──────┬─────┘ └┬┘
#    先调用,得到 decorator   再用 decorator 包 f
```

`@retry(times=3)` 里的 `retry(times=3)` 是**先执行的一次调用**,它必须返回一个装饰器(就是 `decorator`),再用它包 `f`——所以比普通装饰器多一层。每层各管一件事:**外层收参数、中层收函数、内层干活**。

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 只写两层:times 参数无处可放
def retry(func):
    def wrapper(*args, **kwargs):
        ...
    return wrapper

@retry(times=3)     # TypeError: retry() 收到意外的关键字参数 times
def f(): ...

# ✅ 三层:每层各 return 下一层
def retry(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ...
        return wrapper
    return decorator
```

> 🟡 **Java 类比**:你刚写的就是微型版 Spring Retry / Resilience4j 的 `@Retry(maxAttempts=3)`——那边是框架注解+代理,这边是 15 行纯函数。
>
> 🔑 **`raise last_exc` 为什么放循环外**:放循环内第一次失败就抛了,失去重试意义;循环走完才抛,才是「times 次机会都用完了」。测试会验证失败调用次数**恰好**等于 `times`,且抛的是最后一次异常。

> ✅ **做 `retry` 题**:照三层骨架写;`try` 里 `return`,`except` 里记 `last_exc`,循环后 `raise last_exc`。`@functools.wraps(func)` 别漏。

---

## §4.6 缓存装饰器(对应:`memoize`)🟡

把 §4.2 闭包 + §4.4 装饰器合体:**用闭包变量当缓存**。

### 真实场景:外部汇率服务调用很贵(就是作业)

每次算人民币价格都要调外部汇率接口——又慢又按次计费。同一个币种,查过一次就该记住:

```python
def memoize(func):
    cache = {}                              # 闭包变量:每次装饰独立一份

    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:               # args 是元组,天然可当字典键
            wrapper.miss_count += 1         # 真调用才计数(便于验证缓存生效)
            cache[args] = func(*args)       # 没命中 → 真调一次,存结果
        return cache[args]                  # 命中 → 直接给缓存

    wrapper.miss_count = 0
    return wrapper

@memoize
def get_exchange_rate(currency):
    ...                                     # 假设内部是昂贵的网络调用

get_exchange_rate("USD")    # 真调一次,miss_count=1
get_exchange_rate("USD")    # 命中缓存,函数体不再执行,miss_count 仍=1
```

### 为什么 cache 放闭包里?——放错位置的两种灾难 🔴

```python
# ❌ 灾难一:cache 放 wrapper 内部 → 每次调用都新建空字典,永远 miss
def memoize(func):
    def wrapper(*args):
        cache = {}                  # 每次调用都是全新 cache!
        ...

# ❌ 灾难二:cache 放模块级全局 → 所有被装饰函数共用一本账,键互相串
_global_cache = {}                  # get_exchange_rate 和别的函数抢同一个字典

# ✅ cache 放 memoize 的函数体里、wrapper 外面:
#    它是闭包变量,「每次装饰」新建一份——每个被装饰函数有自己的缓存,
#    且随函数一起活着(§4.2 的「变量延寿」)
```

这正是闭包的实战价值:`@memoize` 装饰 10 个函数,就有 10 本互不干扰的缓存。测试会专门验证这一点。

### `args` 为什么能直接当键

`wrapper(*args)` 收到的 `args` 是**元组**(§4.3),元组可哈希,天然是字典键。本作业只处理位置参数;关键字参数要一并做键需额外处理——

> 🟡 **实战**:标准库 `functools.lru_cache` 是完善版(支持 kwargs、LRU 容量上限、线程安全、命中率统计),Ch09 细讲。本题要求**手写**——理解原理后,你才有底气用现成的。

> ✅ **做 `memoize` 题**:`cache = {}` 放闭包位 → `wrapper(*args)` 里 `if args not in cache:` 才 `miss_count += 1` 并真调 → 返回 `cache[args]`;`wrapper.miss_count = 0` 和 `@functools.wraps` 别漏。

---

## ⚠️ Java 老手常踩的坑(本章汇总)

1. **传函数带了括号**:`apply_discount(ps, fn())` 是先调用再传结果;传函数对象永远 `fn` 不带括号。(§4.1)
2. **闭包返回内层函数时加括号**:`return coupon` 是返回券,`return coupon()` 是当场用券(还没给价格)。(§4.2)
3. **列表直接喂给 \*args**:`cart_total(prices)` 会把整个 list 当成一件商品价格;要 `cart_total(*prices)` 打散。(§4.3)
4. **wrapper 忘加 `@functools.wraps(func)`**:装饰后 `__name__` 变 `"wrapper"`,调试/反射/FastAPI 全乱。(§4.4)
5. **带参装饰器只写两层**:`@retry(times=3)` 需要先调一层拿装饰器,三层缺一不可。(§4.5)
6. **cache 放错位置**:放 wrapper 内每次新建(永远 miss);放模块级全局(各函数串账);放装饰器函数体里做闭包变量才对。(§4.6)
7. **闭包里想改外层变量要 `nonlocal`**:只读不用;本章用「函数属性」(`wrapper.call_count`)规避了重新绑定。(§4.2/§4.4)

---

## 📝 本章作业(8 个函数,营销 + 稳定性两条主线)

打开 **`ch04_assignment.py`**,每题 docstring 里标了【对应小节】,卡住回查:

| 函数 | 场景 | 知识点 | 难度 |
|------|------|--------|------|
| `apply_discount` | 促销试算:换算法不换代码 | 函数当参数 | 🟢 |
| `make_coupon` | 发券工厂:满减券 | 闭包 | 🟡 |
| `cart_total` | 购物车结算合计 | *args | 🟢 |
| `build_response` | 统一 API 响应体 | **kwargs | 🟢 |
| `count_calls` | 监控埋点:调用计数 | 装饰器基础 | 🟡 |
| `timer` | 慢接口排查:记录耗时 | 装饰器基础 | 🟡 |
| `retry` | 支付网关抖动自动重试 | 带参装饰器 | 🔴 |
| `memoize` | 汇率查询结果缓存 | 缓存装饰器(综合) | 🟡 |

```bash
uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v
```

全绿 = 掌握 Ch04。装饰器题卡了 → 先默写「`@deco` = `f = deco(f)`」,再回对应 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清 `fn` 和 `fn()` 的区别,并举一个「把行为当参数传」的业务场景(§4.1)
- [ ] 能解释闭包为什么让外层变量「延寿」,和 Java lambda 捕获有何异同(§4.2)
- [ ] 知道 `*args`/`**kwargs` 在函数内的类型,会在调用处用 `*`/`**` 打散(§4.3)
- [ ] 能默写「`@deco` 贴在 def 上 = 哪一句赋值」,并说清装饰在何时执行(§4.4)
- [ ] 知道 wrapper 为什么必须 `*args, **kwargs` + `@functools.wraps`(§4.4)
- [ ] 能说出带参装饰器为什么是三层、每层 return 什么(§4.5)
- [ ] 能解释 memoize 的 cache 为什么放闭包位,放 wrapper 内/全局各有什么后果(§4.6)
- [ ] 8 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。**讲不清 = 没懂**,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「装饰器到底是什么?`@count_calls` 这一行等价于什么?为什么它不用 Spring 就能实现 AOP?」— 卡壳重读 §4.4
2. 「为什么带参数的装饰器要写三层?每层各 return 什么?」— 卡壳重读 §4.5
3. 「闭包为什么能记住外层已经返回的变量?memoize 的缓存为什么非要放闭包里?」— 卡壳重读 §4.2/§4.6

✅ 自检:不查资料、不堆术语,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch04 掌握后,进 **Ch05 · OOP:魔术方法、继承、dataclass**——理解 Python OOP 和 Java 的本质区别(没有重载、有多继承、靠魔术方法重载运算符),你会手写一个支持 `+`/`len()`/`in` 的 `ShoppingCart`。装饰器不会消失:`@property`、`@classmethod`、`@dataclass` 全是本章知识的直接应用。
