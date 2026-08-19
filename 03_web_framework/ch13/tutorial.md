# Ch13 · HTTP 客户端:httpx 调用 API

> **预计**:0.5 天 ｜ **前置**:M1(函数/dict/推导式)、Ch12(配置外置)｜ **M3 第一章**
> **目标**:先学「**调**」API,再学「写」API。掌握 `httpx` 发 GET/POST/PUT、查询参数、请求头认证、状态码精细处理、超时与重试——这是后面 Ch14+ 写 FastAPI 时「测试自己 API」和「调用外部服务」的基本功。
> 本章主线:你是**订单服务**(order-service)的后端负责人。公司有个统一的「**商品中心**」中台,暴露了 REST API(商品列表 / 搜索 / 创建 / 查单个 / 改库存,要 Bearer Token 认证)。你要用 httpx 写一个**商品中心客户端模块**,供订单服务各处调用。`assets/mock_data/products.json` 就是商品中心文档里的示例数据。

> 📐 **本教程的契约**:§13.1–§13.7、§13.10 每节**精确对应**作业里的一个任务,讲过的才考,考的必讲过。§13.8(Client 设计)和 §13.9(MockTransport)是「为什么这么写」的设计课,讲透但不出独立题;§13.11 是大纲提及的延伸阅读(流式/文件),了解即可。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 httpx 和 requests 的关系,以及为什么现代项目选 httpx
- 发 GET/POST/PUT,说清 `params=` / `json=` / `data=` / `headers=` 各自管什么
- 用 `raise_for_status` 让错误响应「响出来」,并对 404 做业务化精细处理
- 配超时、分清 httpx 异常体系(`HTTPStatusError` vs `TransportError`),写出**只重试值得重试的错误**的重试循环
- 说清为什么 client 要「注入」而不是函数内新建(= Spring 注入 RestTemplate)
- 用 `MockTransport` 写**不起真服务**的 HTTP 客户端测试(= MockWebServer / WireMock)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `fetch_products` | §13.1 | GET + raise_for_status |
| `search_products` | §13.2 | params= 查询参数 + 可选条件 |
| `create_product` | §13.3 | POST + json= body |
| `get_product_or_none` | §13.4 | 404 业务化处理:先判再 raise |
| `fetch_with_auth` | §13.5 | headers= Bearer Token 认证 |
| `update_stock` | §13.6 | PUT + json=;204 无 body 的坑 |
| `fetch_with_retry` | §13.7 | 超时 + 异常体系 + 重试策略 |
| `aggregate_by_category` | §13.10 | 综合:复用 fetch + 分组聚合 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch13_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「raise_for_status、404 先判后抛、重试只重试 5xx/网络错」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 调 HTTP 用 OkHttp / RestTemplate / `HttpClient`。Python 老牌库是 requests,**现代首选**叫什么?它多了一项 requests 没有的什么能力?
2. Java 里你要 `if (resp.statusCode() >= 400) throw ...`。httpx 的 Response 上有个方法,调一下就「4xx/5xx 自动抛异常」,叫什么?
3. OkHttp 拼查询参数用 `HttpUrl.Builder.addQueryParameter("k", v)`。httpx 发 GET 带 `?keyword=键盘&max_price=600`,猜一个参数名。
4. Spring 的 RestTemplate 对 404 会抛 `HttpClientErrorException.NotFound`,你想「404 返回 null,其他错误才抛」得 try-catch。httpx 里更简单的写法是什么?
5. 测 HTTP 客户端,Java 用 MockWebServer / WireMock **起个假服务**。httpx 不起服务、直接在内存里拦截请求返回假响应的类叫什么?

> 猜完,带着验证心态进入正文。第 2、5 题是本章的两大支柱;第 4 题的模式在真实项目里天天用。

---

## §13.1 为什么 httpx + 最简 GET + raise_for_status(对应:`fetch_products`)🟡

### requests vs httpx:一句话选型

