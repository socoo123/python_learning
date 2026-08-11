# Ch08 · collections:Counter / defaultdict / deque / namedtuple

> **预计**:0.5 天 ｜ **前置**:M1 ｜ **M2 第一章**
> **目标**:掌握 Python「自带电池」里最常用的四个容器工具。它们都是你 Java 里熟悉概念的**极简版**——Java 要手写十几行的计数/分组/队列/值对象,Python 一行搞定。运维、数据分析、刷题都高频。
> 本章主线:你是电商平台的值班运维,要基于 `assets/mock_data/access_logs.json`(20 条访问记录)写一份**访问日报**:状态码分布 → Top IP → 和昨日对比恶化指标 → 按状态码分组排查 → 各接口独立访客数(UV)→ 最近 N 条请求 → 最新错误栈 → 结构化日志记录 → 汇总成日报 dict。

> 📐 **本教程的契约**:下面每一节(§8.1–§8.9)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 用 `Counter` 一行完成计数(= Java `Map + getOrDefault` 循环),缺键自动返回 0
- 用 `most_common(n)` 一行取 Top-N(= Java 排序 + limit),说清并列时谁排前面
- 用 `Counter` 加减法做「今日 vs 昨日」对比,说清减法为什么**丢弃 ≤0 的键**
- 用 `defaultdict(list)` 分组、`defaultdict(set)` 去重计数(= Java `computeIfAbsent`)
- 用 `deque(maxlen=n)` 做滚动窗口、`appendleft` 做「最新在前」栈(= Java `ArrayDeque`)
- 用 `namedtuple` 定义轻量不可变记录(= Java `record`),`**` 解包 dict 秒转对象

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `count_by_status` | §8.1 | Counter 创建 / 计数 / 缺键返 0 |
| `top_ips` | §8.2 | Counter.most_common Top-N |
| `status_diff` | §8.3 | Counter 算术(+/-,丢弃非正键) |
| `group_by_status` | §8.4 | defaultdict(list) 分组 |
| `unique_ips_by_path` | §8.5 | defaultdict(set) 去重计数(UV) |
| `recent_paths` | §8.6 | deque(maxlen) 滚动窗口 |
| `recent_errors` | §8.7 | deque 双端操作 appendleft |
| `to_namedtuple` | §8.8 | namedtuple 转换 / 访问 / 不可变 |
| `build_daily_report` | §8.9 | 综合:四大件合奏出日报 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch08_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「四大件各替代 Java 什么、maxlen 怎么滚动」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 数状态码频率要 `Map<Integer,Integer> + merge(k,1,Integer::sum)`。Python 一个类叫什么?
2. Java 取「次数最多的前 3 个 IP」要排序 + `limit(3)`。Python 的 Counter 上哪个方法一行搞定?
3. Java 分组要 `computeIfAbsent(k, k -> new ArrayList<>())`。Python 哪个 dict 子类在**声明处**写一次工厂就永远自动?
4. Java `ArrayDeque` 两头 O(1)。Python 的 `deque` 加个什么参数就能变成「自动挤掉最旧」的滚动窗口?
5. Java 14+ `record AccessLog(String ip, ...)`。Python 标准库里一行定义的等价物叫什么?

> 猜完,带着验证心态进入正文。第 3 题的「工厂」和第 4 题的 `maxlen` 是本章最香的两个点。

---

## §8.1 Counter:创建与计数(对应:`count_by_status`)🟢

`Counter` 是「自动计数的 dict」。给它任意可迭代对象,它数每个元素出现几次。

### Java 对照最小例

```java
// Java:统计一组状态码出现次数
Map<Integer, Integer> counts = new HashMap<>();
for (Log log : logs) {
    counts.merge(log.getStatus(), 1, Integer::sum);
}
counts.getOrDefault(999, 0);   // 查缺键还得手写默认值
```

```python
# Python:一行
from collections import Counter
c = Counter(log["status"] for log in logs)
c[999]      # 0  ← 缺键不抛 KeyError,直接返回 0(天生 getOrDefault)
```

### 真实场景例:状态码分布(本章日报第一段)

