# Ch10 · 正则表达式与字符串处理

> **预计**:0.5 天 ｜ **前置**:M1(Ch06 用过 str 方法硬抠日志)｜ **M2 第三章**
> **目标**:正则语法你早会了(Java 经验直接复用),本章真正要学的是 **Python `re` 模块的 API 风格**、**命名分组 `(?P<>)`**、**sub 的三形态**、以及 **f-string 高级排版**——外加一个判断力:「什么时候根本不该用正则」。
> 本章主线:你是电商平台值班运维,拿到导出的 `assets/mock_data/nginx_logs.txt`(13 行原始访问日志,混入 2 行脏数据),安全团队要一份**审计快报**:校验 IP 白名单 → 从全文提取 IP → 结构化解析每一行 → 对外分享前脱敏(IP + 手机号)→ 解析告警规则配置 → 排版输出 Top-N 表 → 汇总成完整快报。

> 📐 **本教程的契约**:下面每一节(§10.2–§10.9)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按对应表回查小节。§10.1 是速查备查,随用随翻。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 `search` / `match` / `fullmatch` 的区别,以及它们各自对应 Java `Matcher` 的哪个方法(有坑!)
- 用 `findall` 一次抓全部匹配,并躲开「有分组时返回值变形」的陷阱
- 用 `(?P<name>...)` 命名分组 + `groupdict()` 把一行日志变成 dict(= Java `(?<name>...)`,差一个字母)
- 用 `re.sub` 的三种替换形态(固定串 / 反向引用 `\1` / 函数替换)做脱敏
- 用 `re.split` 按「多个分隔符」拆分,说清和 Java `String.split` 的尾部空串差异
- 用 f-string 的 `{x:<16}` `{n:,}` `{r:.1%}` 排出版面对齐的文本报告

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `is_valid_ip` | §10.2 | search / match / fullmatch + Match 对象 |
| `extract_ips` | §10.3 | findall + `(?:...)` 非捕获分组陷阱 |
| `parse_log_line` | §10.4 | 命名分组 + groupdict + re.compile |
| `mask_ip` | §10.5 | sub + 命名反向引用 `\g<name>` |
| `redact_phones` | §10.5 | sub + 函数替换(lambda) |
| `parse_alert_codes` | §10.6 | re.split 多分隔符 |
| `parse_log_text` | §10.7 | str.splitlines + 逐行正则(str vs re 分工) |
| `format_top_table` | §10.8 | f-string 对齐 / 宽度 |
| `build_report` | §10.9 | 综合:解析 + Counter + f-string 全链路 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch10_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「fullmatch 坑、命名分组、sub 三形态」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 要 `Pattern.compile("\\d+").matcher(s).find()` 三步。Python 的 `re` 模块找第一个匹配,一个函数叫什么?
2. Java `matcher.matches()` 要求**整串**匹配。Python 的 `re.match` 是「整串」还是「从头」?整串那个叫什么?
3. Java 命名分组 `(?<ip>...)`。Python 的写法多了哪个字母?
4. Java 替换时用 `$1` 引用分组(`replaceAll("$1.*.*")`)。Python 的反向引用长什么样?
5. Java `String.format("%-16s%5d", name, n)` 左对齐排版。Python f-string 大括号里怎么写?

> 猜完,带着验证心态进入正文。第 2 题的 `match` 陷阱和第 4 题的 `\1` 歧义是本章最容易踩的两个坑。

---

## §10.1 正则语法速查(备查 · 随用随翻)🟢

正则元字符跨语言通用,你 Java 经验直接搬。这张表不用背,卡住回来查:

| 语法 | 含义 | 例子 |
|------|------|------|
| `\d` `\w` `\s` | 数字 / 单词字符 / 空白 | `\d{3}` 三位数字 |
| `.` | 任意字符(除换行) | |
| `+` `*` `?` | 1~多次 / 0~多次 / 0~1次 | `https?` 匹配 http/https |
| `{m,n}` | m 到 n 次 | `\d{1,3}` 1~3 位 |
| `[...]` / `[^...]` | 字符集 / 取反 | `[A-Z]`;`[^\]]` 非 `]` |
| `^` / `$` | 行首 / 行尾 | |
| `\b` | 单词边界 | `\b1[3-9]\d{9}\b` 手机号 |
| `(...)` | 捕获分组(存起来) | |
| `(?:...)` | **非捕获**分组(只分组不存) | `(?:\.\d{1,3}){3}` 见 §10.3 |
| `(?P<name>...)` | **命名分组**(Python 写法) | 见 §10.4 |
| `.*` / `.*?` | 贪婪 / 非贪婪 | `<p>.*?</p>` 见 §10.10 |