`requests` 是 Python 老牌 HTTP 库(只同步,API 经典);**`httpx` 是现代首选**:API 几乎照抄 requests,但**同步 + 异步都支持**(Ch18 异步章直接复用本章全部知识),还内置 `MockTransport` 做测试(§13.9)。本课程统一用 httpx。

> 🟡 **Java 对比**:requests ≈ Apache HttpClient(老、稳、功能止步);httpx ≈ OkHttp / Spring `WebClient`(现代、同步异步通吃)。2020 年后的新项目没有理由不选 httpx。

### Java 对照最小例

```java
// Java 11 HttpClient:发个 GET 要 4 步
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder(URI.create(url)).GET().build();
HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
if (resp.statusCode() >= 400) throw new RuntimeException("HTTP " + resp.statusCode());
```

```python
import httpx

resp = httpx.get("https://product-center/api/products")   # 一行发 GET
resp.raise_for_status()        # 4xx/5xx 抛 HTTPStatusError;2xx/3xx 放行
products = resp.json()         # 解析 JSON 响应体 → Python list/dict
```

### Response 对象四件套

```python
resp.status_code    # 200(int)
resp.json()         # JSON 响应体 → Python 对象(等价 json.loads(resp.text))
resp.text           # 原始文本
resp.headers        # 响应头(大小写不敏感的 dict-like)
```

### 🔴 `raise_for_status`:Java 老手最容易漏的一行

httpx **默认不认为 4xx/5xx 是错误**——请求成功发出、响应成功收到,就是「成功」。不主动检查,404 的报错页面会被当成正常数据继续往下传:

❌ **错误写法**(404 时 `resp.json()` 可能直接 JSONDecodeError,或者更糟——返回了错误结构的 dict,bug 一路传播到业务层才炸):

```python
resp = client.get(url)
return resp.json()          # 404/500 时这里拿到的是错误页/错误体,不是商品!
```

✅ **正确写法**(生产代码几乎总要调,让错误在源头炸出来):

```python
resp = client.get(url)
resp.raise_for_status()     # 4xx/5xx → httpx.HTTPStatusError(带 .response 可查细节)
return resp.json()
```

> 💡 `HTTPStatusError` 上有 `e.response.status_code` / `e.response.text`,日志排障时全靠它。它和 Java 的 `HttpClientErrorException` 一个角色。

### 真实场景例:拉商品中心全量列表

商品中心文档:`GET /api/products` 返回商品数组(就是 `products.json` 那 10 条):

```python
resp = client.get("https://product-center/api/products")
resp.raise_for_status()
products = resp.json()
products[0]     # {"id": 1, "name": "机械键盘", "category": "电脑外设", "price": 599.0, ...}
len(products)   # 10
```

> ✅ 做 `fetch_products` 题:三行——`client.get(url)` → `raise_for_status()` → `return resp.json()`。

---

## §13.2 查询参数 params:别用手拼 URL(对应:`search_products`)🟢

### Java 对照最小例

```java
// OkHttp:拼查询参数
HttpUrl url = HttpUrl.parse(base).newBuilder()
    .addQueryParameter("keyword", "键盘")      // 自动 URL 编码
    .addQueryParameter("max_price", "600")
    .build();
```

```python
# httpx:一个 dict 搞定,同样自动 URL 编码
resp = client.get("https://product-center/api/products",
                  params={"keyword": "键盘", "max_price": 600})
# 实际请求:/api/products?keyword=%E9%94%AE%E7%9B%98&max_price=600
```

### 🔴 f-string 拼 query:两个雷

❌ **错误写法**:

```python
resp = client.get(f"{url}?keyword={keyword}&max_price={max_price}")
# 雷 1:中文/空格/& 不编码 → URL 非法或语义错乱(keyword="a&b" 直接拼出第二个参数!)
# 雷 2:可选条件为 None 时拼出 keyword=None 这种垃圾参数
```

✅ **正确写法**(`params=` 自动编码;按需往 dict 里放):

