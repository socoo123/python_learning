"""
Ch33 作业：用 FastAPI 封装 AI 服务。

🎯 主线场景：你是「极客商城」AI 组工程师。Ch32 的客服 Agent 内部跑通了，现在要
开放给小程序/App——把 LLM 能力封装成生产级 HTTP API，带上四个生产件：
依赖注入（可测试）、token 成本估算（可计费）、精确缓存（省重复钱）、限流 429（防刷），
外加一个 SSE 流式端点（打字机体验）。

三个核心套路（和 Java Spring Boot 一一对应）：
  1. 依赖注入（Depends）注入 LLM     = Spring @Autowired + @MockBean
     —— 测试时用 app.dependency_overrides 换成假 LLM，离线跑、不花钱。
  2. Pydantic 请求模型自动校验      = Spring @RequestBody + @Valid
     —— 缺字段/类型错 → 422，FastAPI 全包了。
  3. 逻辑和路由分离（chat_logic）   = Service 层 vs Controller 层
     —— handle_chat 只管「接 HTTP」，真正干活的是 chat_logic，可独立测试。

本作业【不调真实 LLM】：默认注入 EchoLLM（离线 echo），测试用假 LLM 覆盖。
真实用法（接 Anthropic SDK）在 tutorial.md §33.11 有完整示例。

8 个函数 + app 装配。在每处 TODO 写实现，然后：

    uv run pytest 05_ai_framework/ch33/test_ch33_assignment.py -v

全绿 = 你掌握了 Ch33。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# ========== §33.2 LLM 协议与默认实现：EchoLLM ==========


class EchoLLM:
    """
    【默认实现 · §33.2】一个【离线假 LLM】：ask(query) 原样回 "echo:{query}"。
    生产时把它换成真实 SDK 的封装类（同样实现 ask 方法，内部调 client.messages.create）。

    为什么要有它？
      - 默认依赖能跑（不连网、不花钱、CI 友好）
      - 定义了「LLM 协议」：只要带 .ask(query)->str 就能注入（鸭子类型 / Protocol）
      - 和 Java 的「面向接口编程」一个道理：Controller 依赖接口，DefaultImpl 给个默认实现

    Java 对比：= 一个实现了 ChatService 接口的默认 EchoServiceImpl。
    """

    def ask(self, query: str) -> str:
        return f"echo:{query}"


# ========== §33.2 Pydantic 请求模型（= Java DTO + @Valid）==========


class ChatRequest(BaseModel):
    """
    【请求模型 · §33.2】POST /chat 与 /chat/stream 的请求体。FastAPI 拿到 JSON 后：
      ① 按 Pydantic 解析  ② 校验类型/必填  ③ 失败返回 422（不是 400）
    你只管把 body 当普通对象用。

    字段：
      - query：用户的问题（必填，缺失 → 422）
      - user：调用方用户标识（可选，默认 "guest"）——限流按它分桶计数

    Java 对比：= Spring 的 @RequestBody ChatRequestDTO + @Valid + Bean Validation。
    """

    query: str
    user: str = "guest"


# ========== App 装配 + 模块级状态（保留，别擦——路由要靠装饰器注册）==========

app = FastAPI(title="极客商城 AI 客服 API", version="0.1.0")

# 教学版用模块级 dict 当「账本」和「缓存」（生产换 Redis：多实例共享 + TTL 过期）。
# ⚠️ 全局状态会在测试之间残留——本章测试用 autouse fixture 每个用例前 clear()。
RATE_LIMIT = 3                          # 每用户最多 3 次（教学版取小，便于触发 429）
REQUEST_LEDGER: dict[str, int] = {}     # 限流账本：user -> 已放行次数
CHAT_CACHE: dict[str, dict] = {}        # 响应缓存：query -> {"reply": ..., "tokens": ...}


# ========== §33.3 依赖注入：get_llm ==========


def get_llm() -> EchoLLM:
    """
    【依赖 · §33.3】FastAPI 依赖函数：返回一个 LLM 实例（默认 EchoLLM）。
    路由函数用 Depends(get_llm) 声明依赖，FastAPI 自动调用它、把返回值塞给参数。

    为什么要包成依赖而不是直接 EchoLLM()？
      —— **可替换**。测试时：
          app.dependency_overrides[get_llm] = lambda: FakeLLM()
      生产时（读环境变量决定用哪个 LLM）：
          def get_llm():
              if os.getenv("LLM_PROVIDER") == "anthropic":
                  return AnthropicLLM()
              return EchoLLM()
      路由代码完全不用改。这就是「依赖注入」的价值。

    Java 对比：
      - 路由函数 Depends(get_llm)  = Spring 构造器 @Autowired ChatService chatService
      - app.dependency_overrides   = Spring 测试里 @MockBean 替换实现

    示例（测试）：
        app.dependency_overrides[get_llm] = lambda: _MockLLM()
        # 之后所有 Depends(get_llm) 拿到的都是 _MockLLM 实例

    思路：
        return EchoLLM()
    """
    # TODO: 返回一个 LLM 实例（默认 EchoLLM()）
    ...


# ========== §33.4 成本估算：estimate_tokens ==========


def estimate_tokens(text: str) -> int:
    """
    【成本估算 · §33.4】估算一段文本的 token 数，用于计费日志/成本看板。

    教学版约定（离线，没有真 API 的 usage）：
        每 2 个字符 ≈ 1 token，不足 1 按 1 记（保底 1，防漏账/除零）。
    生产环境别估算：读 SDK 返回的 resp.usage（input_tokens/output_tokens），
    或用 tiktoken 精确数。

    示例（手算验证）：
        estimate_tokens("")                    -> 1   （保底）
        estimate_tokens("你好")                 -> 1   （2 字符）
        estimate_tokens("echo:你好")            -> 3   （7 字符）
        estimate_tokens("机械键盘还有货吗")       -> 4   （8 字符）
        estimate_tokens("echo:机械键盘还有货吗")  -> 6   （13 字符）

    思路：
        return max(1, len(text) // 2)

    为什么 max(1, ...)？
        空回复记 0 token，成本看板漏账；下游拿 token 数做分母还会除零。
        一次调用再短也是一次调用，保底 1。
    """
    # TODO: 每 2 字符 ≈ 1 token，保底 1
    ...


# ========== §33.5 逻辑层：chat_logic ==========


def chat_logic(llm, query: str) -> dict:
    """
    【核心逻辑 · §33.5】真正的「业务逻辑」——调 llm 拿回复，连同 token 用量一起返回。
    刻意从路由里拆出来：
      - llm 是入参（不直接 new），方便测试传假对象
      - 不碰 HTTP/FastAPI，纯函数，好测
      - handle_chat 只负责「接 HTTP + 调它」，职责单一

    响应里为什么带 tokens？
      ① 服务端写日志/看板，成本可追踪（§33.4）；② 前端可展示「本次消耗」。

    Java 对比：= Service 层的 chat() 方法；handle_chat 是 Controller。

    示例：
        chat_logic(EchoLLM(), "你好")              -> {"reply": "echo:你好", "tokens": 3}
        chat_logic(EchoLLM(), "机械键盘还有货吗")     -> {"reply": "echo:机械键盘还有货吗", "tokens": 6}

    思路：
        reply = llm.ask(query)
        return {"reply": reply, "tokens": estimate_tokens(reply)}
    """
    # TODO: 调 llm.ask(query)，把回复和 token 估算一起包成 dict 返回
    ...


# ========== §33.6 缓存：chat_with_cache ==========


def chat_with_cache(llm, query: str, cache: dict) -> dict:
    """
    【缓存 · §33.6】带精确缓存的聊天：同一 query 第二次直接命中，LLM 零调用。
    客服 FAQ 场景「支持 7 天无理由退货吗」一天被问 8000 次——答案不变，不该重算 8000 次。

    约定：
      - 命中：返回 {**cache[query], "cached": True}（不调 llm）
      - 未命中：走 chat_logic，把【纯净结果】{"reply","tokens"} 存进 cache，
        返回 {**result, "cached": False}
      - cached 是「这一次请求」的元信息，**只在返回时现加，绝不存进缓存**
        （否则命中后取出来的 cached 永远是第一次存的 False）

    语法点：{**d, "cached": True} = dict 解包合并（摊开 d 再盖一个键），
    ≈ Java 的 new HashMap<>(d) + put("cached", true)。

    示例（mock 是带 calls 记录的假 LLM，回 "MOCK:{query}"）：
        cache = {}
        chat_with_cache(mock, "你好", cache)
            -> {"reply": "MOCK:你好", "tokens": 3, "cached": False}   # 真调，mock.calls == ["你好"]
        chat_with_cache(mock, "你好", cache)
            -> {"reply": "MOCK:你好", "tokens": 3, "cached": True}    # 命中，mock.calls 还是 ["你好"]
        cache["你好"] == {"reply": "MOCK:你好", "tokens": 3}           # 缓存里没有 cached 键

    思路：
        if query in cache: return {**cache[query], "cached": True}
        result = chat_logic(llm, query)
        cache[query] = result
        return {**result, "cached": False}

    生产提醒：
        - dict 换成 Redis（key=query，value=JSON，加 TTL）。
        - 涉及用户隐私的对话（「我的订单」）缓存键要带 user 或禁用缓存——把 A 的订单答给 B 是事故。
    """
    # TODO: 命中返回带 cached:True；未命中走 chat_logic、存纯净结果、返回带 cached:False
    ...


# ========== §33.7 限流：allow_request ==========


def allow_request(ledger: dict, user: str, limit: int) -> bool:
    """
    【限流 · §33.7】计数器限流：每用户最多放行 limit 次，超限返回 False。
    LLM 烧钱，一个脚本哥一夜能刷穿额度——限流必须挡在路由最前面（§33.8）。

    约定：
      - ledger：{user: 已放行次数} 的账本（dict）
      - 放行：ledger[user] += 1，返回 True
      - 超限（已用 >= limit）：返回 False，**计数不再涨**（拒绝的请求不消耗配额）
      - 新用户从 0 起（dict.get 容错，别 KeyError）

    示例：
        ledger = {}
        allow_request(ledger, "u1001", 2)   # -> True   ledger == {"u1001": 1}
        allow_request(ledger, "u1001", 2)   # -> True   ledger == {"u1001": 2}
        allow_request(ledger, "u1001", 2)   # -> False  超限，ledger 仍是 {"u1001": 2}
        allow_request(ledger, "u1002", 2)   # -> True   换个用户，独立配额
        allow_request({}, "u1001", 0)       # -> False  limit=0 全拒（边界）

    思路：
        used = ledger.get(user, 0)
        if used >= limit: return False
        ledger[user] = used + 1
        return True

    为什么返回 bool 而不是抛异常？
        限额判断是业务决策，「拒绝后怎么办」留给调用方——路由层转成 429（§33.8）。
        生产换时间窗限流（slowapi 库 ≈ Java bucket4j），本函数的教学版用计数器，
        行为确定、好测。
    """
    # TODO: 查账本 → 超限 False → 否则计数 +1 返回 True
    ...


# ========== §33.8 路由装配：handle_health / handle_chat ==========


@app.get("/health")
def handle_health():
    """
    【健康检查 · §33.8】GET /health，返回 {"status": "ok"}。
    生产环境 K8s/ELB 每 5 秒探活就打这个端点——必须轻量、零外部依赖。
    （探 /chat 会真打 LLM：探活也烧钱，一天 17280 次。）

    思路：
        return {"status": "ok"}
    """
    # TODO: 返回 {"status": "ok"}
    ...


@app.post("/chat")
def handle_chat(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    """
    【聊天路由 · §33.8 · 综合题】POST /chat，接收 {"query": ..., "user": ...}。

    装配顺序就是防御纵深（两行不能换）：
      ① 先限流：allow_request(REQUEST_LEDGER, body.user, RATE_LIMIT) 不通过 →
         raise HTTPException(status_code=429, detail="请求太频繁，请稍后再试")
         —— 恶意脚本刷必中缓存的重复问题，也照样被挡在最前。
      ② 后缓存：return chat_with_cache(llm, body.query, CHAT_CACHE)
         —— 放行之后才查缓存，命中就省一次 LLM 调用。

    - body: ChatRequest —— FastAPI 看到「Pydantic 模型作参数」就自动解析 + 校验（失败 422）。
    - llm: Depends(get_llm) —— 声明依赖，测试时被 dependency_overrides 换成假 LLM。
    - HTTPException = Spring 的 ResponseStatusException：框架捕获后转成 429 JSON 响应。

    Java 对比：= Spring @RestController 里：
        @PostMapping("/chat")
        public ChatReply chat(@Valid @RequestBody ChatRequest body) { ... }

    示例（RATE_LIMIT=3，默认 EchoLLM）：
        POST /chat {"query": "你好"}                  -> 200 {"reply": "echo:你好", "tokens": 3, "cached": false}
        再发一次相同请求                               -> 200 {...同上..., "cached": true}
        第 4 次请求（任意 query）                      -> 429 {"detail": "请求太频繁，请稍后再试"}
        POST /chat {}                                 -> 422（缺必填字段 query）

    思路：
        if not allow_request(REQUEST_LEDGER, body.user, RATE_LIMIT):
            raise HTTPException(status_code=429, detail="请求太频繁，请稍后再试")
        return chat_with_cache(llm, body.query, CHAT_CACHE)
    """
    # TODO: 先限流（超限 raise HTTPException 429），通过后走 chat_with_cache
    ...


# ========== §33.9 SSE 流式：handle_chat_stream ==========


@app.post("/chat/stream")
def handle_chat_stream(body: ChatRequest, llm: EchoLLM = Depends(get_llm)):
    """
    【流式 · §33.9】POST /chat/stream，用 SSE（Server-Sent Events）流式返回。
    普通 /chat 要等全部生成完；SSE 边产边发，前端打字机效果，首字 0.3 秒。

    三件套（缺一不可）：
      ① 生成器：def gen(): ... yield ...（惰性产值，FastAPI 边 yield 边写连接）
      ② 消息格式：每条 "data: <内容>\\n\\n"（\\n\\n 是一条消息的结束符）
      ③ media_type="text/event-stream"（忘了前端按 JSON 解析就炸）
    结尾补一条 "data: [DONE]\\n\\n"——OpenAI 沿袭下来的结束约定，前端读到它知道流结束。

    Java 对比：= Spring 的 SseEmitter / WebFlux Flux<ServerSentEvent>。
    Python 的生成器天然是「惰性产值」，和流式绝配。

    示例（假 LLM 回 "MOCK:hi"）：
        POST /chat/stream {"query": "hi"}
        响应体逐字蹦出：
            data: M\\n\\ndata: O\\n\\ndata: C\\n\\ndata: K\\n\\ndata: :\\n\\ndata: h\\n\\ndata: i\\n\\ndata: [DONE]\\n\\n

    思路：
        def gen():
            text = llm.ask(body.query)        # 真实场景：换成 SDK 的流式接口（§33.11）
            for ch in text:
                yield f"data: {ch}\\n\\n"
            yield "data: [DONE]\\n\\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    生产提醒：流式端点一样要限流（allow_request 原样可用）；教学版聚焦 SSE 机制本身。
    """
    # TODO: 内层生成器逐字 yield "data: {ch}\n\n" + 结尾 [DONE]，外层 StreamingResponse
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 本地手动试：uv run python 05_ai_framework/ch33/ch33_assignment.py，然后另开终端：
    #   curl -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"query":"你好"}'
    #   curl -N -X POST localhost:8000/chat/stream -H 'Content-Type: application/json' -d '{"query":"你好"}'
    #   （连发 4 次 /chat 可以看到 429；同一个 query 发两次可以看到 cached 变 true）
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
