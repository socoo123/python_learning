# Ch13 · HTTP 客户端:httpx 调用 API

> **预计**:0.5 天 ｜ **前置**:M1 ｜ **M3 第一章**
> **目标**:先学「**调**」API,再学「写」API。掌握 `httpx` 发 GET/POST、处理状态码、超时——这是后面 Ch14+ 写 FastAPI 时「测试自己 API」和「调用外部服务」的基础。

> 📐 **本教程的契约**:§13.1–§13.3 对应作业。§13.5 的 MockTransport 是测试关键技巧。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `fetch_products` | §13.1 | GET + raise_for_status |
| `create_product` | §13.2 | POST + json body |
| `get_product_or_none` | §13.3 | 状态码处理(404) |

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 调 HTTP 你用过什么(HttpClient/OkHttp/RestTemplate)?Python 主流的现代库叫什么?
2. Java 检查状态码要 `if (resp.statusCode() >= 400)`。httpx 一个方法叫什么,直接抛异常?
3. POST 发 JSON body,httpx 哪个参数自动序列化?
4. 不想为测试起一个真服务,httpx 提供了什么来「拦截请求返回假响应」?

---

## §13.1 为什么 httpx + 基础 GET

Python 老牌 HTTP 库是 `requests`(同步),现代首选是 **`httpx`**:API 几乎和 requests 一样,但**同步+异步都支持**(Ch18 异步会用到),还能用 `MockTransport` 做测试。本课程统一用 httpx。

> 🟡 **Java 对比**:httpx ≈ OkHttp / Spring `RestTemplate` / `WebClient`。requests ≈ 老的 Apache HttpClient。

### 最简 GET

```python
import httpx

resp = httpx.get("https://api.example.com/products")
resp.status_code      # 200
resp.json()           # 解析 JSON 响应体 → Python 对象
resp.text             # 原始文本
resp.headers          # 响应头
```

### `raise_for_status`:状态码自动抛异常

```python
resp = httpx.get(url)
resp.raise_for_status()    # 4xx/5xx 直接抛 HTTPStatusError,2xx/3xx 放行
```

> 🤯 这是 Java 老手会爱的:httpx 不像某些库默认静默吞错误,`raise_for_status` 让「请求失败」明确成异常。**生产代码几乎总要调它**,否则 404/500 会被当成「正常响应」继续处理。

> ✅ 做 `fetch_products` 题:`client.get(url)` + `raise_for_status()` + `resp.json()`。

---

## §13.2 POST + json body(对应:`create_product`)

```python
# POST 发 JSON
resp = httpx.post(url, json={"name": "键盘", "price": 599})
#                       ↑ json= 自动:① 序列化 dict→JSON ② 设 Content-Type: application/json

# 其他参数
httpx.get(url, params={"category": "book", "page": 1})   # 查询参数 ?category=book&page=1
httpx.post(url, json=data, headers={"Authorization": "Bearer xxx"})   # 请求头
```

> 🟡 **Java 对比**:`json=` 参数 = OkHttp 的 `RequestBody.create(json, JSON_MEDIA_TYPE)`,但 httpx 一个参数搞定,不用手动序列化 + 设 Content-Type。

> ✅ 做 `create_product` 题:`client.post(url, json=product)` + `raise_for_status` + `resp.json()`。

---

## §13.3 状态码处理:404 特殊对待(对应:`get_product_or_none`)

`raise_for_status` 对所有 4xx/5xx 一视同仁(都抛)。但有时你想**特殊处理某个状态码**(如 404 返回 None,其他错误才抛):

```python
resp = client.get(url)
if resp.status_code == 404:      # 单独放行 404(资源不存在是「正常业务结果」)
    return None
resp.raise_for_status()           # 其余错误(500 等)才抛
return resp.json()
```

> 这是 REST 客户端的常见模式:「查单个资源,不存在不算错,返回 None;服务端真出错才抛」。

> ✅ 做 `get_product_or_none` 题:见上。

---

## §13.4 Client / 超时 / 连接复用(了解)

每次 `httpx.get(url)` 都新建连接(慢)。多次请求用 `httpx.Client` **复用连接**(连接池):

```python
with httpx.Client(base_url="http://localhost:8000", timeout=5.0) as client:
    # base_url 让后续用相对路径
    client.get("/api/products")          # 实际 http://localhost:8000/api/products
    client.get("/api/orders")
# with 退出自动关连接池
```

**超时**:`timeout=5.0`(秒)。不设超时是生产大忌——网络挂起会让请求永远卡住。

> 本节作业接收 `client` 参数,就是为了让外部决定 client 配置(base_url/超时/连接池),函数只关心业务。

---

## §13.5 测试神器:MockTransport 🔴

**问题**:测 `fetch_products` 总不能真起一个服务器。怎么测?

**答案**:`httpx.MockTransport` 拦截请求,返回你预设的假响应。**不用真服务**。

```python
import httpx

def handler(request):                       # handler 决定怎么响应
    # request.url / request.method / request.read()(请求体)都可读
    return httpx.Response(200, json=[{"name": "键盘"}])

transport = httpx.MockTransport(handler)
client = httpx.Client(transport=transport)  # 这个 client 的请求被 handler 接管

fetch_products(client, "http://x/api")      # 拿到假响应 [{"name":"键盘"}]
```

`handler` 是个函数,接收 `request`,返回 `httpx.Response(状态码, json=...)`。你可以:
- 按状态码返回不同响应(200/404/500)
- 读取请求验证(`request.read()` 拿 body,`request.url` 拿 URL)

> 🟡 **Java 对比**:= MockWebServer / WireMock / Spring `MockRestServiceServer`。httpx 的 MockTransport 内置,无需三方库。本课程 M3 所有「调用 HTTP」的测试都用它。

测试文件里的 `make_client(handler)` 就是这个套路,看一眼就懂。

---

## §13.6 Java 老手常踩的坑 ⚠️

1. **忘 `raise_for_status`**:不调它,404/500 会被当正常响应,bug 难查。生产代码总要调。
2. **POST 忘 `json=`**:用 `data=` 发的是表单,`json=` 才是 JSON body。调 API 几乎都用 `json=`。
3. **不设超时**:生产大忌。网络挂起 → 请求永远卡住 → 线程耗尽。永远 `timeout=`。
4. **每次新建连接**:循环里 `httpx.get()` 性能差。用 `httpx.Client` 复用。
5. **测试起真服务**:别为测试起 server。用 MockTransport。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `fetch_products` | GET + raise_for_status | 🟢 |
| `create_product` | POST + json | 🟢 |
| `get_product_or_none` | 404 处理 | 🟡 |

```bash
uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v
```

---

## ✅ 自测

- [ ] 能用 httpx 发 GET/POST,知道 `json=` 和 `params=` 的区别
- [ ] 知道 `raise_for_status` 的作用,为什么生产必须调
- [ ] 会用 MockTransport 写不依赖真服务的测试
- [ ] 3 个作业全绿

## 🎓 费曼挑战

1. 「为什么 `raise_for_status` 几乎总要调?不调会怎样?」— 重读 §13.1
2. 「MockTransport 怎么让我们不用真服务就能测 HTTP 调用?」— 重读 §13.5

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch13 掌握「调」API 后,进 **Ch14 · FastAPI 入门**——开始「**写**」API。定义 Pydantic 模型、写第一个 `@app.get`/`@app.post`,用 TestClient 测自己的 API。
