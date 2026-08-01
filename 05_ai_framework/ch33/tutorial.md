# Ch33 · 用 FastAPI 封装 AI 服务

> **预计**:0.5–1 天 ｜ **前置**:Ch18(async)、Ch28(LLM)、Ch16(Depends) ｜ **M5 收官章** ⭐
> **目标**:把 Ch28 学的「调 LLM」包装成生产级 HTTP API——前端/客户端只管 POST `/chat`,不用关心背后用哪家模型、怎么鉴权、怎么重试。综合实战,M5 毕业作。

> 📐 **本教程的契约**:§33.3–§33.5 对应作业 4 个函数,**§33.7 SSE 流式是进阶(可选)**。作业【不调真实 LLM】,默认注入 `EchoLLM`(离线 echo),测试用假 LLM 覆盖。真实用法(接 Anthropic/OpenAI)在 §33.6 有完整示例。

---

## 🗺️ 本章地图

**为什么 AI 要封装成 API**:LLM 调用慢(秒级)、贵(按 token)、不稳定(要重试)、可能流式(SSE)——这些脏活累活应该集中在后端 API 层,让前端只看到一个干净的 `POST /chat`。同时 API 层还能统一做**限流、缓存、成本控制、计费、日志**——这些是「AI 工程化」的核心。

**作业 ↔ 教程对应表**:

| 作业函数 | 对应小节 | 核心知识点 | 难度 |
|----------|----------|-----------|------|
| `get_llm` | §33.3 | Depends 依赖注入 + `dependency_overrides` 可替换 | 🟡 |
| `chat_logic` | §33.4 | 逻辑/路由分离(Service vs Controller) | 🟢 |
| `handle_health` | §33.5 | 健康检查端点(探活,不烧钱) | 🟢 |
| `handle_chat` | §33.5 | 路由 + Pydantic body + Depends 组合拳 | 🟡 |
| `handle_chat_stream` | §33.7 | SSE 流式(进阶,可选) | 🔴 |

> 综合征用:**Ch16**(Depends)、**Ch18**(async)、**Ch28**(LLM 调用)、**Ch14**(FastAPI+Pydantic+TestClient)——这一章是把前四章的招式串成一套连招。

---

## ⏱️ 学习路径:费曼五步(约 60–90 分钟)

① 预览猜 → ② 写 assignment(4–5 个函数)→ ③ pytest 红绿 → ④ 费曼复述 → ⑤ 存闪卡。

---

## ① 预览猜(先想,再读)

1. 前端要调你的 AI 能力,你给它暴露 HTTP 接口。**为什么不直接把 SDK 暴露给前端**?(提示:API key、限流、模型可换)
2. 测试时不想真打 LLM(慢、贵、CI 不稳),怎么把 LLM「换掉」?(提示:回想 Spring `@MockBean`)
3. `handle_chat` 里调 `chat_logic` 还是直接写业务?为什么要拆?(提示:可测性、职责单一)
4. LLM 回复要 10 秒,用户盯着转圈很难受。怎么让它「首字 0.3 秒就开始蹦」?(提示:流式 SSE)
5. K8s 每 5 秒探活你的服务,你让它探 `/chat` 吗?为什么要有单独的 `/health`?

---

## §33.1 默认 LLM:EchoLLM(离线,真实换真 SDK)

```python
class EchoLLM:
    def ask(self, query: str) -> str:
        return f"echo:{query}"        # 离线假实现,真实换 SDK
```

为什么默认是个「假」LLM?
- **离线可跑**:CI、单元测试、本地调试都不连网、不烧钱。
- **定义协议**:任何带 `ask(query) -> str` 的对象都能注入(鸭子类型 / `Protocol`)。`EchoLLM` 是这个协议的「默认实现」。
- **和 Java 一个理**:面向接口编程——Controller 依赖 `ChatService` 接口,默认给个 `EchoServiceImpl`,生产换 `AnthropicServiceImpl`。

> 🟡 **Java 对比**:= `class EchoServiceImpl implements ChatService`。真实实现里 `ask()` 内部调 `client.messages.create(...)`(§28.3)。

---

## §33.2 Pydantic 请求模型(= Java DTO + @Valid)

```python
class ChatRequest(BaseModel):
    query: str
    max_tokens: int = 1024
```

FastAPI 看到「Pydantic 模型作参数」就自动:① 解析 JSON body ② 校验类型/必填 ③ 失败返回 **422**(不是 400)。你只管把 `body` 当普通对象用,**永远不用写 `if query is None`**。

