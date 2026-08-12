# Ch27 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 配置分层的两层规则?env 读出来什么类型? | 默认值兜底 < 环境变量覆盖。读出来【永远是 str】,"95" 必须 float() 才能和数字阈值比 | ⬜ |
| 2 | `"95" < "80"` 结果?为什么危险? | False(字典序,"9">"8")。不崩但结果错:磁盘 95% 还认为没超 80%。配置层先 float() 再比较 | ⬜ |
| 3 | load_thresholds 为什么入参 env dict 而不直接读 os.environ? | 依赖当参数传:测试传 {"DISK_THRESHOLD":"95"} 即可,不用 monkeypatch.setenv、不污染真实环境。运行时传 dict(os.environ) | ⬜ |
| 4 | 手写配置分层的生产升级版? | pydantic-settings 的 BaseSettings(Ch22):声明字段即完成读 env + 类型转换 + 默认值 + 必填 fail-fast。= Spring @ConfigurationProperties | ⬜ |
| 5 | psutil.disk_usage 的 free/total 单位?报告里怎么处理? | 【字节】!必须 / (1024**3) 转 GB,round(x, 2) 留两位小数。percent 字段直接是百分比 | ⬜ |
| 6 | psutil.cpu_percent() 不传 interval 的坑? | 首次调用恒返回 0.0(它算「距上次调用」的平均,首次没有"上次")→ 假健康。传 interval=0.1 阻塞采样 | ⬜ |
| 7 | check_port 怎么探活?失败有哪些异常? | socket.create_connection((host,port), timeout=2.0),with 包住用完即关。拒连/超时/DNS 失败全是 OSError 子类,一个 except 兜住,返回 ok=False 不抛 | ⬜ |
| 8 | 网络调用忘 timeout 会怎样? | urlopen/create_connection 默认可能挂起几分钟,巡检脚本卡死。网络调用【必设 timeout】 | ⬜ |
| 9 | build_health_report 怎么汇总?all([]) 返回什么? | all(c.get("ok",False) for c in checks.values()) = Java allMatch。all([]) 返回 True(vacuous truth),空检查视为健康 | ⬜ |
| 10 | 汇总时为什么 c.get("ok", False) 而不是 c["ok"]? | 脏数据缺 ok 键时 get 按 False 处理,宁误告不漏判;c["ok"] 遇脏数据 KeyError 崩掉巡检 | ⬜ |
| 11 | urllib POST JSON 四步? | dumps(payload)→encode("utf-8")→Request(url, data, Content-Type:application/json, method=POST)→urlopen(timeout)。2xx 算送达 | ⬜ |
| 12 | send_webhook 为什么 except Exception 返回 False?为什么不用 requests? | 网络抖动/超时/DNS 失败绝不让巡检崩(崩了就漏告警),失败返 False 记日志。urllib 零依赖,受限服务器好部署;复杂 HTTP 才上 requests/httpx | ⬜ |
| 13 | run_inspection 的 webhook_sent 三态? | None=没推(健康或没配 url);True=推了且成功;False=推了但失败 | ⬜ |
| 14 | run_inspection 的编排逻辑怎么不测真机? | 各检查是模块级 def,测试 monkeypatch.setattr(模块, "check_disk", fake) 换成假数据,只验编排:阈值透传、异常才推、payload 是报告 | ⬜ |
| 15 | 巡检脚本生产化清单? | ① systemd/supervisor 守护或 cron(schedule 进程挂就停)② webhook URL 走环境变量 ③ 连续推送失败告警升级 ④ 加日志(Ch12)⑤ check_port 配置驱动接入 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「配置分层 + 环境变量类型转换坑」?
- [ ] 能说清「cpu_percent 首次 0.0」和「disk free 是字节」两坑?
- [ ] 能说清「webhook 为何 except 返回 bool,绝不抛」?
- [ ] 能说清「all([]) 的 vacuous truth」和「get 防御脏数据」?
- [ ] 能说清「模块级小函数 + monkeypatch」的可测性设计?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
