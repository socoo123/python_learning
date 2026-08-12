"""
Ch28 作业：LLM SDK 调用（Anthropic / OpenAI)。

学「调」LLM——和 Java 调 REST API 一样，但 Python SDK 把 HTTP/JSON 封装成方法调用。
核心：发消息(messages)、解析响应(.content)、估 token、算成本、多轮对话、重试。

🎯 主线场景：电商后台「商品营销文案生成器」——读 products.json 的商品，
调 LLM 生成带货文案，支持多轮改写、控成本、扛网络抖动。

设计要点：本作业【不调真实 API】。client 用鸭子类型(只要带 .messages.create() 就行),
测试用 FakeClient 离线跑。真实用法在 tutorial.md §28.9 有完整示例(配 API key)。

7 个函数。在每处 TODO 写实现，然后:

    uv run pytest 05_ai_framework/ch28/test_ch28_assignment.py -v

全绿 = 你掌握了 Ch28。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:
- response 是 LLM 响应对象，anthropic 形如 response.content = [TextBlock(text=...), ...]
  (每个 block 有 .type 和 .text);也可能是字符串或 dict 列表。extract_text 要兼容。
- client 带 .messages.create(model=..., system=..., messages=[...], max_tokens=...)。
"""

# Claude 各模型的 (每 token 美元) 单价表:(输入价, 输出价)
# 来源: https://www.anthropic.com/pricing (2024 年价格,会变动,理解原理即可)
PRICING = {
    "claude-3-5-sonnet-20241022": (3e-6, 15e-6),      # 输入 $3/百万 token,输出 $15/百万
    "claude-3-haiku-20240307": (0.25e-6, 1.25e-6),    # 便宜的小模型
}


# ========== §28.2 解析响应:extract_text ==========


def extract_text(response) -> str:
    """
    【解析 · §28.2】从 LLM 响应对象里提取纯文本，兼容三种形态:
      ① anthropic 风格:response.content 是 [TextBlock(...)] 列表 → 拼接各 block.text
      ② response.content 直接是字符串 → 返回它
      ③ response 本身就是字符串 → 返回它

    示例:
        extract_text(resp)   # resp.content=[TextBlock(text="你好")] -> "你好"
        extract_text(resp2)  # resp2.content=[B("a"), B("b")]        -> "ab"
        extract_text("hi")   -> "hi"

    提示(duck typing,getattr 容错):
        content = getattr(response, "content", response)   # 没有 .content 就当它本身是内容
        if isinstance(content, str): return content
        遍历 block: text = getattr(block,"text",None) 或 block.get("text")(dict 情况)
    """
    # TODO: getattr(response,"content",response);str 直接返回;否则遍历 block 取 .text/["text"] 拼接
    ...


# ========== §28.3 构造消息:build_user_message ==========


def build_user_message(content: str) -> dict:
    """
    【消息 · §28.3】构造一条 user 消息。LLM API 的对话单位是 {"role":..., "content":...}。

    示例:
        build_user_message("你好")   -> {"role": "user", "content": "你好"}
        build_user_message("给机械键盘写文案") -> {"role": "user", "content": "给机械键盘写文案"}

    提示:一行 return 搞定。抽成函数是为了 DRY——以后加字段(如 name)只改这里。
    """
    # TODO: return {"role": "user", "content": content}
    ...


# ========== §28.4 发请求:call_llm ==========


def call_llm(
    client,
    system: str,
    user: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 1024,
) -> str:
    """
    【发请求 · §28.4】用 client 发一次「system + 单轮 user」请求，返回模型回复文本。
    client.messages.create(...) 是同步调用，返回响应对象。

    示例:
        call_llm(client, "你是文案助手", "给机械键盘写文案") -> "指尖机械狂想,敲击即享受!"

    提示(对比 Java HttpClient.post + Jackson 反序列化):
        response = client.messages.create(
            model=model, system=system, max_tokens=max_tokens,
            messages=[build_user_message(user)],     # 复用 §28.3
        )
        return extract_text(response)                # 复用 §28.2
    """
    # TODO: client.messages.create(model/system/max_tokens/messages=[build_user_message(user)]);return extract_text
    ...


# ========== §28.5 token 与成本:estimate_tokens / estimate_cost ==========