### 🟡 Python 特有的第一步:原始字符串 `r'...'`

正则里全是反斜杠(`\d` `\b` `\w`)。Python 普通字符串把 `\` 当转义符,`\d` 不是合法转义会警告;要匹配字面量反斜杠时更惨:

❌ **错误写法**(反斜杠地狱,和 Java 一样难受):

```python
'\\d+\\.\\d+'        # 每个 \ 都要写两次,可读性灾难
'\\\\'               # 匹配一个字面量反斜杠,要写 4 个
```

✅ **正确写法**:**正则一律加 `r` 前缀**(raw string,`\` 不再当转义符):

```python
r'\d+\.\d+'          # 所见即所得
r'\\'                # 匹配字面量反斜杠,2 个就够
```

> 🟡 **Java 对比**:Java 没有原始字符串,`"\\d+"` 永远双写——你已经忍了很多年。Python 的 `r'...'` 就是为此而生。**本章所有正则字面量都带 `r`,形成肌肉记忆。**

---

## §10.2 search / match / fullmatch:三个「找」的区别(对应:`is_valid_ip`)🟡

`re` 模块最常用的三个查找函数,区别只在**匹配锚点**:

```python
import re

re.search(r'\d+', 'abc123def456')     # 找【任意位置】第一个 → 匹配 '123'
re.match(r'\d+', 'abc123')            # 只从【开头】试 → None(开头是字母)
re.fullmatch(r'\d+', '123456')        # 要求【整串】匹配 → 匹配
re.fullmatch(r'\d+', '123abc')        # → None(尾巴多了 abc)
```

三者返回 `Match` 对象或 `None`(没找到)。**`if` 判断时 None 是 falsy,Match 是 truthy**:

```python
m = re.search(r'\d+', 'abc123')
if m:                   # ✅ Pythonic 的判空写法
    m.group()           # '123'  整个匹配到的文本
```

### Java 对照最小例(最大的坑在这里)🔴

```java
Pattern p = Pattern.compile("\\d+");
Matcher m = p.matcher("abc123");
m.find();       // true   任意位置找 = Python re.search
m.matches();    // false  要求【整串】匹配 = Python re.fullmatch !!
```

```python
re.search(r'\d+', 'abc123')       # = Java find()
re.fullmatch(r'\d+', 'abc123')    # = Java matches() → None
re.match(r'\d+', 'abc123')        # 「从头开始」——Java 里【没有】直接对应物!
```

> 🔴 **命名陷阱**:Java 的 `matches()` 是**整串**匹配,Python 的 `match()` 只是**从头**匹配——同名不同义!记忆法:**Python 的 fullmatch 才是 Java 的 matches**。

### Match 对象:取分组

```python
m = re.search(r'(\d{3})-(\w+)', 'order: 500-internal')
m.group(0)    # '500-internal'  整个匹配(= group())
m.group(1)    # '500'           第 1 个捕获分组
m.group(2)    # 'internal'      第 2 个
m.groups()    # ('500', 'internal')  全部分组的元组
```

### 真实场景例:校验白名单 IP 配置(`is_valid_ip` 的原型)

配置中心拉下来一批「IP 白名单」,上线前要逐条校验格式。**校验必须整串匹配**——这是 `fullmatch` 的专属场景:

❌ **错误写法**(用 search 做校验,脏数据放行):

```python
re.search(r'\d{1,3}(?:\.\d{1,3}){3}', '192.168.1.1!!!')   # 居然能匹配!前 11 个字符合法
re.search(r'\d{1,3}(?:\.\d{1,3}){3}', 'x192.168.1.1')     # 也匹配!从位置 1 开始
```

✅ **正确写法**(fullmatch 卡死整串):

```python
re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}', '192.168.1.1')      # ✅ Match
re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}', '192.168.1.1 ')     # None 尾巴有空格也不行
re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}', '1.2.3')            # None 段数不够
```

但 `fullmatch` 只能验**形状**,验不了**范围**——`256.1.1.1` 形状合法却不是合法 IP。纯正则写 0-255 判断又臭又长(见延伸阅读),实战做法是**分工**:正则验形状,`str.split` + `all()` 验范围:

```python
def is_valid_ip(ip: str) -> bool:
    if re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}', ip) is None:
        return False                      # 形状不对,直接枪毙
    return all(int(seg) <= 255 for seg in ip.split('.'))   # str 方法验范围
