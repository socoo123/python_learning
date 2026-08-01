"""
Ch33 作业:用 FastAPI 封装 AI 服务。

把 Ch28 学的「调 LLM」包装成生产级 HTTP API——前端/客户端只管 POST /chat,
不用关心背后用哪家模型、怎么鉴权、怎么重试。这就是「AI 服务化」。

三个核心套路(和 Java Spring Boot 一一对应):
  1. 依赖注入(Depends)注入 LLM     = Spring @Autowired + @MockBean
     —— 测试时用 app.dependency_overrides 换成假 LLM,离线跑、不花钱。
  2. Pydantic 请求模型自动校验      = Spring @RequestBody + @Valid
     —— 缺字段/类型错 → 422,FastAPI 全包了。
  3. 逻辑和路由分离(chat_logic)   = Service 层 vs Controller 层
     —— handle_chat 只管「接 HTTP」,真正干活的是 chat_logic,可独立测试。

本作业【不调真实 LLM】:默认注入 EchoLLM(离线 echo),测试用假 LLM 覆盖。
真实用法(接 Anthropic/OpenAI SDK)在 tutorial.md §33.6 有完整示例。

4 个函数 + app 装配。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch33/test_ch33_assignment.py -v

全绿 = 你掌握了 Ch33。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# ========== §33.1 默认 LLM:EchoLLM(离线,真实换真 SDK)==========


class EchoLLM:
    """
    【默认实现 · §33.1】一个【离线假 LLM】:ask(query) 原样回 "echo:{query}"。
    生产时把它换成真实 SDK 的封装类(同样实现 ask 方法,内部调 client.messages.create)。

    为什么要有它?
      - 默认依赖能跑(不连网、不花钱、CI 友好)
      - 定义了「LLM 协议」:只要带 .ask(query)->str 就能注入(鸭子类型 / Protocol)
      - 和 Java 的「面向接口编程」一个道理:Controller 依赖接口,DefaultImpl 给个默认实现

    Java 对比:= 一个实现了 ChatService 接口的默认 EchoServiceImpl。
    """

    def ask(self, query: str) -> str:
        return f"echo:{query}"


# ========== §33.2 Pydantic 请求模型(= Java DTO + @Valid)==========


class ChatRequest(BaseModel):
    """
    【请求模型 · §33.2】POST /chat 的请求体。FastAPI 拿到 JSON 后:
      ① 按 Pydantic 解析  ② 校验类型/必填  ③ 失败返回 422
    你只管把 body 当普通对象用。

    Java 对比:= Spring 的 @RequestBody ChatRequestDTO + @Valid + Bean Validation。
    缺 query 字段 → FastAPI 自动返回 422(不用你写 if query is None)。
    """

    query: str
    max_tokens: int = 1024          # 可选,默认 1024


# ========== App 装配(保留,别擦——路由要靠装饰器注册)==========

app = FastAPI(title="AI Chat API", version="0.1.0")


# ========== §33.3 依赖注入:get_llm(对应:get_llm)==========


def get_llm() -> EchoLLM:
    """
    【依赖 · §33.3】FastAPI 依赖函数:返回一个 LLM 实例(默认 EchoLLM)。
    路由函数用 Depends(get_llm) 声明依赖,FastAPI 自动调用它、把返回值塞给参数。

    为什么要包成依赖而不是直接 EchoLLM()?
      —— **可替换**。测试时:
          app.dependency_overrides[get_llm] = lambda: FakeLLM()
      生产时(读环境变量决定用哪个 LLM):
          def get_llm():
              if os.getenv("LLM_PROVIDER") == "anthropic":
                  return AnthropicLLM()
              return EchoLLM()
      路由代码完全不用改。这就是「依赖注入」的价值。

    Java 对比:
      - 路由函数 Depends(get_llm)  = Spring 构造器 @Autowired ChatService chatService
      - app.dependency_overrides   = Spring 测试里 @MockBean / @ReplaceBean 替换实现

    示例(测试):
        app.dependency_overrides[get_llm] = lambda: _MockLLM()
        # 之后所有 Depends(get_llm) 拿到的都是 _MockLLM 实例

    思路:
        return EchoLLM()
    """
    # TODO: 返回一个 LLM 实例(默认 EchoLLM())
    ...


# ========== §33.4 核心逻辑:chat_logic(对应:chat_logic)==========


def chat_logic(llm, query: str) -> dict:
    """
    【核心逻辑 · §33.4】真正的「业务逻辑」——调 llm,把回复包成 {"reply": ...}。
    刻意从路由里拆出来:
      - llm 是入参(不直接 new),方便测试传假对象
      - 不碰 HTTP/FastAPI,纯函数,好测
      - handle_chat 只负责「接 HTTP + 调它」,职责单一

    Java 对比:= Service 层的 chat() 方法;handle_chat 是 Controller。

    示例:
        chat_logic(EchoLLM(), "你好")  -> {"reply": "echo:你好"}

    思路:
        return {"reply": llm.ask(query)}
    """
    # TODO: 调 llm.ask(query),把结果包成 {"reply": ...}
    ...


# ========== §33.5 路由:handle_health / handle_chat(对应:同名函数)==========


@app.get("/health")
def handle_health():
    """
    【健康检查 · §33.5】GET /health,返回 {"status": "ok"}。
    生产环境 K8s/ELB 探活就打这个端点,不需要调真 LLM(否则探活也烧钱)。

    思路:
        return {"status": "ok"}
    """
    # TODO: 返回 {"status": "ok"}
    ...


@app.post("/chat")
def handle_chat(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    """
    【聊天路由 · §33.5】POST /chat,接收 {query, max_tokens},调 LLM,返回 {"reply": ...}。

    - body: ChatRequest —— FastAPI 看到「Pydantic 模型作参数」就自动从 JSON body 解析+校验。
    - llm: Depends(get_llm) —— 声明依赖,FastAPI 自动调 get_llm() 把结果塞进来。
      (测试时被 dependency_overrides 换成假 LLM)

    路由函数本身只做三件事:解析入参 → 调逻辑 → 返回。**业务细节交给 chat_logic**。

    Java 对比:= Spring @RestController 里:
        @PostMapping("/chat")
        public ChatReply chat(@Valid @RequestBody ChatRequest body) { ... }

    示例:
        POST /chat {"query":"hi"}  -> 200 {"reply":"echo:hi"}  (或 MOCK:hi,看注入谁)

    思路:
        return chat_logic(llm, body.query)
    """
    # TODO: 调 chat_logic(llm, body.query) 返回
    ...


# ========== §33.7 SSE 流式:handle_chat_stream(进阶,可选)==========


@app.post("/chat/stream")
def handle_chat_stream(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    """
    【流式 · §33.7 · 进阶】POST /chat/stream,用 SSE(Server-Sent Events)流式返回。
    每个 token/字 拆成一个小 chunk 立刻发出去,前端实现「打字机」效果,首字快、体验好。

    - StreamingResponse 接收一个【生成器】,FastAPI 边产边发(不用等全部生成完)。
    - media_type="text/event-stream" 是 SSE 协议格式:每条 "data: xxx\\n\\n"。
    - 前端用 EventSource 或 fetch + ReadableStream 消费。

    Java 对比:= Spring 的 SseEmitter / WebFlux Flux<ServerSentEvent>。
    普通 JSON 一次性返回 vs SSE 流式:前者等满 10s 才看到字,后者 0.3s 就开始蹦字。

    示例:
        POST /chat/stream {"query":"hi"}
        -> "data: echo:h\\n\\n" "data: echo:i\\n\\n" (逐字)

    思路:
        def gen():
            text = llm.ask(body.query)
            for ch in text:
                yield f"data: {ch}\\n\\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    """
    # TODO(进阶,可选): 造生成器逐字 yield "data: {ch}\\n\\n",return StreamingResponse
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 本地手动试:uv run python 05_ai_framework/ch33/ch33_assignment.py,然后另开终端 curl。
    #   curl -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"query":"hi"}'
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