用 `access_logs.json` 的 20 条记录,实际算出来是:

```python
c = Counter(log["status"] for log in logs)
c                   # Counter({200: 13, 201: 2, 500: 3, 404: 1, 401: 1})
c[200]              # 13
c[999]              # 0   ← 没出现过的状态码,安全返回 0
sum(c.values())     # 20  ← 总数校验:20 条日志一条没丢
```

### 三种创建方式

```python
Counter("aabbbc")                  # Counter({'b': 3, 'a': 2, 'c': 1})  来自可迭代对象
Counter([200, 200, 404])           # Counter({200: 2, 404: 1})
Counter({200: 13, 500: 3})         # 直接包一个 dict(原样)
Counter(ok=13, error=3)            # Counter({'ok': 13, 'error': 3})    关键字参数
```

❌ **错误写法**(Java 思维手写循环):

```python
c = {}
for log in logs:
    s = log["status"]
    if s not in c:          # 每次都判断,啰嗦
        c[s] = 0
    c[s] += 1
```

✅ **正确写法**:`Counter(log["status"] for log in logs)` 一行。生成器表达式产什么,Counter 就数什么。

> 🟡 **Java 对比**:`Counter` ≈ `Map + getOrDefault(k,0) + merge` 三合一,且**缺键返 0 是类型级行为**,不用每个调用点手写。这让「计数」代码在 Python 里几乎永远是一行。

> ✅ 做 `count_by_status` 题:`Counter(log["status"] for log in logs)`,直接返回 Counter 对象(不要转 dict,测试要验类型)。

---

## §8.2 Counter.most_common:Top-N(对应:`top_ips`)🟢

`most_common(n)` 返回出现最多的前 n 个 `(元素, 次数)` 元组,按次数**降序**。Top-N 排行榜一行搞定(运维/热搜/销量榜高频)。

### Java 对照最小例

```java
// Java:统计 + 取 Top3 IP
Map<String, Long> counts = logs.stream()
    .collect(Collectors.groupingBy(Log::getIp, Collectors.counting()));
List<String> top3 = counts.entrySet().stream()
    .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
    .limit(3).map(Map.Entry::getKey).toList();
```

```python
# Python:一行
top3 = Counter(log["ip"] for log in logs).most_common(3)
```

### 真实场景例:找出访问最频繁的 IP

```python
ips = Counter(log["ip"] for log in logs)
ips.most_common(3)
# [('192.168.1.1', 5), ('10.0.0.5', 3), ('172.16.0.3', 2)]

ips.most_common(1)[0]   # ('192.168.1.1', 5)  ← 取冠军
ips.most_common()       # 不传 n → 全部 8 个 IP,按次数降序
```

> 🤯 注意返回的是**元组列表** `[("ip", 5), ...]`,不是 dict。只要元素:`[ip for ip, _ in ips.most_common(3)]`。

### 并列时谁排前面?🟡

数据里有 **6 个 IP 都是 2 次**(172.16.0.3 / 8.8.8.8 / 1.1.1.1 / 203.0.113.5 / 198.51.100.2 / 192.0.2.1),第 3 名为什么是 `172.16.0.3`?

**规则:次数相同的按「首次出现顺序」排**。172.16.0.3 在第 9 条日志首次登场,比其他 2 次的 IP 都早,所以排最前。这个特性来自:Counter 是 dict 子类(3.7+ 保证插入有序)+ `most_common` 的排序是稳定的。

```python
ips.most_common(4)
# [..., ('172.16.0.3', 2), ('8.8.8.8', 2)]
# 8.8.8.8 首次出现在第 11 条,晚于 172.16.0.3(第 9 条),排它后面
```

❌ **错误写法**(手写排序,又啰嗦又容易错):

```python
sorted(ips.items(), key=lambda kv: kv[1], reverse=True)[:n]   # 能跑,但为什么要自己写?
```

✅ **正确写法**:`ips.most_common(n)`。语义明确,并列顺序有保障。

