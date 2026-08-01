# Ch28 · LLM SDK 调用:Anthropic / OpenAI

> **预计**:1 天 ｜ **前置**:M1、Ch13(httpx 概念)｜ **M5 开篇**
> **目标**:学会用 Python SDK「调」LLM——发消息、解析响应、估 token、加重试。和 Java 调 REST API 本质一样,但 SDK 把 HTTP/JSON 封装成了方法调用,体验像调本地函数。

> 📐 **本教程的契约**:§28.2–§28.6 对应作业 5 个函数。**作业不调真实 API**(用 FakeClient 离线测),真实用法(配 API key)在本教程有完整示例。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `extract_text` | §28.2 | 解析 LLM 响应(.content 的多种形态)+ duck typing |
| `call_llm` | §28.3 | client.messages.create 同步调用 |
| `build_messages` | §28.4 | 多轮对话 messages 列表 + 不 mutate 入参 |
| `estimate_tokens` | §28.5 | token 估算 + 计费/上下文窗口意识 |
| `with_retry` | §28.6 | 网络调用的重试(EAFP) |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① 预览猜 → ② 写 assignment(5 个函数)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 调一个 AI API 要 `HttpClient` + 拼 JSON body + 反序列化。Python 的 `anthropic` / `openai` SDK 把它简化成什么?
2. 模型返回的文本藏在响应对象的哪个字段?为什么不是直接的字符串?
3. 多轮对话,客户端要每次把「全部历史」发给模型吗?为什么?(提示:LLM 无状态)
4. 「1000 个 token」大概是多少英文单词?多少中文字?(计费和上下文窗口都靠它)
5. 网络调用必失败,你的代码怎么扛?(重试——和 Ch24 subprocess 一个套路)

---

## §28.1 SDK vs 裸 HTTP 🟡

调 LLM 两种方式:
- **裸 HTTP**(httpx/requests):自己拼 `POST /v1/messages`,自己解析 JSON。灵活但啰嗦。
- **官方 SDK**:`client.messages.create(...)`,SDK 帮你拼请求、解析响应、处理鉴权/重试/流式。**日常用 SDK**。

```python
# anthropic SDK
from anthropic import Anthropic
client = Anthropic()                      # 自动读 ANTHROPIC_API_KEY 环境变量
resp = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="你是助手",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.content[0].text)               # 模型回复
```

> 🟡 **Java 对比**:= `OkHttp`/`HttpClient` + Jackson 反序列化。SDK 把这些压成一个方法调用,响应对象是强类型的(像 Java 的 DTO)。openai SDK 用法几乎一样(换 `client.chat.completions.create(...)`)。

**鉴权铁律**:API key **绝不写进代码**,走环境变量(`ANTHROPIC_API_KEY`)或 `.env`(Ch12/Ch22 讲过)。SDK 默认读环境变量,所以代码里看不到明文 key。

> 🔴 **本作业不调真实 API**:为了离线可测、不花钱、CI 能跑,作业用 **FakeClient**(只要带 `.messages.create()` 的鸭子类型对象)。真实用法见上面的示例。

---

## §28.2 解析响应:extract_text(对应:`extract_text`)🟡

模型回复**不是直接字符串**,而是结构化对象(因为可能有多段文本、工具调用、思考等):

```python
resp = client.messages.create(...)
resp.content            # [TextBlock(type="text", text="你好"), ...]  ← 列表!
resp.content[0].text    # "你好"
```

为什么是列表?一次回复可能有多个内容块(文本 + 工具调用 + 引用),所以 `content` 是**块的列表**。作业 `extract_text` 要兼容多种形态(anthropic 的 block 列表 / 字符串 / dict 列表),用 duck typing:

```python
def extract_text(response) -> str:
    content = getattr(response, "content", response)   # 没有就当它本身是内容
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts)
```

- `getattr(response, "content", response)`:有 `.content` 取它,没有就把 response 本身当内容(兼容字符串入参)。这是 duck typing 的容错套路。
- 遍历 block,取 `.text`(对象)或 `["text"]`(dict),拼接。

> ✅ 做 `extract_text`:`getattr(response,"content",response)` → str 直接返回 → 否则遍历取 `.text`/`["text"]` 拼接。

---

## §28.3 发请求:call_llm(对应:`call_llm`)🟢

```python
def call_llm(client, system, user, model="claude-3-5-sonnet-20241022", max_tokens=1024):
    response = client.messages.create(
        model=model, system=system, max_tokens=max_tokens,
        messages=[{"role": "user", "content": user}],
    )
    return extract_text(response)          # 复用 §28.2
```

- `client.messages.create(...)`:**同步**调用,阻塞到模型返回(几秒)。SDK 也有异步版(`AsyncAnthropic`,Ch18 学的 async)。
- 参数:`model`(用哪个模型)、`system`(设定角色/规则)、`messages`(对话)、`max_tokens`(最多生成多少 token,防超长 + 控成本)。
- 复用 `extract_text` 解析——**小函数组合**,不要把解析逻辑塞进调用里。

> ✅ 做 `call_llm`:`client.messages.create(model/system/max_tokens/messages=[user])` → `extract_text`。

---

## §28.4 多轮对话:build_messages(对应:`build_messages`)🟡

**关键认知**:LLM 是**无状态**的——它不记得上一句。多轮对话靠**客户端每次把全部历史发过去**:

```python
def build_messages(history, user):
    return [*history, {"role": "user", "content": user}]
```

- 每次请求的 `messages` = 完整历史 + 新消息。模型靠这些历史「恢复」上下文。
- `role` 交替:`user`(用户)/ `assistant`(模型上轮回复)。多轮就是 user↔assistant 来回。
- **历史越长,token 越多,越贵**(§28.5)——所以有「上下文窗口」上限和「记忆截断」策略(Ch30 Memory 讲)。

