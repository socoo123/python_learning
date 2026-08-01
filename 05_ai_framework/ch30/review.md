# Ch30 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | LCEL 是什么?`\|` 为什么能串联? | LangChain 声明式链语法:prompt \| model \| parser,数据左→右流。`\|` 靠 Runnable 重载 __or__/__ror__(运算符重载)= Java Stream/Reactor 管道 | ⬜ |
| 2 | PromptTemplate.invoke 返回什么?要纯文本怎么办? | 返回【StringPromptValue 对象】不是 str!要文本用 .to_string() 或 .format()。这是 LCEL 统一接口(组件间传对象) | ⬜ |
| 3 | 为什么普通函数要包成 RunnableLambda? | 只有 Runnable 才能用 `\|` 串进管道。RunnableLambda 把任意 f(x)->y 包成 Runnable 步。统一接口让 FakeModel/真模型可互换 | ⬜ |
| 4 | build_chain 为什么要 to_text 适配?真链需要吗? | FakeModel(lambda)只会 f"{s}" 拼接,遇 PromptValue 渲染乱码,所以要 to_text 转字符串。【真链不需要】——真 ChatModel 原生吃 PromptValue | ⬜ |
| 5 | LLM 记忆怎么实现?LangChain 有什么? | 无状态→记忆=客户端维护 messages 列表每轮 append、下次带上。LangChain 有 RunnableWithMessageHistory 自动管。历史越长越贵 | ⬜ |
| 6 | LCEL 自带哪些能力? | stream(流式)、batch、retry、回调/可观测、统一 invoke 接口。一个链声明式拿到这些 | ⬜ |
| 7 | 直接 SDK 还是 LangChain? | 简单一问一答→SDK(轻、可控)。复杂流水线(RAG/Agent/多步/流式/记忆)→LangChain 省事但抽象多、调试难。别无脑上 | ⬜ |
| 8 | 记忆无限增长的坑? | 历史全发→token 爆炸+超窗口。生产要窗口记忆(留最近N轮)/摘要记忆(压缩旧对话) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「LCEL `\|` = 运算符重载管道」?
- [ ] 能说清「PromptValue vs str + to_text 适配」?
- [ ] 能说清「何时 SDK 何时 LangChain」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
