# Ch11 · 数据交换:json / csv / datetime

> **预计**:0.5 天 ｜ **前置**:Ch02 ｜ **M2 第四章**
> **目标**:拿下数据交换三件套——`json`(序列化/反序列化)、`csv`(表格读写)、`datetime`(时间与时区,对比 Java `java.time`)。核心战力:**datetime 不能直接 json.dumps 的坑**、**naive/aware 时区陷阱**、**csv 为什么不能用 split(",")**。
> 本章主线:你是电商中台工程师,负责「订单数据交换」模块——收款事件从 MQ 以 JSONL 进来(`assets/mock_data/order_events.json`,7 条混合时区的事件),你要:解析事件 → 给前端发订单回执 → 解析事件时间 → 推算预计送达日 → 把 WMS 的 UTC 时间换算成北京时间 → 读运营的调价 CSV → 给财务导出对账 CSV → 给下游发订单快照 → 最后汇总成**每日对账报表**。

> 📐 **本教程的契约**:下面每一节(§11.1–§11.9)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 `loads/dumps` 与 `load/dump` 的区别(字符串 vs 文件),背出 JSON → Python 的类型映射表
- 用 `ensure_ascii=False` / `indent=2` / `sort_keys=True` 产出可读、可 diff 的 JSON
- 用 `datetime.fromisoformat` 解析 ISO 时间(含 `Z` 后缀),用 `strftime` 格式化出自定义格式
- 用 `timedelta` 做日期推算(自动跨月/跨年,不用自己算每月几天)
- 说清 naive vs aware datetime,用 `astimezone` 安全地做时区换算(并说出手动 +8 小时的后果)
- 用 `csv.DictReader` / `DictWriter` 读写 CSV,说清为什么 `split(",")` 是错的
- 用 `default` 钩子让 `json.dumps` 序列化 datetime(= Jackson 自定义 Serializer)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `parse_order_event` | §11.1 | json.loads 解析事件 |
| `order_receipt_json` | §11.2 | json.dumps 三参数:indent / ensure_ascii / sort_keys |
| `parse_event_time` | §11.3 | datetime.fromisoformat(含 Z 后缀) |
| `delivery_date` | §11.4 | date + timedelta 日期推算 |
| `utc_to_beijing` | §11.5 | timezone + astimezone 时区换算 |
| `parse_price_csv` | §11.6 | csv.DictReader + StringIO |
| `export_reconcile_csv` | §11.7 | csv.DictWriter + StringIO |
| `snapshot_to_json` | §11.8 | default 钩子序列化 datetime |
| `daily_reconcile_report` | §11.9 | 综合:JSONL + 时区过滤 + strftime + csv 写出 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch11_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「datetime 为什么不能直接 dumps」「naive/aware 的坑」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 用 Jackson `objectMapper.readValue(s, Map.class)` 解析 JSON。Python 标准库哪个函数?返回什么类型?
2. Java 里 `LocalDateTime.parse("2026-07-21T10:30:00")`。Python 解析 ISO 字符串用哪个方法?
3. 财务 CSV 里金额写成 `"1,299.00"`(带引号防逗号)。手写 `line.split(",")` 会发生什么?
4. MQ 事件时间戳 `"2026-07-20T17:00:00Z"`(UTC)——换成北京时间是**几号**几点?凭直觉答,然后记住这个结果怎么算出来的。
5. `json.dumps({"paid_at": datetime.now()})` 会发生什么?Java 里你怎么解决同类问题?

> 猜完,带着验证心态进入正文。第 3、4 题是本章最容易踩的坑,第 5 题是全章的「主线 BOSS」。

---

## §11.1 json.loads:解析订单事件(对应:`parse_order_event`)🟢

MQ 里的收款事件是 **JSONL**(每行一个 JSON 对象),消费端第一件事就是 `json.loads` 把字符串变成 dict。

### Java 对照最小例

```java
// Java (Jackson)
Map<String, Object> event = objectMapper.readValue(
    "{\"order_id\":\"ORD-1001\",\"amount\":599.0}", Map.class);
```

```python
# Python:标准库自带,不用引依赖
import json
event = json.loads('{"order_id":"ORD-1001","amount":599.0}')
event["order_id"]   # 'ORD-1001'
```

### 四个函数,两两配对

