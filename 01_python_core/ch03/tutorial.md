# Ch03 · 控制流、迭代器、生成器、推导式

> **预计**:1 天 ｜ **前置**:Ch02
> **目标**:掌握 Python 效率的核心——**推导式**、**for-else**、**生成器 `yield`**、**迭代器**。这些是 Python 相对 Java 最"顺手"的地方,也是运维/AI 章节的基础(流式处理大日志、流式读 LLM token)。

> 📐 **本教程的契约**:下面每一节(§3.1–§3.5)都**精确对应**作业里的一道题。讲过的才考,考的必讲过。卡住时,按作业题号回查对应小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 用**列表推导式**(带条件/带变换)替代 for+append,写出声明式代码
- 解释 `for-else` 的语义(Java 完全没有),用素数判断展示它
- 用 `enumerate` 拿「带序号的遍历」,用 `zip` 并行配对两个序列
- 用 `yield` 写**生成器**,理解惰性求值为什么能处理 GB 级文件
- 理解**迭代器协议**(`__iter__`/`__next__`),知道迭代器「只能遍历一次」

**作业 ↔ 教程对应表**:

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `cheap_product_names` | §3.1 | 列表推导式(带条件) |
| `is_prime` | §3.2 | for-else |
| `indexed_summary` | §3.3 | enumerate |
| `names_and_prices_zipped` | §3.3 | zip |
| `iter_error_lines` | §3.4 | 生成器 yield |
| `top_n_by_price` | §3.5 | 迭代器消费 |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 看下面的差异,先猜 Python 怎么实现 | 本页 ① |
| ② 先动手 | 打开 `ch03_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"yield 到底做了什么""for-else 何时执行" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性**:先扫 ① 猜一猜 → 跳去 ② 写作业 → 哪题卡了回对应 § 查 → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java 取 list 元素+索引要 `for (int i=0; i<list.size(); i++)` 或 `IntStream.range`。Python 一个函数怎么拿到「索引+元素」?
2. Java 判断素数,循环找因子,要一个 `boolean found` 标志变量再判断。Python 有个 `for-else`,能省掉这个标志,怎么写?
3. Java 要并行遍历两个等长 list 得自己控制索引。Python 一个函数叫什么?
4. Java 读 10GB 日志一次性 `Files.readAllLines` 会 OOM。Python 用什么关键字写一个「逐行产出」的函数,永远不爆内存?
5. Java 的 `Iterator` 用完能再用吗?Python 的迭代器呢?

> 猜完,带着验证心态进入正文。

---

## §3.1 列表推导式(对应:`cheap_product_names`)🟡

Ch01/Ch02 你已经用过列表推导式的基础形式。这里正式讲透。

### 语法骨架

```python
[表达式 for 变量 in 可迭代对象 if 条件]
```

读作:「对序列里**每个**元素,若满足**条件**,算出**表达式**,收集成列表」。三部分:**变换表达式**、**循环**、**过滤条件**(可选)。

```python
# 1. 纯变换
[n * 2 for n in [1, 2, 3]]              # [2, 4, 6]

# 2. 变换 + 过滤
[n for n in range(10) if n % 2 == 0]    # [0, 2, 4, 6, 8]

# 3. 过滤 + 取字段(本节作业这种)
[p["name"] for p in products if p["price"] < 200]
```

### 等价的传统写法(帮你建立直觉)

```python
result = []
for p in products:
    if p["price"] < 200:        # ← 同一个 if
        result.append(p["name"]) # ← 同一个表达式
```

推导式就是把这三行压成一行,**顺序完全一致**(表达式 → for → if)。

> 🟡 **Java 对比**:等价于 `products.stream().filter(p -> p.price < 200).map(p -> p.name).toList()`。Python 的推导式是**命令式的语法糖**(看得见循环),Java Stream 是**声明式的流水线**(看不见循环)。

### 为什么用推导式

- **短**:3 行变 1 行,Python 社区推崇(Pythonic)。
- **快**:推导式在 CPython 里比 for+append 快约 30%(专用字节码,不每次查 `append` 属性)。
- **可读**:熟悉后一眼看出「过滤+变换」意图。

### 同理:字典推导 / 集合推导

把外层括号换掉,语法一致(Ch02 已用):
```python
{p["name"]: p["price"] for p in products}   # 字典推导 → dict
{p["category"] for p in products}           # 集合推导 → set(自动去重)
```

### 坑:别嵌套太深

```python
# 一层、两层 OK
[x for row in matrix for x in row]          # 拍平二维列表(勉强可读)