> ✅ 做 `top_ips` 题:`Counter(log["ip"] for log in logs).most_common(n)`。注意 `n=0` 返回 `[]`、n 超过总数返回全部——`most_common` 自动处理,不用特判。

---

## §8.3 Counter 算术:加减(对应:`status_diff`)🟡

Counter 支持 `+` `-` `&`(交集取 min)`|`(并集取 max)。值班场景里最实用的是**减法**:「今天 vs 昨天同时段,哪些指标恶化了?」

### 关键规则:算术结果丢弃 ≤ 0 的键 🔴

```python
Counter(a=3, b=1) - Counter(a=1, b=5)   # Counter({'a': 2})  ← b: 1-5=-4,直接消失
Counter(a=2) + Counter(a=1, b=3)        # Counter({'a': 3, 'b': 3})
```

加法和减法都**只保留计数为正的键**——减没了的键不会出现(也不是 0)。配合「缺键返 0」,`diff[404]` 依然是安全的。

### 真实场景例:和昨日同时段对比

```python
today     = Counter({200: 13, 201: 2, 500: 3, 404: 1, 401: 1})   # 今天(access_logs.json 算出)
yesterday = Counter({200: 10, 500: 1, 404: 5})                   # 昨天同时段

today - yesterday
# Counter({200: 3, 201: 2, 500: 2, 401: 1})
# 500 从 1 → 3,恶化 +2,要告警!
# 404 从 5 → 1,好转了,差集里【没有】404 这个键(不是 0,不是 -4)

diff = today - yesterday
404 in diff        # False ← 键被丢弃了
diff[404]          # 0     ← 但缺键返 0,读取依然安全
```

❌ **错误认知**:以为 `today - yesterday` 会保留 `404: -4` 或 `404: 0`——都不会,键直接消失。想表达「恶化量」时这正合意;想保留完整差值(含负数)就手写:

```python
{s: today[s] - yesterday[s] for s in set(today) | set(yesterday)}   # 需要完整差值时的写法
```

✅ **正确用法**:恶化检测直接用 `today - yesterday`,结果里每个键都是「变多了」的指标。

> 🟡 **Java 对比**:Java 没有对应物,要写双层循环 + `merge`。Python 一个减号。`&` / `|` 同理(本章不考,知道有即可)。

> ✅ 做 `status_diff` 题:函数收两个 Counter(today, yesterday),返回 `today - yesterday`。一行,但要在 docstring 示例里体会「404 消失」这个坑。

---

## §8.4 defaultdict(list):分组(对应:`group_by_status`)🟡

分组是高频场景:把一堆记录按某 key 归类。普通 dict 第一次遇到新 key 会 KeyError,要先判断——这就是 Java 里 `computeIfAbsent` 解决的事。

### ❌→✅ 对照

❌ **普通 dict**(每个 key 都要先判存在):

```python
groups = {}
for log in logs:
    s = log["status"]
    if s not in groups:       # 啰嗦,每个分组场景都写一遍
        groups[s] = []
    groups[s].append(log)
```

😐 **Ch02 学过的 `setdefault`**(能跑但每次访问都重复):

```python
groups.setdefault(s, []).append(log)
```

✅ **defaultdict(list)**(工厂写在声明处一次,之后永远自动):

```python
from collections import defaultdict
groups = defaultdict(list)               # 工厂 = list:缺键时自动调 list() 造 []
for log in logs:
    groups[log["status"]].append(log)    # 新 status 自动建 [],直接 append
```

### 真实场景例:按状态码分组排查

值班时要看「所有 500 的具体是哪几条」:

```python
groups = defaultdict(list)
for log in logs:
    groups[log["status"]].append(log)

len(groups[200])   # 13
len(groups[500])   # 3  ← 这三条就是 /api/orders/1 和 /api/products 的那几次
len(groups[404])   # 1
```

### 「工厂」机制:传的是【可调用对象】,不是实例 🔴

`defaultdict(list)` 里的 `list` 是**工厂函数**——遇到缺键时调用 `list()` 造一个新空 list。所以:

❌ **错误写法**(又踩 Ch02 的可变默认坑):

```python
defaultdict([])     # ❌ 传了一个【固定的 list 实例】,所有缺键共享同一个!
```

