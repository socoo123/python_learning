# Ch27 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 配置分层的规则?环境变量读出来什么类型? | 默认 < 环境变量覆盖。环境变量读出来【永远是字符串】,比较数字必须 float()/int() 转换,否则字符串比较结果错乱 | ⬜ |
| 2 | load_thresholds 的设计?对应 Java 什么? | 默认 dict 兜底 + if KEY in env 覆盖 + float 转换。= Spring @Value("${x:默认}") + 自动类型转换。生产升级版是 pydantic-settings(Ch22) | ⬜ |
| 3 | check_disk/check_memory 为什么返回带 ok 键的 dict? | 不只返回数字,直接给「健不健康」判断,上游用起来简单。ok = percent < threshold(阈值来自配置) | ⬜ |
| 4 | build_health_report 怎么汇总?all([]) 返回什么? | all(c.get("ok",False) for c in checks.values()) = Java allMatch。all([]) 返回 True(vacuous truth),所以空检查视为健康 | ⬜ |
| 5 | send_webhook 为什么用 stdlib urllib 不引 requests? | 零依赖,巡检脚本越少依赖越好部署(受限服务器)。简单 POST 用 urllib 够了。requests 要装 | ⬜ |
| 6 | webhook POST JSON 的关键步骤? | dumps(payload).encode("utf-8") → Request(url, data, Content-Type:application/json, method=POST) → urlopen。忘 Content-Type 服务器不认 | ⬜ |
| 7 | send_webhook 为什么必须 except 返回 bool? | 网络调用可能抖动/超时/DNS 失败。webhook 推送【绝不】让巡检脚本崩(崩了就漏告警)。EAFP,失败返 False 记日志 | ⬜ |
| 8 | 巡检脚本生产化的要点? | ① systemd/supervisor 守护 ② webhook URL 走环境变量 ③ 多次失败告警升级 ④ 加日志(Ch12)⑤ schedule 定时(Ch26) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「配置分层 + 环境变量类型转换坑」?
- [ ] 能说清「webhook 为何 except 返回 bool,绝不抛」?
- [ ] 能说清「all([]) 的 vacuous truth 语义」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
