# Ch30 · LangChain 基础:LCEL

> **预计**:1 天 ｜ **前置**:Ch28、Ch29、Ch18(| 管道概念)｜ **M5 第 3 章**
> **目标**:用 LangChain 的 **LCEL**(`prompt | model | parser`)把「拼 prompt → 调模型 → 解析」这条链**声明式**拼起来——像 Unix 管道。告别每次手写三步。

> 📐 **本教程的契约**:§30.2–§30.6 对应作业 5 个函数。**不调真实 LLM**:model 步用 `RunnableLambda` 包个普通函数当 FakeModel。

---

## 🗺️ 本章地图

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `build_prompt` | §30.2 | PromptTemplate.from_template |
| `as_runnable` | §30.3 | RunnableLambda:任意函数 → 可用 `\|` 串的步骤 |
| `build_chain` | §30.4 | LCEL `\|` 管道组装(含 PromptValue→str 适配) |
| `run_chain` | §30.5 | chain.invoke 执行 |
| `append_turn` | §30.6 | 对话记忆原理(messages 列表) |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Ch28/29 每次「拼 prompt → 调用 → 解析」都重复写三步,能不能像 Unix 管道 `a | b | c` 串起来?
2. LangChain 的 LCEL 里,`\|` 号为什么能串联组件?它背后是什么(Python 运算符重载,Ch05)?
3. PromptTemplate 的 `invoke` 返回的是字符串吗?(剧透:不是——这会坑到你)
4. LLM 无状态(Ch28),LangChain 怎么做「带记忆的对话」?
5. 「Runnable」是什么抽象?为什么普通函数要先包成 RunnableLambda 才能进管道?

---

## §30.1 LCEL 是什么 🟡

**LCEL**(LangChain Expression Language)是 LangChain 的声明式链语法。核心思想:**每个组件都是一个 `Runnable`,用 `|` 串起来**,数据从左流到右:

```python
chain = prompt | model | parser
result = chain.invoke({"q": "你好"})
# 内部:prompt 渲染 → model 调用 → parser 解析 → 最终结果
```

> 🟡 **对比 Java**:像 Java 8 Stream `list.stream().map().filter().collect()`,或 Reactor `flux.map().filter()`。LCEL 是「组件级」的管道——每个 `\|` 是一个处理阶段。背后靠 Runnable 重载 `__or__` / `__ror__`(Ch05 运算符重载)实现。

**为什么用 LCEL**:
- 声明式:一眼看出数据流。
- 统一接口:所有组件 `invoke`/`stream`/`batch`,可替换(`RunnableLambda`↔真 ChatModel)。
- 自带能力:流式、重试、并发、可观测(回调)。

> 🔴 **本作业不调真实 LLM**:model 步用 `RunnableLambda` 包个 echo 函数。真实场景把那一步换成 `ChatAnthropic`/`ChatOpenAI`。

---

## §30.2 PromptTemplate:build_prompt(对应)🟢

LangChain 的 prompt 是个**对象**,不是裸字符串:

```python
def build_prompt(template):
    return PromptTemplate.from_template(template)

p = build_prompt("回答:{q}")
p.invoke({"q": "你好"})          # ⚠️ 返回 StringPromptValue,不是 str!
p.invoke({"q": "你好"}).to_string()   # "回答:你好"
p.format(q="你好")               # "回答:你好"(.format 直接返回 str)
```

- `from_template("...{q}...")`:解析 `{q}` 占位符。
- ⚠️ **`invoke` 返回 `StringPromptValue` 对象**(不是字符串)!这是 LCEL 的统一接口(组件间传对象)。要纯文本用 `.to_string()` 或 `.format()`。

> ✅ 做 `build_prompt`:`return PromptTemplate.from_template(template)`。

---

## §30.3 RunnableLambda:as_runnable(对应)🟡

普通函数不能直接 `|` 进管道——必须包成 **Runnable**。`RunnableLambda` 把任意 `f(x)->y` 包成 Runnable 步骤:

```python
def as_runnable(fn):
    return RunnableLambda(fn)

up = as_runnable(lambda s: s.upper())
up.invoke("abc")        # "ABC"
chain = up | as_runnable(lambda s: s + "!")   # Runnable 之间能用 | 串
chain.invoke("hi")      # "HI!"
```

- 本作业用它包 **FakeModel**(返回固定/echo 文本的函数)。真实场景换成 `ChatAnthropic(model=...)`。
- 这就是「**统一接口**」的威力:管道里任何一步都能换成真模型 / 假模型,其余不变。

> ✅ 做 `as_runnable`:`return RunnableLambda(fn)`。

---

## §30.4 管道组装:build_chain(对应)🔴

```python
def build_chain(prompt, model_runnable, parser):
    # 真实 ChatModel 能直接吃 PromptValue;FakeModel 需要纯字符串,加个 to_text 适配
    to_text = RunnableLambda(lambda v: v.to_string() if hasattr(v, "to_string") else str(v))
    return prompt | to_text | model_runnable | parser
```

