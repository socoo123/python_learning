# Ch26 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 监控告警 pipeline 的 5 个环节? | 解析(extract)→ 聚合(count)→ 阈值(find_spike)→ 告警(build_alert)→ 定时(schedule)。每环节小函数,串成 pipeline | ⬜ |
| 2 | re.match 和 re.search 区别?解析日志用哪个? | match 只匹配【开头】,search 在【任意位置】找。日志目标在行中间,用 search | ⬜ |
| 3 | extract_ts_status 非法行为什么返回 None 不抛异常? | 运维脚本绝不为一条脏数据崩。返回 None 让上游 continue 跳过(EAFP)。ts[:16] 截到分钟 | ⬜ |
| 4 | `counts[minute] = counts.get(minute,0)+1` 对应 Java 什么? | map.merge(minute,1,Integer::sum) 或 getOrDefault(k,0)+1。一行做「不存在当 0 + 累加」 | ⬜ |
| 5 | 告警消息为什么返回 dict 不直接 print 字符串? | dict 能 json.dumps 推 webhook、入库、改格式;字符串锁死格式。数据 vs 表现分离(同 Ch25) | ⬜ |
| 6 | schedule 库怎么表达「每 10 分钟跑」?要怎么真正触发? | schedule.every(10).minutes.do(f)。但要配 while True + schedule.run_pending() 才真正触发(进程内事件循环) | ⬜ |
| 7 | schedule vs cron vs Java ScheduledExecutorService? | schedule=进程内(挂了就停,单点);cron/systemd timer=系统级可靠;Java ScheduledExecutorService=schedule 的 Java 等价 | ⬜ |
| 8 | 为什么生产监控不能只靠 schedule? | 进程挂了定时就停(单点)。要 systemd/supervisor 守护,或用 cron/任务队列(Celery/ARQ)兜底 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「监控告警 pipeline 五环节」?
- [ ] 能说清「dict.get(k,0)+1 流式聚合 vs Java merge」?
- [ ] 能说清「schedule 的局限 + 生产兜底」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