```

> 💡 这就是「str 方法 vs 正则」分工的第一次实战:**各干擅长的**(§10.7 展开讲)。注意 `fullmatch` 自带整串锚定,**不用再写 `^...$`**。

> ✅ 做 `is_valid_ip` 题:先 `re.fullmatch` 判形状(None 则 False),再 `ip.split('.')` + `all(int(seg) <= 255 ...)` 判范围。

---

## §10.3 findall 找全部 + 分组陷阱(对应:`extract_ips`)🟢

`findall` 一次抓出**所有**匹配,返回字符串列表——相当于把 Java 的 `while (m.find()) list.add(m.group())` 循环压成一行。

### Java 对照最小例

```java
List<String> ips = new ArrayList<>();
Matcher m = Pattern.compile("\\d{1,3}(?:\\.\\d{1,3}){3}").matcher(text);
while (m.find()) ips.add(m.group());
```

```python
ips = re.findall(r'\d{1,3}(?:\.\d{1,3}){3}', text)   # 一行,返回 list[str]
```

### 真实场景例:从审计日志全文捞 IP

```python
text = "from 1.2.3.4 to 10.0.0.5, last hop 8.8.8.8"
re.findall(r'\d{1,3}(?:\.\d{1,3}){3}', text)
# ['1.2.3.4', '10.0.0.5', '8.8.8.8']   按出现顺序,重复不去重
```

对 `nginx_logs.txt` 全文跑,能捞出 11 个 IP——`192.168.1.1` 出现 3 次就在列表里占 3 个位置(**findall 不去重**,要去重外面套 `set`)。

### 🔴 分组陷阱:模式里有 `(...)` 时,findall 返回值变形

IP 正则里「点+数字」要重复 3 次,自然的写法是加分组 `(\.\d{1,3}){3}`。但**只要模式里有捕获分组,findall 就只返回分组内容**:

❌ **错误写法**(捕获分组 → 返回值变形):

```python
re.findall(r'\d{1,3}(\.\d{1,3}){3}', 'ip 192.168.1.1')
# ['.1']   ← 只返回了分组最后一次匹配的内容,整个 IP 丢了!
```

✅ **正确写法**(`(?:...)` 非捕获分组:只分组、不捕获):

```python
re.findall(r'\d{1,3}(?:\.\d{1,3}){3}', 'ip 192.168.1.1')
# ['192.168.1.1']   ✓
```

规则:**findall 的模式里,只为「重复/分组」不为「提取」时,一律 `(?:...)`**。`\b` 单词边界也别忘:防止 `12345.6.7.8` 这类串从中间切开匹配。

> 💡 作业文件里 `IP_RE` 已作为脚手架预编译好(带 `\b` 和 `(?:...)`),`extract_ips` 题专注练 `findall` 本身。想看分组陷阱的报错现场,把 `(?:` 的 `?:` 删掉试试。

> ✅ 做 `extract_ips` 题:对预编译的 `IP_RE` 调 `.findall(text)`,一行返回。

---

## §10.4 命名分组 + groupdict + re.compile(对应:`parse_log_line`)🔴 本章核心

序号分组 `group(1)`/`group(2)` 有两个毛病:魔法数字不可读、正则里插一个分组全乱序。**命名分组**给每个分组起名字,`groupdict()` 一次导出成 dict——结构化解析的标配。

### Java 对照最小例:就差一个字母 `P` 🟡

```java
// Java:(?<name>...)
Matcher m = Pattern.compile("(?<year>\\d{4})-(?<month>\\d{2})").matcher("2026-08");
m.find();
m.group("year");   // "2026"
```

```python
# Python:(?P<name>...) —— 注意大写 P,历史包袱
m = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})', '2026-08')
m.group('year')        # '2026'   按名字取
m.groupdict()          # {'year': '2026', 'month': '08'}   一次拿全 ★
```

> 🔴 **唯一语法差异就是那个 `P`**。写 Java 肌肉记忆 `(?<name>...)` 在 Python 里直接 `SyntaxError`……哦不,是 `re.error: missing >`。看到这个名字陌生的报错,先检查是不是忘了 P。

### re.compile:预编译 🟡

```python
IP_RE = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')   # 模块级编译一次
IP_RE.findall(text)     # 之后当对象方法用,等价 re.findall(同一模式, text)
```

什么时候需要 `compile`?
- **用一次**的正则:直接 `re.search(r'...', text)`。`re` 模块内部会缓存最近 512 个编译结果,不用担心重复编译的开销。
- **循环里反复用 / 模块级共享**:`re.compile` 存成常量。可读性更好(正则有了名字),也省掉缓存查找。

Java 必须显式 `Pattern.compile` 才能用;Python 两种风格都行,**团队约定俗成:复杂正则 compile 到模块级,顺手起个自解释的名字**。

### 真实场景例:nginx 日志正则逐段拆解

`nginx_logs.txt` 每行长这样:

```
192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234
```

对照格式逐段写,**每个要提取的字段一个命名分组**:

| 正则片段 | 匹配什么 | 技巧 |
|----------|----------|------|
| `(?P<ip>\d{1,3}(?:\.\d{1,3}){3})` | `192.168.1.1` | 4 段数字点连,`(?:...)` 重复不分组 |
| ` - - \[` | ` - - [` | 字面量,`[` 转义成 `\[` |
| `(?P<time>[^\]]+)` | `10/Oct/2023:13:55:36 +0000` | `[^\]]+` = `]` 之前的所有字符(时间里符号杂,取反最省事) |
| `\] "` | `] "` | 字面量 |
| `(?P<method>[A-Z]+)` | `GET` | 大写字母 |
| ` (?P<path>\S+)` | ` /api/products` | `\S+` = 非空白字符(路径无空格) |
| ` HTTP/[\d.]+"` | ` HTTP/1.1"` | `[\d.]` = 数字或点 |
| ` (?P<status>\d{3}) (?P<bytes>\d+)` | ` 200 1234` | 状态码固定 3 位,字节数任意位 |

组合(太长就两个 `r'...'` 拼接,Python 相邻字符串自动连接):

```python
LOG_RE = re.compile(
    r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) - - \[(?P<time>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d{3}) (?P<bytes>\d+)'
)