✅ **正确写法**:`defaultdict(list)`(传类/函数本身),同理 `defaultdict(int)` → 默认 0、`defaultdict(set)` → 默认空 set(下一节用)、`defaultdict(dict)` → 默认空 dict。

### 收尾:`dict(groups)` 转回普通 dict

```python
return dict(groups)   # 转回普通 dict
```

为什么要转?两个实战理由:① 普通 dict 才能干净地 JSON 序列化/打印;② 防止下游代码**误触自动建键**——`groups[999]` 会悄悄创建一个 `999: []`,普通 dict 则老老实实 KeyError。

> 🟡 **Java 对比**:`defaultdict(list)` ≈ 把 `computeIfAbsent(k, k -> new ArrayList<>())` 的「k -> new ArrayList<>()」挪到声明处写一次。哲学:重复模式下沉到数据结构里。

> ✅ 做 `group_by_status` 题:`defaultdict(list)` + 遍历 append + `dict(groups)` 返回(测试会验 `type(g) is dict`)。

---

## §8.5 defaultdict 进阶:set 工厂做 UV 去重(对应:`unique_ips_by_path`)🟡

`defaultdict` 的威力在换工厂。换 `set` 就是「按 key 收集去重元素」——正是**接口独立访客数(UV)**的计算模型。

### 真实场景例:每个接口有多少个不同 IP 访问

日报要区分「访问量(PV)」和「访客数(UV)」:`/api/products` 被访问 9 次,但背后是几个不同的人?

```python
uv = defaultdict(set)
for log in logs:
    uv[log["path"]].add(log["ip"])     # set 自动去重:同一 IP 重复访问只算一个

len(uv["/api/products"])   # 7  ← 9 次访问来自 7 个不同 IP(192.168.1.1 一个人刷了 3 次)
len(uv["/login"])          # 1  ← 只有 203.0.113.5 来过
```

最后转成 `{路径: UV 数}` 的普通 dict:

```python
{path: len(ips) for path, ips in uv.items()}
# {'/api/products': 7, '/api/orders': 2, '/': 2, '/api/users': 2,
#  '/api/orders/1': 1, '/admin': 1, '/login': 1}
```

### 顺便:`defaultdict(int)` = 手动版 Counter

```python
counts = defaultdict(int)
for log in logs:
    counts[log["status"]] += 1    # 缺键自动是 0(int() == 0),直接 += 1
```

效果和 `Counter` 一样,但没有 `most_common` 等附加方法。**理解原理即可,实战直接用 Counter**。

❌ **错误写法**(对 set 工厂用 append):

```python
uv = defaultdict(set)
uv["/api/products"].append(log["ip"])   # ❌ AttributeError: set 没有 append
```

✅ **正确写法**:set 用 `.add()`;list 才用 `.append()`。选工厂时想清楚收集语义:**要顺序和重复 → list;要去重 → set**。

> 🟡 **Java 对比**:`Map<String, Set<String>>` + `computeIfAbsent(k, k -> new HashSet<>())` + `.add()`。Python 同样把模板沉进声明处。

> ✅ 做 `unique_ips_by_path` 题:`defaultdict(set)` 收集 → `{path: len(ips) for ...}` 字典推导式转出计数。

---

## §8.6 deque 与 maxlen 滚动窗口(对应:`recent_paths`)🟡

`deque`(发音 "deck",double-ended queue)两头都能 O(1) 增删。先看它解决的老大难:

### 为什么不能用 list 当队列?🔴

```python
q = [1, 2, 3, ... 一万个元素]
q.pop(0)     # ❌ O(n)!首元素弹出后,后面每个元素都要往前搬一格
```

`list.pop(0)` 是 **O(n)** 的隐藏性能炸弹,循环里用就是 O(n²)。`deque.popleft()` 是 **O(1)**。

> 🟡 **Java 对比**:`deque` ≈ `ArrayDeque`。规则一样:**队列/栈用 deque,随机索引用 list**(`deque[i]` 索引是 O(n),别这么用)。

### 四端操作速览

