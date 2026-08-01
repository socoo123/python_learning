# Ch32 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Agent 和 Ch28 单轮调用本质区别? | Ch28 流程【写死】(你写 call_llm);Agent 让【模型决定】流程(调啥工具/几次/何时停)。决策权从代码→模型 | ⬜ |
| 2 | ReAct 是什么?三个环节? | Reason+Act+Observation 循环:模型【思考】(Reason)→【调工具】(Act)→【看结果】(Observation)→再思考,直到给答案 | ⬜ |
| 3 | make_registry 为什么用字典不用 if/else? | 表驱动 vs 分支驱动。字典【开放】,加工具只改一行;if/else 每加工具要改代码。函数当一等公民,自带 __name__ | ⬜ |
| 4 | execute_tool 为什么错误也返回字符串? | 错误【当数据不当炸弹】。错误信息本身有价值——模型看到「未知工具 add」下轮能纠错。raise 会剥夺模型自我修正机会 | ⬜ |
| 5 | **args 是什么?结果为什么 str()? | `**args` 把 dict 展开成关键字参数 `{"a":2}→func(a=2)`。str() 因为结果要拼进 prompt 喂回 LLM,模型只懂文本 | ⬜ |
| 6 | parse_action 怎么拆 TOOL: name ARGS: {...}? | partition("ARGS:") 拆成三段(name/分隔符/json),只拆第一个。json.loads 解析 args。比 split 更可控 | ⬜ |
| 7 | max_iters 为什么必须有? | LLM 会犯傻【无限循环】(反复调同工具)。max_iters 是【安全阀】,防烧光 API 额度。= Java 的超时熔断 | ⬜ |
| 8 | 文本协议(ReAct)vs 原生 tool use 选哪个? | 【生产选原生】tool use(结构化 tool_call,不解析失败)。文本协议只用于原理学习/不支持原生的小模型。LangChain ReAct 内部还用文本 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Agent vs 单轮:决策权从代码转移到模型」?
- [ ] 能画出 ReAct 循环图(Reason→Act→Observation→再 Reason)?
- [ ] 能说清「为什么错误返回字符串而不是 raise」+「为什么 str()」?
- [ ] 能说清「max_iters 的必要性」+「生产为什么用原生 tool use」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
