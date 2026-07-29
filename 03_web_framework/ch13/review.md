# Ch13 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | httpx 和 requests 的关系?为什么选 httpx? | API 几乎一样,但 httpx **同步+异步都支持**(Ch18 用),且内置 MockTransport 测。requests 只同步。= Java OkHttp | ⬜ |
| 2 | `raise_for_status()` 干嘛?为什么生产几乎总要调? | 4xx/5xx 自动抛 HTTPStatusError。不调的话 404/500 会被当正常响应继续处理,bug 难查 | ⬜ |
| 3 | POST 发 JSON body 用哪个参数?和 `params=` 区别? | `json=dict` 自动序列化+设 Content-Type。`params=` 是【查询参数】(?key=val),`data=` 是表单。调 API 用 json= | ⬜ |
| 4 | 怎么特殊处理 404(返回 None),其他错误才抛? | 先判 `resp.status_code == 404: return None`,再 `raise_for_status()`。因为 raise_for_status 对所有 4xx 一视同仁 | ⬜ |
| 5 | MockTransport 干嘛?为什么测试用它? | 拦截 httpx 请求,返回预设假响应,**不用真服务**。handler 函数按 request 返回 Response。= Java MockWebServer/WireMock | ⬜ |
| 6 | httpx.Client(连接池)和超时怎么用? | `with httpx.Client(base_url=..., timeout=5.0) as client` 复用连接 + 设超时。不设超时是生产大忌(网络挂起→永久卡住) | ⬜ |
| 7 | 拿响应体 JSON / 状态码 / 请求体 分别怎么写? | `resp.json()` 响应JSON;`resp.status_code` 状态码;handler 里 `request.read()` 读请求体 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「raise_for_status 为何必须调、不调的后果」?
- [ ] 能说清「MockTransport 如何让测试不依赖真服务」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
