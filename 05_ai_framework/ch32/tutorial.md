# Ch32 · Agent 开发:Tool Use / ReAct

> **预计**:1 天 ｜ **前置**:Ch28(SDK 调用)、Ch29(结构化输出)｜ **M5 继续**
> **目标**:学会写一个**会自己用工具的 Agent**——LLM 不再是「问一句答一句」,而是进入「思考→调工具→看结果→再思考」的循环,自主完成多步任务。和 Ch28 单轮调用是质的飞跃:Ch28 你写死流程,Ch32 让模型决定流程。

> 📐 **本教程的契约**:§32.2–§32.6 对应作业 5 个函数。**作业不调真实 LLM**(用 FakeDecider 离线测),真实用法(接 Anthropic/OpenAI 的 tool use API)在 §32.7 有完整示例。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `make_registry` | §32.2 | 工具注册表(函数当一等公民)+ duck typing |
| `execute_tool` | §32.3 | 查表调用 + EAFP 兜底 + 结果 stringify |
| `parse_action` | §32.4 | 文本协议解析(startswith + partition + json.loads) |
| `react_step` | §32.5 | 单步决策派发(Command 模式) |
| `run_agent_loop` | §32.6 | ReAct 主循环 + 终止条件 + 死循环防护 |

---

## ⏱️ 学习路径:费曼五步(约 70 分钟)

① 预览猜 → ② 写 assignment(5 个函数)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Ch28 你写死「先调 LLM 再打印」,流程是固定的。如果让 LLM **自己决定**要不要调工具、调哪个,代码结构会变成什么?(提示:循环)
2. Java 里你能写出「方法自己决定调哪个 bean」吗?Spring 的 `@Autowired` 是编译期注入,Agent 的「调工具」是什么时候决定的?
3. 「ReAct」拆开是 Reason + Act。一个循环里模型先想(Reason)再动手(Act),动手后看到结果再想——这和你平时解决问题的方式像不像?
4. 如果模型一直调同一个工具反复横跳,你的程序会死循环吗?怎么防?
5. 工具返回的是 `int`/`dict`,但模型只懂文本,中间怎么转换?

---

## §32.1 什么是 Agent(以及它和 Ch28 的区别)🟡

**Ch28 单轮调用**:你写 `answer = call_llm(...)`——问一次、答一次、结束。模型是个**纯函数**,不碰外部世界。

**Ch32 Agent**:模型有**工具**可用(查数据库、算数、调 API、读文件)。它自己看问题,决定:
- 「这个我得先查一下」→ 调工具 A → 看结果
- 「信息还不够」→ 调工具 B → 看结果
- 「够了」→ 给出最终答案

这是个**循环**,不是单次调用。模型在循环里扮演「决策者」,你的代码扮演「执行器」。

```
        ┌─────────────────────────────────┐
        ↓                                 │
   ┌─────────┐   决策(tool/answer)   ┌────┴──────┐
   │ Decider │ ────────────────────→ │ 执行/终止  │
   │ (LLM)   │ ←──────────────────── │           │
   └─────────┘    observations       └───────────┘
        ↑                                  │
        └──── query + 历史观察 ────────────┘
```

> 🟡 **Java 对比**:Java 里没有等价物。Java 的方法调用是**编译期/代码里写死**的(`a.foo()`),而 Agent 的工具调用是**运行时由 LLM 决定**的。最接近的类比是**规则引擎**(Drools)或**状态机**,但 Agent 的「转移函数」是一个神经网络,不是硬编码规则。这就是为什么 Agent 是新范式——决策权交给了模型。

**ReAct 论文**(2022):Reason + Act 交替。模型每轮输出:
1. **Thought**(思考):「我需要先算 2+3」
2. **Action**(动作):「调 add(2,3)」
3. **Observation**(观察):「5」(工具返回)
4. 回到 Thought……直到「我现在可以回答了」。

---

## §32.2 工具注册表:make_registry(对应:`make_registry`)🟢