m = LOG_RE.search(line)       # 用 search:允许行首有前缀(如采集器加的 tag)
if m is None:                 # 脏数据行
    return None
d = m.groupdict()
# {'ip': '192.168.1.1', 'time': '10/Oct/2023:13:55:36 +0000', 'method': 'GET',
#  'path': '/api/products', 'status': '200', 'bytes': '1234'}
```

> 🟡 **正则抓到的永远是字符串**:`status`/`bytes` 要 `int()` 转换后才能参与统计。这是日志解析最容易忘的一步。

> 💡 为什么用 `search` 不用 `match`?生产日志常被采集器加上行首前缀(时间戳、trace id),`search` 容忍前缀。§10.2 说了,要「整串严格校验」才用 `fullmatch`。

> ✅ 做 `parse_log_line` 题:`LOG_RE`(作业里已编译好)`search` → 判 None → `groupdict()` → `status`/`bytes` 转 int → 返回 dict。非法行返回 None。

---

## §10.5 sub 替换三形态:固定串 / 反向引用 / 函数(对应:`mask_ip`、`redact_phones`)🟡

`re.sub(模式, 替换成, 文本)` 替换所有匹配。**「替换成」有三种形态**,按替换内容对匹配内容的依赖程度递进:

### 形态 1:固定字符串(替换内容与匹配无关)

```python
re.sub(r'\d', '#', 'a1b22')        # 'a#b##'   每个数字变 #
```

### 形态 2:反向引用 `\1`(替换内容 = 匹配的一部分)🟡

安全审计场景:日志要**对外分享**,IP 保留前两段定位网段、后两段打码。替换内容依赖匹配内容的前半段——用反向引用:

❌ **Java 写法搬不过来**:`$1` 是 Java 的,Python 里不识别。

```java
// Java:replaceAll 里用 $1 引用第 1 个分组
text.replaceAll("(\\d{1,3}\\.\\d{1,3})\\.\\d{1,3}\\.\\d{1,3}", "$1.*.*");
```

✅ **Python 写法**(`\1` 或更安全的 `\g<1>`;命名分组用 `\g<name>`):

```python
re.sub(r'\b(?P<net>\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}\b',   # 前两段捕获进命名分组 net
       r'\g<net>.*.*',                                        # 反向引用拼回
       'from 192.168.1.1 to 10.0.0.5')