| 函数 | 方向 | 操作对象 |
|------|------|----------|
| `json.loads(s)` | 字符串 → 对象 | **s** = string |
| `json.dumps(obj)` | 对象 → 字符串 | **s** = string |
| `json.load(f)` | 文件 → 对象 | 文件句柄 |
| `json.dump(obj, f)` | 对象 → 文件 | 文件句柄 |

> 记忆法:**带 `s` 的操作字符串**。Ch06 学过的 `json.load(f)` 就是文件版。

### JSON → Python 类型映射(和 Java 泛型擦除不同,这里是确定的)🟡

| JSON | Python | 备注 |
|------|--------|------|
| object | `dict` | |
| array | `list` | |
| string | `str` | |
| number(整) | `int` | |
| number(小数) | `float` | |
| true / false | `True` / `False` | 首字母大写! |
| null | `None` | 不是 `null`! |

```python
json.loads('{"qty": 2, "amount": 59.9, "paid": true, "coupon": null}')
# {'qty': 2, 'amount': 59.9, 'paid': True, 'coupon': None}
```

### 真实场景例:消费一条 MQ 收款事件

```python
line = '{"order_id": "ORD-1001", "amount": 599.0, "occurred_at": "2026-07-21T09:15:00+08:00"}'
event = json.loads(line)
event["amount"]        # 599.0
event["occurred_at"]   # '2026-07-21T09:15:00+08:00'  ← 字符串!§11.3 再把它变 datetime
```

### 解析失败:别吞异常,让它抛 🔴

事件体脏数据免不了。`json.loads` 对非法 JSON 抛 `json.JSONDecodeError`(**它是 ValueError 的子类**):

❌ **错误写法**(吞异常返回 None,调用方拿到 None 更懵,错误被掩盖):

```python
try:
    return json.loads(text)
except json.JSONDecodeError:
    return None        # 坏事件静默丢失,财务对账对不上时你查三天
```

✅ **正确写法**:直接 `json.loads(text)`,让 `JSONDecodeError` 抛给上层——消费框架捕到后进**死信队列**,和 Java 里 MQ 消费失败重试/进 DLQ 一个套路。

```python
json.loads("not json")
# json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

> 🟡 **Java 对比**:`readValue` 抛 `JsonProcessingException`(受检异常,逼你 catch);Python 的 `JSONDecodeError` 非受检,**选择不 catch 时直接传播**——这正是你要的行为。

> ✅ 做 `parse_order_event` 题:一行 `json.loads(text)`,不要 try/except。测试会验「非法 JSON 抛 JSONDecodeError」。

---

## §11.2 json.dumps:序列化与格式化(对应:`order_receipt_json`)🟢

订单支付成功,要给前端/下游回一个**回执 JSON**。要求:美观(人要看)、中文不转义、键有序(方便对账 diff)。

### Java 对照最小例

```java
// Java (Jackson):美观输出要配 writerWithDefaultPrettyPrinter,键排序要开 SerializationFeature
String s = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(receipt);
```

```python
# Python:三个参数搞定
json.dumps({"buyer": "张三", "amount": 599.0}, indent=2, ensure_ascii=False, sort_keys=True)
```

### 三个高频参数(逐个看效果)

```python
data = {"buyer": "张三", "amount": 599.0}

json.dumps(data)
# '{"buyer": "\\u5f20\\u4e09", "amount": 599.0}'   ← ❶ 中文被转义成 \uXXXX,日志里没法看

json.dumps(data, ensure_ascii=False)
# '{"buyer": "张三", "amount": 599.0}'              ← ❷ 中文原样输出 ✅

json.dumps(data, indent=2, ensure_ascii=False)
# '{\n  "buyer": "张三",\n  "amount": 599.0\n}'     ← ❸ 缩进美观(打印出来是多行)