# 三层以上 → 难读,老实写 for 循环
```

> ✅ 做 `cheap_product_names` 题:`[p["name"] for p in products if p["price"] < max_price]`。注意是比较 `<`(严格小于),边界值 `max_price` 本身不算。

---

## §3.2 for-else(对应:`is_prime`)🔴

这是 **Java 完全没有**的语法,面试常考,但实际项目用得不多——理解语义即可。

### 语义(一句话)

> `for ... else:` 的 **else 在循环【没有被 `break` 提前终止】时执行**。循环正常跑完(或一次都没进),才走 else。

```python
for i in range(5):
    if i == 3:
        break          # 提前跳出 → else 【不执行】
else:
    print("正常结束")  # 不会打印

for i in range(5):
    if i == 99:
        break          # 永远不会 break → 循环正常跑完
else:
    print("正常结束")  # ✅ 会打印
```

> 🤯 **Java 老手震惊点**:`else` 在这里和 `if` 毫无关系!它更像「`nobreak`」「`completed`」。名字起得差是 Python 公认的历史包袱,但既来之则安之。

### 经典应用:素数判断(本节作业)

不用 for-else,Java 思路要一个标志变量:
```python
# ❌ Java 风格:用 flag
def is_prime(n):
    if n < 2:
        return False
    has_factor = False
    for i in range(2, n):
        if n % i == 0:
            has_factor = True
            break
    return not has_factor
```

用 for-else,**省掉 flag**:
```python
# ✅ Pythonic:for-else
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False   # 找到因子 → 立即返回(相当于 break 出循环)
    else:
        return True        # 循环一个因子都没找到 → 正常结束 → 走 else → 是素数
```

**关键理解**:`return False` 会让函数直接结束(循环也终止了),所以不会进 else;只有循环**完整跑完没提前退出**,才进 else 返回 True。

> 边界 `is_prime(2)`:`range(2, 2)` 是**空的**,循环一次都不执行,视为「正常结束」→ 走 else → 返回 True。✓(2 是最小素数)

### 什么时候 else 真的「非用不可」

for-else 的价值在:循环外需要知道「中途有没有 break」,而**不想引入 flag 变量**。搜索类场景最典型。但说实话,大多数情况 `return` 或 `any()/all()` 更清晰。记住语义即可,不必强行用。

> ✅ 做 `is_prime` 题:见上面的 Pythonic 版本。

---

## §3.3 enumerate / zip(对应:`indexed_summary`、`names_and_prices_zipped`)🟡

这两个内置函数是 Python 遍历的两大神器,Java 老手会立刻爱上。

### enumerate:遍历时同时拿「索引 + 元素」

```java
// Java:拿索引很啰嗦
for (int i = 0; i < list.size(); i++) {
    System.out.println(i + ": " + list.get(i));
}
// 或
IntStream.range(0, list.size()).forEach(i -> ...);
```

```python
# Python:enumerate 一行
for i, name in enumerate(["a", "b", "c"]):
    print(i, name)       # 0 a / 1 b / 2 c

# 序号从 1 开始(本节作业要这个)
for i, name in enumerate(["a", "b", "c"], start=1):
    print(i, name)       # 1 a / 2 b / 3 c
```

`enumerate(序列, start)` 返回 `(序号, 元素)` 对。`start` 默认 0。

> 🟡 **Java 对比**:没有直接等价物,最接近的是 `IntStream.range(0,n).mapToObj(i -> ...)`,啰嗦。enumerate 是 Python 的日常。

**本节作业 `indexed_summary`** 就是 `enumerate(products, 1)` + 列表推导式 + f-string:
```python
[f"{i}. {p['name']} (¥{p['price']})" for i, p in enumerate(products, 1)]
```

### zip:并行配对多个序列

把 N 个等长序列「拉链式」配对成元组:

```python
names  = ["键盘", "鼠标", "显示器"]
prices = [599, 159, 2199]

list(zip(names, prices))
# [("键盘", 599), ("鼠标", 159), ("显示器", 2199)]
```

```java
// Java:没有内置 zip,要自己控制索引或用 Stream
for (int i = 0; i < names.size(); i++) {
    pair(names.get(i), prices.get(i));
}
```

### 坑:zip 按最短的截断

```python
list(zip([1, 2, 3], ["a", "b"]))     # [(1,'a'), (2,'b')] —— 第三个 3 被丢掉!
list(zip_longest([1,2,3], ["a","b"])) # 需 itertools.zip_longest 才补 None
```

> `zip` 返回的是**迭代器**(不是列表),所以通常包一层 `list(...)` 物化。这点和 §3.5 迭代器相关。

> ✅ 做 `names_and_prices_zipped` 题:先两个列表推导式抽出 `names` 和 `prices`,再 `list(zip(names, prices))`。

---

## §3.4 生成器 yield(对应:`iter_error_lines`)🔴

这是本章**最重要、最 Pythonic**的概念,也是 Java 和 Python 差异最大的地方之一。请慢慢读。

### 问题:10GB 日志怎么处理?

```python
# ❌ 一次性读进内存 → 10GB 日志直接 OOM
all_lines = open("huge.log").readlines()
errors = [line for line in all_lines if "ERROR" in line]