# 'from 192.168.*.* to 10.0.*.*'
```

> 🔴 **`\1` 的歧义坑**:替换串 `'\1' + '0'` 拼成 `'\10'`,会被解读成「第 10 个分组」而不是「第 1 个分组 + 字符 0」!**`\g<1>` / `\g<net>` 永远无歧义,实战统一用 `\g<>` 形式**。反向引用在替换串里,所以替换串也要带 `r`。

### 形态 3:函数替换(替换内容要**算**出来)🔴

客服系统展示手机号要「中间四位打码」:`13812345678` → `138****5678`。打码逻辑是字符串运算,固定串和反向引用都做不到——**给一个函数,吃 Match 吐字符串**:

```python
re.sub(r'\b1[3-9]\d{9}\b',
       lambda m: m.group()[:3] + '****' + m.group()[-4:],   # 每个匹配都调一次
       '客服 13812345678 / 值班 13900001111')
# '客服 138****5678 / 值班 139****1111'
```

手机号模式拆解:`1` 开头 + 第二位 `[3-9]` + 再 9 位 `\d{9}` = 11 位;`\b` 防长数字串误伤(`13812345678901` 这种 14 位串,`\b` 会让匹配失败——可以试试去掉 `\b` 会怎样)。

> 🟡 **Java 对比**:Java 9+ 也有 `Matcher.replaceAll(m -> ...)`,但写法啰嗦少见;Python 的 `re.sub` 函数替换 + lambda(Ch04 学过)是**主流日常写法**。规则:**替换内容是匹配的「子集」用反向引用;要「计算」用函数**。

> ✅ 做 `mask_ip` 题:模式里把「前两段」捕获成命名分组,替换串用 `\g<名字>.*.*`。
> ✅ 做 `redact_phones` 题:`re.sub(手机号模式, lambda m: ...拼接..., text)`,首尾保留、中间 4 个 `*`。

---

## §10.6 re.split:按「模式」拆分(对应:`parse_alert_codes`)🟢

`str.split` 只认**一个固定分隔符**;告警规则这类人工维护的配置,分隔符花样百出(逗号、分号、空格混用)——`re.split` 按**模式**切:

### Java 对照最小例

```java
"500, 502;503".split("[,;\\s]+");   // Java 的 split 本身就吃正则
```

```python
re.split(r'[,;\s]+', '500, 502;503')   # ['500', '502', '503']
```

### 🟡 尾部空串:Java 丢,Python 留

这是两个语言行为不同的暗坑:

```java
"500,502,".split(",");   // Java:["500", "502"]   尾部空串被【悄悄丢弃】
```

```python
re.split(r',', '500,502,')   # Python:['500', '502', '']  尾部空串【保留】
',500'.split(','),  re.split(r',', ',500')
# 两边一样:['', '500']      前导空串都保留
```

Python 的哲学是「不偷偷丢数据」。所以拆完习惯**过滤空串**:

```python
[s for s in re.split(r'[,;\s]+', rule) if s]
```

### 真实场景例:解析告警规则配置

监控系统的告警规则是运维手写的字符串:`"500, 502;503"`(逗号分号空格随缘)。解析成状态码列表:

```python
rule = "500, 502;503"
[int(s) for s in re.split(r'[,;\s]+', rule) if s]   # [500, 502, 503]
```

`[,;\s]+` 的 `+` 让「逗号+空格」这种**连续分隔符**当作一个切口,不会产生空串碎片;`if s` 兜底首尾分隔符产生的空串。

> ✅ 做 `parse_alert_codes` 题:`re.split(r'[,;\s]+', ...)` → 列表推导 `int(s)` + `if s` 过滤。想想空字符串输入会得到什么。

---

## §10.7 str 方法 vs 正则:什么时候别用正则(对应:`parse_log_text`)🟡

正则是重武器:可读性差、易写错。**能用 str 方法解决的,一律别上正则**。决策表:

| 需求 | 用 | 例子 |
|------|----|------|
| 包含/前缀/后缀判断 | `in` / `startswith` / `endswith` | `line.startswith('#')` |
| 按**固定**分隔符切 | `str.split` / `splitlines` / `rsplit` | `ip.split('.')` |
| 去首尾空白 | `strip` / `lstrip` / `rstrip` | |
| 固定子串替换 | `str.replace` | `s.replace('\t', ' ')` |
| **模式**匹配/提取/替换 | `re` | IP、邮箱、日志结构、手机号 |

还记得 Ch06 吗?你用 `line.split('"')[1].split()[1]` 硬抠过同一份 nginx 日志——每一步都依赖「字段恰好按引号/空格分布」,格式一抖就碎。本章 `LOG_RE` 一个模式搞定,这就是「固定结构用 str,**模式结构用正则**」的分界线。

### 真实场景例:整份日志文本 → 结构化条目

按行切分是 str 的活(切的是固定字符 `\n`,与模式无关);行内解析是正则的活:

```python
def parse_log_text(text: str) -> list[dict]:
    entries = []
    for line in text.splitlines():      # str 的活:按行切(\n / \r\n 都认)
        m = LOG_RE.search(line)         # 正则的活:行内模式解析
        if m is None:
            continue                    # 脏数据行,跳过
        d = m.groupdict()
        d["status"] = int(d["status"])
        d["bytes"] = int(d["bytes"])
        entries.append(d)
    return entries
