# Ch17 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 中间件的「洋葱模型」是什么?call_next 前后各在何时执行? | 请求层层进、响应层层出。`call_next` 前 = 请求进入时跑;`await call_next` 放行;后 = 响应出来时跑。= Java Filter/Interceptor | ⬜ |
| 2 | `call_next` 为什么必须 `await`? | 它是 async(返回协程)。忘 await 得到协程对象而非 response。Ch18 异步详讲 | ⬜ |
| 3 | `@app.exception_handler(NotFoundError)` 干嘛?对应 Java? | 注册异常处理器:业务代码 raise NotFoundError → 自动被处理器接住 → 返统一格式 HTTP 响应。= Spring @ControllerAdvice + @ExceptionHandler | ⬜ |
| 4 | 业务异常(自定义)和程序异常(ValueError)怎么区分处理? | 业务异常(资源不存在/权限不足等业务规则)→ 4xx + 自定义处理器;程序异常(bug)→ 500 + 兜底处理器 + 记日志 | ⬜ |
| 5 | CORS 怎么配?`allow_origins=["*"]` 有什么坑? | `app.add_middleware(CORSMiddleware, allow_origins=..., allow_methods=..., allow_headers=...)`。坑:`*` + `allow_credentials=True` 浏览器拒绝;生产限定具体域名 | ⬜ |
| 6 | 未注册处理器的异常返回什么? | **500** Internal Server Error。生产应注册兜底 Exception 处理器,格式化 + 记日志 + 不暴露堆栈 | ⬜ |
| 7 | 多个中间件的执行顺序? | 【后注册先执行】(洋葱最外层)。鉴权类要早注册(外层),保证在业务前拦 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「洋葱模型 + call_next 时机」?
- [ ] 能说清「自定义异常 + 全局处理器为何比手写 JSONResponse 好」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