```python
from collections import deque
d = deque([1, 2, 3])
d.append(4)       # 右端入 → deque([1, 2, 3, 4])
d.appendleft(0)   # 左端入 → deque([0, 1, 2, 3, 4])
d.pop()           # 右端出 → 4
d.popleft()       # 左端出 → 0,全部 O(1)
```

### 杀手锏:`maxlen` 定长 → 滚动窗口

```python
recent = deque(maxlen=3)      # 最多装 3 个,满了再 append,【最旧的自动被挤掉】
for x in [1, 2, 3, 4, 5]:
    recent.append(x)
list(recent)                  # [3, 4, 5]  ← 恰好是最后 3 个
```

### 真实场景例:最近 N 条请求

值班大盘上「最近 5 条请求路径」:

```python
recent = deque(maxlen=5)
for log in logs:              # 20 条依次流入,像实时监控流
    recent.append(log["path"])
list(recent)
# ['/login', '/api/products', '/api/products', '/', '/api/products']  ← 第 16~20 条
```

不用手动 `if len > n: 删最旧`——**窗口逻辑被 maxlen 吃掉了**。日志滚动、聊天记录、「最近访问」列表都是这个模式。

边界行为(不用特判,deque 自动正确):`maxlen=0` 时什么都留不住(返回 `[]`);数据不足 n 条时保留全部。

> ✅ 做 `recent_paths` 题:`deque(maxlen=n)` + 遍历 `append(log["path"])` + `list(recent)`。

---

## §8.7 deque 双端操作:appendleft(对应:`recent_errors`)🟡

`append` 从右进、`appendleft` 从左进。配合 `maxlen`:**从哪端加,满了就挤掉另一端**。

### 真实场景例:错误告警栈「最新在前」

监控页面要展示「最近 3 条错误请求」,**最新的排最上**(像异常栈)。从左边压栈:

```python
errors = deque(maxlen=3)
for log in logs:
    if log["status"] >= 400:        # 4xx/5xx 都算错误
        errors.appendleft(log)      # 新的压到最左,最旧的从右边被挤掉

[e["ip"] for e in errors]
# ['198.51.100.2', '198.51.100.2', '203.0.113.5']   ← 最新(第18条)在前
[e["path"] for e in errors]
# ['/api/products', '/api/products', '/login']
```

推演一遍 5 条错误(第 8/11/15/17/18 条)依次 appendleft 进 `maxlen=3`:

```
[e8] → [e11, e8] → [e15, e11, e8] → [e17, e15, e11](e8 被挤掉)→ [e18, e17, e15](e11 被挤掉)
```

❌ **错误写法**(方向搞反):

```python
errors.append(log)    # 用 append + maxlen:留下的是最旧的 3 条在新、最新的在右端,
                      # 得到 [e15, e17, e18] —— 顺序是【最旧在前】,不符合告警栈语义
```

✅ **正确写法**:`appendleft` 压栈,左边永远是最新。记住口诀:**append 进右挤左(时间正序),appendleft 进左挤右(时间倒序)**。

> 🟡 **Java 对比**:`ArrayDeque` 的 `addFirst`/`addLast`。但 Java 没有 maxlen 这种「自动挤」——要自己判 size。Python 又少写四行。

> ✅ 做 `recent_errors` 题:遍历 logs,`status >= 400` 的 `appendleft` 进 `deque(maxlen=n)`,返回 `list(errors)`。

---

## §8.8 namedtuple:轻量不可变记录(对应:`to_namedtuple`)🟡

日志在内存里一直是 `dict`,访问要写 `log["status"]`(字符串键,IDE 不补全,打错字不报错)。`namedtuple` 给元组加字段名,一行定义出**不可变值对象**——Java `record` 的标准库平替。

### 定义与访问

```python
from collections import namedtuple

AccessLog = namedtuple("AccessLog", ["ip", "method", "path", "status"])
# 也可空格分隔:namedtuple("AccessLog", "ip method path status")

log = AccessLog(ip="192.168.1.1", method="GET", path="/api/products", status=200)
log.ip        # '192.168.1.1'  ← 字段名访问,可读、可补全
log.status    # 200
log[0]        # '192.168.1.1'  ← 本质还是 tuple,索引也行
```