```

对 `nginx_logs.txt` 全文跑:13 行进,11 条出(2 行脏数据被 `continue` 静默跳过)。

> 🟡 **Java 对比**:`splitlines()` ≈ Java 11 `str.lines()`(都认 `\n`/`\r\n`);而 `"x".split("\n")` 只认 `\n`,Windows 换行会残留 `\r`。处理文本文件首选 `splitlines()`。

> ✅ 做 `parse_log_text` 题:`text.splitlines()` → 循环里 `LOG_RE.search` + 判空跳过 + `groupdict()` + 两个 int 转换 → append。

---

## §10.8 f-string 高级用法:对齐、千分位、百分比(对应:`format_top_table`)🟡

快报要「版面对齐」才好看。f-string 的 `{表达式:格式说明}` 一行搞定 Java `String.format` 的活儿:

### 对齐三剑客:`<` 左对齐、`>` 右对齐、`^` 居中

```python
ip, n = '192.168.1.1', 3
f"{ip:<16}"     # '192.168.1.1     '  左对齐,总宽 16(名字列)
f"{n:>5}"       # '    3'             右对齐,总宽 5(数字列右齐才好对比)
f"{'Top':^10}"  # '   Top    '        居中
```

```java
// Java 等价:String.format("%-16s%5d", ip, n) —— % 占位符顺序易错,f-string 内联所见即所得
```

### 数字与比例:`,` 千分位、`.2f` 精度、`.1%` 百分比

```python
f"{1234567:,}"      # '1,234,567'   千分位(= Java "%,d")
f"{3.14159:.2f}"    # '3.14'        保留 2 位小数
f"{5/11:.1%}"       # '45.5%'       自动 ×100 加 % 号(错误率直接出)
```

### 真实场景例:Top-N 排行表

```python
rows = [("192.168.1.1", 3), ("10.0.0.5", 2)]
lines = [f"== {'Top IP'} =="]
for rank, (name, count) in enumerate(rows, 1):
    lines.append(f"{rank}. {name:<16}{count:>5}")