json.dumps({"b": 1, "a": 2}, indent=2, sort_keys=True)
# '{\n  "a": 2,\n  "b": 1\n}'                       ← ❹ 键排序,两次输出可 diff
```

- `ensure_ascii=False` —— 中文/emoji 原样输出(默认 True 转义,**联调时最烦的点**)
- `indent=2` —— 美观缩进(不写就是一行紧凑输出)
- `sort_keys=True` —— 键按字典序排。财务对账、配置 diff 时,**同样内容永远产出同样字符串**
- (附带)`separators=(",", ":")` —— 去掉逗号/冒号后的空格,发网络报文最省字节:`json.dumps({"a":1,"b":2}, separators=(",",":"))` → `'{"a":1,"b":2}'`

### 真实场景例:订单回执

```python
receipt = {"order_id": "ORD-1001", "buyer": "张三", "amount": 599.0}
print(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True))
# {
#   "amount": 599.0,
#   "buyer": "张三",
#   "order_id": "ORD-1001"
# }
```

❌ **错误写法**(以为转义后中文「丢了」):

```python
s = json.dumps({"buyer": "张三"})
assert "张三" in s   # 💥 AssertionError:s 里是 \u5f20\u4e09,不是张三
```

✅ **正确写法**:`ensure_ascii=False`。注意转义只是**显示形式**,`json.loads` 回来数据完全等价——但为了日志可读,联调输出一律加上这个参数。

> 🟡 **Java 对比**:Jackson 默认不转义非 ASCII,`ensure_ascii=True` 这个「默认转义」是 Python 的历史包袱。记住:**只要输出可能含中文,就加 `ensure_ascii=False`**。

> ✅ 做 `order_receipt_json` 题:`json.dumps(order, indent=2, ensure_ascii=False, sort_keys=True)`,三个参数缺一不可。

---

## §11.3 datetime:解析与格式化(对应:`parse_event_time`)🟡

事件里的 `occurred_at` 是字符串,要做时间计算得先变成 `datetime` 对象。

### Python 时间类型 vs Java java.time

| Python | Java | 含义 |
|--------|------|------|
| `date` | `LocalDate` | 只有日期 |
| `datetime` | `LocalDateTime` / `OffsetDateTime` | 日期+时间(可带时区) |
| `time` | `LocalTime` | 只有时间 |
| `timedelta` | `Duration` / `Period` | 时间差 |

### 解析:fromisoformat(3.11+ 最省心)

```python
from datetime import datetime

datetime.fromisoformat("2026-07-21T10:30:00")          # datetime(2026, 7, 21, 10, 30)
datetime.fromisoformat("2026-07-21T10:30:00+08:00")    # 带时区 → aware datetime
datetime.fromisoformat("2026-07-21T02:30:00Z")         # 3.11+ 直接认 "Z"(UTC),返回 +00:00
datetime.fromisoformat("2026-07-21")                   # 只有日期也行 → 当天 00:00:00
```

> ⚠️ 历史代码里会看到 `"...Z".replace("Z", "+00:00")` 的写法——那是 3.11 之前 `fromisoformat` 不认 `Z` 的 workaround,现在不用了。

反向:`dt.isoformat()` 把 datetime 变回 ISO 字符串:

```python
datetime(2026, 7, 21, 10, 30).isoformat()   # '2026-07-21T10:30:00'
```

### 格式化:strftime(自定义格式)

ISO 适合机器交换,**给人看**(财务报表、页面展示)要自定义格式,用 `strftime`(f = format):

```python
dt = datetime(2026, 7, 21, 10, 30)
dt.strftime("%Y/%m/%d")        # '2026/07/21'   ← 财务对账表要的斜杠日期
dt.strftime("%Y-%m-%d %H:%M")  # '2026-07-21 10:30'
dt.strftime("%m-%d")           # '07-21'
```

常用占位符:`%Y` 4位年、`%m` 2位月、`%d` 2位日、`%H` 24制时、`%M` 分、`%S` 秒。

反过来,**非 ISO 格式**的字符串用 `strptime`(p = parse)解析:

```python
datetime.strptime("2026/07/21", "%Y/%m/%d")   # datetime(2026, 7, 21, 0, 0)
```

### 真实场景例:解析 MQ 事件时间戳

```python
event = json.loads('{"order_id": "ORD-1004", "occurred_at": "2026-07-21T02:30:00Z"}')
dt = datetime.fromisoformat(event["occurred_at"])
dt.utcoffset()     # datetime.timedelta(0)  ← Z 被认成 UTC
dt.hour            # 2  ← 注意这是 UTC 的 2 点,北京时间要 §11.5 换算
```

❌ **错误写法**(用 strptime 解 ISO,又慢又啰嗦):

```python
datetime.strptime("2026-07-21T10:30:00", "%Y-%m-%dT%H:%M:%S")   # 能跑,但何必手写格式串
```

✅ **正确写法**:ISO 格式一律 `fromisoformat`;只有非 ISO(如 `"2026/07/21"`)才动用 `strptime`。

> 🟡 **Java 对比**:`fromisoformat` ≈ `LocalDateTime.parse(s)`(Java 默认走 ISO);`strftime/strptime` ≈ `DateTimeFormatter.ofPattern(...)` 的 format/parse。Python 免建 formatter,直接传格式串。

> ✅ 做 `parse_event_time` 题:`datetime.fromisoformat(s)` 一行。测试会喂带 `Z`、带 `+08:00`、不带时区三种形态。

---

## §11.4 timedelta:日期推算(对应:`delivery_date`)🟡

下单页要显示「预计送达:7 月 24 日」= 下单日期 + 3 天。这种推算**千万别自己算**「这个月有几天」。

### Java 对照最小例

```java
LocalDate delivery = LocalDate.parse("2026-07-21").plusDays(3);   // 2026-07-24
```

```python
from datetime import date, timedelta
delivery = date.fromisoformat("2026-07-21") + timedelta(days=3)   # date(2026, 7, 24)
```

### timedelta 就是「一段时间」,和日期加减随便组合

```python
timedelta(days=3)                          # 3 天(还有 hours/minutes/seconds/weeks)
date.fromisoformat("2026-01-31") + timedelta(days=1)   # date(2026, 2, 1)  ← 自动跨月
date.fromisoformat("2026-12-31") + timedelta(days=1)   # date(2027, 1, 1)  ← 自动跨年
date.fromisoformat("2026-07-21") + timedelta(days=-1)  # date(2026, 7, 20) 负值=往前
```

两个 date/datetime **相减**得到 timedelta,`.days` 取整天数:

```python
d2 - d1                       # timedelta(days=20)
(d2 - d1).days                # 20
(d2 - d1).total_seconds()     # datetime 差按秒算用这个
```

### 真实场景例:预计送达日期

```python
def delivery_date(order_date_s, days):
    return (date.fromisoformat(order_date_s) + timedelta(days=days)).isoformat()