### dict → namedtuple:`**` 解包(本节作业核心)

解析出的日志是 dict,键名恰好和字段一致时,`**` 一行转对象:

```python
d = {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}
log = AccessLog(**d)      # ** 把 dict 解包成关键字参数(Ch04 学过)
log.path                  # '/api/products'
```

### 不可变 + 可哈希 + tuple 本质

```python
log.status = 500        # ❌ AttributeError:namedtuple 不可变
log._replace(status=299)  # ✅ 「修改」= 返回新实例:AccessLog(..., status=299)

log == ("192.168.1.1", "GET", "/api/products", 200)   # True ← 和等值 tuple 相等

{log: 1}                # ✅ 可哈希,能当 dict 键 / 进 set(不可变的红利)
```

❌ **错误写法**(想就地改字段):

```python
log.ip = "8.8.8.8"      # AttributeError。日志记录是历史事实,本来就不该改
```

✅ **正确写法**:`log._replace(ip="8.8.8.8")` 拿一个改了字段的新对象。

> 🟡 **Java 对比**:`record AccessLog(String ip, String method, String path, int status) {}`。Python 三兄弟:`namedtuple`(最轻,本章)、`typing.NamedTuple`(加类型注解)、`@dataclass(frozen=True)`(Ch05,功能最全)。要轻量值对象先想到 namedtuple。

> 💡 作业文件里 `AccessLog` 的定义**已作为脚手架给出**(和 Ch38 的 TreeNode 一样),你的任务是练 `to_namedtuple` 的转换与使用——读懂那行定义就是本节的考点。

> ✅ 做 `to_namedtuple` 题:`return AccessLog(**d)`。

---

## §8.9 综合:组装访问日报(对应:`build_daily_report`)🔴

最后把四大件合起来,一次遍历产出完整日报。这题是 §8.1–§8.7 的「大合奏」——每段你都单独写过,现在组合进一个函数:

```python
def build_daily_report(logs: list[dict]) -> dict:
    status_counts = Counter(log["status"] for log in logs)      # §8.1
    top = Counter(log["ip"] for log in logs).most_common(3)     # §8.2
    uv = defaultdict(set)                                       # §8.5
    latest = deque(maxlen=5)                                    # §8.6
    errors = deque(maxlen=3)                                    # §8.7
    for log in logs:
        uv[log["path"]].add(log["ip"])
        latest.append(log["path"])
        if log["status"] >= 400:
            errors.appendleft(log)
    return {
        "total": len(logs),
        "status_counts": dict(status_counts),
        "top_ips": top,
        "path_uv": {p: len(s) for p, s in uv.items()},
        "latest_paths": list(latest),
        "latest_errors": list(errors),
    }
```

对 20 条 access_logs 跑出来的真实结果:

```python
{
  "total": 20,
  "status_counts": {200: 13, 201: 2, 500: 3, 404: 1, 401: 1},
  "top_ips": [("192.168.1.1", 5), ("10.0.0.5", 3), ("172.16.0.3", 2)],
  "path_uv": {"/api/products": 7, "/api/orders": 2, "/": 2, "/api/users": 2,
              "/api/orders/1": 1, "/admin": 1, "/login": 1},
  "latest_paths": ["/login", "/api/products", "/api/products", "/", "/api/products"],
  "latest_errors": [第18条, 第17条, 第15条],   # 最新在前
}
```

> 🟡 **设计要点**:四大件各管一段,互不干扰——Counter 管计数、defaultdict(set) 管去重、deque 管滚动窗口。这就是「选对数据结构,代码自己变短」。

> ✅ 做 `build_daily_report` 题:按上面的结构与键名实现(键名测试会逐个验)。空列表要返回全空日报,四大件天然支持,不用特判。

---

## §8.10 Java 老手常踩的坑 ⚠️

