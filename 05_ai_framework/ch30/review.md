# Ch30 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | LCEL 是什么?`|` 为什么能串联组件? | LangChain 声明式链语法:每个组件是 Runnable,`a \| b` = `a.__or__(b)` 返回新 RunnableSequence(Ch05 运算符重载)。数据左→右流,像 Java Stream/Reactor 管道 | ⬜ |
| 2 | `PromptTemplate.invoke(...)` 返回什么?要纯文本怎么办? | 返回 **StringPromptValue 对象**,不是 str(LCEL 统一接口:组件间传对象)。要文本用 `.to_string()` 或 `.format(...)` | ⬜ |
| 3 | 普通函数能直接 `\|` 进 LCEL 管道吗?怎么办? | 不能(不是 Runnable,`\|` 会 TypeError)。用 `RunnableLambda(fn)` 包成 Runnable 步骤——FakeModel 和真 ChatModel 因此可互换 | ⬜ |
| 4 | build_chain 里 to_text 适配是干嘛的?真实链需要吗? | prompt 步输出 PromptValue,FakeModel(普通函数)只会 f"{s}" 拼接会渲染成 repr 乱码,所以要 to_text 转 str。**真链不需要**——ChatModel 原生吃 PromptValue | ⬜ |
| 5 | chain 有哪些执行方式?区别? | `invoke(单条)` / `batch(list[dict],内部并发,顺序对应)` / `stream(流式)`。批量别手写 for+invoke,用 batch | ⬜ |
| 6 | LLM 对话「记忆」在代码层面是什么? | LLM 无状态 → 记忆 = 客户端维护 messages 列表,每轮 append、下次把历史渲染进 prompt 一起发。LangChain 有 RunnableWithMessageHistory 自动管 | ⬜ |
| 7 | append_turn / chat_once 为什么返回新列表而不改入参? | 可变默认参数陷阱(Ch02):mutate 入参会改坏调用方的 history。返回 `[*history, ...]` 新列表,调用方显式 `history = chat_once(...)[1]` 更新,无隐藏副作用 | ⬜ |
| 8 | 记忆无限增长有什么坑?生产怎么办? | 历史全发 → token 爆炸 + 超上下文窗口。生产用窗口记忆(只留最近 N 轮)/ 摘要记忆(旧对话压缩成摘要) | ⬜ |
| 9 | 直接 SDK 还是 LangChain? | 简单一问一答 → SDK(轻、可控);RAG/Agent/多步/流式/记忆 → LangChain 省事但抽象多、调试难、版本变化快。别无脑上 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「LCEL `|` = 运算符重载管道」?
- [ ] 能说清「PromptValue vs str + to_text 适配为什么存在」?
- [ ] 能说清「batch vs for+invoke」的区别?
- [ ] 能说清「记忆 = messages 列表 + 渲染进 prompt」?
- [ ] 能说清「何时 SDK 何时 LangChain」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