- 缺 `query` → 422(必填字段缺失)
- `query` 传数字 → 422(类型错)
- 多传 `junk` 字段 → 默认忽略(Pydantic 不报错)

> 🟡 **Java 对比**:= `@Valid @RequestBody ChatRequestDTO body` + Bean Validation(`@NotBlank` 等)。422 是 FastAPI 的约定:校验失败统一 422。

---

## §33.3 依赖注入:get_llm(对应:`get_llm`)🟡

```python
def get_llm() -> EchoLLM:
    return EchoLLM()

@app.post("/chat")
def handle_chat(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    #                                    ^^^^^^^^^^^^^^^ FastAPI 自动调 get_llm()
    return chat_logic(llm, body.query)
```

**为什么要包成依赖而不是 `llm = EchoLLM()` 写死在路由里?** —— **可替换**。

**测试时**:
```python
app.dependency_overrides[get_llm] = lambda: _MockLLM()
# 之后所有 Depends(get_llm) 拿到的都是 _MockLLM,完全离线
```

**生产时**(读环境变量决定用谁):
```python
def get_llm() -> ChatService:
    if os.getenv("LLM_PROVIDER") == "anthropic":
        return AnthropicLLM()
    return EchoLLM()
```

**路由代码一行不改**。这就是依赖注入的价值——把「用哪个实现」的决策推迟到组装时/测试时。

> 🟡 **Java 对比**(三件套一一对应):
> | FastAPI | Spring Boot |
> |---------|-------------|
> | `def get_llm()` 依赖函数 | `@Bean` / `@Configuration` 方法 |
> | `llm: EchoLLM = Depends(get_llm)` | `@Autowired ChatService llm`(构造器注入) |
> | `app.dependency_overrides[get_llm] = ...` | 测试里 `@MockBean` / `@TestConfiguration` 替换 Bean |

> ✅ 做 `get_llm`:就一行 `return EchoLLM()`。重点不在代码,在**理解它为什么是个依赖**。

---

## §33.4 核心逻辑:chat_logic(对应:`chat_logic`)🟢

```python
def chat_logic(llm, query: str) -> dict:
    return {"reply": llm.ask(query)}
```

刻意从路由里拆出来:
- `llm` 是**入参**(不直接 `new`),测试传假对象就行——**不依赖 FastAPI**,纯函数。
- `handle_chat` 只管「接 HTTP + 调它」,职责单一。
- 业务变复杂(加历史、加缓存、加计费)时,改 `chat_logic`,路由不动。

> 🟡 **Java 对比**:= Service 层 `chat()` 方法 vs Controller 层。Controller 薄、Service 厚——Java 老手的肌肉记忆,Python 里一模一样。

> ✅ 做 `chat_logic`:`return {"reply": llm.ask(query)}`。

---

## §33.5 路由:handle_health / handle_chat(对应:同名函数)

### handle_health(健康检查)🟢

```python
@app.get("/health")
def handle_health():
    return {"status": "ok"}
```

**为什么不探 `/chat`**?K8s/ELB 每 5 秒探一次活,如果探 `/chat` 会真打 LLM——**探活也烧钱**。健康检查应该是「轻量、不依赖外部服务」的。

### handle_chat(聊天路由)🟡

```python
@app.post("/chat")
def handle_chat(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    return chat_logic(llm, body.query)
```

路由函数就三件事:**解析入参 → 调逻辑 → 返回**。`@app.post` 装饰器注册路由,`body: ChatRequest` 自动校验,`llm = Depends(get_llm)` 自动注入——FastAPI 把 HTTP 的样板全包了。

> 🟡 **Java 对比**:
> ```java
> @RestController
> public class ChatController {
>     @Autowired private ChatService chatService;       // = Depends(get_llm)
>     @PostMapping("/chat")
>     public ChatReply chat(@Valid @RequestBody ChatRequest body) {  // = body: ChatRequest
>         return chatService.chat(body.getQuery());     // = chat_logic(llm, body.query)
>     }
> }
> ```
> FastAPI 一个装饰器 + 类型注解 = Spring 的 `@RestController` + `@PostMapping` + `@Valid` + `@RequestBody` + `@Autowired`。注解驱动,Python 用类型注解驱动。

> ✅ 做 `handle_health`:`return {"status":"ok"}`;做 `handle_chat`:`return chat_logic(llm, body.query)`。

---

## §33.6 真实用法示例(接真 SDK)

