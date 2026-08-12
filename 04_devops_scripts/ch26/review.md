# Ch26 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 监控告警 pipeline 的 6 个环节? | 解析(extract)→ 聚合(count)→ 阈值(find_spike)→ 告警(build_alert)→ 报告(format_report)→ 定时(schedule)。每环节小函数,组合成 pipeline | ⬜ |
| 2 | 为什么监控不能「看到一条 5xx 就报警」? | 单条可能是偶发(用户网抖)。按分钟聚合 + 超阈值才说明系统真有问题 | ⬜ |
| 3 | re.match 和 re.search 区别?解析日志用哪个? | match 只匹配【开头】,search 在【任意位置】找。日志目标在行中间,用 search | ⬜ |
| 4 | extract_ts_status 非法行为什么返回 None 不抛异常? | 运维脚本绝不为一条脏数据崩。返回 None 让上游 continue 跳过(EAFP)。ts[:16] 截到分钟 | ⬜ |
| 5 | `counts[minute] = counts.get(minute,0)+1` 对应 Java 什么? | map.merge(minute,1,Integer::sum) 或 getOrDefault(k,0)+1。一行做「不存在当 0 + 累加」 | ⬜ |
| 6 | `500 <= status < 600` 是什么语法?Java 怎么写? | Python 链式比较。Java 得拆开:status >= 500 && status < 600 | ⬜ |
| 7 | find_spike_minutes 为什么要 sorted?阈值用 > 还是 >=? | sorted 让结果按分钟排序、稳定可测。阈值用 >=(达到就告) | ⬜ |
| 8 | 告警消息为什么返回 dict 不直接 print 字符串? | dict 能 json.dumps 推 webhook、入库、换格式;字符串锁死格式。数据 vs 表现分离(同 Ch25) | ⬜ |
| 9 | severity 怎么分级?为什么? | count >= threshold*2 算 critical,否则 warning。分级让告警系统决定要不要半夜打电话 | ⬜ |
| 10 | alert_on_spikes 里为什么要 `counts[m]`? | find_spike_minutes 只返回分钟字符串;告警要的 count 得回 counts 里查(前输出是后输入) | ⬜ |
| 11 | format_report 怎么把多行拼成一个字符串?对应 Java 什么? | "\n".join(lines) ≈ String.join("\n", lines)。空列表单独返回「系统正常」文案 | ⬜ |
| 12 | schedule 库怎么表达「每 10 分钟跑」?要怎么真正触发? | schedule.every(10).minutes.do(f)。但要配 while True + schedule.run_pending() 才真正触发(进程内事件循环) | ⬜ |
| 13 | schedule vs cron vs Java ScheduledExecutorService?生产能只靠 schedule 吗? | schedule=进程内(挂了就停,单点);cron/systemd=系统级可靠;Java SES=schedule 等价。生产别只靠 schedule,要守护/兜底 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「监控告警 pipeline 六环节」?
- [ ] 能说清「dict.get(k,0)+1 流式聚合 vs Java merge」?
- [ ] 能说清「数据 vs 表现分离」(build_alert 出 dict,format_report 出文本)?
- [ ] 能说清「schedule 的局限 + 生产兜底」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