# ✅ 生成器:逐行产出,内存恒定(几十 KB)
def iter_error_lines(lines):
    for line in lines:
        if "ERROR" in line:
            yield line           # ← 产出这一行,暂停;下次被要时再继续
```

### yield 到底做了什么?

普通函数:从头跑到尾,`return` 一次就结束。
**生成器函数**(函数体里出现 `yield`):变成一台「**可暂停的机器**」。

```python
def iter_error_lines(lines):
    for line in lines:
        if "ERROR" in line:
            yield line          # ① 产出值 ② 在这里【冻结】,保留所有局部变量

gen = iter_error_lines(["INFO a", "ERROR boom", "ERROR crash"])
# 注意:调用函数【不会执行函数体】,只是造了一台机器(生成器对象)

next(gen)   # → "ERROR boom"  (机器运转到第一个 yield,产出并冻结)
next(gen)   # → "ERROR crash"  (从冻结处复苏,转到下一个 yield)
next(gen)   # → StopIteration   (没得产了,机器停转)
```

**三个关键点**:
1. **定义生成器函数**(有 yield)≠ **运行它**。`gen = iter_error_lines(...)` 只是造机器,一行都没跑。
2. **`next(gen)` 才驱动机器**运转到下一个 yield 并产出值。
3. **惰性**:要一个产一个,不提前把所有结果算出来。所以能处理无限/超大数据。

### 实际怎么用?(很少手写 next)

日常我们用 `for` 或 `list()` 消费生成器,Python 自动调 `next`:
```python
for line in iter_error_lines(lines):   # for 自动 next,直到 StopIteration
    print(line)

list(iter_error_lines(lines))          # 一次性把所有产出物化成列表
```

> 🟡 **Java 对比**:Java 最接近的是 `Stream`(惰性)或 `Iterator`(命令式)。但 Python 生成器用**普通的 for + yield** 写,比 Java 的 Spliterator/Stream.Builder 简单得多。Java 21 的虚拟线程 + `Stream.generate` 思路类似,但语法远不如 yield 直观。

### 为什么生成器省内存

```
列表版本:   读 1000 万行 → 内存里存 1000 万行 → 过滤 → 还是巨大
生成器版本: 读 1 行 → 判断 → 是 ERROR 就 yield 出去 → 内存里始终只有 1 行
```

数据像水流过管道,不蓄水。这正是 Ch26(大日志流式分析)和 Ch33(LLM 流式 token)的基础。

> ✅ 做 `iter_error_lines` 题:`for line in lines: if "ERROR" in line: yield line`。注意是 **yield 不是 return**(return 会直接结束函数,只能返回一个值)。

---

## §3.5 迭代器协议与消费(对应:`top_n_by_price`)🔴

生成器是「迭代器」的一种。这里讲清楚**迭代器**这个底层概念。

### 两个概念:可迭代对象 vs 迭代器

- **可迭代对象(Iterable)**:能被 `for` 遍历的东西。`list`、`dict`、`str`、`range`、生成器都是。= Java 的 `Iterable`。
- **迭代器(Iterator)**:实际执行遍历的「游标对象」,有 `__next__()` 方法。= Java 的 `Iterator`。

```python
nums = [1, 2, 3]          # 可迭代对象(list)
it = iter(nums)           # iter() 从可迭代对象造一个迭代器(游标指向开头)
next(it)                  # 1   游标前进
next(it)                  # 2
next(it)                  # 3
next(it)                  # StopIteration(到头了)
```

> 🟡 **Java 对比**:`iter(x)` ≈ `x.iterator()`,`next(it)` ≈ `it.next()`,`StopIteration` ≈ `hasNext()` 返回 false。Python 用「抛异常」表示到头,Java 用 `hasNext()` 预先问。

### 关键性质:迭代器【只能遍历一次】

```python
it = iter([1, 2, 3])
list(it)                  # [1, 2, 3]  ← 游标走到底
list(it)                  # []         ← 已经空了!游标不会回退
```

这是和 list 最大的区别:list 能反复遍历,迭代器用完即弃。生成器也是迭代器,同样只能消费一次。

### 本节作业:`top_n_by_price` 消费迭代器

输入是一个迭代器/生成器(模拟流式来源)。要排序就得先拿到全部——但迭代器只能往前走,怎么办?

**答案:用 `list(iterable)` 把迭代器【一次性物化】成列表**(游标从头走到尾,收集所有元素),之后就能反复用、能排序:
```python
def top_n_by_price(product_iter, n=3):
    products = list(product_iter)                              # 物化(耗尽迭代器)
    top = sorted(products, key=lambda p: p["price"], reverse=True)[:n]
    return [p["name"] for p in top]
