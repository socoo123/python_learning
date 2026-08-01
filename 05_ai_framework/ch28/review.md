# Ch28 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 调 LLM 用 SDK 还是裸 HTTP?API key 放哪? | 用官方 SDK(封装 HTTP/鉴权/重试/流式)。API key 走环境变量(ANTHROPIC_API_KEY),绝不进代码/git | ⬜ |
| 2 | 为什么 response.content 是列表不是字符串? | 一次回复可能多个内容块(文本/工具调用/引用),所以 content 是块列表。取文本:resp.content[0].text | ⬜ |
| 3 | extract_text 怎么兼容多形态响应? | getattr(response,"content",response) 容错;str 直接返回;否则遍历块取 .text(对象)或 ["text"](dict)拼接。duck typing | ⬜ |
| 4 | LLM 有状态吗?多轮对话怎么实现? | 【无状态】,不记得上句。多轮 = 客户端每次把【全部历史】(user/assistant 交替)发过去。历史越长越贵 | ⬜ |
| 5 | build_messages 为什么不 mutate 入参? | 无副作用:返回 [*history, 新消息] 新列表。直接 append 会改坏调用方的 history(可变参数陷阱) | ⬜ |
| 6 | token 是什么?粗估?为什么要关心? | 计费+上下文窗口单位(≈词根)。英文 4字符≈1token。关心:计费按 token、上下文窗口有上限、max_tokens 卡输出 | ⬜ |
| 7 | with_retry 为什么用 errors 参数过滤? | 只重试【瞬时错误】(429/5xx/超时)。400 参数错重试也没用。默认 Exception 全重试,生产要收窄 | ⬜ |
| 8 | 生产重试还要加什么? | 指数退避(1s/2s/4s 避免猛打)。SDK/tenacity 自带;高并发用 AsyncAnthropic,别在 async 里调同步 client(阻塞事件循环) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「SDK vs 裸 HTTP + key 走环境变量」?
- [ ] 能说清「LLM 无状态 → 多轮发全部历史」?
- [ ] 能说清「重试只针对瞬时错误 + 退避」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