Agent 的工具不是写死在代码里的 `if`,而是**登记在一个表里**,模型只能从这个表里选。这就是「注册表」模式。

```python
def add(a, b): return a + b
def mul(a, b): return a * b

reg = make_registry(add, mul)      # {"add": add, "mul": mul}
reg["add"](2, 3)                   # 5
```

```python
def make_registry(*funcs):
    return {f.__name__: f for f in funcs}
```

- `*funcs`:可变参数,收进一个元组(Ch02 学过)。`make_registry(add, mul)` → `funcs = (add, mul)`。
- `f.__name__`:Python 函数对象自带的属性,就是 `def` 时的名字。`add.__name__ == "add"`。
- 字典推导式一步生成 `{名字: 函数}`。

> 🟡 **Java 对比**:Java 你得写 `interface Tool { String getName(); String run(Map args); }`,然后 `Map<String, Tool> reg = new HashMap<>(); reg.put("add", new AddTool());`——一堆样板。Python 函数是一等公民,自带 `__name__`,一个推导式搞定。**这就是动态语言省下的代码量**。

> 🔴 **为什么用字典不用 if/else?** 如果你写 `if name == "add": ... elif name == "mul": ...`,每加一个工具就要改代码、改测试。字典是**开放的**:新工具 `make_registry(add, mul, divide)` 就行,主循环零改动。这是「表驱动」vs「分支驱动」,和 Ch16 策略模式一个道理。

> ✅ 做 `make_registry`:`return {f.__name__: f for f in funcs}`。

---

## §32.3 执行工具:execute_tool(对应:`execute_tool`)🟡

模型决定调 `add` 后,你的代码要去注册表里查到这个函数,按模型给的参数调用,返回结果。

```python
def execute_tool(name, args, registry):
    if name not in registry:
        return f"错误:未知工具 {name}"
    try:
        return str(registry[name](**args))
    except Exception as e:
        return f"错误:{e}"
```

三条路径,缺一不可:

1. **未知工具**:`registry` 里没有 → 返回 `错误:未知工具 xxx`。模型可能幻觉出不存在的工具名,要兜住。
2. **正常调用**:`registry[name](**args)`——`**args` 把 dict 展开成关键字参数(Ch02 学过)。`args={"a":2,"b":3}` → `func(a=2, b=3)`。
3. **调用抛异常**:`except` 兜住,返回 `错误:...`。比如模型给了错的参数类型(`add("x", 3)` 报 TypeError)。

> 🔴 **为什么结果要 `str()`?** 工具可能返回 `int`(5)、`float`(2.5)、`dict`、自定义对象……但 ReAct 循环要把结果**拼进 prompt 喂回给 LLM**,LLM 只懂文本。所以统一 `str()`。对比 Java:你也会把结果 `JSON.stringify` 成字符串塞回 prompt。

> 🟡 **为什么错误也返回字符串而不是抛异常?** 因为错误信息**本身是有价值的观察**——模型看到 `错误:未知工具 add` 后,下一轮可能改调 `sum`(如果存在)。如果你抛异常中断循环,模型就没机会自我纠正了。**把错误当数据,而不是当炸弹**——这是 Agent 设计的关键。

> ✅ 做 `execute_tool`:`if name not in registry` 返回错误串;`try: return str(registry[name](**args)) except Exception as e: return f"错误:{e}"`。

---

## §32.4 解析动作:parse_action(对应:`parse_action`)🟡

模型每轮输出一段**文本**,你得解析出「它要干嘛」。这就是 ReAct 的「文本协议」——模型按约定格式输出动作,你按约定格式解析。

两种动作:
```
ANSWER: 答案文本              ← 模型决定收尾
TOOL: 工具名 ARGS: {"a": 1}   ← 模型决定调工具
```

