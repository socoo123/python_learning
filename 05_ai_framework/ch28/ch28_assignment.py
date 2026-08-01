"""
Ch28 作业:LLM SDK 调用(Anthropic / OpenAI)。

学「调」LLM——和 Java 调 REST API 一样,但 Python SDK 把 HTTP/JSON 封装成方法调用。
核心:发消息(messages)、解析响应(.content)、估 token、重试。

设计要点:本作业【不调真实 API】。client 用鸭子类型(只要带 .messages.create() 就行),
测试用 FakeClient 离线跑。真实用法在 tutorial.md 里有完整示例(配 API key)。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch28/test_ch28_assignment.py -v

全绿 = 你掌握了 Ch28。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:
- response 是 LLM 响应对象,anthropic 形如 response.content = [TextBlock(text=...), ...]
  (每个 block 有 .type 和 .text);也可能是字符串或 dict 列表。extract_text 要兼容。
- client 带 .messages.create(model=..., system=..., messages=[...], max_tokens=...)。
"""


# ========== §28.2 解析响应:extract_text ==========


def extract_text(response) -> str:
    """
    【解析 · §28.2】从 LLM 响应对象里提取纯文本,兼容三种形态:
      ① anthropic 风格:response.content 是 [TextBlock(...)] 列表 → 拼接各 block.text
      ② response.content 直接是字符串 → 返回它
      ③ response 本身就是字符串 → 返回它

    示例:
        extract_text(resp)   # resp.content=[TextBlock(text="你好")] -> "你好"
        extract_text("hi")   -> "hi"

    思路(getattr 容错,duck typing):
        content = getattr(response, "content", response)   # 没有就当它本身就是内容
        if isinstance(content, str): return content
        parts = []
        for block in content:
            text = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
            if text: parts.append(text)
        return "".join(parts)
    """
    # TODO: getattr(response,"content",response);str 直接返回;否则遍历 block 取 .text 拼接
    ...


# ========== §28.3 发请求:call_llm ==========


def call_llm(
    client,
    system: str,
    user: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 1024,
) -> str:
    """
    【发请求 · §28.3】用 client 发一次「system + 单轮 user」请求,返回模型回复文本。
    client.messages.create(...) 是同步调用,返回响应对象。

    示例:
        call_llm(client, "你是助手", "你好") -> "你好!有什么可以帮你?"

    思路(对比 Java HttpClient.post + 反序列化):
        response = client.messages.create(
            model=model, system=system, max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
        )
        return extract_text(response)        # §28.2 复用解析
    """
    # TODO: client.messages.create(...);return extract_text(response)
    ...


# ========== §28.4 多轮对话:build_messages ==========


def build_messages(history: list[dict], user: str) -> list[dict]:
    """
    【多轮 · §28.4】把历史消息 + 新 user 消息拼成 messages 列表(不修改原 history)。
    每条形如 {"role": "user"/"assistant", "content": "..."}。

    示例:
        build_messages([{"role":"user","content":"hi"},{"role":"assistant","content":"hello"}], "再来")
            -> [{"role":"user",...},{"role":"assistant",...},{"role":"user","content":"再来"}]

    思路(新建列表,别 mutate 入参——可变默认参数陷阱 Ch02):
        return [*history, {"role": "user", "content": user}]
    """
    # TODO: 返回 history 副本 + 追加 user 消息
    ...


# ========== §28.5 token 估算:estimate_tokens ==========


def estimate_tokens(text: str) -> int:
    """
    【token · §28.5】粗估一段文本的 token 数(英文约 4 字符 ≈ 1 token)。
    精确要用 tiktoken / SDK 的 count_tokens,这里给粗估即可。

    示例:
        estimate_tokens("hello world")  -> 2     # 11 字符 // 4 = 2
        estimate_tokens("")             -> 1     # 至少 1(空也占 token)

    思路:
        return max(1, len(text) // 4)
    """
    # TODO: max(1, len(text) // 4)
    ...


# ========== §28.6 重试:with_retry ==========


def with_retry(func, attempts: int = 3, errors=Exception):
    """
    【重试 · §28.6】调用 func,失败(attempts 次内)重试,全失败则抛最后一次异常。
    errors 指定哪些异常算「可重试」(默认所有)。

    示例:
        with_retry(lambda: 42)                          -> 42            # 一次成功
        n=[0]; f=lambda:(n.__setitem__(0,n[0]+1) or 1/n[0] if n[0]>=2 else (_ for _ in ()).throw(ValueError))
        with_retry(f, attempts=3, errors=ValueError)    -> 第三次成功
        with_retry(lambda:(_ for _ in ()).throw(ValueError()), attempts=2, errors=ValueError)  # 抛 ValueError

    思路(EAFP,Ch07 学过):
        last = None
        for _ in range(attempts):
            try:
                return func()
            except errors as e:
                last = e
        raise last
    """
    # TODO: for 循环 try/except errors,记住 last;全失败 raise last
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示用 FakeClient(真实用法见 tutorial.md:from anthropic import Anthropic; client=Anthropic(api_key=...))
    class _B:
        def __init__(s, t): s.type, s.text = "text", t
    class _R:
        def __init__(s, t): s.content = [_B(t)]
    class _M:
        def __init__(s, p): s.p = p
        def create(s, **k): return s.p._c(k)
    class FakeClient:
        def __init__(s, t="ok"): s.t, s.calls, s.messages = t, [], _M(s)
        def _c(s, k): s.calls.append(k); return _R(s.t)

    c = FakeClient("你好!有什么可以帮你?")
    print("call_llm:", call_llm(c, "你是助手", "你好"))
    print("tokens:", estimate_tokens("hello world"))
