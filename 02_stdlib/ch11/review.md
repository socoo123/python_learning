# Ch11 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `json.loads/load` 和 `dumps/dump` 区别? | 带 `s` 的操作【字符串】,不带的操作【文件句柄】。loads=解析,dumps=序列化。记法:**s = string** | ⬜ |
| 2 | 默写 JSON → Python 类型映射(6 种)? | object→dict,array→list,string→str,number→int/float,true/false→**True/False**,null→**None**(首字母大写,两个最易错) | ⬜ |
| 3 | MQ 消费里解析 JSON 失败,为什么不该 try/except 返回 None? | 吞异常=坏事件静默丢失,对账对不上查三天。让 `JSONDecodeError`(ValueError 子类)抛给上层,进**死信队列** | ⬜ |
| 4 | `json.dumps` 三个高频参数?各解决什么? | `ensure_ascii=False` 中文不转义(默认转 `\uXXXX`);`indent=2` 美观缩进;`sort_keys=True` 键排序→同样内容永远同样字符串,可 diff 对账 | ⬜ |
| 5 | ISO 字符串 ↔ datetime 怎么互转?`"Z"` 后缀呢? | `datetime.fromisoformat(s)` 解析(3.11+ 直接认 Z=UTC);`dt.isoformat()` 转回。非 ISO 格式才用 `strptime(s, 格式串)` | ⬜ |
| 6 | 自定义展示格式(如财务要的 `2026/07/21`)用什么? | `dt.strftime("%Y/%m/%d")`(f=format)。占位符:%Y 年 %m 月 %d 日 %H 时 %M 分 %S 秒 | ⬜ |
| 7 | 日期加减推算用什么?为什么不能自己算天数? | `date + timedelta(days=n)`(自动跨月/跨年/闰年);`date - date` 得 timedelta,`.days` 取天数。自己算要处理大小月闰年,必错 | ⬜ |
| 8 | naive vs aware datetime?对应 Java 什么? | naive 无时区(≈LocalDateTime),aware 带 tzinfo(≈OffsetDateTime)。判断:`dt.utcoffset()` 是 None 即 naive。**跨时区必须 aware** | ⬜ |
| 9 | 时区换算正确姿势?手动 `+timedelta(hours=8)` 错在哪? | `aware_dt.astimezone(timezone(timedelta(hours=8)))`,按「同一时刻」换算、自动跨日。手动 +8h 数值对但**丢掉时区信息**,结果还是 naive | ⬜ |
| 10 | 对 naive datetime 调 `astimezone()` 会发生什么? | **不报错**,但按【运行机器本地时区】解释——UTC 机房的服务器和 +08:00 的本机算出来差 8 小时,CI 红本地绿的悬案源头 | ⬜ |
| 11 | 为什么 CSV 不能 `split(",")`? | 值可能被引号包住且内含逗号(`"1,299.00"`),split 会裂开。`csv` 模块懂引号规则,还自动处理 `\r\n`/`\n` 两种换行 | ⬜ |
| 12 | `csv.DictReader` 两个必记细节? | ① 读出的**所有值都是 str**,数字列要 `float()/int()`;② 内存解析用 `io.StringIO(text)` 包装,不用落地文件 | ⬜ |
| 13 | `csv.DictWriter` 写出三步?行尾是什么? | `DictWriter(buf, fieldnames=[...])` → `writeheader()` → `writerows(rows)`,最后 `buf.getvalue()`。行尾默认 **`\r\n`**(RFC 4180/Excel 方言),值含逗号自动加引号 | ⬜ |
| 14 | `json.dumps` 遇到 datetime 报什么错?怎么用 default 钩子救? | TypeError(JSON 规范没有日期类型)。`json.dumps(obj, default=钩子)`:钩子里 `isinstance(o,(datetime,date))` → `o.isoformat()`,其他类型 **raise TypeError**(返回 None 会静默放走坏数据)。嵌套结构递归生效 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「json.dumps 为什么不能直接序列化 datetime、default 钩子何时被调用、钩子里为什么必须 raise」?
- [ ] 能口算 `"2026-07-20T17:00:00Z"` 的北京时间,并说清 naive.astimezone 的坑?
- [ ] 能说清「CSV 为什么不能 split(",")、DictReader 的值为什么全是 str」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
