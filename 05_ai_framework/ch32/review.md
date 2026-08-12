# Ch32 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆，再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面（问题） | 背面（答案） | 掌握 |
|---|---|---|---|
| 1 | Agent 和 Ch28 单轮调用本质区别？ | Ch28 流程【写死】（你写 call_llm）；Agent 让【模型决定】流程（调啥工具/几次/何时停）。决策权从代码→模型 | ⬜ |
| 2 | ReAct 是哪三个环节的循环？ | Reason（思考）→ Act（调工具）→ Observation（看结果）→ 再 Reason，直到模型给 answer | ⬜ |
| 3 | make_registry 为什么用字典不用 if/else？ | 表驱动 vs 分支驱动。字典【开放】，加工具只改登记一行；if/else 每加工具要改主循环。函数一等公民，自带 `__name__` | ⬜ |
| 4 | execute_tool 为什么错误也返回字符串而不是 raise？ | 错误【当数据不当炸弹】。错误信息是有价值的观察——模型看到「未知工具」下轮能纠错；raise 中断循环 = 剥夺模型自我修正机会 | ⬜ |
| 5 | `registry[name](**args)` 里 `**args` 干嘛的？结果为什么 str()？ | `**args` 把 dict 展开成关键字参数 `{"name":"键盘"}`→`f(name="键盘")`。str() 因为观察要拼进 prompt 喂回 LLM，模型只懂文本 | ⬜ |
| 6 | parse_action 拆 `TOOL: name ARGS: {...}` 为什么用 partition 不用 split？ | `partition("ARGS:")` 只拆【第一个】分隔符，稳定返回三段；split 会全拆，JSON 里含 "ARGS:" 字样就错位 | ⬜ |
| 7 | run_agent_loop 里 max_iters 为什么必须有？ | LLM 会犯傻【无限循环】（反复调同工具）。max_iters 是【安全阀】防烧光 API 额度 ≈ Java 超时熔断/线程池拒绝策略 | ⬜ |
| 8 | observations 为什么每轮全量传给 decider？ | LLM【无状态】，下一轮决策依赖之前的工具结果（如第 2 轮的 SKU 来自第 1 轮观察）。代价是 token 贵，复杂任务配 Memory 摘要 | ⬜ |
| 9 | decider 为什么能离线测？ | 【依赖注入】：decider 只是个 `f(query, observations)->dict` 的可调用。测试传 FakeDecider 按脚本出牌，生产传接 LLM 的函数 ≈ Java 构造器注入 Mock | ⬜ |
| 10 | 工具 schema 是干嘛的？description 为什么重要？ | schema（名字+描述+参数 JSON Schema）告诉模型【有哪些工具可用】。模型选工具全靠读 description——写烂了就乱调 | ⬜ |
| 11 | 文本协议（ReAct）vs 原生 tool use，生产选哪个？ | 【生产选原生】tool use（结构化 tool_call，不会解析失败）。文本协议只用于原理学习/不支持原生的小模型；LangChain ReAct 内部还用文本 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Agent vs 单轮：决策权从代码转移到模型」？
- [ ] 能画出 ReAct 循环图（Reason→Act→Observation→再 Reason）？
- [ ] 能走一遍「机械键盘还有货吗」的两步工具链（lookup_product 拿 SKU → check_stock 查库存）？
- [ ] 能说清「为什么错误返回字符串而不是 raise」+「为什么 str()」？
- [ ] 能说清「max_iters 的必要性」+「生产为什么用原生 tool use」？

## 📅 复习日程

- [ ] +1 天　日期：________
- [ ] +3 天　日期：________
- [ ] +7 天　日期：________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
