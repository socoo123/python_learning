# Ch24 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `subprocess` 对应 Java 什么?`run` 返回什么对象? | = `ProcessBuilder`。`run` 返回 `CompletedProcess`(`.args/.returncode/.stdout/.stderr`),一个调用顶 Java 的 start+读流+waitFor 五步 | ⬜ |
| 2 | `capture_output` / `text` / `timeout` 三参数各防什么坑? | 不设 capture_output → `r.stdout` 是 `None`;不设 text → 拿到 bytes 要手动 decode;不设 timeout → 子进程 hang 脚本永远 hang | ⬜ |
| 3 | 为什么不能 `shell=True`? | 命令注入:shell 会解析 `;` `|` 等元字符,参数含用户输入就被注入。永远传 list 让 Python 直接 exec | ⬜ |
| 4 | `run` 遇到非 0 退出码会抛异常吗?要它抛怎么办? | 默认**不抛**(`check=False`),非 0 只是 `returncode != 0`。加 `check=True` → 抛 `CalledProcessError` | ⬜ |
| 5 | `run_command_safely` 的封装模式?catch 有什么讲究? | EAFP:异常拍扁成 `(bool, str)` 返回,调用方看布尔(= Java catch IOException 返回 Result)。catch 要具体(FileNotFoundError/TimeoutExpired),裸 `except:` 会吞掉 KeyboardInterrupt 和 bug | ⬜ |
| 6 | 三平台 ping 参数各是什么?最大的坑? | Windows `-n 1 -w <ms>`;macOS `-c 1 -W <ms>`;Linux `-c 1 -W <秒>`。🔴 macOS 的 `-W` 是毫秒、Linux 是秒,同名参数差 1000 倍 | ⬜ |
| 7 | ping 已经有 `-W` 超时了,为什么 `subprocess.run` 还要再设 timeout? | 双保险:参数单位搞错/平台差异导致 ping 自身死等时,subprocess timeout(设稍大,如 timeout+2)会杀掉它,脚本不卡死 | ⬜ |
| 8 | 测 ping「不通」分支为什么要用 `.invalid` 域名? | RFC2606 保留假域名,DNS 查询**立即失败**,ping 秒回非 0,不用真等超时;测「通」用 127.0.0.1 回环 | ⬜ |
| 9 | 字节 → GB 用 1024³ 还是 1000³?为什么? | 1024³(= `df -h` 的数)。1000³ 是硬盘厂商标的 GB,数字虚高——「500GB 硬盘只剩 465G」就是这个差 | ⬜ |
| 10 | 为什么 `check_thresholds` 要拆成不碰 psutil 的纯函数? | 可测性:纯函数输入确定→输出确定,随便构造 metrics 断言;揉在一起的话,你没法让测试机内存「刚好 81%」 | ⬜ |
| 11 | `psutil` 读内存使用率/磁盘剩余各怎么写? | `psutil.virtual_memory().percent`(直接给百分比);`psutil.disk_usage(path).free`(字节,要过 bytes_to_gb) | ⬜ |
| 12 | `psutil.cpu_percent()` 首次调用为什么返回 0.0? | 它算「距上次调用」的平均,首次没有「上次」所以无意义。传 `interval=0.1` 阻塞采样,或丢弃首次值 | ⬜ |

## 🎓 费曼自检

- [ ] 能不翻书说清「subprocess 三参数各防什么坑 + shell=True 为什么禁用」?
- [ ] 能讲清「EAFP 拍扁成 (bool,str)」模式,以及为什么 catch 具体异常?
- [ ] 能默写三平台 ping 参数,讲清 macOS 毫秒坑和超时双保险?
- [ ] 能讲清「阈值判断拆纯函数」的可测性论证?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