1. **用 `list` 当队列**:`list.pop(0)` 是 O(n),循环里用直接 O(n²)。队列一律 `deque` + `popleft()`。
2. **Counter 缺键返 0 是特性不是 bug**:但别和普通 dict 混——`{200: 13}[999]` 照样 KeyError。
3. **Counter 减法丢弃 ≤0 的键**:`today - yesterday` 里好转/持平的指标会**消失**,不是 0 也不是负数。
4. **`most_common` 返回元组列表**:`[("ip", 5), ...]`,不是 dict;并列时按首次出现顺序排。
5. **`defaultdict([])` 是固定实例**:所有缺键共享同一个 list(可变默认坑)。要传**工厂** `defaultdict(list)`。
6. **忘记 `dict(groups)` 转回普通 dict**:下游误访问 `groups[不存在的key]` 会悄悄建空键,污染数据。
7. **namedtuple 不可变**:改字段抛 `AttributeError`;「修改」要用 `log._replace(field=新值)` 返回新实例。
8. **deque 别按下标随机访问**:`d[i]` 是 O(n);要索引就用 list。deque 只为两端操作而生。

---

## 📖 延伸阅读:ChainMap / OrderedDict(本章不考)

- **`ChainMap`**:把多个 dict「叠」起来查询,先查第一个没有再查下一个。常用于**配置层叠**(默认配置 ← 用户配置 ← 命令行参数)。
- **`OrderedDict`**:保持插入顺序的 dict。Python 3.7+ 普通 `dict` 已保证有序,所以它现在只在需要 `move_to_end` 等额外操作时出场。

知道有这两个工具即可,日常 90% 用 Counter / defaultdict / deque / namedtuple。

---

## 📝 本章作业

打开 **`ch08_assignment.py`**,9 个任务,一条主线串起来:状态码分布 → Top IP → 昨日对比 → 分组排查 → UV → 最近 N 条 → 错误栈 → 结构化记录 → 汇总日报。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `count_by_status` | Counter 创建/计数 | 🟢 |
| `top_ips` | Counter.most_common | 🟢 |
| `status_diff` | Counter 减法 | 🟡 |
| `group_by_status` | defaultdict(list) | 🟡 |
| `unique_ips_by_path` | defaultdict(set) UV | 🟡 |
| `recent_paths` | deque(maxlen) | 🟡 |
| `recent_errors` | appendleft 双端 | 🟡 |
| `to_namedtuple` | namedtuple 转换 | 🟡 |
| `build_daily_report` | 综合 | 🔴 |

```bash
uv run pytest 02_stdlib/ch08/test_ch08_assignment.py -v
```

全绿 = 掌握 Ch08。卡住 → 按对应表回查 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「Counter 替代了 Java 的什么?为什么 `c[不存在的键]` 返回 0」(§8.1)
- [ ] 能解释 `most_common` 并列名次的排序规则(§8.2)
- [ ] 能说清 Counter 减法为什么**丢弃** ≤0 的键,以及这对「恶化检测」为何正好合用(§8.3)
- [ ] 能写 `defaultdict(list)`/`defaultdict(set)`,并解释「传工厂不是传实例」(§8.4/§8.5)
- [ ] 知道为什么队列用 deque 不用 list,`maxlen` 怎么实现滚动窗口(§8.6)
- [ ] 说清 `append` vs `appendleft` 配 maxlen 时各挤哪一端(§8.7)
- [ ] 能解释 namedtuple 不可变、可哈希、`**` 解包(§8.8)
- [ ] 9 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Counter 到底替代了 Java 哪些样板代码?`most_common` 并列时谁排前面?」— 卡壳重读 §8.1/§8.2
2. 「`defaultdict(list)` 为什么能自动建空列表?为什么不能写 `defaultdict([])`?」— 卡壳重读 §8.4
3. 「`deque(maxlen=n)` 怎么实现滚动窗口?appendleft 时挤掉哪一端?」— 卡壳重读 §8.6/§8.7

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch08 掌握后,进 **Ch09 · itertools + functools**——函数式利器。`groupby`/`chain`/`combinations`/`lru_cache`/`partial`,对比 Java Stream 但更强,本章的日报脚本到那里还能再简化一轮。