```python
params = {}
if keyword is not None:
    params["keyword"] = keyword
if max_price is not None:
    params["max_price"] = max_price
resp = client.get(url, params=params)   # params 为空 dict 时就是不带 query,干净
```

### 真实场景例:商品中心搜索接口

文档:`GET /api/products/search?keyword=<可选>&max_price=<可选>`,两个条件都可省,都不传 = 全量:

```python
search_products(client, "/api/products/search", keyword="键盘", max_price=600)
# → GET /api/products/search?keyword=键盘&max_price=600 → [机械键盘(599)]

search_products(client, "/api/products/search")
# → GET /api/products/search(无 query)→ 全量 10 条
```

> 🟡 **细节**:`params` 的值可以是 list——`params={"tag": ["hot", "new"]}` → `?tag=hot&tag=new`(多值参数,等价 Java 里多次 `addQueryParameter` 同名键)。本章作业用不到,见到认识即可。

> ✅ 做 `search_products` 题:组装 `params` dict(**只放非 None 的条件**)→ `client.get(url, params=params)` → `raise_for_status` → `resp.json()`。

---

## §13.3 POST + json body(对应:`create_product`)🟢

### Java 对照最小例

```java
// OkHttp:手动序列化 + 手动指定 MediaType
String body = objectMapper.writeValueAsString(Map.of("name", "机械键盘", "price", 599));
RequestBody rb = RequestBody.create(body, MediaType.get("application/json"));
Request req = new Request.Builder().url(url).post(rb).build();
```

```python
# httpx:json= 一个参数 = 序列化 + Content-Type 两件事
resp = client.post(url, json={"name": "机械键盘", "price": 599})
# 自动:① dict → JSON 字符串 ② 请求头 Content-Type: application/json
```

### 🔴 `json=` / `data=` / `files=` 别用错

| 参数 | 发的是什么 | Content-Type | 场景 |
|------|-----------|--------------|------|
| `json=dict` | JSON 字符串 | `application/json` | **调 REST API 99% 用它** |
| `data=dict` | 表单编码 `a=1&b=2` | `application/x-www-form-urlencoded` | 老式表单提交 |
| `files={...}` | multipart | `multipart/form-data` | 文件上传(§13.11) |

❌ **错误写法**(用 `data=` 调 JSON API——服务端按 JSON 解析直接 400/415):

```python
client.post(url, data={"name": "键盘"})     # 发的是 name=键盘,不是 JSON!
```

✅ **正确写法**:

```python
client.post(url, json={"name": "键盘", "price": 599})
```

### 真实场景例:新建商品,拿回服务端分配的 id

文档:`POST /api/products`,成功返回 **201** + 完整商品(含生成的 id):

```python
resp = client.post("/api/products", json={"name": "机械键盘", "price": 599.0, "stock": 120})
resp.raise_for_status()
created = resp.json()       # {"id": 11, "name": "机械键盘", "price": 599.0, "stock": 120}
created["id"]               # 11 —— 后续改库存、查详情都靠这个 id
```

> 🟡 **Java 对比**:`json=` ≈ `RequestBody.create(json, JSON_MEDIA_TYPE)` + `objectMapper.writeValueAsString` 二合一。Spring 用户:`client.post(url, json=obj)` ≈ `restTemplate.postForObject(url, dto, ...)` 自动序列化 DTO。

> ✅ 做 `create_product` 题:`client.post(url, json=product)` → `raise_for_status` → `resp.json()`。

---

## §13.4 状态码精细处理:404 是业务结果不是异常(对应:`get_product_or_none`)🟡

`raise_for_status` 对所有 4xx/5xx 一视同仁全抛。但 REST 客户端有个经典模式:**「查单个资源,不存在不算错,返回 None;服务端真出错才抛」**——订单服务查商品时,商品可能已下架(404),这是正常业务分支;而 500 是商品中心真挂了,必须炸出来。

### Java 对照最小例

```java
// Spring RestTemplate:404 也抛异常,想放行只能 try-catch 再判类型,啰嗦
try {
    return restTemplate.getForObject(url, Product.class);
} catch (HttpClientErrorException.NotFound e) {
    return null;
}
```

