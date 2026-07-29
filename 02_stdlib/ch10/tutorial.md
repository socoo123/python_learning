# Ch10 · 正则表达式与字符串处理

> **预计**:0.5 天 ｜ **前置**:M1 ｜ **M2 第三章**
> **目标**:掌握 Python `re` 模块——`match`/`search`/`findall`/`sub`/`split`,分组与命名分组。正则本身跨语言(你 Java 经验直接复用),本章重点是 **Python `re` 的 API** 和 **命名分组语法**。

> 📐 **本教程的契约**:下面每一节都对应作业。正则语法看 §10.1 速查,nginx 日志正则的逐段拆解看 §10.5。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `parse_nginx_log` | §10.3/§10.5 | 命名分组 + search + groupdict |
| `extract_ips` | §10.2 | re.findall |
| `redact_phones` | §10.2 | re.sub |
| `split_on` | §10.2 | re.split |

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## §10.1 正则语法速查(Java 老手秒懂,扫一遍)

正则元字符跨语言通用,你 Java 经验直接搬:

| 语法 | 含义 | 例子 |
|------|------|------|
| `\d` | 数字 [0-9] | `\d+` 一串数字 |
| `\w` | 字母数字下划线 | `\w+` 单词 |
| `\s` | 空白(空格/tab/换行) | |
| `.` | 任意一个字符(除换行) | |
| `+` | 前一个,1 次或多次 | `\d+` |
| `*` | 前一个,0 次或多次 | |
| `?` | 前一个,0 或 1 次 | `https?` 匹配 http/https |
| `{m,n}` | m 到 n 次 | `\d{1,3}` 1~3 位 |
| `[...]` | 字符集(任选一个) | `[A-Z]` 大写字母 |
| `[^...]` | 取反 | `[^\]]` 非 ] 的字符 |
| `^` / `$` | 行首 / 行尾 | |
| `\b` | 单词边界 | `\bword\b` 精确匹配 |
| `(...)` | 捕获分组 | |
| `(?:...)` | 非捕获分组(不存) | `(?:\.\d{1,3}){3}` 重复 3 次 |
| `(?P<name>...)` | **命名分组**(Python 写法) | 见 §10.3 |

> 🟡 **Python 转义坑**:正则里的 `\d` 在 Python 字符串中要写 `r'\d'`(原始字符串)。如果写 `'\d'`,Python 会警告(因为 `\d` 不是合法转义)。**正则一律用 `r'...'` 原始字符串**。

---

## §10.2 re 模块五大函数

```python
import re

re.search(模式, 文本)     # 在文本里【找第一个】匹配,返回 Match 或 None(最常用)
re.match(模式, 文本)      # 只从【开头】匹配(Java matches 头部)
re.fullmatch(模式, 文本)  # 整个文本完全匹配
re.findall(模式, 文本)    # 找【所有】匹配,返回字符串列表
re.finditer(模式, 文本)   # 同上,返回 Match 迭代器
re.sub(模式, 替换, 文本)  # 替换所有匹配
re.split(模式, 文本)      # 按模式拆分
```

### 各函数示例

```python
re.search(r'\d+', 'abc123def')    # <Match>  找到 123
re.match(r'\d+', 'abc123')        # None     开头不是数字
re.findall(r'\d+', 'a1b22c333')   # ['1','22','333']
re.sub(r'\d', '#', 'a1b2')        # 'a#b#'
re.split(r'[,;]', 'a,b;c')        # ['a','b','c']
```

> 🟡 **Java 对比**:= `Pattern.compile(模式)` + `matcher(文本)` + `.find()/.matches()/.group()`。Python 不用显式 compile 也能用(内部会缓存),更简洁。`search` = Java `find`(找任意位置),`match` = Java `matches`(从开头)。

### Match 对象

```python
m = re.search(r'(\d+)-(\w+)', 'order: 1234-abc')
m.group(0)    # '1234-abc'  整个匹配
m.group(1)    # '1234'      第 1 个分组
m.group(2)    # 'abc'       第 2 个分组
m.groups()    # ('1234','abc')
```

---

## §10.3 命名分组(本节重点)

给分组起名字,比 `group(1)`/`group(2)` 可读得多。**Python 用 `(?P<name>...)`**(注意大写 P):

```python
m = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})', '2026-07')
m.group('year')        # '2026'   按名字取
m.group('month')       # '07'
m.groupdict()          # {'year':'2026', 'month':'07'}   一次拿全
```

