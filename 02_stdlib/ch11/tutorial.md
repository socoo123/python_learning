# Ch11 · 数据交换:json / csv / datetime

> **预计**:0.5 天 ｜ **前置**:Ch02 ｜ **M2 第四章**
> **目标**:掌握数据交换三件套——`json`(序列化)、`datetime`(时间,对比 Java `java.time`)。重点是 **datetime 不能直接 json.dumps 的坑**和它的解法。

> 📐 **本教程的契约**:下面每一节对应作业里的一个任务。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `parse_products_json` | §11.1 | json.loads |
| `to_pretty_json` | §11.2 | json.dumps(indent/ensure_ascii) |
| `parse_iso_datetime` | §11.3 | datetime.fromisoformat |
| `days_between` | §11.4 | date + timedelta |
| `to_json_with_datetime` | §11.5 | default 钩子(序列化 datetime) |

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## §11.1 json:loads / dumps(对应:`parse_products_json`)🟢

`json` 模块四个核心函数,**两两配对**(字符串版带 `s`):

| 函数 | 方向 | 作用 |
|------|------|------|
| `json.loads(s)` | 字符串 → 对象 | parse(解析) |
| `json.dumps(obj)` | 对象 → 字符串 | serialize(序列化) |
| `json.load(f)` | 文件 → 对象 | 从文件读 |
| `json.dump(obj, f)` | 对象 → 文件 | 写到文件 |

```python
import json

# 解析
json.loads('[{"name":"键盘","price":599}]')   # [{'name':'键盘','price':599}]
json.loads('{"a":1}')                          # {'a':1}

# 序列化
json.dumps({"a": 1})                           # '{"a": 1}'
```

> 🟡 **Java 对比**:= Jackson/Gson 的 `readValue`/`writeValueAsString`。JSON 数组 → Python `list`,JSON 对象 → Python `dict`,JSON 数字 → int/float。Python 内置 json 够用,无需三方库。

> ✅ 做 `parse_products_json` 题:`json.loads(text)`。

---

## §11.2 json.dumps 格式化(对应:`to_pretty_json`)🟢

```python
json.dumps({"name":"键盘","price":599})
# '{"name": "键盘", "price": 599}'   ← 默认中文转义!不可读

json.dumps({"name":"键盘","price":599}, ensure_ascii=False)
# '{"name": "键盘", "price": 599}'           ← 中文原样输出 ✅

json.dumps({"a":1}, indent=2)
# '{\n  "a": 1\n}'                            ← 缩进美观

json.dumps({"b":2,"a":1}, sort_keys=True)
# '{"a": 1, "b": 2}'                          ← 键排序
```

**两个最常用参数**:
- `ensure_ascii=False` —— 中文/emoji 原样输出(默认 True 会转义成 `\uXXXX`,调试时不可读)
- `indent=2` —— 美观缩进

> ✅ 做 `to_pretty_json` 题:`json.dumps(obj, indent=2, ensure_ascii=False)`。

---

## §11.3 datetime:解析与格式化(对应:`parse_iso_datetime`)🟡

Python 时间类型(对比 Java `java.time`):

| Python | Java 对应 | 含义 |
|--------|-----------|------|
| `date` | `LocalDate` | 只有日期 |
| `datetime` | `LocalDateTime` | 日期+时间 |
| `time` | `LocalTime` | 只有时间 |
| `timedelta` | `Duration`/`Period` | 时间差 |

```python
from datetime import date, datetime

# 创建
datetime(2026, 7, 21, 10, 30)        # 2026-07-21 10:30:00
date(2026, 7, 21)                     # 2026-07-21
date.today()                          # 今天

# ISO 字符串 ↔ 对象(3.7+ 最方便的方式)
datetime.fromisoformat("2026-07-21T10:30:00")   # 字符串 → datetime
datetime(2026,7,21,10,30).isoformat()           # datetime → '2026-07-21T10:30:00'
date.fromisoformat("2026-07-21")                # 字符串 → date
```

> 🟡 **Java 对比**:`fromisoformat` ≈ `LocalDateTime.parse(s)`;`isoformat()` ≈ `.toString()`(Java 默认就是 ISO 格式)。Python 的 ISO 解析 3.11+ 很宽松,各种格式都认。

> ✅ 做 `parse_iso_datetime` 题:`datetime.fromisoformat(s)`。

---

## §11.4 timedelta:时间差(对应:`days_between`)🟡

两个 `date`/`datetime` 相减得到 `timedelta`,`.days` 取天数:

```python
from datetime import date

d1 = date.fromisoformat("2026-07-01")
d2 = date.fromisoformat("2026-07-21")
delta = d2 - d1          # timedelta(days=20)
delta.days               # 20
delta.total_seconds()    # datetime 差用这个

# 加减时间
date.today() + timedelta(days=7)    # 一周后
```

> 🟡 **Java 对比**:`Duration.between(d1,d2).toDays()`。Python 直接 `d2 - d1` 更直观(运算符重载)。

> ✅ 做 `days_between` 题:`abs((date.fromisoformat(s2) - date.fromisoformat(s1)).days)`(abs 保证顺序无关)。

---

## §11.5 序列化陷阱:datetime 不能直接 dumps(对应:`to_json_with_datetime`)🔴

**大坑**:`json.dumps` 默认不认识 `datetime`,直接序列化会报错:

```python
json.dumps({"created_at": datetime(2026,7,21)})
# TypeError: Object of type datetime is not JSON serializable
```

### 解法:`default` 钩子

`json.dumps(obj, default=函数)` —— 遇到不认识的类型时,调用 `default(对象)`,让它返回一个 json 认识的值(通常是字符串):

```python
def _datetime_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()         # 转成 ISO 字符串
    raise TypeError(f"不支持: {type(o)}")

json.dumps({"created_at": datetime(2026,7,21,10,30)}, default=_datetime_default)
# '{"created_at": "2026-07-21T10:30:00"}'   ✅
```

> 🟡 **Java 对比**:= Jackson 的自定义 `JsonSerializer` / `@JsonFormat`。Python 一个 `default` 函数搞定所有自定义类型。
>
> **进阶**:正式项目里推荐用 `@dataclass` + Pydantic(M3 Ch14),它自动处理 datetime 序列化,不用手写 default。本章先理解原理。

> ✅ 做 `to_json_with_datetime` 题:写 `_datetime_default` 钩子,`json.dumps(obj, default=_datetime_default)`。

---

## §11.6 csv(简介,本章不考)

```python
import csv
with open("data.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)      # 每行变成 dict(用表头当键)
    for row in reader:
        print(row["name"], row["price"])
```

知道有 `csv.DictReader`/`DictWriter` 即可,日常 CSV 处理够用。大数据量用 pandas。

---

## §11.7 时区坑(简介,本章不考)

Python datetime 默认是 **naive**(无时区)。涉及多时区要加 `tzinfo`:

```python
from datetime import timezone, timedelta
tz = timezone(timedelta(hours=8))    # UTC+8
datetime(2026,7,21,10,30, tzinfo=tz)  # aware datetime
```

> ⚠️ 生产代码涉及时间,**始终用 aware datetime**(带时区),否则跨时区会出诡异 bug。这和 Java 用 `ZonedDateTime` 一个道理。本章不深入,记住「naive 不可用于跨时区」。

---

## §11.8 Java 老手常踩的坑 ⚠️

1. **中文转义**:`json.dumps` 默认 `ensure_ascii=True`,中文变 `\uXXXX`。调试/存中文用 `ensure_ascii=False`。
2. **datetime 不能直接 dumps**:必须用 `default` 钩子或 Pydantic。
3. **loads vs load / dumps vs dump**:带 `s` 的操作字符串,不带的操作文件。别搞混。
4. **naive datetime 跨时区**:默认 datetime 无时区,跨时区计算会错。生产用 aware。
5. **ISO 格式最稳**:`fromisoformat`/`isoformat` 是 3.7+ 最佳实践,别用老的 `strptime`/`strftime`(除非自定义格式)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `parse_products_json` | json.loads | 🟢 |
| `to_pretty_json` | json.dumps 格式化 | 🟢 |
| `parse_iso_datetime` | datetime.fromisoformat | 🟢 |
| `days_between` | date + timedelta | 🟡 |
| `to_json_with_datetime` | default 钩子 | 🟡 |

```bash
uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v
```

---

## ✅ 自测

- [ ] 知道 `loads/load`、`dumps/dump` 的区别(字符串 vs 文件)
- [ ] 能用 `default` 钩子让 json.dumps 支持 datetime
- [ ] 知道 `ensure_ascii=False` 让中文不转义
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么 json.dumps 不能直接序列化 datetime?怎么解决?」— 重读 §11.5
2. 「Python datetime 和 Java java.time 怎么对应?naive/aware 是什么?」— 重读 §11.3/§11.7

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch11 掌握后,进 **Ch12 · 现代工具链(logging/配置/项目结构)**——M2 收官。把工程化基础打好,准备进 M3 Web 框架。