```python
# httpx:先判 404 放行,再 raise_for_status 兜底其余错误——顺序就是全部诀窍
resp = client.get(url)
if resp.status_code == 404:     # 单独放行:不存在 = 正常业务结果
    return None
resp.raise_for_status()          # 其余 4xx/5xx(400/401/500...)照样抛
return resp.json()
```

### 🔴 为什么不用 try-except 判 404

❌ **错误写法**(能跑,但绕:异常里还得再判一次状态码,且把「流程控制」写成了「异常处理」):

```python
try:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        return None
    raise
```

✅ **正确写法**就是上面的「先 `if` 判 404,再 `raise_for_status`」——httpx 不自动抛异常的设计,让**状态码判断回归普通 if**,这比 Java 的异常驱动流程更清晰。

### 真实场景例

```python
get_product_or_none(client, "/api/products/1")     # {"id": 1, "name": "机械键盘", ...}
get_product_or_none(client, "/api/products/999")   # None(已下架,业务上正常)
get_product_or_none(client, "/api/internal/error") # 商品中心 500 → HTTPStatusError 抛出
```

> 💡 顺带认识 2xx 家族:`200` 查询/更新成功、`201` 创建成功、`204` 删除成功(无 body,见 §13.6)。`raise_for_status` 对它们全部放行。

> ✅ 做 `get_product_or_none` 题:四行——`get` → `if 404: return None` → `raise_for_status` → `resp.json()`。**顺序不能反**(先 raise 就把 404 也抛了)。

---

## §13.5 请求头与 Bearer Token 认证(对应:`fetch_with_auth`)🟢

商品中心不是裸奔的:所有写操作和敏感查询都要带 `Authorization: Bearer <token>` 头,token 错/缺 → **401**。

### Java 对照最小例

```java
Request req = new Request.Builder()
    .url(url)
    .header("Authorization", "Bearer " + token)   // OkHttp:逐个 .header 加
    .build();
```

```python
# httpx:headers= 收 dict
resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
```

### 真实场景例:单个请求带头 vs Client 级公共头

**单个请求带**(本章作业用法,token 由调用方传入):

```python
fetch_with_auth(client, "/api/products/1", token="abc123")
# → 请求头 Authorization: Bearer abc123 → 200 + 商品详情
# token 错误 → 401 → raise_for_status 抛出
```

**整个 Client 统一带**(真实项目更常用:创建 client 时配一次,之后每个请求自动带):

```python
with httpx.Client(
    base_url="https://product-center",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "order-service/1.0"},
) as client:
    client.get("/api/products")        # 自动带 Authorization 和 User-Agent
```

### 🔴 token 硬编码进源码 = 事故

❌ **错误写法**:

```python
TOKEN = "prod-token-8f3k..."      # 进 git → 泄露;换环境要改代码
```

✅ **正确写法**(Ch12 的配置外置直接用上):

```python
import os
token = os.environ.get("PRODUCT_CENTER_TOKEN")   # 部署时注入,代码只读
```

> ✅ 做 `fetch_with_auth` 题:`client.get(url, headers={"Authorization": f"Bearer {token}"})` → `raise_for_status` → `resp.json()`。

---

## §13.6 PUT / DELETE:改与删(对应:`update_stock`)🟢

### REST 方法语义速查

| 方法 | 语义 | 幂等 | 本章场景 |
|------|------|------|---------|
| GET | 查 | ✅ | 列表/搜索/查单个 |
| POST | 增(创建子资源) | ❌ | 新建商品 |
| PUT | 全量改/替换 | ✅ | 调整库存 |
| PATCH | 部分改 | 看实现 | (了解) |
| DELETE | 删 | ✅ | 下架商品 |

> 💡 **幂等** = 同一请求发 N 次和发 1 次效果相同。它直接决定 §13.7 的重试策略:PUT/DELETE/GET 幂等,网络抖动时重试安全;POST 不幂等,盲目重试可能建两条数据(真实项目用幂等键解决,了解即可)。

