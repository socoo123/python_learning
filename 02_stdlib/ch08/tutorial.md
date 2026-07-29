# Ch08 · collections:Counter / defaultdict / deque / namedtuple

> **预计**:0.5 天 ｜ **前置**:M1 ｜ **M2 第一章**
> **目标**:掌握 Python「自带电池」里最常用的四个容器工具。它们都是你 Java 里熟悉概念的**极简版**——Java 要手写十几行的计数/分组/双端队列,Python 一行搞定。运维、数据分析、刷题都高频。

> 📐 **本教程的契约**:下面每一节(§8.1–§8.5)都**精确对应**作业里的一个任务,全部围绕「访问日志分析」实战。讲过的才考,考的必讲过。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 用 `Counter` 一行完成计数、Top-N(= Java 手写 Map 循环)
- 用 `defaultdict` 一行完成分组(= Java `computeIfAbsent`)
- 用 `deque` 做双端队列和滚动窗口(= Java `ArrayDeque`)
- 用 `namedtuple` 定义轻量不可变对象(= Java `record`)

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `count_by_status` | §8.1 | Counter 创建 + 计数 |
| `top_ips` | §8.2 | Counter.most_common(Top-N) |
| `group_by_status` | §8.3 | defaultdict 分组 |
| `recent_paths` | §8.4 | deque(maxlen) 滚动窗口 |
| `AccessLog` / `to_namedtuple` | §8.5 | namedtuple |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 先猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch08_assignment.py`,先试着写 | assignment |
| ③ 提取+反馈 | 写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 讲清"Counter/defaultdict 各替代了 Java 什么" | 本页 ④ |
| ⑤ 存闪卡 | 标 [`review.md`](./review.md) 复习日期 | review.md |

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java 数一组词的频率要 `Map<String,Integer> + getOrDefault + 循环`。Python 一个类叫什么,几行搞定?
2. Java 按 key 分组要 `computeIfAbsent(k, k -> new ArrayList<>())`。Python 有没有更短的?
3. Java 用 `ArrayList` 当队列,`remove(0)` 是 O(n)。Python 哪个类 `popleft` 是 O(1)?
4. Java 14+ 用 `record Point(int x, int y)` 定义不可变值对象。Python 标准库里等价的是什么?
5. 想取「出现次数最多的前 3 个」,Java 要排序+截断,Python 一个方法叫什么?

> 猜完,带着验证心态进入正文。

---

## §8.1 Counter:计数器(对应:`count_by_status`)🟢

`Counter` 是「自动计数的 dict」。给它任意可迭代对象,它数每个元素出现几次。

```python
from collections import Counter

Counter("aabbbc")               # Counter({'b': 3, 'a': 2, 'c': 1})
Counter([200, 200, 404, 500])   # Counter({200: 2, 404: 1, 500: 1})
Counter(log["status"] for log in logs)   # 数每个状态码 —— 本节作业
```

### 取值:不存在的键返回 0(不抛 KeyError)

```python
c = Counter([200, 200, 404])
c[200]      # 2
c[999]      # 0   ← 关键!普通 dict 会 KeyError,Counter 返回 0
```

> 🟡 **Java 对比**:Java 要 `map.getOrDefault(k, 0)` 每次写一遍;Python 的 Counter 天生如此。这让计数代码极干净。

### 还支持算术

```python
Counter(a=2, b=1) + Counter(a=1, c=3)   # Counter({'a': 3, 'c': 3, 'b': 1})  加
Counter(a=3) - Counter(a=1)             # Counter({'a': 2})                    减
```

> ✅ 做 `count_by_status` 题:`Counter(log["status"] for log in logs)`。

---

## §8.2 Counter 进阶:most_common(对应:`top_ips`)🟢

`most_common(n)` 返回出现最多的前 n 个 `(元素, 次数)`,降序。**Top-N 一行搞定**(运维/排行榜高频)。

```python
c = Counter(log["ip"] for log in logs)
c.most_common(3)
# [("192.168.1.1", 5), ("10.0.0.5", 3), ("172.16.0.3", 2)]

c.most_common()     # 不传 n → 全部,按次数降序
c.most_common(1)[0] # ("192.168.1.1", 5) —— 取冠军
```

### Java 等价(对比一下有多啰嗦)

```java
// Java:统计 + Top3
Map<String,Long> counts = logs.stream()
    .collect(Collectors.groupingBy(Log::getIp, Collectors.counting()));