```python
def parse_action(text):
    import json
    text = text.strip()
    if text.startswith("ANSWER:"):
        return {"type": "answer", "text": text[len("ANSWER:"):].strip()}
    if text.startswith("TOOL:"):
        rest = text[len("TOOL:"):]               # ' add ARGS: {"a":1}'
        name_part, _, args_part = rest.partition("ARGS:")
        return {
            "type": "tool",
            "name": name_part.strip(),
            "args": json.loads(args_part.strip()),
        }
    return {"type": "error", "text": f"无法解析:{text}"}
```

- `text[len("ANSWER:"):]`:切掉前缀,剩下的就是答案。`strip()` 去掉首尾空格。
- `rest.partition("ARGS:")`:把 `"add ARGS: {...}"` 拆成 `("add ", "ARGS: ", "{...}")` 三段——分隔符前、分隔符、分隔符后。比 `split` 更可控(只拆一次,且 ARGS 的 JSON 里就算有 ARGS 字样也不影响,因为只拆第一个)。
- `json.loads`:把 ARGS 的 JSON 文本解析成 dict。模型的参数必须是合法 JSON。

> 🟡 **Java 对比**:= 手写 `String.startsWith` + `String.split` + `Jackson ObjectMapper.readValue`。Python 的字符串方法名更长但意思一样,`partition` 是 Python 独有的(Java 没有直接对应,得用 `indexOf` + `substring`)。

> 🔴 **为什么用文本协议而不是 JSON?** 教学版用文本协议是为了让你看清「解析」这件事。**真实生产不用这个**——见 §32.7,现代 LLM API(Anthropic/OpenAI 的 tool use)直接返回**结构化的 tool_call 对象**,你拿到的就是 `{"name":"add","input":{"a":2}}` 这种 dict,根本不用 parse。文本协议是 ReAct 论文时代的产物(模型只会续写文本),现在被「原生 function calling」取代了。但理解文本协议有助于你看懂原理,且很多开源框架(LangChain ReAct Agent)还在用。

> ✅ 做 `parse_action`:`strip()` → `startswith("ANSWER:")` 切前缀返回 answer → `startswith("TOOL:")` 用 `partition("ARGS:")` 拆 name/json,`json.loads` 解析 args → 否则返回 error。

---

## §32.5 单步执行:react_step(对应:`react_step`)🟢

把上一步解析出的决策 dict **执行掉**,返回这一步的输出。

```python
def react_step(decision, registry):
    t = decision.get("type")
    if t == "answer":
        return decision["text"]                  # 最终答案
    if t == "tool":
        return execute_tool(decision["name"],
                            decision.get("args", {}), registry)
    return decision.get("text", f"未知决策类型:{t}")
```

- `answer`:直接返回 text(主循环看到 type==answer 就终止)。
- `tool`:委托给 `execute_tool`(§32.3),拿观察结果。
- 其他(error/未知):返回错误/提示串,主循环会把它当观察喂回模型,让模型下一轮纠错。

> 🟢 **Java 对比**:这是 **Command 模式**。`decision` 是 Command 对象(`{"type":..., ...}`),`react_step` 是执行器(`execute()`)。Java 里你得定义 `interface Command { String execute(); }` 再写 `AnswerCommand`/`ToolCommand` 两个类——Python 一个 dict + if 分流就完事。

> ✅ 做 `react_step`:`decision.get("type")` 分流:answer 返回 text;tool 调 `execute_tool(name, args, registry)`;else 返回错误串。

---

## §32.6 ReAct 主循环:run_agent_loop(对应:`run_agent_loop`)🔴

把前面 4 个函数**组合**成完整循环。这是本章的核心,也是 Agent 的灵魂。

```python
def run_agent_loop(decider, registry, query, max_iters=5):
    observations = []
    for _ in range(max_iters):
        decision = decider(query, observations)         # ① 决策(Reason)
        if decision.get("type") == "answer":            # ② 终止判断
            return decision["text"]
        result = react_step(decision, registry)         # ③ 执行(Act)
        observations.append(result)                     # ④ 观察(Observation)
    return "未能在 max_iters 内得出答案"                  # ⑤ 兜底
```

