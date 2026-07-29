# Ch11 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `json.loads/load` 和 `dumps/dump` 区别? | 带 `s` 的(loads/dumps)操作【字符串】;不带的(load/dump)操作【文件】。loads=解析,dumps=序列化 | ⬜ |
| 2 | `json.dumps` 默认把中文输出成什么?怎么修? | 默认 `ensure_ascii=True`,中文转义成 `\uXXXX`(不可读)。加 `ensure_ascii=False` 让中文原样输出 | ⬜ |
| 3 | 为什么 `json.dumps(datetime对象)` 会报错?怎么解决? | json 只认基本类型,不认识 datetime。解法:`json.dumps(obj, default=钩子函数)`,钩子里把 datetime 转成 isoformat 字符串。= Java 自定义 JsonSerializer | ⬜ |
| 4 | Python `date`/`datetime`/`timedelta` 对应 Java 什么? | date=LocalDate,datetime=LocalDateTime,timedelta=Duration/Period | ⬜ |
| 5 | ISO 字符串和 datetime 怎么互转? | `datetime.fromisoformat(s)` 字符串→对象;`dt.isoformat()` 对象→字符串。这是 3.7+ 最佳实践,比 strptime/strftime 简单 | ⬜ |
| 6 | 两个 date 相减得到什么?怎么取天数? | 得到 `timedelta`,`.days` 取整天数,`.total_seconds()` 取总秒数。要绝对值用 abs() | ⬜ |
| 7 | naive datetime 和 aware datetime? | naive=无时区(默认),aware=带 tzinfo。**跨时区必须用 aware**,否则出错。生产代码始终带时区 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「json.dumps 为什么不能直接序列化 datetime,default 钩子怎么救」?
- [ ] 能说清「naive/aware datetime 的区别和坑」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