List<String> top3 = counts.entrySet().stream()
    .sorted(Map.Entry.<String,Long>comparingByValue().reversed())
    .limit(3).map(Map.Entry::getKey).toList();
```
```python
# Python:一行
top3 = Counter(log["ip"] for log in logs).most_common(3)
```

> 🤯 这就是 Python 在数据处理上的「降维打击」。Java 老手学会 Counter 后会到处想用。

> ✅ 做 `top_ips` 题:`Counter(log["ip"] for log in logs).most_common(n)`。

---

## §8.3 defaultdict:带默认值的 dict(对应:`group_by_status`)🟡

分组是高频场景:把一堆东西按某 key 归类。普通 dict 第一次遇到新 key 会 KeyError,要先判断。

```python
# ❌ 普通 dict:每次要判断 key 在不在
groups = {}
for log in logs:
    if log["status"] not in groups:      # 啰嗦
        groups[log["status"]] = []
    groups[log["status"]].append(log)

# ✅ defaultdict(list):key 不存在时自动建空 list
from collections import defaultdict
groups = defaultdict(list)               # 工厂 = list(即 [])
for log in logs:
    groups[log["status"]].append(log)    # 新 status 自动建 [],直接 append
```

### `defaultdict(工厂)` 的工厂是什么

`defaultdict(list)` 里的 `list` 是个**工厂函数**——遇到不存在的键时,调用 `list()` 造个空 list 当默认值。同理:

```python
defaultdict(int)         # 默认 0(常用于计数:int() == 0)
defaultdict(set)         # 默认空 set
defaultdict(dict)        # 默认空 dict
```

> 🟡 **Java 对比**:`defaultdict(list)` ≈ `computeIfAbsent(k, k -> new ArrayList<>())`,但写在声明处一次,后面每次访问都自动,不用重复写。这正是 Ch02 `group_by_category` 用 `setdefault` 的升级版(更优雅)。

> ✅ 做 `group_by_status` 题:`defaultdict(list)` + 遍历 append,最后 `dict(groups)` 转回普通 dict。

---

## §8.4 deque:双端队列 + maxlen(对应:`recent_paths`)🟡

`deque`(发音 "deck",double-ended queue)两头都能 O(1) 增删。解决 `list.pop(0)` 的性能问题:

```python
from collections import deque

d = deque([1, 2, 3])
d.appendleft(0)     # 左侧入队 O(1)   → deque([0,1,2,3])
d.append(4)         # 右侧入队 O(1)   → deque([0,1,2,3,4])
d.popleft()         # 左侧出队 O(1)   → 0  (list.pop(0) 是 O(n)!)
d.pop()             # 右侧出队 O(1)
```

> 🟡 **Java 对比**:= `ArrayDeque`。Python 的 `list` 当队列用 `pop(0)` 是 **O(n)**(要整体搬移),数据量大时很慢;`deque.popleft()` 是 O(1)。

### 杀手锏:`maxlen` 定长队列(滚动窗口)

```python
recent = deque(maxlen=3)         # 最多容纳 3 个,满了再 append 会【挤掉最旧的】
for x in [1, 2, 3, 4, 5]:
    recent.append(x)
# 遍历完后 recent == deque([3, 4, 5])  —— 自动只保留最后 3 个!
list(recent)                      # [3, 4, 5]
```

这就是本节作业 `recent_paths` 的精髓:**用 `deque(maxlen=n)` 自动保留最近 n 条**,不用手动管理。日志/聊天记录/最近访问的「滚动窗口」场景神器。

> ✅ 做 `recent_paths` 题:`deque(maxlen=n)` + 遍历 append + `list(recent)`。

---

## §8.5 namedtuple:轻量不可变对象(对应:`AccessLog`)🟡

`namedtuple` 给元组加「字段名」,既不可变又能按名字访问——= Java `record` 的轻量版。

```python
from collections import namedtuple

# 定义(一行,类似 Java record)
AccessLog = namedtuple("AccessLog", ["ip", "method", "path", "status"])
# 也可用空格分隔的字符串:namedtuple("AccessLog", "ip method path status")

# 创建
log = AccessLog(ip="1.2.3.4", method="GET", path="/", status=200)

# 按字段名访问(可读!)
log.ip            # "1.2.3.4"
log.status        # 200