### Java 对照最小例

```java
restTemplate.put(url, requestBody);                    // PUT:无返回
restTemplate.exchange(url, HttpMethod.DELETE, null, Void.class);  // DELETE
```

```python
resp = client.put(url, json={"delta": -2})     # PUT 带 json body,和 post 一个套路
resp = client.delete(url)                      # DELETE 一般无 body
```

### 真实场景例:订单成交,调商品中心扣库存

文档:`PUT /api/products/{id}/stock`,body `{"delta": -2}`(负=扣减),返回更新后的商品:

```python
resp = client.put("/api/products/1/stock", json={"delta": -2})
resp.raise_for_status()
resp.json()       # {"id": 1, "name": "机械键盘", "stock": 118, ...}
```

### 🔴 DELETE 的 204 陷阱:没 body 别调 `.json()`

❌ **错误写法**:

```python
resp = client.delete("/api/products/9")
resp.raise_for_status()
return resp.json()          # 204 No Content:body 是空的 → JSONDecodeError!
```

✅ **正确写法**(204 表示「删成功,没东西返回」,看状态码就够):

```python
resp = client.delete("/api/products/9")
resp.raise_for_status()
return resp.status_code == 204
```

> ✅ 做 `update_stock` 题:`client.put(url, json={"delta": delta})` → `raise_for_status` → `resp.json()`(这题服务端有返回体,204 的坑知道就行)。

---

## §13.7 超时 + 异常体系 + 重试(对应:`fetch_with_retry`)🔴

本章最硬的一节,也是生产代码和玩具代码的分水岭。

### httpx 异常体系:两大类,处置完全不同

```
httpx.HTTPError                     # 总基类
├── HTTPStatusError                 # 响应「到了」,但状态码 4xx/5xx(raise_for_status 抛)
└── TransportError                  # 响应「没到」:网络层故障
    ├── TimeoutException            #   超时(ConnectTimeout 连不上 / ReadTimeout 读一半卡死)
    ├── ConnectError                #   连接被拒(DNS 失败、对端宕机)
    └── ...
```

> 🟡 **Java 对比**:`HTTPStatusError` ≈ Spring 的 `HttpClientErrorException/HttpServerErrorException`;`TimeoutException` ≈ `HttpTimeoutException`/`SocketTimeoutException`;`ConnectError` ≈ `ConnectException`。httpx 把它们组织在一棵树下,`except httpx.HTTPError` 可一网打尽。

### 超时:不设是生产大忌

❌ **错误写法**(裸奔——对端挂起时,你的请求线程**永远卡住**,线程池耗尽,服务跟着死):

```python
httpx.get(url)                    # 用默认超时?httpx 默认 5s,但显式声明才是工程态度
httpx.Client()                    # 同上:别依赖默认值,配置要看得见
```

✅ **正确写法**(Client 级统一配,或单个请求覆盖):

```python
client = httpx.Client(base_url="...", timeout=5.0)          # 统一 5 秒
client.get(url, timeout=10.0)                               # 单个请求放宽到 10s
httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=1.0)   # 细分四种超时(了解)
```

### 重试策略:只重试「值得重试」的错误

商品中心抖动,订单服务不能一次 503 就跪。但**乱重试比不重试更糟**:

| 错误 | 重试有用吗 | 原因 |
|------|-----------|------|
| 5xx(502/503/500) | ✅ 值得 | 服务端临时故障,稍后可能恢复 |
| 超时/连接错误 | ✅ 值得 | 网络抖动,重发可能就好 |
| 4xx(400/401/404) | ❌ 没用 | **你的请求本身有问题**,重发 100 次还是错 |

### 真实场景例:带重试的拉取(作业 `fetch_with_retry` 的完整逻辑)