> ⚠️ **别 mutate 入参**:`return [*history, ...]` 新建列表,不 `history.append(...)`。`append` 会改坏调用方的 history(可变默认参数陷阱,Ch02)。函数应该是「无副作用」的——这对应 Java 里别直接改别人传进来的 List。

> ✅ 做 `build_messages`:`return [*history, {"role":"user","content":user}]`。

---

## §28.5 token 估算:estimate_tokens(对应:)🟡

**token** 是 LLM 计费和上下文窗口的基本单位(≈ 一个词根)。不是字符、不是单词,是模型分词后的单元。

- 粗估:英文约 **4 字符 ≈ 1 token**;中文约 **1 字 ≈ 1-2 token**。
- 精确:用 `tiktoken` 库(openai 模型)或 SDK 的 `client.messages.count_tokens(...)`(anthropic)。

```python
def estimate_tokens(text):
    return max(1, len(text) // 4)          # 粗估,够用于「这段会不会超窗口」的判断
```

**为什么要关心 token**:
- **计费**:按输入 token + 输出 token 收钱。`max_tokens` 卡输出上限防超支。
- **上下文窗口**:模型一次能吃进的 token 有上限(如 200k)。历史 + 当前消息超了就「遗忘」最早的。

> ✅ 做 `estimate_tokens`:`return max(1, len(text) // 4)`。

---

## §28.6 重试:with_retry(对应:`with_retry`)🟡

网络调用必失败(超时、限流 429、服务端 5xx)。重试是标配——和 Ch24 `run_command_safely` 同一个 EAFP 套路:

```python
def with_retry(func, attempts=3, errors=Exception):
    last = None
    for _ in range(attempts):
        try:
            return func()
        except errors as e:
            last = e
    raise last
```

- `errors` 指定「哪些异常算可重试」(默认所有)。生产里你只想重试**瞬时错误**(超时/429/5xx),不重试 400(参数错,重试也没用)。这就是 `errors=` 参数的意义。
- 真实生产用指数退避(exponential backoff):第 2 次等 1s、第 3 次等 2s、第 4 次等 4s……避免猛打服务端。SDK/`tenacity` 库自带,这里手写理解原理。

> 🟡 **Java 对比**:= Spring Retry `@Retryable` / Resilience4j。Python 手写也就 6 行(EAFP 简洁)。

> ✅ 做 `with_retry`:`for _ in range(attempts): try return func() except errors as e: last=e` → `raise last`。

---

## §28.7 真实用法示例(讲透,带 API key)

```python
import os
from anthropic import Anthropic

client = Anthropic()                      # 读环境变量 ANTHROPIC_API_KEY

def ask(question: str) -> str:
    return with_retry(
        lambda: call_llm(client, "你是一个简洁的 Python 助手", question),
        attempts=3,
    )

if __name__ == "__main__":
    # export ANTHROPIC_API_KEY=sk-ant-...
    print(ask("用一行 Python 反转字符串"))
```

- API key 通过 `ANTHROPIC_API_KEY` 环境变量给(不写代码里)。
- `with_retry` 包住调用,瞬时错误自动重试。
- openai SDK 同理:`from openai import OpenAI; client.chat.completions.create(model="gpt-4o", messages=[...])`,响应解析 `resp.choices[0].message.content`。

---

## §28.8 Java 老手常踩的坑 ⚠️

1. **API key 写进代码 / 进 git**:泄漏即烧钱。走环境变量,`.env` 加 `.gitignore`。
2. **以为模型有记忆**:LLM 无状态,多轮必须每次发全部历史(否则它「失忆」)。
3. **不设 `max_tokens`**:模型可能输出超长,既慢又贵。设上限。
4. **不重试**:网络抖动直接报错给用户。生产必加重试(带退避)。
5. **重试所有错误**:400(参数错)重试也没用,只重试瞬时错误(429/5xx/超时)。
6. **裸 HTTP 硬刚**:能用 SDK 就别手拼 JSON(鉴权、重试、流式、新字段 SDK 都帮你处理了)。
7. **同步调用阻塞**:高并发场景用 `AsyncAnthropic`(Ch18),别在 async 函数里调同步 client(会阻塞事件循环)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `extract_text` | 解析响应 + duck typing | 🟡 |
| `call_llm` | 同步调用 + 复用 | 🟢 |
| `build_messages` | 多轮 messages + 不 mutate | 🟡 |
| `estimate_tokens` | token 估算 | 🟢 |
| `with_retry` | 重试(EAFP) | 🟡 |

```bash
uv run pytest 05_ai_framework/ch28/test_ch28_assignment.py -v
```

全绿 = 掌握 Ch28。

---

## ✅ 自测

- [ ] 知道为什么用 SDK 不用裸 HTTP,以及 API key 走环境变量
- [ ] 能从 `.content` 列表里抽出文本(duck typing 兼容多形态)
- [ ] 理解 LLM 无状态,多轮靠每次发全部历史
- [ ] 知道 token 是计费/上下文单位,会粗估
- [ ] 会写带 `errors` 过滤的重试,知道为什么只重试瞬时错误
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么模型回复的 `content` 是列表而不是字符串?」— 重读 §28.2
2. 「LLM 是无状态的」对客户端代码意味着什么?— 重读 §28.4
3. 「为什么重试要区分错误类型?哪些错误重试也没用?」— 重读 §28.6/§28.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch29 Prompt 工程 + 结构化输出

会「调」了,接下来学「**怎么问**」——Prompt 设计(few-shot/CoT)+ 用 Pydantic 强制 LLM 返回结构化 JSON,告别手写正则解析。