delivery_date("2026-07-21", 3)    # '2026-07-24'
delivery_date("2026-01-31", 1)    # '2026-02-01'  ← 1 月 31 日 +1 天,自动跨月
```

❌ **错误写法**(Java 老手偶尔会犯的「自己算」):

```python
y, m, d = 2026, 1, 31
d += 1                       # 2026-01-32?? 然后你开始写每月天数表 + 闰年判断……
```

✅ **正确写法**:`timedelta` 把这些全包了(闰年、大小月、跨年),和标准库作者比严谨你不会赢。

> 🟡 **Java 对比**:`plusDays(n)` / `ChronoUnit.DAYS.between(d1, d2)`。Python 直接运算符重载 `date + timedelta`、`date - date`,更直白。

> ✅ 做 `delivery_date` 题:`date.fromisoformat` + `timedelta(days=days)`,返回 `.isoformat()`。测试会验跨月、跨年、0 天、负天数。

---

## §11.5 时区:naive vs aware,astimezone 换算(对应:`utc_to_beijing`)🔴

**本章最大坑**。WMS(仓储系统)回传的时间是 UTC:`"2026-07-20T17:00:00Z"`。财务问「7 月 20 日(北京时间)收了几笔款」——这条事件算 20 号还是 21 号?

```python
dt = datetime.fromisoformat("2026-07-20T17:00:00Z")
# UTC 17:00 + 8 小时 = 北京时间 2026-07-21 01:00 → 算 21 号!
# 直接看字符串前缀 "2026-07-20" 就分类,账就错了
```

### naive vs aware

| | naive(无时区) | aware(带时区) |
|---|---|---|
| 长相 | `datetime(2026, 7, 21, 10, 30)` | `datetime(2026, 7, 21, 10, 30, tzinfo=...)` |
| `.utcoffset()` | `None` | `timedelta(hours=8)` |
| 类比 Java | `LocalDateTime` | `OffsetDateTime` |
| 风险 | 「10:30 是哪里的 10:30?」说不清 | 含义明确,可跨时区换算 |

构造 aware 的最简方式——固定偏移:

```python
from datetime import timezone, timedelta