> 🟡 **Java 对比**:Java 是 `(?<year>\d{4})`(没有 P)。Python 历史包袱多了个 P。功能一样。

> ✅ 这就是 `parse_nginx_log` 的核心:`LOG_RE.search(line)` → `m.groupdict()` 一次拿到 ip/method/path/status。

---

## §10.4 re.compile:预编译

同一段正则用多次时,`re.compile` 预编译成对象,稍快且可复用:

```python
IP_RE = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')   # 模块级编译一次
IP_RE.findall(text)        # 等价 re.findall(r'...', text),但复用更高效
IP_RE.search(text)
```

> 用一次的正则直接 `re.search(...)` 即可;用多次(尤其循环里)就 `compile`。

---

## §10.5 实战:parse_nginx_log 逐段拆解 🔴

nginx 日志格式:
```
192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234
```

逐段写正则(每个要提取的部分用命名分组):

```
(?P<ip>\d+\.\d+\.\d+\.\d+)              # 192.168.1.1   4 段数字点连
 - - \[                                  #  - - [     (字面量,要匹配)
(?P<time>[^\]]+)                         # 10/Oct/...+0000   ] 前的所有字符
\] "                                     # ] "
(?P<method>[A-Z]+)                       # GET   大写字母
 (?P<path>\S+)                           # /api/products   非空白字符
 HTTP/[\d.]+"                            # HTTP/1.1"
 (?P<status>\d+)                         # 200
```

组合(注意用原始字符串 `r'...'`,换行用字符串拼接):
```python
LOG_RE = re.compile(
    r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<time>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d+)'
)

def parse_nginx_log(line):
    m = LOG_RE.search(line)
    if not m:                # 非法行,search 返回 None
        return None
    d = m.groupdict()        # {ip, time, method, path, status}
    d["status"] = int(d["status"])   # status 默认是字符串,转成 int
    return d
```

**几个关键点**:
- `[^\]]+` 匹配「非 `]` 的字符一个或多个」——用来抓 `[...]` 里的时间(因为时间含 `/` `:` `+` 各种符号,用「取反」最省事)。
- `\S+` 匹配「非空白字符」——路径 `/api/products` 没有空格,用 `\S+`。
- `HTTP/[\d.]+` 匹配 `HTTP/1.1`(`[\d.]` 是数字或点)。
- 字面量的 `[` `]` `"` 要在正则里精确写出来(`]` 在外面不用转义,`[` 在字符集外一般也行,但保险可写 `\[`)。

---

## §10.6 re vs str 方法:何时用正则

能用 `str` 方法解决就别上正则(正则可读性差、易错):

```python
# ✅ 简单判断用 str 方法
"2026-07" in text
text.startswith("http")
text.split(",")[0]

# 🔴 复杂模式才用正则(IP、邮箱、日志结构、手机号)
re.findall(r'\d+\.\d+\.\d+\.\d+', text)
```

---

## §10.7 Java 老手常踩的坑 ⚠️

1. **忘加 `r` 原始字符串**:`'\d'` 会警告,必须 `r'\d'`。
2. **`match` vs `search`**:`match` 只看开头,`search` 找任意位置。要找文本中间的内容用 `search`。
3. **`findall` 有分组时行为变化**:如果模式里有分组,`findall` 返回分组元组而非整个匹配。要整个匹配就别用分组,或用 `(?:...)` 非捕获分组。
4. **贪婪 vs 非贪婪**:`.*` 贪婪(尽量多匹配),`.*?` 非贪婪(尽量少)。提取标签内容用 `.*?`。
5. **命名分组是 `(?P<name>...)`**:别忘了那个 `P`(Java 没有)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `parse_nginx_log` | 命名分组 + search | 🔴 |
| `extract_ips` | findall | 🟢 |
| `redact_phones` | sub | 🟢 |
| `split_on` | split | 🟢 |

```bash
uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v
```

---

## ✅ 自测

- [ ] 能用 `(?P<name>...)` 命名分组 + `groupdict()` 提取结构化数据
- [ ] 知道 `search` vs `match` vs `findall` 的区别
- [ ] 知道正则必须用 `r'...'` 原始字符串
- [ ] 4 个作业全绿

## 🎓 费曼挑战

1. 「Python 命名分组怎么写?它比 group(1) 好在哪?和 Java 有何不同?」— 重读 §10.3
2. 「search/match/findall 分别在什么场景用?」— 重读 §10.2

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch10 掌握后,进 **Ch11 · json / csv / datetime**——数据交换三件套,重点处理 datetime 序列化(对比 Java `java.time`)。
