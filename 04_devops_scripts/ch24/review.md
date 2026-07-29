# Ch24 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | subprocess 对应 Java 什么?run 返回什么对象? | = ProcessBuilder。run 返回 CompletedProcess,含 .returncode/.stdout/.stderr/.args。一步到位,比 Java start+waitFor+读流爽 | ⬜ |
| 2 | subprocess.run 的 capture_output/text/timeout 各防什么坑? | capture_output=True 把输出收进结果(否则打到控制台拿不到);text=True 返回 str 不是 bytes;timeout=超时抛 TimeoutExpired(否则脚本 hang) | ⬜ |
| 3 | 为什么不能 shell=True? | 命令注入风险:shell=True 把命令交给 shell 解析,参数含用户输入就可注入。永远传 list 让 Python 直接 exec | ⬜ |
| 4 | run 默认非 0 退出码会抛异常吗?要它抛怎么办? | 默认【不抛】(check=False),非 0 只是 returncode!=0。要抛加 check=True → 抛 CalledProcessError | ⬜ |
| 5 | run_command_safely 的设计模式?返回什么? | EAFP:try/except 捕获 FileNotFoundError/TimeoutExpired,把异常拍扁成 (bool, str) 返回。调用方不用 try,看布尔。= Java catch IOException 返回 Result | ⬜ |
| 6 | 跨平台 ping 怎么写?通不通怎么看? | platform.system() 判系统:Unix 用 -c/-W,Windows 用 -n/-w。returncode==0=通。subprocess timeout 要比 ping 自身 -W 大做兜底 | ⬜ |
| 7 | psutil 对 Java 老手的意义?读内存/磁盘怎么写? | = Java OperatingSystemMXBean 的平替但跨平台一致。内存:psutil.virtual_memory().percent;磁盘可用:psutil.disk_usage(path).free / (1024**3) | ⬜ |
| 8 | .invalid 域名为什么适合测试 ping 失败? | RFC2606 保留假域名,DNS 查询【立即失败】,ping 快速返回非 0,不用真等超时 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「subprocess 三参数 capture_output/text/timeout 防的三个坑」?
- [ ] 能说清「shell=True 的命令注入风险」?
- [ ] 能说清「EAFP 把异常拍扁成 (bool,str) 的运维封装模式」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