```python
for attempt in range(retries):                    # retries=3:最多试 3 次
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()                        # 成功:直接返回
    except httpx.HTTPStatusError as e:
        if e.response.status_code < 500:          # 4xx:重试无意义,立刻抛
            raise
        if attempt == retries - 1:                # 5xx 但已是最后一次:抛
            raise
        # 否则:进下一轮,重试
    except httpx.TransportError:                  # 超时/连接错误
        if attempt == retries - 1:
            raise
        # 否则:重试
```

对「503 → 503 → 200」的商品中心,这段代码第 3 次拿到数据;对一直 503 的,试满 3 次把最后一次的 `HTTPStatusError` 抛给调用方;对 400,第 1 次就抛、**不多发一个请求**。

> 💡 真实项目还会加**指数退避**(第 n 次重试前 sleep 2ⁿ 秒,防雪崩)和直接用 `tenacity` 库。本章聚焦「异常分类决定重试与否」这个核心判断,退避了解即可。

> ✅ 做 `fetch_with_retry` 题:照上面的循环写。测试会用计数器验证:4xx 只发 1 次请求、5xx 发满 retries 次、超时也会触发重试——**蒙不对**。

---

## §13.8 Client 设计:连接复用、base_url 与「注入」(讲透,不出独立题)🟡

### 为什么作业函数都接收 `client` 参数

❌ **错误写法**(函数内自己发请求——没法配超时、没法复用连接、**测试时拦不住**):

```python
def fetch_products(url):
    resp = httpx.get(url)     # 每次新建连接;测试想 mock 只能 monkeypatch,丑
```

✅ **正确写法**(client 从外部传入 = **依赖注入**):

```python
def fetch_products(client: httpx.Client, url: str):
    resp = client.get(url)
    ...
```

> 🟡 **Java 对比**:这就是 Spring 里注入 `RestTemplate`/`WebClient` Bean,而不是每个方法里 `new OkHttpClient()`。调用方决定 client 的配置(base_url/超时/公共头/连接池),函数只关心业务;**测试时传一个带 MockTransport 的 client**(§13.9),不用起真服务。

### Client 的三件配置(创建时一次配好)

```python
with httpx.Client(
    base_url="https://product-center",               # 之后用相对路径:/api/products
    timeout=5.0,                                     # §13.7:统一超时
    headers={"Authorization": f"Bearer {token}"},    # §13.5:公共头
) as client:
    client.get("/api/products")          # 实际请求 https://product-center/api/products
    client.get("/api/orders")
# with 退出自动关闭连接池
```

**连接复用**:每次 `httpx.get()` 顶层调用都新建 TCP 连接(TLS 握手很贵);`Client` 持有连接池,多次请求复用——和 OkHttp 的「`OkHttpClient` 全局单例」最佳实践完全一致。循环里调 API,务必用同一个 Client。

> 💡 本章作业里 `make_client(handler)` 帮你造好测试 client;实战中你自己 `httpx.Client(base_url=..., timeout=...)`。**同一份业务函数,两种 client 都能跑**——这就是注入的价值。

---

## §13.9 MockTransport:不起真服务测 HTTP(讲透,测试用)🔴

**问题**:测 `fetch_products`,总不能真部署一个商品中心。

**答案**:`httpx.MockTransport`——给 Client 换一个「假引擎」,请求不出进程,直接由你的 handler 函数返回预设响应。

### 最小例

```python
import httpx

def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=[{"name": "机械键盘"}])

client = httpx.Client(transport=httpx.MockTransport(handler))
fetch_products(client, "http://anything/api")     # → [{"name": "机械键盘"}],没发真请求
```

> 🟡 **Java 对比**:≈ MockWebServer / WireMock / Spring `MockRestServiceServer`,但 httpx **内置**且不起端口——handler 就是个普通函数,测试里没有网络、没有并发、没有端口占用。

### handler 里能读什么、能演什么