print("\n".join(lines))
# == Top IP ==
# 1. 192.168.1.1         3
# 2. 10.0.0.5            2
```

名字列左对齐(读名字)、数字列右对齐(比大小)——这是排版的直觉约定。`enumerate(rows, 1)` 从 1 开始编号(Ch03)。

### 两个零碎但好用

```python
f"{ip=}"            # "ip='192.168.1.1'"   调试神器(3.8+),连变量名一起打
f"{d['ip']}"        # 双引号 f-string 里用单引号取键(3.12 前不能复用同种引号)
```

> 🟡 **Java 对比**:Java 15 的 text block 只管多行、不管插值;`String.format` 的 `%5d`/`%-16s` 与 f-string 的 `:>5`/`:<16` 一一对应。f-string 赢在内联表达式 + 格式说明紧贴变量。

> ✅ 做 `format_top_table` 题:标题行 `f"== {title} =="` + 每行 `f"{rank}. {name:<16}{count:>5}"`,`"\n".join` 收尾。空 rows 只输出标题行,不用特判。

---

## §10.9 综合:审计快报全链路(对应:`build_report`)🔴

最后把整条链路串起来:**原始文本 → 逐行解析(§10.4/§10.7)→ Counter 统计(Ch08 复用)→ f-string 排版(§10.8)**。每一段你都单独练过,现在合成一个函数:

```python
def build_report(text: str) -> str:
    lines = text.splitlines()                      # §10.7 str 按行切
    entries = []
    for line in lines:
        m = LOG_RE.search(line)                    # §10.4 命名分组解析
        if m is None:
            continue
        d = m.groupdict()
        d["status"] = int(d["status"])
        entries.append(d)

    total = len(entries)
    errors = sum(1 for e in entries if e["status"] >= 400)
    rate = errors / total if total else 0.0        # 防空文本除零
    status_counts = Counter(e["status"] for e in entries)          # Ch08
    top = Counter(e["ip"] for e in entries).most_common(3)

    report = [
        "===== 日志审计快报 =====",
        f"有效请求: {total} 条 (丢弃脏数据 {len(lines) - total} 行)",
        f"错误率: {rate:.1%} ({errors}/{total})",                    # §10.8 百分比
        f"状态码分布: {' '.join(f'{s}×{status_counts[s]}' for s in sorted(status_counts))}",
        "Top 3 IP:",
    ]
    for rank, (ip, count) in enumerate(top, 1):                     # §10.8 对齐
        report.append(f"{rank}. {ip:<16}{count:>5}")
    return "\n".join(report)