```python
import os
from anthropic import Anthropic
from fastapi import Depends, FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

class AnthropicLLM:
    """真实实现:内部调 Anthropic SDK(Ch28)。"""
    def __init__(self):
        self.client = Anthropic()          # 读 ANTHROPIC_API_KEY 环境变量
    def ask(self, query: str) -> str:
        resp = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": query}],
        )
        return resp.content[0].text         # §28.2

def get_llm() -> AnthropicLLM:
    return AnthropicLLM()                   # 生产用真的

@app.post("/chat")
def chat(body: ChatRequest, llm: AnthropicLLM = Depends(get_llm)):
    return {"reply": llm.ask(body.query)}
```

- `AnthropicLLM` 和 `EchoLLM` **接口一样**(都有 `ask`),换依赖即可,路由代码零改动——这就是 §33.3 依赖注入的回报。
- API key 走环境变量(Ch28 铁律),代码里没有明文。

---

## §33.7 SSE 流式(进阶,可选)🔴

LLM 生成慢(几秒到十几秒)。普通 `/chat` 要等**全部生成完**才一次性返回 JSON,用户盯着转圈。**SSE(Server-Sent Events)** 让后端「边产边发」,前端实现打字机效果,首字 0.3 秒就出来。

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
def handle_chat_stream(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    def _gen():
        text = llm.ask(body.query)            # 真实场景:换成流式 SDK 调用
        for ch in text:
            yield f"data: {ch}\n\n"           # SSE 协议:每条 "data: xxx\n\n"
    return StreamingResponse(_gen(), media_type="text/event-stream")
```

要点:
- `StreamingResponse` 接收一个**生成器**,FastAPI 边 `yield` 边往连接写,**不等全部产完**。
- `media_type="text/event-stream"` 是 SSE 协议。每条消息格式 `data: <内容>\n\n`,前端用 `EventSource` 或 `fetch + ReadableStream` 消费。
- 真实场景:Anthropic/OpenAI SDK 有流式 API(`stream=True`),`_gen` 里 `for event in client.messages.stream(...): yield ...`,逐 token 推。

> 🔴 **Java 对比**:= Spring `SseEmitter` 或 WebFlux `Flux<ServerSentEvent>`。Python 用生成器 + `StreamingResponse` 更简洁——生成器天然是「惰性产值」,完美匹配流式。
>
> 🟢 **普通 JSON vs SSE 对比**:
> | | 普通 `/chat` | SSE `/chat/stream` |
> |---|---|---|
> | 首字延迟 | 等满 10s | 0.3s 开始蹦 |
> | 协议 | `application/json` | `text/event-stream` |
> | 前端 | `fetch().then(r=>r.json())` | `EventSource` / `ReadableStream` |
> | 实现复杂度 | 简单 | 略复杂(生成器) |
> | 适用 | 后台任务、非交互 | ChatGPT 式聊天 UI |

> ✅ 做 `handle_chat_stream`(进阶可选):造生成器逐字 `yield f"data: {ch}\n\n"`,`return StreamingResponse(_gen(), media_type="text/event-stream")`。

---

## §33.8 生产意识:长耗时 / 限流 / 缓存 / 成本 🔴

AI 服务和普通 CRUD API 不一样,有四个「生产坑」必须知道(本章只需建立意识,实战在 M5+ 项目里):

### ① 长耗时
LLM 调用秒级起步。问题:
- HTTP 客户端/网关默认超时 30s,长回复可能被掐断 → 调高超时或上 SSE。
- 同步调用阻塞 worker → 用 `AsyncAnthropic`(Ch18)+ `async def` 路由,或在路由里 `await run_in_threadpool(llm.ask, ...)`。
- 长任务(生成报告、批量)→ 别让 HTTP 请求挂着,改成**任务队列**(Celery/ARQ):POST 立即返回 `task_id`,后台慢慢跑,客户端轮询 `/task/{id}`。

### ② 限流(Rate Limit)
LLM 烧钱,一个用户狂调能把你调破产。API 层必须限流:
- 按 user/IP 限流(`slowapi` 库,= Spring `bucket4j`)。
- 按token 预算限流(每用户每天 10 万 token)。
- LLM 提供商自己也有 rate limit(429),你要捕获取重试(§28.6)。

### ③ 缓存
同样的 query 多次问,LLM 每次都重算——浪费。缓存策略:
- **精确缓存**:`query` → `reply` 存 Redis,命中直接返回(快、省、但只能命中完全一样的问法)。
- **语义缓存**:向量相似度高的 query 复用(Ch30 RAG 套路,进阶)。
- 缓存要在 `chat_logic` 层加,路由层透明。

### ④ 成本控制
- `max_tokens` 卡输出上限(§28.5)——防超长输出烧钱。
- 日志记录每次调用的 token 数,做成本看板。
- 不同端点用不同模型(贵模型走付费用户,便宜模型走免费层)。

> 🟡 **Java 对比**:这些和 Spring 里加 `@RateLimiter`(Resilience4j)、`@Cacheable`(Spring Cache)、`@Async`(任务)是同一类问题,只是 Python 生态用 `slowapi`/`redis`/`Celery` 这些库。AI 服务的特殊之处在于**调用慢 + 贵**,所以这四点比普通 CRUD 更关键。

---

## §33.9 Java 老手常踩的坑 ⚠️

1. **把 LLM 写死在路由里**(`llm = EchoLLM()`)→ 测试没法替换、换模型要改一堆地方。**永远走 `Depends`**。
2. **测试真打 LLM** → CI 慢、不稳、烧钱。**永远用 `dependency_overrides` 注入假 LLM**。
3. **忘了清理 `dependency_overrides`** → 一个用例的假 LLM 污染下一个用例。用 `fixture` 的 teardown(`app.dependency_overrides.clear()`),或 `try/finally`。
4. **把业务逻辑塞进路由** → 路由难测、逻辑和 HTTP 耦合。**Service 层(`chat_logic`)和 Controller 层(`handle_chat`)分开**。
5. **健康检查探 `/chat`** → 探活也烧 LLM 钱。专门的 `/health` 不调外部依赖。
6. **SSE 忘了 `media_type`** → 前端按普通 JSON 解析就炸。必须 `text/event-stream`。
7. **同步 LLM 调用阻塞 async 路由** → 高并发场景用 `AsyncAnthropic` + `await`,或在 async 路由里用 `run_in_threadpool` 包同步调用。
8. **不限流** → 一个恶意用户一晚上烧光你的 API 额度。生产必加 rate limit。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `get_llm` | Depends 依赖 + 可替换 | 🟡 |
| `chat_logic` | 逻辑/路由分离 | 🟢 |
| `handle_health` | 健康检查端点 | 🟢 |
| `handle_chat` | 路由 + Pydantic + Depends | 🟡 |
| `handle_chat_stream` | SSE 流式(进阶) | 🔴 |

```bash
uv run pytest 05_ai_framework/ch33/test_ch33_assignment.py -v
```

全绿 = 掌握 Ch33。

---

## ✅ 自测

- [ ] 能说清「为什么 LLM 要包成依赖」(可替换、可测试)
- [ ] 会用 `app.dependency_overrides` 注入假 LLM 做离线测试,并知道要清理
- [ ] 理解路由(`handle_chat`)和逻辑(`chat_logic`)为什么要分
- [ ] 知道 Pydantic 校验失败返回 422(不是 400)
- [ ] 能讲清 SSE 流式相对普通 JSON 的优势(首字延迟、打字机效果)
- [ ] 知道 AI 服务的四个生产坑(长耗时、限流、缓存、成本)
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么不把 LLM 写死在路由里?`Depends` 给我们换了什么?」— 重读 §33.3
2. 「`chat_logic` 和 `handle_chat` 各自的职责?为什么要拆?」— 重读 §33.4/§33.5
3. 「SSE 流式相比一次性 JSON,延迟和体验差在哪?」— 重读 §33.7
4. 「AI 服务上线前,你最该加哪四样东西?」— 重读 §33.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:M5 毕业 🎓

Ch28–Ch33 走完一遍:**调 LLM(Ch28)→ Prompt 工程(Ch29)→ RAG(Ch30/Ch31)→ Agent(Ch32)→ 封装成服务(Ch33)**——你已经能搭一个「生产级 AI 应用」了。

M5 毕业项目建议(挑一个做):
- 把 Ch31 的 RAG 包成 `/chat` 流式 API(本章 §33.6+§33.7 套路),前端做一个 ChatGPT 风格 UI。
- 把 Ch32 的 Agent 包成 `/agent/run` 异步 API,用任务队列(Celery/ARQ)处理长任务。

之后进入 **M6 LeetCode 实战(Ch34+)**——用 Pythonic 方式刷题,体验「Python 3 行 = Java 15 行」的爽感。