- 核心:`a | b | c | d` 把 Runnable 串成链,数据依次流过。
- ⚠️ **PromptValue → str 适配**:prompt 步输出 `StringPromptValue`,真实 ChatModel 能直接吃它;但我们的 FakeModel(lambda)只会 `f"{s}"` 拼接,遇到 PromptValue 渲染成乱码。所以加 `to_text` 把它转成字符串。
  - 这是「真实 vs 模拟」的差异,真实链 `prompt | ChatModel | StrOutputParser` 不需要 `to_text`(ChatModel 原生处理 PromptValue)。教程这么写是为了让 FakeModel 能跑通。

> 🔴 **`|` 的本质**:Runnable 类重载了 `__or__`,`a | b` 返回一个新的 `RunnableSequence`。这是 Ch05 运算符重载的实战——让 API 像数学公式一样直观。

> ✅ 做 `build_chain`:`prompt | to_text | model_runnable | parser`。

---

## §30.5 执行:run_chain(对应)🟢

```python
def run_chain(chain, variables):
    return chain.invoke(variables)
```

`chain.invoke({"q":"你好"})`:按顺序 prompt 渲染 → to_text → model → parser → 返回最终结果。一个 `invoke` 跑完整条链。

> ✅ 做 `run_chain`:`return chain.invoke(variables)`。

---

## §30.6 对话记忆:append_turn(对应)🟡

LLM 无状态(Ch28),「记忆」靠**客户端维护 messages 列表**,每轮追加、下次请求带上:

```python
def append_turn(history, user, assistant):
    return [*history, {"role":"user","content":user}, {"role":"assistant","content":assistant}]
```

- LangChain 有 `RunnableWithMessageHistory` 自动管这个(自动把历史塞进 prompt)。这里手写理解原理:记忆 = 一个不断 append 的对话列表。
- **历史越长越贵**(token),所以有「窗口记忆」(只留最近 N 轮)、摘要记忆(把旧对话压缩成摘要)等策略。

> ✅ 做 `append_turn`:`return [*history, {user}, {assistant}]`(不 mutate 入参)。

---

## §30.7 真实用法示例(讲透)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = PromptTemplate.from_template("用一句话解释:{concept}")
model = ChatAnthropic(model="claude-3-5-sonnet-20241022")   # 真模型,原生吃 PromptValue
chain = prompt | model | StrOutputParser()                  # 真·三步链,无需 to_text

print(chain.invoke({"concept": "闭包"}))
# chain.stream({...}) 还能流式输出(打字机效果)
```

- 真模型换上去,链结构不变——**这就是统一接口的价值**。
- `chain.stream()`、`chain.batch([...])`、重试、回调,LCEL 自带。

---

## §30.8 直接用 SDK 还是 LangChain?🟡

工程判断(别无脑上 LangChain):
- **简单调用**(一问一答):直接 SDK(Ch28)更轻、可控、少一层抽象。
- **复杂流水线**(RAG、Agent、多步、流式、记忆):LangChain 省事,但抽象层多、调试难、版本变化快。
- 趋势:很多人回归「SDK + 手写」,LangChain 适合快速搭原型。

> 🟡 别「拿着锤子看啥都是钉子」。本章教你懂 LCEL,不是让你什么都用 LangChain。

---

## §30.9 Java 老手常踩的坑 ⚠️

1. **以为 `prompt.invoke` 返回字符串**:它返回 `StringPromptValue`。要文本用 `.to_string()`/`.format()`。
2. **FakeModel 直接吃 PromptValue**:lambda `f"{promptvalue}"` 渲染成乱码。真实 ChatModel 才原生处理 PromptValue。
3. **滥用 LangChain**:简单调用也套 LangChain,徒增抽象和调试难度。SDK 能搞定就 SDK。
4. **忘 `|` 背后是运算符重载**:理解了才不被魔法迷惑(Runnable 重载 `__or__`)。
5. **记忆无限增长**:历史全发→token 爆炸。生产要窗口/摘要策略。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `build_prompt` | PromptTemplate | 🟢 |
| `as_runnable` | RunnableLambda | 🟡 |
| `build_chain` | LCEL `\|` + PromptValue 适配 | 🔴 |
| `run_chain` | chain.invoke | 🟢 |
| `append_turn` | 记忆原理 | 🟡 |

```bash
uv run pytest 05_ai_framework/ch30/test_ch30_assignment.py -v
```

全绿 = 掌握 Ch30。

---

## ✅ 自测

- [ ] 懂 LCEL `\|` 是声明式管道,背后靠运算符重载
- [ ] 知道 `PromptTemplate.invoke` 返回 PromptValue 不是 str
- [ ] 会用 RunnableLambda 把普通函数包成可串的步骤
- [ ] 能组装 `prompt | model | parser` 链并 invoke
- [ ] 理解记忆 = 维护 messages 列表
- [ ] 能判断何时用 SDK 何时用 LangChain
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「LCEL 的 `\|` 为什么能串联组件?」— 重读 §30.1/§30.4
2. 「为什么 build_chain 里要加 to_text?真实链需要吗?」— 重读 §30.4
3. 「什么时候该用 LangChain,什么时候直接 SDK?」— 重读 §30.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch31 RAG 实战

会调(Ch28)、会问(Ch29)、会串(Ch30)。接下来 RAG——让 LLM 基于【你的文档】回答:文档切片 → 向量化 → 检索 top-k → 拼上下文 → 回答。这是企业落地 LLM 的头号场景。