```python
def handler(request):
    request.method                    # "GET" / "POST" / "PUT"
    str(request.url)                  # 完整 URL
    request.url.params                # 查询参数(QueryParams,可 .get("keyword"))
    request.headers.get("authorization")   # 请求头
    request.read()                    # 请求体 bytes(json.loads 可还原)
    # 能演的戏:
    return httpx.Response(200, json={...})      # 正常
    return httpx.Response(404)                  # 业务状态码
    return httpx.Response(503)                  # 服务端故障
    raise httpx.ConnectTimeout("boom")          # 模拟超时(异常直接从 client.get 抛出)
```

### 计数器:验证「重试了几次」

handler 是闭包,可以带状态——本章 `fetch_with_retry` 的测试靠它**区分真重试和蒙对**:

```python
calls = {"n": 0}
def handler(request):
    calls["n"] += 1
    if calls["n"] < 3:
        return httpx.Response(503)     # 前两次装病
    return httpx.Response(200, json=[{"name": "机械键盘"}])

# fetch_with_retry(client, url, retries=3) 应成功,且 calls["n"] == 3
# 若实现没重试,第 1 次 503 就抛了;若乱重试 4xx,另一个用例里 calls["n"] 会对不上
```

> 💡 测试文件顶部的 `make_client(handler)` 就是这个套路的封装,看一眼就懂。

---

## §13.10 综合:聚合商品数据出报表(对应:`aggregate_by_category`)🔴

最后一题把整章串起来,也是 SYLLABUS 点名的实战场景。

**场景**:运营要一份「各类目货品汇总」——订单服务从商品中心拉全量商品,按 `category` 分组,输出每个类目的**商品数**和**售价合计**(Σ `price`,不是库存金额 `price × stock`),按合计**降序**。这就是「调 API + M1 数据处理」的最小真实闭环。

### 思路分解(全是旧知识)

```python
def aggregate_by_category(client, url):
    products = fetch_products(client, url)     # ① 复用 §13.1 的函数:拉全量(含 raise_for_status)
    groups = {}
    for p in products:                          # ② 分组累加(Ch02 dict / Ch08 defaultdict 的技能)
        g = groups.setdefault(p["category"], {"count": 0, "total": 0.0})
        g["count"] += 1
        g["total"] += p["price"]
    result = [                                  # ③ 整形成报表行
        {"category": cat, "count": g["count"], "total_price": round(g["total"], 2)}
        for cat, g in groups.items()
    ]
    result.sort(key=lambda row: row["total_price"], reverse=True)   # ④ 降序(Ch02 sorted)
    return result
```

### 用 products.json 真实数据跑一遍

商品中心返回 10 条商品,聚合结果(已手工验算):

```python
[
    {"category": "电脑外设", "count": 4, "total_price": 3226.0},   # 599+159+2199+269
    {"category": "生活用品", "count": 2, "total_price": 1798.0},   # 199+1599
    {"category": "影音设备", "count": 2, "total_price": 1698.0},   # 1299+399
    {"category": "图书",     "count": 2, "total_price": 164.5},    # 89+75.5
]
```

> 💡 `round(x, 2)` 是金额累加的防御习惯(浮点连加可能出现 `164.50000000000003`);本章数据恰好精确,但习惯要养成。
> 💡 真实项目里这种聚合该让**服务端做**(SQL `GROUP BY`),客户端聚合只适合小数据量/服务端没提供接口的场景——知道边界在哪。

> ✅ 做 `aggregate_by_category` 题:直接调你写好的 `fetch_products`,然后分组 → 整形 → 降序。测试断言和上面表格逐字一致。

---

## §13.11 延伸阅读:流式响应与文件传输(大纲提及,了解即可,不考)

- **大文件下载(流式)**:`with client.stream("GET", url) as resp: for chunk in resp.iter_bytes(): ...`——不把整个文件读进内存,≈ Java 的 `InputStream` 逐块读。
- **文件上传**:`client.post(url, files={"file": ("report.csv", open("report.csv", "rb"))})`——multipart 表单,≈ OkHttp 的 `MultipartBody`。
- **异步 httpx**:`async with httpx.AsyncClient() as client: await client.get(...)`——Ch18 专门讲,本章同步 API 学扎实,到时零成本迁移。

---