BEIJING = timezone(timedelta(hours=8))       # UTC+8,中国无夏令时,固定偏移够用
datetime(2026, 7, 21, 10, 30, tzinfo=BEIJING)
```

### astimezone:时区换算的唯一正确姿势

```python
utc_dt = datetime.fromisoformat("2026-07-20T17:00:00+00:00")   # aware(UTC)
bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))        # 换算到 UTC+8
bj_dt.isoformat()   # '2026-07-21T01:00:00+08:00'   ← 跨日了!自动处理
bj_dt.date()        # date(2026, 7, 21)
```

`astimezone` 按「**同一时刻**」换算:不同时区、同一瞬间,所以日期可能翻页——这正是对账要的行为。

❌ **错误写法一**(手动 +8 小时,丢掉时区信息):

```python
naive_utc + timedelta(hours=8)   # 数值上对了,但结果是 naive——
                                 # 之后和谁比、往哪存,全靠你脑子记「这已经是北京时间」
```

❌ **错误写法二**(对 naive datetime 调 astimezone):

```python
datetime(2026, 7, 20, 17, 0).astimezone(BEIJING)
# 不报错!但 Python 会按【运行机器的本地时区】解释这个 naive 时间——
# 服务器在 UTC 机房和你本机 +08:00,算出来差 8 小时。CI 上红、本地绿的经典悬案。
```

✅ **正确写法**:输入带时区(`fromisoformat` 解出 aware)→ `astimezone(BEIJING)` → 再取 date/格式化。如果输入真是 naive 的 UTC,先 `replace(tzinfo=timezone.utc)` 标明身份再换算。

> 🟡 **Java 对比**:`OffsetDateTime.withZoneSameInstant(ZoneId.of("+08:00"))`——名字就说了「同一瞬间」。命名时区(Asia/Shanghai)用 `zoneinfo.ZoneInfo`(需 tzdata,见延伸阅读);中国固定 +8,`timezone(timedelta(hours=8))` 就够。

> ✅ 做 `utc_to_beijing` 题:`datetime.fromisoformat(s).astimezone(timezone(timedelta(hours=8))).isoformat()`。测试会喂 `Z`、`+00:00`、`+02:00` 三种输入,含跨日 case。

---

## §11.6 csv 读取:DictReader(对应:`parse_price_csv`)🟡

运营发来一张**调价单 CSV**(Excel 导出),要读进来准备更新价格:

```csv
sku,price
KB-001,549.00
MS-002,139.00
```

### Java 对照(痛点回忆)

```java
// Java:要么手写 split(引号陷阱见下),要么引 opencsv/commons-csv
String[] parts = line.split(",");   // 遇到 "1,299.00" 就裂成三段
```

```python
# Python:标准库自带,还能直接从字符串读(不用落地文件)
import csv, io

reader = csv.DictReader(io.StringIO(text))
rows = list(reader)   # [{'sku': 'KB-001', 'price': '549.00'}, ...]
```

### DictReader:表头当键,每行一个 dict

```python
text = "sku,price\nKB-001,549.00\nMS-002,139.00\n"
for row in csv.DictReader(io.StringIO(text)):
    print(row)
# {'sku': 'KB-001', 'price': '549.00'}
# {'sku': 'MS-002', 'price': '139.00'}
```

两个必记细节:
1. **所有值都是 str**!`row["price"]` 是 `'549.00'` 不是数字,要自己 `float(...)`。
2. `\n` 和 `\r\n`(Windows/Excel)都能认,不用自己处理换行。

`io.StringIO(text)` 把字符串包装成「内存文件」,csv 模块不关心来源是文件还是内存——**写测试、处理 HTTP 上传的 CSV 内容都用这招**,不用落地临时文件。

### 为什么不能用 split(",")🔴

```python
# 真实调价单混入引号字段(Excel 对含逗号的值自动加引号):
line = 'BK-004,"1,299.00"'
line.split(",")                       # ['BK-004', '"1', '299.00"']  💥 裂成三段
list(csv.reader(io.StringIO(line)))   # [['BK-004', '1,299.00']]     ✅ 引号内逗号被正确理解
```

CSV 规范里引号可以包住逗号、甚至换行——手写 split 永远处理不完这些 case。

❌ **错误写法**:`[line.split(",") for line in text.splitlines()]`
✅ **正确写法**:`csv.DictReader(io.StringIO(text))`,再把 price 列 `float()`。

> ✅ 做 `parse_price_csv` 题:`DictReader` 逐行读,返回 `[{"sku": 原样, "price": float(row["price"])}, ...]`。测试会喂带引号的 `"549.00"` 和 `\r\n` 换行,手写 split 过不了。

---

## §11.7 csv 写出:DictWriter(对应:`export_reconcile_csv`)🟡

财务要**每日对账 CSV**(导进 Excel 用)。内存里拼好,直接回 HTTP 响应或写文件。

### 最小例

```python
import csv, io

buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=["order_id", "amount", "status"])
w.writeheader()                                  # 先写表头行
w.writerow({"order_id": "ORD-1001", "amount": 599.0, "status": "PAID"})
w.writerows([...])                               # 多行用 writerows
buf.getvalue()                                   # 拿到 CSV 字符串
# 'order_id,amount,status\r\nORD-1001,599.0,PAID\r\n'
```

### 两个细节

1. **换行是 `\r\n`**:csv 模块默认 Excel 方言(RFC 4180),行尾 `\r\n`。写断言时对 `\r\n` 有心理准备;真实文件写出时用 `open(path, "w", newline="")`,避免二次换行。
2. **自动加引号**:值里含逗号/引号/换行时,csv 模块自动用双引号包住——这正是你放弃 f-string 拼接的理由:

```python
w = csv.writer(buf)                    # writer 写 list,DictWriter 写 dict
w.writerow(["ORD-1001", "1,299.00"])   # → ORD-1001,"1,299.00"  ✅ 自动保护
```

❌ **错误写法**(f-string 拼 CSV,金额带千分位逗号就炸):

```python
"\n".join(f'{r["order_id"]},{r["amount"]}' for r in rows)   # amount = "1,299.00" 时列错位
```

✅ **正确写法**:`DictWriter`(`fieldnames` 固定列序)+ `writeheader()` + `writerows(rows)`。

> 🟡 **Java 对比**:= opencsv 的 `StatefulBeanToCsv`,但不用建 writer 对象链,`StringIO` 充当了 `StringWriter`。

> ✅ 做 `export_reconcile_csv` 题:`fieldnames=["order_id", "amount", "status"]`,空 rows 也要输出表头。测试断言精确到 `\r\n`。

---

## §11.8 序列化陷阱:datetime 不能直接 dumps(对应:`snapshot_to_json`)🔴

给下游系统发**订单快照**,里面带着 datetime 字段:

```python
snapshot = {"order_id": "ORD-1001", "paid_at": datetime(2026, 7, 21, 10, 30)}
json.dumps(snapshot)
# 💥 TypeError: Object of type datetime is not JSON serializable
```

JSON 规范里**没有日期类型**——全世界都拿字符串凑合(ISO 格式是事实标准)。Python 不替你猜格式,直接报错。

### 解法:default 钩子

`json.dumps(obj, default=f)`:遇到不认识的类型就调 `f(对象)`,让它返回一个 JSON 认识的值(通常是 str)。所有自定义类型一个钩子全收:

```python
def _default(o):                          # 定义在函数内部即可,用完即弃
    if isinstance(o, (datetime, date)):
        return o.isoformat()              # datetime → ISO 字符串
    raise TypeError(f"不支持序列化: {type(o).__name__}")   # 其他类型:照抛

json.dumps(snapshot, default=_default)
# '{"order_id": "ORD-1001", "paid_at": "2026-07-21T10:30:00"}'  ✅

