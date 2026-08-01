# Ch29 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | fill_template 怎么容错(缺失占位符不报错)? | format_map(_Safe(kwargs)),_Safe 是 dict 子类,__missing__ 返回 ""。普通 format 遇缺失键抛 KeyError | ⬜ |
| 2 | few-shot 是什么?结尾为什么留「输出:」不写答案? | 给模型几个 输入→输出 示例让它照做。结尾留「输出:」利用【完形填空】效应,模型自动接着写 | ⬜ |
| 3 | 为什么不能直接 json.loads LLM 输出? | 模型常带 ```json 围栏、前后解释文字 → json.loads 必崩。用 parse_json_lenient 兜底(先围栏再 {...}) | ⬜ |
| 4 | parse_structured 怎么把 JSON 变强类型? | parse_json_lenient 取 dict → model_cls.model_validate(data)。= Jackson readValue,带类型校验,类型不符抛 ValidationError | ⬜ |
| 5 | 比手写正则解析 LLM 输出更好的办法? | 结构化输出:Pydantic model_validate(强类型校验)或工具调用(从源头强制合法 JSON)。正则只做兜底 | ⬜ |
| 6 | CoT 是什么?关键短语? | Chain-of-Thought:要求模型【先写推理再给答案】,提升复杂题准确率。关键短语「一步步思考」/「Let's think step by step」 | ⬜ |
| 7 | 生产级 LLM 应用的标准管道? | 模板填充 → few-shot → 调用(call_llm)→ 容错解析(parse_json_lenient)→ 强类型对象(parse_structured) | ⬜ |
| 8 | Prompt 工程为什么算「工程」? | 同模型不同问法质量差很多。Prompt 是【给 LLM 的 SQL】——用可复制套路稳定把输出变成可用的东西 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「json.loads LLM 输出会崩 + 兜底 + 更好的结构化办法」?
- [ ] 能说清「few-shot 完形填空 + CoT 提升准确率」?
- [ ] 能说清「Pydantic model_validate 强类型解析 vs 手写正则」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