逐行拆:

1. **`observations = []`**:收集每一轮工具的返回值。这是模型的「记忆」——和 Ch28 多轮对话的 history 同理。
2. **`decider(query, observations)`**:让「大脑」(LLM 或测试里的 FakeDecider)看问题 + 历史观察,决定下一步。这就是 **Reason**。
3. **`type == "answer"` 就返回**:终止条件。模型自己说「我答完了」就停。
4. **`react_step(...)`**:执行决策(调工具)。这就是 **Act**。
5. **`observations.append(result)`**:工具结果喂回 observations,下一轮模型能看到。这就是 **Observation**。
6. **`max_iters` 兜底**:如果模型一直不 answer(陷入死循环),硬上限保证程序会停。

> 🔴 **为什么必须有 max_iters?** LLM 会犯傻:调了工具、看了结果不满意、又调同一个工具、又不满意……无限循环。`max_iters` 是**安全阀**,对应 Java 里线程池的 `RejectedExecutionHandler`、HTTP client 的超时熔断。生产环境的 Agent **必须**有这个,否则一个失控的 Agent 能把你的 API 额度烧光。

> 🔴 **为什么 observations 每轮全量传给 decider?** LLM 无状态(Ch28 讲过)。它每次决策都要看到「问题 + 之前所有工具结果」才能判断「我现在信息够了吗」。代价:observations 越长,token 越多,越贵 + 越慢。复杂任务要配 **Memory / 上下文压缩**(Ch30),把老的观察摘要掉。

> 🟡 **decider 是可注入的**——这是测试的关键。真实环境 decider 是 `lambda q, obs: parse_action(call_llm(...))`(LLM 出文本 → parse_action 出决策);测试环境是 FakeDecider(按次序返回脚本)。**依赖注入**,Ch16 策略模式学过。这就是为什么作业能离线测:decider 不绑定真模型。

> ✅ 做 `run_agent_loop`:`observations=[]`;`for _ in range(max_iters)`:`decision = decider(query, observations)`;`answer` 返回 text;否则 `react_step(decision, registry)` + `observations.append`;越界返回兜底串。

---

## §32.7 真实用法:接 Anthropic / OpenAI 的 tool use

教学版用文本协议(parse_action)。**生产版不用**——现代 LLM API 原生支持 **function calling / tool use**:你把工具的 schema 喂给模型,模型直接返回结构化的 `tool_call`,不用解析文本。

```python
# anthropic 原生 tool use
import anthropic
client = anthropic.Anthropic()

tools = [{
    "name": "add",
    "description": "两个数相加",
    "input_schema": {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    },
}]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "2+3=?"}],
)
# response.content 里有 ToolUseBlock(name="add", input={"a":2,"b":3})
# 直接拿到结构化决策,不用 parse_action
```

把原生 tool use 接到本章的 `run_agent_loop` 上,decider 大概是:

```python
def llm_decider(query, observations):
    msg = [{"role": "user", "content": query}]
    for obs in observations:
        msg.append({"role": "user", "content": f"观察:{obs}"})
    resp = client.messages.create(model=..., tools=tools, messages=msg)
    for block in resp.content:
        if block.type == "tool_use":                    # 结构化,不解析文本
            return {"type": "tool", "name": block.name, "args": block.input}
    return {"type": "answer", "text": resp.content[0].text}
```

**对比教学版**:
- 教学版:LLM 输出 `"TOOL: add ARGS: {...}"` 文本 → `parse_action` 解析(可能解析失败)。
- 生产版:LLM 输出 `ToolUseBlock` 结构 → 直接是 dict(不会解析失败)。

> 🔴 **为什么教学版还学文本协议?** ① 看懂原理——ReAct 本质就是文本协议;② 很多场景模型不支持原生 tool call(开源小模型、某些 API),只能用文本协议兜底;③ LangChain 的 ReAct Agent 内部就是这个套路。学文本协议不亏。

---