# 也支持索引(它本质还是 tuple)
log[0]            # "1.2.3.4"

# 不可变
log.ip = "x"      # ❌ AttributeError
```

### dict → namedtuple(本节作业 `to_namedtuple`)

```python
d = {"ip": "1.2.3.4", "method": "GET", "path": "/", "status": 200}
log = AccessLog(**d)        # ** 把 dict 解包成关键字参数
log.path                    # "/"
```

### 什么时候用 namedtuple?

- 想要**不可变**的值对象(坐标、配置、日志记录)
- 嫌定义 `class` 太重,又嫌 `dict` 访问 `d["ip"]` 不如 `log.ip` 可读
- 需要**当字典键**或放进 set(不可变 → 可哈希)

> 🟡 **Java 对比**:= `record AccessLog(String ip, String method, ...) {}`(Java 14+)。Python 还有个更现代的 `typing.NamedTuple`(支持类型注解)和 `@dataclass(frozen=True)`(Ch05 讲过),后两者功能更全。namedtuple 最轻量。

> ✅ 做 `AccessLog`/`to_namedtuple` 题:`namedtuple("AccessLog", [...])` 定义;`AccessLog(**d)` 转换。

---

## §8.6 ChainMap / OrderedDict(了解,本章不考)

- **`ChainMap`**:把多个 dict「叠」起来查询,先查第一个,没有再查下一个。常用于**配置层叠**(默认配置 ← 用户配置 ← 命令行参数)。
- **`OrderedDict`**:保持插入顺序的 dict。但 Python 3.7+ 普通 `dict` 已经保证有序,所以 `OrderedDict` 现在很少用(主要在需要 `move_to_end` 等额外功能时)。

知道有这两个工具即可,日常 90% 用 Counter/defaultdict/deque/namedtuple。

---

## §8.7 Java 老手常踩的坑 ⚠️

1. **用 `list` 当队列**:`list.pop(0)` 是 O(n)!队列用 `deque.popleft()`。
2. **Counter 不存在的键返回 0**:这是特性不是 bug,但别和普通 dict 混(普通 dict 会 KeyError)。
3. **`most_common` 返回元组列表**:`[("ip", 5), ...]`,不是 dict。要只拿元素用 `[k for k,_ in c.most_common(n)]`。
4. **`defaultdict` 的默认值是「调用工厂」**:写 `defaultdict(list)` 不是 `defaultdict([])`(后者是固定同一个 list,所有键共享——又是 Ch02 那个可变默认坑)。
5. **namedtuple 不可变**:想改字段会报错;要"改"得用 `log._replace(ip="x")` 返回新实例。

---

## 📝 本章作业

打开 **`ch08_assignment.py`**,5 个任务,围绕 `access_logs.json`(20 条访问记录)。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `count_by_status` | Counter 计数 | 🟢 |
| `top_ips` | Counter.most_common | 🟢 |
| `group_by_status` | defaultdict 分组 | 🟡 |
| `recent_paths` | deque(maxlen) 滚动窗口 | 🟡 |
| `AccessLog` / `to_namedtuple` | namedtuple | 🟡 |

```bash
uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v
```
全绿 = 掌握 Ch08。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「Counter 替代了 Java 的什么?为何 `c[不存在的键]` 返回 0」(§8.1)
- [ ] 能用 `defaultdict(list)` 一行写分组,并解释它比 `setdefault` 好在哪(§8.3)
- [ ] 知道为什么队列要用 `deque` 而不是 `list`(`pop(0)` 的 O(n) 问题)(§8.4)
- [ ] 能解释 `deque(maxlen=n)` 怎么实现滚动窗口(§8.4)
- [ ] 5 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Counter 到底替代了 Java 哪些样板代码?most_common 比手写排序好在哪?」— 卡壳重读 §8.1/§8.2
2. 「defaultdict(list) 为什么能自动建空列表?它和 Ch02 的 setdefault 有什么区别?」— 卡壳重读 §8.3
3. 「为什么用 deque 而不是 list 当队列?maxlen 怎么实现滚动窗口?」— 卡壳重读 §8.4

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch08 掌握后,进 **Ch09 · itertools + functools**——函数式利器。`groupby`/`chain`/`combinations`/`lru_cache`/`partial`,刷题和数据处理的神器,对比 Java Stream 但更强大。
