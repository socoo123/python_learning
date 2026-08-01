# Ch33 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。
> 本章是 M5 收官章,串起 Ch16/Ch18/Ch28——复习时连同那几章一起回。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 为什么 LLM 要包成 `Depends(get_llm)` 依赖而不是写死在路由里? | **可替换**:测试用 `app.dependency_overrides[get_llm]=lambda: FakeLLM()` 离线跑;生产读环境变量决定用哪个模型。路由代码零改动 = Spring `@Autowired` + `@MockBean` | ⬜ |
| 2 | 怎么用假 LLM 做离线测试? | `app.dependency_overrides[get_llm] = lambda: _MockLLM()` 覆盖依赖。用完**必须清理**(`.clear()`),否则污染其他用例。用 fixture 的 teardown | ⬜ |
| 3 | `chat_logic` 和 `handle_chat` 为什么要拆? | 职责分离:路由只管「接 HTTP + 调逻辑 + 返回」,业务在 `chat_logic`(纯函数,llm 作入参,不依赖 FastAPI,好测)。= Java Service vs Controller | ⬜ |
| 4 | Pydantic 校验失败返回什么状态码? | **422**(不是 400)。缺必填字段、类型错都 422。FastAPI 看到 Pydantic 模型作参数就自动校验,不用写 `if x is None` | ⬜ |
| 5 | 为什么健康检查用 `/health` 而不是探 `/chat`? | K8s/ELB 每 5s 探活,探 `/chat` 会真打 LLM = **探活也烧钱**。`/health` 轻量、不依赖外部服务,返回 `{"status":"ok"}` | ⬜ |
| 6 | SSE 流式相对普通 JSON 的优势? | 首字延迟 0.3s(普通 JSON 要等满 10s)。`StreamingResponse(gen(), media_type="text/event-stream")`,生成器逐字 `yield "data: x\n\n"`,前端打字机效果 | ⬜ |
| 7 | SSE 的 media_type 是什么?消息格式? | `text/event-stream`。每条消息 `data: <内容>\n\n`。前端用 `EventSource` 或 `fetch+ReadableStream` 消费。忘了 media_type 前端按 JSON 解析就炸 | ⬜ |
| 8 | AI 服务的四个生产坑? | ① 长耗时(超时/队列/async)② 限流(防烧钱,slowapi)③ 缓存(精确/语义,Redis)④ 成本(max_tokens/日志/分级模型)。比普通 CRUD 更关键,因为 LLM 又慢又贵 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「为什么 LLM 是依赖 + 怎么测试时替换」?
- [ ] 能说清「路由 vs 逻辑层分离」的道理(对比 Java Controller/Service)?
- [ ] 能说清「SSE 流式 vs 普通 JSON」的延迟差异 + 实现要点?
- [ ] 能列出 AI 服务的四个生产坑(长耗时/限流/缓存/成本)?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
> M5 毕业 🎓 —— 回顾 Ch28(调 LLM)→ Ch29(Prompt)→ Ch30/31(RAG)→ Ch32(Agent)→ Ch33(封装服务),你已经能搭生产级 AI 应用了。