## §32.8 Java 老手常踩的坑 ⚠️

1. **以为 Agent = 多调几次 LLM**:不是。Agent 的关键是**模型决定流程**(调什么工具、调几次、何时停),不是你写死的循环。决策权在模型,不在代码。
2. **不设 max_iters**:LLM 犯傻会无限循环,烧钱烧时间。**必加硬上限**。生产还要加每次调用的超时 + 总 token 上限。
3. **错误抛异常中断循环**:工具失败应该返回错误串、让模型看到、下一轮纠错。直接 raise 会剥夺模型自我修正的机会。**错误当数据,不当炸弹**。
4. **结果不 stringify**:模型只懂文本,工具返回 int/dict 直接喂会出问题。统一 `str()`。
5. **不传 observations**:模型无状态,忘了把历史观察喂回去,模型每轮都「失忆」,反复调同一工具。
6. **硬编码工具名**:`if name == "add"` 分支写死——每加工具就改代码。用注册表(字典),新工具加一行就行。
7. **混淆「answer」和「tool」的终止语义**:`react_step` 不区分终止,但 `run_agent_loop` 要在 `type=="answer"` 时 return。终止逻辑在主循环,不在单步。
8. **生产用文本协议**:能用原生 tool use(§32.7)就别自己 parse 文本。文本解析是脆弱的(模型格式飘了就崩),结构化 API 才是正道。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `make_registry` | 注册表 + 函数一等公民 + `__name__` | 🟢 |
| `execute_tool` | 查表调用 + EAFP + `**args` + stringify | 🟡 |
| `parse_action` | 文本协议解析 + `partition` + `json.loads` | 🟡 |
| `react_step` | 决策派发(Command 模式) | 🟢 |
| `run_agent_loop` | ReAct 主循环 + 终止 + 死循环防护 | 🔴 |

```bash
uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v
```

全绿 = 掌握 Ch32。

**实现提示**:
- `make_registry`:字典推导式,`f.__name__`。
- `execute_tool`:先 `in` 检查,再 `try` 调用,`except Exception` 兜底。注意 `**args`。
- `parse_action`:`strip()` + `startswith` + `partition("ARGS:")` + `json.loads`。记得 `import json`。
- `react_step`:`decision.get("type")` 分流,answer/tool/else 三路。tool 委托给 `execute_tool`。
- `run_agent_loop`:`observations=[]` → for max_iters → decider → answer 判断 → react_step + append → 兜底。

---

## ✅ 自测

- [ ] 能说清 Agent 和 Ch28 单轮调用的本质区别(决策权在谁手里)
- [ ] 知道 ReAct 是 Reason+Act+Observation 的循环,能画出循环图
- [ ] 会用 `*funcs` + `f.__name__` + 字典推导式做注册表
- [ ] 理解 `execute_tool` 为什么把错误也返回成字符串(错误当数据)
- [ ] 会用 `partition` + `json.loads` 解析 `TOOL: name ARGS: {...}` 协议
- [ ] 理解 `max_iters` 为什么必须有(LLM 会死循环)
- [ ] 知道生产环境用原生 tool use,不用文本协议
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么 Agent 比单轮调用强?决策权的转移体现在哪?」— 重读 §32.1
2. 「如果模型陷入死循环反复调同一工具,你的代码会怎样?怎么防?」— 重读 §32.6 的 max_iters
3. 「execute_tool 为什么把异常也返回成字符串,而不是 raise?」— 重读 §32.3
4. 「原生 tool use 和文本协议(ReAct)各有什么优劣?生产选哪个?」— 重读 §32.4/§32.7

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch33 MCP(模型上下文协议)

会写 Agent 了。但每个框架(Anthropic、OpenAI、LangChain)的工具注册表都不一样,工具没法跨框架复用。下一章学 **MCP(Model Context Protocol)**——一个让「工具」变成可复用、可发现的标准协议,就像「USB 之于硬件」之于「MCP 之于 LLM 工具」。