def estimate_tokens(text: str) -> int:
    """
    【token · §28.5】粗估一段文本的 token 数(英文约 4 字符 ≈ 1 token)。
    精确要用 tiktoken / SDK 的 count_tokens，这里给粗估即可。

    示例:
        estimate_tokens("hello world")  -> 2     # 11 字符 // 4 = 2
        estimate_tokens("")             -> 1     # 至少 1(空也占 token)
        estimate_tokens("a"*40)         -> 10

    提示: return max(1, len(text) // 4)
    """
    # TODO: max(1, len(text) // 4)
    ...


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    【成本 · §28.5】按模型单价算一次调用的成本(美元)。
    计费 = 输入 token × 输入单价 + 输出 token × 输出单价(输出通常更贵)。

    示例(用 PRICING 表,sonnet: 输入 3e-6,输出 15e-6):
        estimate_cost("claude-3-5-sonnet-20241022", 50, 100)
            -> 50*3e-6 + 100*15e-6 = 0.00165
        estimate_cost("claude-3-haiku-20240307", 1000, 1000)
            -> 1000*0.25e-6 + 1000*1.25e-6 = 0.0015

    提示:
        in_price, out_price = PRICING[model]   # 解包元组
        return input_tokens * in_price + output_tokens * out_price
    """
    # TODO: 查 PRICING[model] 得 (in_price, out_price),返回 in*in_price + out*out_price
    ...


# ========== §28.6 多轮对话:build_messages ==========


def build_messages(history: list[dict], user: str) -> list[dict]:
    """
    【多轮 · §28.6】把历史消息 + 新 user 消息拼成 messages 列表(不修改原 history)。
    每条形如 {"role": "user"/"assistant", "content": "..."}。LLM 无状态,多轮靠每次发全部历史。

    示例:
        build_messages([{"role":"user","content":"hi"},{"role":"assistant","content":"hello"}], "再来")
            -> [{"role":"user",...},{"role":"assistant",...},{"role":"user","content":"再来"}]
        build_messages([], "first") -> [{"role":"user","content":"first"}]

    提示(新建列表,别 mutate 入参——可变默认参数陷阱 Ch02):
        return [*history, build_user_message(user)]
    """
    # TODO: 返回 history 副本 + 追加 build_user_message(user)
    ...


# ========== §28.7 重试:with_retry ==========


def with_retry(func, attempts: int = 3, errors=Exception):
    """
    【重试 · §28.7】调用 func,失败(attempts 次内)重试,全失败则抛最后一次异常。
    errors 指定哪些异常算「可重试」(默认所有)。生产里只重试瞬时错误(429/5xx/超时)。

    示例:
        with_retry(lambda: 42)                                -> 42     # 一次成功
        with_retry(flaky_times_2, attempts=3, errors=ValueError) -> "ok"  # 第3次成功
        with_retry(always_fail, attempts=2, errors=ValueError)   # 抛 ValueError

    提示(EAFP,Ch07 学过):
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


# ========== §28.8 综合:generate_product_description ==========


def generate_product_description(client, product: dict, tone: str = "活泼") -> str:
    """
    【综合 · §28.8】商品营销文案生成器——串起前面所有函数,完成业务闭环。
    输入商品 dict(来自 products.json)和语气,输出一段营销文案。要求带重试,扛网络抖动。

    示例:
        product = {"name": "机械键盘", "category": "电脑外设", "price": 599.0}
        generate_product_description(client, product, tone="活泼")
            -> "指尖机械狂想,敲击即享受!⌨️"   (client 是 FakeClient 时返回其预设文本)

    提示(组合优于继承——不用写类,几个小函数一拼就是业务):
        prompt = f"给商品写一段{tone}风格的带货文案(30字内):" \
                 f"{product['name']},品类{product['category']},价格¥{product['price']}"
        return with_retry(
            lambda: call_llm(client, "你是电商文案助手", prompt, max_tokens=100),
            attempts=3,
        )
    """
    # TODO: 拼 prompt(含 tone/name/category/price)→ with_retry(lambda: call_llm(...), attempts=3)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示用 FakeClient(真实用法见 tutorial.md §28.9:from anthropic import Anthropic; client=Anthropic())
    class _B:
        def __init__(s, t):
            s.type, s.text = "text", t

    class _R:
        def __init__(s, t):
            s.content = [_B(t)]

    class _M:
        def __init__(s, p):
            s.p = p

        def create(s, **k):
            return s.p._c(k)

    class FakeClient:
        def __init__(s, t="ok"):
            s.t, s.calls, s.messages = t, [], _M(s)

        def _c(s, k):
            s.calls.append(k)
            return _R(s.t)

    c = FakeClient("指尖机械狂想,敲击即享受!")
    kb = {"name": "机械键盘", "category": "电脑外设", "price": 599.0}
    print("文案:", generate_product_description(c, kb, tone="活泼"))
    print("prompt 实际发送:", c.calls[0]["messages"][0]["content"][:40], "...")
    print("tokens:", estimate_tokens("hello world"))
    print("成本(50in/100out):", estimate_cost("claude-3-5-sonnet-20241022", 50, 100))