json.dumps(snapshot, default=_default, ensure_ascii=False)
# 快照里有中文买家名时,顺手加上 ensure_ascii=False(§11.2)
```

钩子会**递归生效**:嵌套在 list/dict 深处的 datetime 也会走到它。钩子里对不认识的类型**必须 raise TypeError**——不 raise 而返回 None 的话,坏数据就静默进 JSON 了(和 §11.1 别吞异常一个道理)。

### Java 对照

```java
// Java (Jackson):注册自定义序列化器,或字段上加 @JsonFormat
objectMapper.registerModule(new JavaTimeModule());   // 还要引 jackson-datatype-jsr310
```

> 🟡 Python 一个函数参数搞定。**进阶预告**:正式项目用 Pydantic(M3 Ch14)——模型直接声明 `paid_at: datetime`,`.model_dump_json()` 自动处理,不用手写 default。本章先理解底层原理。

> ✅ 做 `snapshot_to_json` 题:`json.dumps(obj, default=钩子, ensure_ascii=False)`,钩子里 `isinstance(o, (datetime, date))` → `o.isoformat()`,否则 `raise TypeError`。测试会喂嵌套 datetime 和不支持的 set。

---

## §11.9 综合:每日对账报表(对应:`daily_reconcile_report`)🔴

把本章家伙什全合起来,产出财务要的**每日对账 CSV**:

> 输入:MQ 导出的 JSONL 文本(每行一个收款事件,`occurred_at` 带任意时区)+ 目标日期(北京时间)。
> 输出:CSV,表头 `date,order_id,amount`;只保留**换算成北京时间后**落在目标日的事件;按发生时间升序;日期格式 `2026/07/21`;金额两位小数。

```python
def daily_reconcile_report(events_text, day):
    beijing = timezone(timedelta(hours=8))
    target = date.fromisoformat(day)
    events = []
    for line in events_text.splitlines():          # JSONL:逐行
        line = line.strip()
        if not line:                               # 文件末尾空行,跳过
            continue
        e = json.loads(line)                                    # §11.1
        dt = datetime.fromisoformat(e["occurred_at"])           # §11.3
        dt = dt.astimezone(beijing)                             # §11.5 换算北京时间
        if dt.date() == target:                                 # 按北京时间的【日期】过滤
            events.append((dt, e))
    events.sort(key=lambda t: t[0])                # aware datetime 可直接比大小(比的是时刻)
    buf = io.StringIO()
    w = csv.writer(buf)                                         # §11.7
    w.writerow(["date", "order_id", "amount"])
    for dt, e in events:
        w.writerow([dt.strftime("%Y/%m/%d"),                    # §11.3 斜杠格式
                    e["order_id"],
                    f'{e["amount"]:.2f}'])                      # 金额两位小数(Ch07 f-string)
    return buf.getvalue()
