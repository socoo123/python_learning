# Ch33 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆，再翻答案**。连续 2 次秒答 → 退役 ✅。
> 本章是 M5 收官章，串起 Ch14/Ch16/Ch18/Ch28——复习时连同那几章一起回。

## 🔖 闪卡

| # | 正面（问题） | 背面（答案） | 掌握 |
|---|---|---|---|
| 1 | 为什么 AI 能力必须封装成后端 API，而不是把 SDK 甩给前端？ | 和「前端不直连数据库」同理：API key 裸奔、无法限流防刷、缓存各算各的、换模型要全端发版、成本无从统计。LLM 又慢又贵，必须有服务端守门人 | ⬜ |
| 2 | 为什么 LLM 要包成 `Depends(get_llm)` 依赖而不是写死在路由里？ | **可替换**：测试用 `app.dependency_overrides[get_llm]=lambda: FakeLLM()` 离线跑；生产读环境变量决定用哪个模型。路由代码零改动 = Spring `@Autowired` + `@MockBean` | ⬜ |
| 3 | 用完 `dependency_overrides` 为什么要清理？怎么清？ | 全局字典，不清会污染后续用例（假 LLM 泄漏）。fixture teardown 里 `app.dependency_overrides.clear()` | ⬜ |
| 4 | 教学版 `estimate_tokens` 的约定？`max(1, ...)` 防什么？ | 每 2 字符 ≈ 1 token，保底 1。空回复记 0 会漏账、下游做分母会除零。生产读 SDK 返回的 `resp.usage`，别估算 | ⬜ |
| 5 | `chat_logic` 和 `handle_chat` 为什么要拆？ | 职责分离：路由只管「接 HTTP + 调逻辑 + 返回」，业务在 `chat_logic`（纯函数，llm 作入参，不依赖 FastAPI，好测）。= Java Service vs Controller | ⬜ |
| 6 | `chat_with_cache` 里 `cached` 标记为什么不能存进缓存？ | 存进去后命中取出的永远是第一次存的旧值（False）。**缓存只存纯净结果** `{"reply","tokens"}`，`cached` 是单次请求的元信息，返回时 `{**result, "cached": True}` 现加 | ⬜ |
| 7 | 限流为什么要放在缓存**前面**？顺序反了会怎样？ | 反了缓存命中的请求不计数，脚本哥拿同一个 query 无限刷也触发不了限流。先限流：每笔请求都计数，恶意流量在最外层被 429 挡掉 | ⬜ |
| 8 | 限流超限时该返回什么？为什么不用 200 + 错误文案？ | **429 Too Many Requests**（`raise HTTPException(status_code=429, detail=...)`）。200 会让客户端以为成功；429 语义化，网关/客户端能识别并自动重试 | ⬜ |
| 9 | `allow_request` 超限时计数还要 +1 吗？为什么？ | **不加**。拒绝的请求不该消耗配额，否则「已放行数」变成「尝试数」，账本失去语义 | ⬜ |
| 10 | Pydantic 校验失败返回什么状态码？发生在限流之前还是之后？ | **422**（不是 400）。校验在路由函数执行**之前**——422 的请求不消耗限流配额、不调 LLM | ⬜ |
| 11 | 为什么健康检查用 `/health` 而不是探 `/chat`？ | K8s/ELB 每 5s 探活，探 `/chat` 会真打 LLM = 探活也烧钱（一天 17280 次）。`/health` 轻量、零外部依赖 | ⬜ |
| 12 | SSE 流式的三件套？结束标记？ | ① 生成器逐条 `yield f"data: {ch}\n\n"` ② `StreamingResponse(gen(), media_type="text/event-stream")` ③ 结尾 `data: [DONE]`（OpenAI 约定，前端读到知道流结束）。忘 media_type 前端按 JSON 解析就炸 | ⬜ |
| 13 | SSE 相比普通 JSON 的优势？ | 首字延迟 0.3s vs 等满 10s；打字机体验。协议 `text/event-stream`，前端用 `EventSource`/`ReadableStream` 消费。= Spring `SseEmitter` / WebFlux `Flux<ServerSentEvent>` | ⬜ |
| 14 | async 路由里能直接调同步 LLM SDK 吗？ | 不能——会卡死事件循环，所有并发请求陪葬。要么 `def` 路由（FastAPI 自动进线程池），要么 `async def` + `AsyncAnthropic`（§33.10） | ⬜ |
| 15 | 分钟级长任务（生成周报）怎么设计 API？ | 别挂 HTTP 等。任务队列（Celery/ARQ ≈ RabbitMQ + @Async）：POST 立即返 202 + `task_id`，客户端轮询 `GET /tasks/{id}` | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「为什么 LLM 是依赖 + 怎么测试时替换 + 为什么要清理」？
- [ ] 能说清「限流→缓存→逻辑」的装配顺序为什么是这个序？
- [ ] 能手算 `estimate_tokens("echo:你好") = 3`，并说清生产上该用什么替代估算？
- [ ] 能说清「缓存只存纯净结果、元信息返回时现加」的分寸？
- [ ] 能默写 SSE 三件套 + `[DONE]` 约定？
- [ ] 能列出 AI 服务的四个生产件（成本估算 / 缓存 / 限流 / 异步与队列）？

## 📅 复习日程

- [ ] +1 天　日期：________
- [ ] +3 天　日期：________
- [ ] +7 天　日期：________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
> M5 毕业 🎓 —— 回顾 Ch28（调 LLM）→ Ch29（Prompt）→ Ch30（LCEL）→ Ch31（RAG）→ Ch32（Agent）→ Ch33（封装服务），你已经能搭生产级 AI 应用了。