```

对 `nginx_logs.txt` 跑出的真实结果:

```
===== 日志审计快报 =====
有效请求: 11 条 (丢弃脏数据 2 行)
错误率: 45.5% (5/11)
状态码分布: 200×5 201×1 401×1 404×1 500×2 502×1
Top 3 IP:
1. 192.168.1.1         3
2. 10.0.0.5            2
3. 8.8.8.8             2
```

> 🟡 **设计要点**:注意 Top 榜的并列——`10.0.0.5` 和 `8.8.8.8` 都是 2 次,`most_common` 按**首次出现顺序**排(Ch08 §8.2),10.0.0.5 第 2 行先登场所以排前面。
> 💡 真实项目里这题会直接调你写好的 `parse_log_text`;本章作业为了让每题独立可测,把解析链条内联完整走一遍——正好当作全章总复习。

> ✅ 做 `build_report` 题:按上面的结构与文案实现(每行文案测试逐个验)。空文本要优雅降级(`rate` 防除零),其余不用特判。

---

## §10.10 Java 老手常踩的坑 ⚠️

1. **忘加 `r` 前缀**:`'\d'` 触发转义警告,`'\\d'` 双写难读。正则一律 `r'...'`(§10.1)。
2. **Java `matches()` ≠ Python `match()`**:Python `match` 只从头,**整串匹配是 `fullmatch`**。做输入校验用 `fullmatch`(§10.2)。
3. **findall 遇分组就变形**:模式里有 `(...)` 时返回分组内容而非整个匹配。只为重复/分组就用 `(?:...)`(§10.3)。
4. **命名分组忘写 `P`**:Python 是 `(?P<name>...)`,Java 是 `(?<name>...)`。报错是 `re.error: missing >`,看到就懂了(§10.4)。
5. **`\1` 的歧义**:`'\10'` 是「第 10 组」不是「第 1 组+0」。替换串统一用 `\g<1>` / `\g<name>`(§10.5)。
6. **Java `split` 丢尾部空串,Python `re.split` 保留**:迁移代码时边界行为不同,拆完记得 `if s` 过滤(§10.6)。
7. **贪婪 `.*` 吃多**:`re.search(r'<p>.*</p>', '<p>a</p><p>b</p>')` 一把吞掉两段;要 `<p>.*?</p>` 非贪婪(尽量少)。提取标签/引号内容时必查。
8. **拿正则干 str 的活**:`',' in s`、`s.split(',')` 这种固定串操作用 str 方法,又快又清楚(§10.7)。

---

## 📖 延伸阅读:本章不考,但值得知道

- **`finditer`**:返回 Match 迭代器,省内存且能拿到每个匹配的 `.start()`/`.end()` 位置。处理超大文本时替代 `findall`。
- **标志位**:`re.I` 忽略大小写、`re.M` 多行模式(`^$` 匹配每行)、`re.S` 让 `.` 连换行也匹配。如 `re.findall(r'error', log, re.I)`。
- **`re.VERBOSE`**:允许正则里写空白和注释,超长模式(如 LOG_RE)可排成多行带注释,可读性极佳。
- **纯 regex 校验 0-255**:`(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)` 一段,重复 4 次——能跑但没法读,所以 §10.2 选择正则+str 分工。

---

## 📝 本章作业

打开 **`ch10_assignment.py`**,9 个任务,一条主线串起来:校验白名单 IP → 全文捞 IP → 命名分组解析单行 → IP/手机号脱敏 → 拆告警规则 → 整文本解析 → 排版 Top-N → 汇总审计快报。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `is_valid_ip` | fullmatch + str 验范围 | 🟡 |
| `extract_ips` | findall + `(?:...)` | 🟢 |
| `parse_log_line` | 命名分组 + groupdict | 🔴 |
| `mask_ip` | sub + `\g<name>` 反向引用 | 🟡 |
| `redact_phones` | sub + lambda 函数替换 | 🟡 |
| `parse_alert_codes` | re.split 多分隔符 | 🟢 |
| `parse_log_text` | splitlines + 逐行正则 | 🟢 |
| `format_top_table` | f-string 对齐 | 🟡 |
| `build_report` | 综合全链路 | 🔴 |

```bash
uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v
```

全绿 = 掌握 Ch10。卡住 → 按对应表回查 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清 `search`/`match`/`fullmatch` 的区别,以及 Java `find()`/`matches()` 各自对应谁(§10.2)
- [ ] 知道 `findall` 遇到捕获分组返回什么、用 `(?:...)` 怎么规避(§10.3)
- [ ] 能写 `(?P<name>...)` 并用 `groupdict()` 一次导出 dict,说清和 Java 差哪个字母(§10.4)
- [ ] 说清什么时候该 `re.compile`、什么时候直接用 `re.xxx`(§10.4)
- [ ] 能写 sub 的三形态,解释 `'\10'` 为什么是坑、`\g<1>` 怎么救(§10.5)
- [ ] 说清 `re.split` 和 Java `split` 的尾部空串差异(§10.6)
- [ ] 给出「该用 str 方法还是正则」的判断原则(§10.7)
- [ ] 会用 `{x:<16}` `{n:,}` `{r:.1%}` 排版(§10.8)
- [ ] 9 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Python 的 `match` 和 Java 的 `matches` 名字像但语义不同,到底差在哪?做校验该用谁?」— 卡壳重读 §10.2
2. 「命名分组怎么写?`groupdict()` 比 `group(1)` 好在哪?」— 卡壳重读 §10.4
3. 「sub 替换的三形态分别适合什么场景?`\1` 有什么坑?」— 卡壳重读 §10.5

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch10 掌握后,进 **Ch11 · 数据交换:json / csv / datetime**——把解析出的日志数据序列化成 JSON 落盘,重点处理 `datetime` 序列化(对比 Java `java.time` 与 Jackson)。