```

对 `order_events.json` 的 7 条事件跑 `day = "2026-07-21"`:

| 事件 | occurred_at(原文) | 北京时间 | 入选? |
|------|-------------------|----------|-------|
| ORD-1001 | 07-21 09:15 +08:00 | 07-21 09:15 | ✅ |
| ORD-1002 | 07-21 11:02 +08:00 | 07-21 11:02 | ✅ |
| ORD-1003 | 07-20 22:30 +08:00 | 07-20 22:30 | ❌ 20 号的 |
| ORD-1004 | 07-21 02:30 **Z** | 07-21 10:30 | ✅ |
| ORD-1005 | 07-20 17:00 +00:00 | 07-21 **01:00** | ✅ 跨日陷阱! |
| ORD-1006 | 07-21 15:40 +08:00 | 07-21 15:40 | ✅ |
| ORD-1007 | 07-20 16:30 **Z** | 07-21 **00:30** | ✅ 跨日陷阱! |

输出(升序,注意 ORD-1005/1007 看字符串前缀是「20 号」,实际是 21 号的款):

```
date,order_id,amount
2026/07/21,ORD-1007,399.00
2026/07/21,ORD-1005,75.50
2026/07/21,ORD-1001,599.00
2026/07/21,ORD-1004,89.00
2026/07/21,ORD-1002,159.00
2026/07/21,ORD-1006,1299.00
```

(实际行尾是 `\r\n`。)验算:399.00 + 75.50 + 599.00 + 89.00 + 159.00 + 1299.00 = **2620.50**,6 笔。

> 🟡 **设计要点**:`json.loads` 管「解析」(§11.1),`astimezone` 管「时区归一」(§11.5),`strftime` 管「人看的格式」(§11.3),`csv.writer` 管「安全导出」(§11.7)——每个工具干自己那段。这就是数据交换的日常:格式进、格式出,中间是语义。

> ✅ 做 `daily_reconcile_report` 题:照上面结构实现。**内联实现、别调前面的函数**(web 端单题跑时其他函数还是骨架)。注意空行跳过、时区换算后再比日期、`\r\n` 行尾。

---

## §11.10 Java 老手常踩的坑 ⚠️

1. **`loads/dumps` vs `load/dump`**:带 `s` 操作字符串,不带操作文件。`json.loads(f)` 传文件句柄会 TypeError。
2. **中文转义**:`json.dumps` 默认 `ensure_ascii=True`,中文变 `\uXXXX`。联调/日志输出加 `ensure_ascii=False`;转义不丢数据,`loads` 回来等价。
3. **吞 JSONDecodeError**:解析失败返回 None,错误被掩盖。让它抛,上层进死信队列。
4. **datetime 直接 dumps**:TypeError。用 `default` 钩子转 isoformat,钩子里不认识的类型要 raise,别返回 None 静默放走。
5. **naive.astimezone()**:不报错,但按**运行机器本地时区**解释——CI 和本地结果不同的悬案源头。先让输入 aware 再换算。
6. **手动 +8 小时当时区换算**:数值对、时区信息丢,后续比较/存储全靠自己记。用 `astimezone`。
7. **`split(",")` 解析 CSV**:引号字段(`"1,299.00"`)直接裂开。csv 模块自动处理引号和 `\r\n`。
8. **DictReader 的值全是 str**:数字列记得 `float()/int()`,否则 `'549.00' + '139.00'` 是字符串拼接。
9. **`fromisoformat` 遇 `Z` 报错是 3.11 前的事**:现在直接认;老代码里 `.replace("Z", "+00:00")` 是历史 workaround。

---

## 📖 延伸阅读(本章不考)

- **Pydantic**(M3 Ch14 重点):声明式模型 `paid_at: datetime`,`model_dump_json()` 自动序列化——告别手写 default 钩子,还白送数据校验。
- **`zoneinfo.ZoneInfo("Asia/Shanghai")`**:命名时区(含历史夏令时规则),需系统 tzdata 或 `pip install tzdata`。中国固定 +8,本章的 `timezone(timedelta(hours=8))` 已够用。
- **`dateutil`**:第三方库,`dateutil.parser.parse` 能猜各种奇葩日期格式("Jul 21, 2026")。
- **pandas `read_csv`**:数据分析场景的 CSV 瑞士刀,运维脚本量级用标准库就够。

---

## 📝 本章作业

打开 **`ch11_assignment.py`**,9 个任务一条主线串起来:解析 MQ 事件 → 订单回执 → 事件时间 → 送达日期 → 时区换算 → 调价 CSV 读入 → 对账 CSV 导出 → 快照序列化 → 每日对账报表。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `parse_order_event` | json.loads | 🟢 |
| `order_receipt_json` | json.dumps 三参数 | 🟢 |
| `parse_event_time` | datetime.fromisoformat | 🟢 |
| `delivery_date` | date + timedelta | 🟡 |
| `utc_to_beijing` | timezone + astimezone | 🔴 |
| `parse_price_csv` | csv.DictReader | 🟡 |
| `export_reconcile_csv` | csv.DictWriter | 🟡 |
| `snapshot_to_json` | default 钩子 | 🔴 |
| `daily_reconcile_report` | 综合 | 🔴 |

```bash
uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v
```

全绿 = 掌握 Ch11。卡住 → 按对应表回查 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能默写 `loads/dumps/load/dump` 四函数分工 + JSON→Python 类型映射表(§11.1)
- [ ] 说清 `ensure_ascii=False` / `indent=2` / `sort_keys=True` 各自解决什么(§11.2)
- [ ] ISO 字符串 ↔ datetime 互转不假思索,知道 strftime/strptime 什么时候才上场(§11.3)
- [ ] 用 timedelta 做跨月/跨年推算,知道为什么不能自己算天数(§11.4)
- [ ] 说清 naive/aware 区别、`astimezone` 语义、「naive.astimezone 为什么不报错却是错的」(§11.5)
- [ ] 说清 `split(",")` 为什么错、DictReader 两个细节(值全是 str、换行自适应)(§11.6)
- [ ] 知道 csv 写出的 `\r\n` 行尾和自动加引号(§11.7)
- [ ] 能手写 default 钩子序列化 datetime,并说明钩子里为什么要 raise TypeError(§11.8)
- [ ] 9 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「为什么 json.dumps 不能直接序列化 datetime?default 钩子是怎么被调用的?钩子里为什么必须 raise?」— 卡壳重读 §11.8
2. 「`2026-07-20T17:00:00Z` 是北京时间几号几点?naive datetime 调 astimezone 会发生什么?」— 卡壳重读 §11.5
3. 「CSV 就一行逗号分隔,为什么不能 split(",")?csv 模块还顺手帮你处理了哪两件事?」— 卡壳重读 §11.6/§11.7

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch11 掌握后,进 **Ch12 · 现代工具链(logging / 配置 / 项目结构)**——M2 收官。本章的对账报表到那里会配上 logging,出问题能查到「哪条事件解析失败进了死信」。
