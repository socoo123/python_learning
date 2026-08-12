# Ch13 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | httpx 和 requests 的关系?为什么选 httpx? | API 几乎一样,但 httpx **同步+异步都支持**(Ch18 用),且内置 MockTransport。requests 只同步。= Java OkHttp vs 老 HttpClient | ⬜ |
| 2 | `raise_for_status()` 干嘛?为什么生产几乎总要调? | 4xx/5xx 自动抛 HTTPStatusError。httpx 默认把错误状态码当「成功响应」,不调则 404/500 的错误体流进业务层,bug 难查 | ⬜ |
| 3 | `params=` / `json=` / `data=` 三者区别? | `params=` 查询参数(?k=v,自动 URL 编码);`json=` JSON body + Content-Type: application/json;`data=` 表单编码。调 REST API 用 json= | ⬜ |
| 4 | 为什么不能用 f-string 拼查询参数? | ① 中文/空格/& 不会 URL 编码,语义错乱;② 可选条件为 None 会拼出 `keyword=None` 垃圾参数。用 `params=` dict,None 就不放进去 | ⬜ |
| 5 | 怎么特殊处理 404(返回 None),其他错误才抛? | 先 `if resp.status_code == 404: return None`,再 `raise_for_status()` 兜底。**顺序是诀窍**:先 raise 会把 404 也抛了。比 try-except 清晰 | ⬜ |
| 6 | 单请求和整个 Client 分别怎么带 Bearer Token? | 单请求:`client.get(url, headers={"Authorization": f"Bearer {token}"})`;Client 级:`httpx.Client(headers={...})` 之后每个请求自动带。token 从 os.environ 读,不硬编码 | ⬜ |
| 7 | GET/POST/PUT/DELETE 的语义和幂等性? | GET 查(幂等)/ POST 增(**不幂等**)/ PUT 全量改(幂等)/ DELETE 删(幂等)。幂等性决定重试是否安全:POST 盲目重试可能建两条数据 | ⬜ |
| 8 | DELETE 返回 204 为什么不能调 `.json()`? | 204 = No Content,body 为空,`resp.json()` 直接 JSONDecodeError。看 `status_code == 204` 就够 | ⬜ |
| 9 | 画 httpx 异常树。哪些错值得重试,为什么? | HTTPError → HTTPStatusError(响应到了,状态码错)/ TransportError(响应没到:TimeoutException、ConnectError)。**5xx 和 TransportError 值得重试**(临时故障);**4xx 不值得**(请求本身有错,重发无用) | ⬜ |
| 10 | 超时怎么配?不配的后果? | `httpx.Client(timeout=5.0)` 或单请求 `client.get(url, timeout=...)`;可细分 `httpx.Timeout(connect=, read=...)`。不配:对端挂起 → 线程永久卡住 → 线程池耗尽 | ⬜ |
| 11 | 为什么作业函数都接收 client 参数而不是内部 httpx.get()? | 依赖注入(= Spring 注入 RestTemplate):① 连接池复用 ② 调用方统一配 base_url/超时/公共头 ③ 测试传 MockTransport client,不起真服务 | ⬜ |
| 12 | MockTransport 怎么用?handler 里能读/演什么? | `httpx.Client(transport=httpx.MockTransport(handler))`。读:`req.method/url.params/headers/read()`;演:返回 `httpx.Response(状态码, json=...)` 或 `raise httpx.ConnectTimeout(...)`。= MockWebServer/WireMock 但内置、不起端口 | ⬜ |
| 13 | 测试里怎么验证「重试了恰好 N 次」? | handler 闭包带计数器 `calls["n"] += 1`,断言调用次数——能区分真重试和蒙对(4xx 只发 1 次、5xx 发满 retries 次) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「raise_for_status 为何必须调 + 404 精细处理为什么先 if 后 raise」?
- [ ] 能说清「重试的判断依据:异常分类 + 幂等性」?
- [ ] 能说清「client 注入」解决哪三个问题,对应 Spring 的什么?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