## §13.12 Java 老手常踩的坑 ⚠️

1. **忘 `raise_for_status`**:httpx 默认把 404/500 当「成功响应」。不调它,错误数据流进业务层(§13.1)。
2. **f-string 拼查询参数**:中文不编码、`&` 截断、`None` 拼进 URL。用 `params=` dict(§13.2)。
3. **POST 用 `data=`**:发的是表单不是 JSON,JSON API 直接 400/415。调 API 用 `json=`(§13.3)。
4. **try-except 判 404**:httpx 不自动抛,先 `if status_code == 404` 放行、再 `raise_for_status` 兜底,顺序就是诀窍(§13.4)。
5. **token 写死在源码**:进 git = 泄露。`os.environ` 注入(Ch12 配置外置,§13.5)。
6. **对 204 调 `.json()`**:DELETE 成功返回 204 No Content,空 body 解析直接 JSONDecodeError(§13.6)。
7. **不设超时**:对端挂起 → 线程永久卡住 → 线程池耗尽。Client 创建时显式 `timeout=`(§13.7)。
8. **4xx 也重试**:请求本身有错,重发无用还放大流量。只重试 5xx 和 TransportError(§13.7)。
9. **函数内 `httpx.get()`**:没法复用连接、没法统一配置、测试拦不住。注入 `client` 参数(§13.8)。
10. **测试起真服务**:端口占用、慢、脆。`MockTransport` 内存拦截(§13.9)。

---

## 📝 本章作业

打开 **`ch13_assignment.py`**,8 个任务,一条主线串起来:给订单服务写一个**商品中心客户端模块**——拉列表 → 搜索 → 创建 → 查单个(404)→ 带认证 → 改库存 → 带重试 → 聚合报表。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `fetch_products` | GET + raise_for_status | 🟢 |
| `search_products` | params= 可选查询参数 | 🟢 |
| `create_product` | POST + json= | 🟢 |
| `get_product_or_none` | 404 先判后抛 | 🟡 |
| `fetch_with_auth` | headers= Bearer | 🟢 |
| `update_stock` | PUT + json= | 🟢 |
| `fetch_with_retry` | 异常分类 + 重试 | 🔴 |
| `aggregate_by_category` | 综合:复用 + 分组聚合 | 🔴 |

```bash
uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v
```

全绿 = 掌握 Ch13。卡住 → 按对应表回查 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 说清 httpx vs requests,为什么选 httpx(§13.1)
- [ ] 解释 `raise_for_status` 的作用,不调会怎样(§13.1)
- [ ] 说清 `params=` / `json=` / `data=` 三者区别(§13.2/§13.3)
- [ ] 默写 404 精细处理模式,并说清为什么不用 try-except(§13.4)
- [ ] 会给单请求和整个 Client 配 Authorization 头(§13.5)
- [ ] 说清 GET/POST/PUT/DELETE 语义和幂等性,知道 204 的坑(§13.6)
- [ ] 画出 httpx 异常树,说清哪些错值得重试、为什么(§13.7)
- [ ] 说清「client 注入」对比 Java 的什么,解决哪三个问题(§13.8)
- [ ] 会用 MockTransport 写测试,含计数器验证重试次数(§13.9)
- [ ] 8 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「httpx 为什么默认不抛异常?`raise_for_status` 和 404 精细处理怎么配合?」— 卡壳重读 §13.1/§13.4
2. 「重试为什么不能一刀切?哪些错误值得重试,背后的判断依据是什么?」— 卡壳重读 §13.7
3. 「为什么说函数内 `httpx.get()` 是坏习惯?注入 client 和 Spring 注入 RestTemplate 是不是一回事?」— 卡壳重读 §13.8

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch13 掌握「调」API 后,进 **Ch14 · FastAPI 入门**——开始「**写**」API。你会发现:FastAPI 的 TestClient 就是 httpx.Client 的包壳,本章的 `resp.json()` / `raise_for_status` / 状态码知识全部直接复用,只是这次你站在**服务端**这一边。
