# Ch29 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `fill_template` 怎么做到缺失占位符不报错? | `format_map(_Safe(kwargs))`;`_Safe` 是 dict 子类,`__missing__` 返回 `""`。普通 format 遇缺失键抛 KeyError | ⬜ |
| 2 | few-shot 是什么?结尾「输出:」为什么不写答案? | 给模型几个 输入→输出 示例让它照格式续写。结尾留空利用**完形填空效应**;写了答案模型可能照抄 | ⬜ |
| 3 | 生产代码里 Prompt 为什么要收敛到一个组装函数? | 单一事实来源:格式只在一处定义,改格式只改一处;散落手拼会格式漂移、解析端全线崩 | ⬜ |
| 4 | 为什么不能直接 `json.loads` LLM 的输出? | 常带 ```json 围栏 + 前后解释文字 → 必崩。`parse_json_lenient` 两级兜底:先抠围栏(非贪婪),再抠最外层 `{...}`(贪婪) | ⬜ |
| 5 | 抠 JSON 的正则为什么要带 `re.S`?围栏里的 `.*?` 为什么要非贪婪? | `re.S` 让 `.` 匹配换行(多行 JSON 才抠得到);非贪婪让匹配到围栏结尾就停,不多吃 | ⬜ |
| 6 | `parse_structured` 怎么把 JSON 变强类型? | `parse_json_lenient` 取 dict → `model_cls.model_validate(data)`。= Jackson `readValue` + 校验;类型不符/缺字段抛 ValidationError | ⬜ |
| 7 | Pydantic 的「矫正 vs 校验」什么意思? | `"5"` → `5` 能转则转(宽容);`"不是数字"` 转不了才抛(严格) | ⬜ |
| 8 | CoT 是什么?关键短语?怎么程序化抽答案? | Chain-of-Thought:要求模型先写推理再给答案,提升复杂题准确率。短语「一步步思考」。用 `<推理>/<答案>` 标签包裹,正则一抠一个准 | ⬜ |
| 9 | `analyze_review` 管道的三步?换真实 LLM 要改哪? | 组装 prompt(build_analysis_prompt)→ 调用(fake_llm)→ 解析(parse_structured)。只把 fake_llm 换成 Ch28 的 call_llm,其余不动 | ⬜ |
| 10 | 测试 LLM 管道为什么用录制回放(fake_llm)而不是真调 API? | 真实调用不可重现、要钱、要网;录制回放(≈ Java WireMock)让管道逻辑可确定性测试 | ⬜ |
| 11 | 比「容错抠 JSON」更根本的解法是什么? | SDK 原生结构化输出(response_format / tool use)从源头强制合法 JSON;容错解析只是兜底 | ⬜ |
| 12 | Prompt 工程为什么算「工程」? | 同模型不同问法质量差很多;Prompt 是「给 LLM 的 SQL」——用可复制套路稳定产出程序可消费的结果 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「json.loads LLM 输出会崩 + 两级兜底正则的分工 + 更根本的结构化输出」?
- [ ] 能说清「few-shot 完形填空效应 + 答案位留空 + 示例 1-3 个够用」?
- [ ] 能说清「model_validate 的矫正 vs 校验,以及比 dict 手工取值强在哪」?
- [ ] 能说清「fake_llm 录制回放的工程意义,换真实 LLM 改哪一行」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