```

> 注意:调用后,原本的 `product_iter` 就空了(test 里有专门验证这一点)。

### 你已经一直在用迭代器

`zip`、`map`、`filter`、`range`(3.x)、生成器,返回的都是迭代器。Python 里「迭代」是统一的协议,这章的所有函数本质上都在玩这套协议。

> ✅ 做 `top_n_by_price` 题:见上。

---

## §3.6 更多迭代工具(了解,本章不考)

这些本章不出题,但后面章节会用到,先混个眼熟:

```python
# map:对每个元素套一个函数(= 推导式的函数版)
list(map(str.upper, ["a", "b"]))        # ["A", "B"]

# filter:按条件过滤(= 推导式的 if 版)
list(filter(None, [0, 1, "", 2]))       # [1, 2](去掉 falsy)

# 星号解包:收/散 多个元素
first, *rest = [1, 2, 3, 4]             # first=1, rest=[2,3,4]
print(*[1, 2, 3])                        # 等价 print(1, 2, 3)

# 生成器表达式:把列表推导式的 [] 换成 () → 惰性版
(x * 2 for x in range(10))              # 生成器,不占内存
sum(x for x in range(100))              # 直接传给 sum,无需 list()
```

> 实战中,列表推导式通常比 `map`/`filter` 更 Pythonic(可读性好)。但 `sum()`/`max()` 这些函数接受生成器表达式,很常用。

---

## §3.7 Java 老手常踩的坑 ⚠️

1. **`zip` 截断到最短**:不等长会丢数据,要 `itertools.zip_longest`。
2. **迭代器只能用一次**:用完记得重新 `iter()` 或重新生成;`list(it)` 物化后可反复用。
3. **生成器函数调用时不执行**:`gen = f()` 只是造机器,要 `next(gen)` 或 `for/list` 才运转。Java 老手常以为调用就跑了。
4. **`yield` vs `return`**:yield 是「暂停并产出」,return 是「彻底结束」。生成器里写 return 会提前终止生成器。
5. **推导式别过度**:超过两层嵌套、带复杂条件,就老实写 for 循环。

---

## 📝 本章作业

打开 **`ch03_assignment.py`**,6 个函数。每题顶部标了【对应小节】,卡住回查。

| 函数 | 知识点 | 难度 |
|------|--------|------|
| `cheap_product_names` | 列表推导式(带条件) | 🟢 |
| `indexed_summary` | enumerate + f-string | 🟢 |
| `names_and_prices_zipped` | zip | 🟢 |
| `is_prime` | for-else | 🟡 |
| `iter_error_lines` | 生成器 yield | 🟡 |
| `top_n_by_price` | 迭代器消费(综合) | 🟡 |

```bash
uv run pytest 01_python_core/ch03/test_ch03_assignment.py -v
```
全绿 = 掌握 Ch03。哪题卡 → 回对应 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「yield 让函数变成什么?调用生成器函数时发生了什么?」(§3.4)
- [ ] 能解释 for-else 的 else 什么时候执行,为什么名字起得烂(§3.2)
- [ ] 知道迭代器只能遍历一次,`list(it)` 物化后才能反复用(§3.5)
- [ ] 会用 `enumerate(seq, 1)` 让序号从 1 开始(§3.3)
- [ ] 6 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「`yield` 到底干了什么?为什么生成器能处理 10GB 文件而不爆内存?」— 卡壳重读 §3.4
2. 「for-else 的 else 什么时候执行?它和 if-else 的 else 是一回事吗?」— 卡壳重读 §3.2
3. 「为什么迭代器只能遍历一次?`list(iter(...))` 之后原迭代器怎么了?」— 卡壳重读 §3.5

✅ 自检:不查资料、不堆术语,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch03 掌握后,进 **Ch04 · 函数:一等公民、闭包、装饰器**——Python 最强大的特性之一(装饰器 = Java 注解 + AOP 的进阶版),你会手写 `@timer`、`@retry`、`@cached`。
