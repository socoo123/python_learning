# Ch32 · Agent 开发：Tool Use / ReAct

> **预计**：1 天 ｜ **前置**：Ch28（SDK 调用）、Ch29（结构化输出）｜ **M5 继续**
> **目标**：学会写一个**会自己用工具的 Agent**——LLM 不再是「问一句答一句」，而是进入「思考→调工具→看结果→再思考」的循环，自主完成多步任务。和 Ch28 单轮调用是质的飞跃：Ch28 你写死流程，Ch32 让模型决定流程。

> 🎯 **主线场景**：电商「智能客服 Agent」。用户问「机械键盘还有货吗」「我 u1001 的订单到哪了」，Agent 自主决定：先 `lookup_product` 查商品 → 再 `check_stock` 查库存 → 最后组织答复。全程没有一个 if/else 是你写的——调什么、调几次、何时停，都是模型（测试里是 FakeDecider）说了算。

> 📐 **本教程的契约**：§32.2–§32.6 对应作业 5 个函数。**作业不调真实 LLM**（用 FakeDecider 离线测），真实用法（接 Anthropic 原生 tool use）在 §32.8 有完整示例。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**：

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `make_registry` | §32.2 | 工具注册表（函数当一等公民 + `__name__`）+ duck typing |
| `execute_tool` | §32.3 | 查表调用 + `**args` + EAFP 兜底 + 结果 stringify |
| `parse_action` | §32.4 | 文本协议解析（startswith + partition + json.loads） |
| `react_step` | §32.5 | 单步决策派发（Command 模式 + dict.get 容错） |
| `run_agent_loop` | §32.6 | ReAct 主循环 + 终止条件 + max_iters 死循环防护 |

---

## ⏱️ 学习路径：费曼五步（约 70 分钟）

① 预览猜 → ② 写 assignment（5 个函数）→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Ch28 你写死「先调 LLM 再打印」，流程是固定的。如果让 LLM **自己决定**要不要调工具、调哪个，代码结构会变成什么？（提示：循环）
2. Java 里 Spring 的 `@Autowired` 是**启动期**注入；Agent 的「调哪个工具」是**什么时候**决定的？
3. 用户问「机械键盘还有货吗」，Agent 需要先查商品拿到 SKU、再按 SKU 查库存——第 2 步的参数依赖第 1 步的结果。这个「结果」怎么传给模型的下一轮思考？
4. 如果模型一直调同一个工具反复横跳，你的程序会死循环吗？怎么防？
5. 工具返回的是 `int`/`dict`，但模型只懂文本，中间怎么转换？

---

## §32.1 什么是 Agent（以及它和 Ch28 的区别）🟡

**Ch28 单轮调用**：你写 `answer = call_llm(...)`——问一次、答一次、结束。模型是个**纯函数**，不碰外部世界，流程 100% 由你的代码写死。

**Ch32 Agent**：模型有**工具**可用（查商品、查订单、查库存）。它自己看问题，决定：

- 「这个我得先查一下商品」→ 调 `lookup_product` → 看结果
- 「拿到 SKU 了，再查下库存」→ 调 `check_stock` → 看结果
- 「信息够了」→ 给出最终答案

这是个**循环**，不是单次调用。模型在循环里扮演「决策者」，你的代码扮演「执行器」：

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

> 🟡 **Java 对比**：Java 的方法调用是**编译期/代码里写死**的（`service.query()`），Agent 的工具调用是**运行时由 LLM 决定**的。最接近的类比是**规则引擎**（Drools）或**状态机**，但 Agent 的「转移函数」是一个神经网络，不是硬编码规则。这就是为什么 Agent 是新范式——**决策权从代码转移到了模型**。

**ReAct 论文**（2022）：Reason + Act 交替。模型每轮输出：

1. **Thought**（思考）：「我需要先查机械键盘的 SKU」
2. **Action**（动作）：「调 `lookup_product("机械键盘")`」
3. **Observation**（观察）：「机械键盘（SKU KB-001）：¥349，库存 12 件」（工具返回）
4. 回到 Thought……直到「我现在可以回答了」。

**真实客服对话追踪**（本章作业的主线场景，先建立直觉）：

| 轮次 | 模型输出（决策） | 你的代码做什么 | 观察（喂回下一轮） |
|------|----------------|---------------|-------------------|
| 1 | `TOOL: lookup_product ARGS: {"name": "机械键盘"}` | 查商品 | `机械键盘（SKU KB-001）：¥349，库存 12 件` |
| 2 | `TOOL: check_stock ARGS: {"sku": "KB-001"}` | 查库存 | `KB-001 当前库存 12 件` |
| 3 | `ANSWER: 机械键盘有货，库存 12 件` | 终止，返回答案 | — |

注意第 2 轮的参数 `KB-001` 来自第 1 轮的观察——**这就是 observations 必须每轮喂回模型的原因**。

---

## §32.2 工具注册表：make_registry（对应：`make_registry`）🟢

Agent 的工具不是写死在代码里的 `if`，而是**登记在一个表里**，模型只能从这个表里选。这就是「注册表」模式。

**Java 对照最小例**——你熟悉的写法：

```java
// Java：接口 + 实现类 + 手动注册，一个工具三个文件
interface Tool { String getName(); String run(Map<String,Object> args); }
class LookupProduct implements Tool { /* ... */ }

Map<String, Tool> registry = new HashMap<>();
registry.put("lookup_product", new LookupProduct());
registry.put("check_stock", new CheckStock());
```

**Python 业务例**——客服 Agent 的工具箱：

```python
def make_registry(*funcs):
    return {f.__name__: f for f in funcs}

# 作业里已备好的三个业务工具（assignment.py 里实现好了，直接登记）
reg = make_registry(lookup_product, list_orders, check_stock)
# -> {"lookup_product": <function ...>, "list_orders": <function ...>, "check_stock": <function ...>}

reg["lookup_product"]("机械键盘")   # "机械键盘（SKU KB-001）：¥349，库存 12 件"
list(reg.keys())                    # ["lookup_product", "list_orders", "check_stock"]——给模型的工具清单
```

三个关键点：

- `*funcs`：可变参数，收进一个元组（Ch02 学过）。`make_registry(a, b, c)` → `funcs = (a, b, c)`；`make_registry()` → 空元组 → 空 dict。
- `f.__name__`：Python 函数对象自带的属性，就是 `def` 时的名字。`lookup_product.__name__ == "lookup_product"`。（lambda 的 `__name__` 是 `"<lambda>"`，所以工具要用 `def` 具名定义。）
- 字典推导式一步生成 `{名字: 函数}`。

> 🔴 **为什么用字典不用 if/else？** ❌ 错误写法：

```python
# ❌ 分支驱动：每加一个工具，这里和测试都要改
def execute(name, args):
    if name == "lookup_product": return lookup_product(**args)
    elif name == "list_orders": return list_orders(**args)
    elif name == "check_stock": return check_stock(**args)
```

✅ 正确写法：表驱动 `registry[name](**args)`。新工具只需 `make_registry(..., refund_order)` 登记一下，主循环**零改动**。这和你在 Java 里用 `Map<String, Strategy>` 替代 switch 是同一个思想（Ch16 策略模式）。

> 🟡 **duck typing**：Python 不要求工具实现某个接口——「只要是 callable、有 `__name__`，就能当工具」。Java 的 `interface Tool` 那层样板全省了。**这就是动态语言省下的代码量**。

> ✅ 做 `make_registry`：`return {f.__name__: f for f in funcs}`。

---

## §32.3 执行工具：execute_tool（对应：`execute_tool`）🟡

模型决定调 `lookup_product` 后，你的代码要去注册表查到这个函数，按模型给的参数调用，返回结果。

**Java 对照最小例**——最接近的是反射调用：

```java
// Java：Method.invoke，受检异常逼你 try/catch 一大片
Method m = registry.get(name);           // 可能 null
Object result = m.invoke(null, args);    // 可能 IllegalArgumentException
```

**Python 业务例**：

```python
def execute_tool(name, args, registry):
    if name not in registry:
        return f"错误:未知工具 {name}"
    try:
        return str(registry[name](**args))
    except Exception as e:
        return f"错误:{e}"

execute_tool("lookup_product", {"name": "机械键盘"}, reg)
# -> "机械键盘（SKU KB-001）：¥349，库存 12 件"
execute_tool("list_orders", {"user": "u1001"}, reg)
# -> "A001 机械键盘 已发货 ¥349; A002 无线鼠标 已完成 ¥129"
execute_tool("delete_db", {}, reg)
# -> "错误:未知工具 delete_db"      ← 模型幻觉出不存在的工具，兜住
execute_tool("list_orders", {}, reg)
# -> "错误:list_orders() missing 1 required positional argument: 'user'"  ← 缺参，兜住
```

三条路径，缺一不可：

1. **未知工具**：`registry` 里没有 → 返回错误串。模型会幻觉（hallucinate）出不存在的工具名，必须兜住。
2. **正常调用**：`registry[name](**args)`——`**args` 把 dict 展开成关键字参数（Ch02 学过）：`args={"name": "机械键盘"}` → `lookup_product(name="机械键盘")`。
3. **调用抛异常**：`except` 兜住，返回错误串。比如缺必填参数（TypeError）、业务逻辑自己 raise。

> 🔴 **为什么结果要 `str()`？** 工具可能返回 `int`（库存数）、`float`、`dict`……但 ReAct 循环要把结果**拼进 prompt 喂回 LLM**，LLM 只懂文本，统一 `str()`。对比 Java：你也会 `objectMapper.writeValueAsString(result)` 再塞回 prompt。

> 🔴 **为什么错误也返回字符串而不是抛异常？** ❌ 错误写法：

```python
# ❌ 直接 raise：循环炸了，模型再也没机会纠错
return registry[name](**args)   # TypeError 一路抛到用户面前
```

✅ 正确写法：错误信息**本身是有价值的观察**——模型看到 `错误:未知工具 delete_db` 后，下一轮可能改调注册表里真实存在的 `lookup_product`（测试 `test_tool_error_continues_loop` 演示了这个纠错过程）。**把错误当数据，而不是当炸弹**——这是 Agent 设计的关键，也是和 Java「异常快速失败」直觉最不一样的地方。

> ✅ 做 `execute_tool`：`if name not in registry` 返回错误串；`try: return str(registry[name](**args)) except Exception as e: return f"错误:{e}"`。

---

## §32.4 解析动作：parse_action（对应：`parse_action`）🟡

模型每轮输出一段**文本**，你得解析出「它要干嘛」。这就是 ReAct 的「文本协议」——模型按约定格式输出动作，你按约定格式解析。

两种动作：

```
ANSWER: 机械键盘有货，库存 12 件          ← 模型决定收尾
TOOL: lookup_product ARGS: {"name": "机械键盘"}   ← 模型决定调工具
```

**Java 对照最小例**：

```java
// Java：startsWith + indexOf/substring + Jackson
if (text.startsWith("TOOL:")) {
    int idx = text.indexOf("ARGS:");
    String name = text.substring(5, idx).trim();
    Map<String,Object> args = new ObjectMapper().readValue(text.substring(idx + 5), Map.class);
}
```

**Python 业务例**：

```python
import json

def parse_action(text):
    text = text.strip()
    if text.startswith("ANSWER:"):
        return {"type": "answer", "text": text[len("ANSWER:"):].strip()}
    if text.startswith("TOOL:"):
        rest = text[len("TOOL:"):]               # ' lookup_product ARGS: {"name": ...}'
        name_part, _, args_part = rest.partition("ARGS:")
        return {"type": "tool",
                "name": name_part.strip(),
                "args": json.loads(args_part.strip())}
    return {"type": "error", "text": f"无法解析:{text}"}

parse_action("ANSWER: 机械键盘有货")
# -> {"type": "answer", "text": "机械键盘有货"}
parse_action('TOOL: lookup_product ARGS: {"name": "机械键盘"}')
# -> {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}}
parse_action("今天天气不错")          # 模型没按格式输出
# -> {"type": "error", "text": "无法解析:今天天气不错"}
```

逐个拆：

- `text[len("ANSWER:"):]`：切掉前缀，剩下的就是答案。`strip()` 去首尾空格（模型输出常带空白）。
- `rest.partition("ARGS:")`：把 `' lookup_product ARGS: {...}'` 拆成 `(" lookup_product ", "ARGS:", ' {...}')` 三段——分隔符前、分隔符、分隔符后。解包时 `_` 丢弃中间的分隔符。
- `json.loads`：把 ARGS 的 JSON 文本解析成 dict。模型的参数必须是合法 JSON。

> 🟡 **为什么用 `partition` 不用 `split`？** ❌ 错误写法：`rest.split("ARGS:")`——如果 args 的 JSON 里恰好含 `ARGS:` 字样（比如 `{"query": "ARGS: 用法"}`），split 会拆出 3+ 段，解析错位。✅ `partition` 只拆**第一个**分隔符，永远返回三段，稳定可控。Java 里没有直接对应（得 `indexOf` + `substring`），这是 Python 字符串的小甜点。

> 🔴 **为什么教学版用文本协议而不是 JSON function calling？** 现代 LLM API（Anthropic/OpenAI 的 tool use）直接返回**结构化的 tool_call 对象**，你拿到的就是 `{"name": "lookup_product", "input": {...}}`，根本不用 parse（见 §32.8）。但学文本协议不亏：① 看懂 ReAct 原理——它本质就是文本协议；② 开源小模型/某些 API 不支持原生 tool call，只能用文本协议兜底；③ LangChain 的 ReAct Agent 内部就是这个套路。

> ✅ 做 `parse_action`：`strip()` → `startswith("ANSWER:")` 切前缀返回 answer → `startswith("TOOL:")` 用 `partition("ARGS:")` 拆 name/json，`json.loads` 解析 args → 否则返回 error。模块顶部已 `import json`。

---

## §32.5 单步执行：react_step（对应：`react_step`）🟢

把上一步解析出的决策 dict **执行掉**，返回这一步的输出。

**Java 对照最小例**——这是 **Command 模式**：

```java
// Java：Command 接口 + 两个实现类 + invoker
interface Command { String execute(); }
class AnswerCommand implements Command { /* ... */ }
class ToolCommand implements Command { /* ... */ }
String out = command.execute();
```

**Python 业务例**——一个 dict + if 分流就完事：

```python
def react_step(decision, registry):
    t = decision.get("type")
    if t == "answer":
        return decision["text"]                  # 最终答案
    if t == "tool":
        return execute_tool(decision["name"],
                            decision.get("args", {}), registry)
    return decision.get("text", f"未知决策类型:{t}")

react_step({"type": "answer", "text": "有货，放心买"}, reg)       # -> "有货，放心买"
react_step({"type": "tool", "name": "check_stock",
            "args": {"sku": "KB-001"}}, reg)                    # -> "KB-001 当前库存 12 件"
react_step({"type": "error", "text": "无法解析:嘿嘿"}, reg)      # -> "无法解析:嘿嘿"（透传）
react_step({"type": "????"}, reg)                               # -> "未知决策类型:????"
```

三路分流：

- `answer`：直接返回 text（主循环看到 type==answer 才终止，react_step 自己不判断终止）。
- `tool`：委托给 `execute_tool`（§32.3），拿观察结果。注意 `decision.get("args", {})`——决策里可能没有 `args` 键，用 `.get` 给默认空 dict，避免 KeyError（Ch02 的 dict.get 容错）。
- 其他（error/未知）：返回错误/提示串，主循环会把它当观察喂回模型，让模型下一轮纠错。

> 🟡 **为什么 error 决策要「透传」而不是再包一层？** `parse_action` 解析失败产出的 `{"type": "error", "text": "无法解析:..."}` 已经是给模型看的提示了，原样返回即可——模型下一轮看到「无法解析」就知道该按格式重新输出。错误当数据，一路流回模型。

> ✅ 做 `react_step`：`decision.get("type")` 分流：answer 返回 text；tool 调 `execute_tool(name, decision.get("args", {}), registry)`；else 返回错误串。

---

## §32.6 ReAct 主循环：run_agent_loop（对应：`run_agent_loop`）🔴

把前面 4 个函数**组合**成完整循环。这是本章的核心，也是 Agent 的灵魂。

```python
def run_agent_loop(decider, registry, query, max_iters=5):
    observations = []
    for _ in range(max_iters):
        decision = decider(query, observations)         # ① 决策（Reason）
        if decision.get("type") == "answer":            # ② 终止判断
            return decision["text"]
        result = react_step(decision, registry)         # ③ 执行（Act）
        observations.append(result)                     # ④ 观察（Observation）
    return "未能在 max_iters 内得出答案"                  # ⑤ 兜底
```

**业务链路逐轮追踪**（用户问「机械键盘还有货吗」，对应测试 `test_stock_check_two_step`）：

| 轮次 | decider 收到的 observations | decider 输出 | 循环动作 |
|------|---------------------------|-------------|---------|
| 1 | `[]` | `tool: lookup_product` | 执行 → append `"机械键盘（SKU KB-001）：¥349，库存 12 件"` |
| 2 | `["机械键盘（SKU KB-001）..."]` | `tool: check_stock` | 执行 → append `"KB-001 当前库存 12 件"` |
| 3 | `["机械键盘...", "KB-001 当前库存 12 件"]` | `answer: 有货，库存 12 件` | **return**，循环结束 |

逐行拆：

1. **`observations = []`**：收集每一轮工具的返回值，是模型的「记忆」——和 Ch28 多轮对话的 history 同理。
2. **`decider(query, observations)`**：让「大脑」看问题 + 历史观察，决定下一步。这就是 **Reason**。
3. **`type == "answer"` 就 return**：终止条件。模型自己说「我答完了」就停。注意：终止逻辑在**主循环**，不在 `react_step`。
4. **`react_step(...)`**：执行决策（调工具）。这就是 **Act**。
5. **`observations.append(result)`**：工具结果喂回 observations，下一轮模型能看到。这就是 **Observation**。
6. **`max_iters` 兜底**：模型一直不 answer 就硬停。

> 🔴 **为什么必须有 max_iters？** ❌ 错误写法：

```python
# ❌ while True：模型犯傻时无限循环，API 额度烧光
while True:
    decision = decider(query, observations)
    ...
```

✅ 正确写法：`for _ in range(max_iters)` + 兜底返回。LLM 会犯傻：调了工具、看了结果不满意、又调同一个工具、又不满意……无限循环。`max_iters` 是**安全阀**，对应 Java 里线程池的 `RejectedExecutionHandler`、HTTP client 的超时熔断。生产环境还要加每次调用的超时 + 总 token 上限。

> 🔴 **为什么 observations 每轮全量传给 decider？** LLM 无状态（Ch28 讲过）。第 2 轮的 `check_stock(sku="KB-001")` 参数来自第 1 轮的观察——模型看不到历史观察就拿不到 SKU。代价：observations 越长，token 越多，越贵越慢。复杂任务要配 **Memory / 上下文压缩**（Ch30），把老的观察摘要掉。

> 🟡 **decider 是可注入的**——这是测试的关键，也是你能离线跑作业的原因。真实环境 decider 是 `lambda q, obs: parse_action(call_llm(...))`（LLM 出文本 → parse_action 出决策）；测试环境是 FakeDecider（按脚本返回决策）。**依赖注入**，Ch16 学过——和 Java 里「构造器注入接口、测试传 Mock」一模一样，只是 Python 里函数本身就是可注入的依赖，连接口都不用定义。

> ✅ 做 `run_agent_loop`：`observations=[]`；`for _ in range(max_iters)`：`decision = decider(query, observations)`；`answer` 返回 text；否则 `react_step(decision, registry)` + `observations.append`；越界返回兜底串。

---

## §32.7 工具 schema：让模型知道有什么工具（了解，作业不考）🟡

到目前为止，注册表是**你的代码**用的。但模型怎么知道「有哪些工具、每个工具吃什么参数」？答案：**把工具的 schema（名字 + 描述 + 参数 JSON Schema）放进 system prompt 或 API 的 tools 字段**。

最小例——手写 JSON Schema：

```python
tools = [{
    "name": "lookup_product",
    "description": "按商品名查商品，返回价格和库存",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "商品名"}},
        "required": ["name"],
    },
}]
```

业务例——用 **Pydantic**（Ch14 学过）生成 schema，避免手写 JSON：

```python
from pydantic import BaseModel, Field

class LookupProductInput(BaseModel):
    name: str = Field(description="商品名，如：机械键盘")

schema = LookupProductInput.model_json_schema()
# -> {"properties": {"name": {"description": "商品名，如：机械键盘", "title": "Name", "type": "string"}},
#     "required": ["name"], "title": "LookupProductInput", "type": "object"}
```

三个 `description` 都很关键：**模型选工具全靠读描述**。`description` 写得烂（比如「查东西」），模型就会在「该查库存时查订单」。生产经验：description 里写清「什么时候用这个工具 + 参数什么意思 + 返回什么」。

> 🟡 **Java 对比**：= 给每个 `Tool` 实现类加 `@Schema` 注解再反射生成 OpenAPI 文档。Pydantic 的 `model_json_schema()` 一行搞定，因为字段类型/描述本来就写在模型里。

> 本节作业不考（作业用 FakeDecider，不需要让真模型理解工具），但 §32.8 接真实 API 时会用到。

---

## §32.8 真实用法：接 Anthropic 原生 tool use

教学版用文本协议（parse_action）。**生产版不用**——现代 LLM API 原生支持 **function calling / tool use**：你把工具的 schema 喂给模型，模型直接返回结构化的 `tool_call`，不用解析文本。

```python
# anthropic 原生 tool use（需 uv sync --extra ai + 配 ANTHROPIC_API_KEY）
import anthropic
client = anthropic.Anthropic()

tools = [{
    "name": "lookup_product",
    "description": "按商品名查商品，返回 SKU、价格和库存",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "商品名"}},
        "required": ["name"],
    },
}]

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "机械键盘还有货吗"}],
)
# response.content 里有 ToolUseBlock(name="lookup_product", input={"name": "机械键盘"})
# 直接拿到结构化决策，不用 parse_action
```

把原生 tool use 接到作业同一套「决策 → 调工具 → 观察」循环上，**不能**把观察拍成普通 user 文本（`观察:{obs}`）。Anthropic 要求：assistant 这一轮必须原样带回 `tool_use`（含 `id`），下一轮 user 必须回带 `tool_use_id` 的 `tool_result`，否则真 API 会拒收。

```python
def run_native_tool_loop(query: str, registry: dict, max_iters: int = 5) -> str:
    messages = [{"role": "user", "content": query}]
    for _ in range(max_iters):
        resp = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=1024,
            tools=tools, messages=messages,
        )
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:                              # 模型给了最终文本 → 收工
            texts = [b.text for b in resp.content if getattr(b, "text", None)]
            return texts[0] if texts else ""
        messages.append({"role": "assistant", "content": resp.content})  # ① 原样回写 tool_use
        results = []
        for block in tool_uses:
            obs = execute_tool(registry, block.name, block.input)       # 复用本章 execute_tool
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,               # ② 必须对上,否则 API 报错
                "content": str(obs),
            })
        messages.append({"role": "user", "content": results})
    return "(达到 max_iters)"
```

作业里的 FakeDecider 不受这套协议约束;接真 API 时走上面这个循环,不要自己把观察拼成 `"观察:..."` 文本。

**对比教学版**：

| | 教学版（文本协议） | 生产版（原生 tool use） |
|---|---|---|
| 模型输出 | `"TOOL: lookup_product ARGS: {...}"` 文本 | `ToolUseBlock` 结构 |
| 解析 | `parse_action`（可能解析失败） | 直接是 dict（不会解析失败） |
| 工具声明 | 写在 prompt 里让模型背 | API `tools` 字段，强约束 |

> 🔴 **为什么教学版还学文本协议？** ① 看懂原理——ReAct 本质就是文本协议；② 开源小模型/某些 API 不支持原生 tool call，只能用文本协议兜底；③ LangChain 的 ReAct Agent 内部就是这个套路。

> **Agent 框架一览**（了解）：LangChain Agents、OpenAI Agents SDK、Claude Agent SDK、以及你自己每天用的 Claude Code——它们的内核都是本章这个循环：**决策 → 调工具 → 观察 → 再决策**，只是多了并行工具调用、子 Agent、权限控制等工程强化。学完本章你已经懂它们的 80% 原理。

---

## §32.9 Java 老手常踩的坑 ⚠️

1. **以为 Agent = 多调几次 LLM**：不是。Agent 的关键是**模型决定流程**（调什么工具、调几次、何时停），不是你写死的循环。决策权在模型，不在代码。
2. **不设 max_iters**：LLM 犯傻会无限循环，烧钱烧时间。**必加硬上限**。生产还要加每次调用超时 + 总 token 上限。
3. **错误抛异常中断循环**：工具失败应该返回错误串、让模型看到、下一轮纠错。直接 raise 会剥夺模型自我修正的机会。**错误当数据，不当炸弹**。
4. **结果不 stringify**：模型只懂文本，工具返回 int/dict 直接喂会出问题。统一 `str()`。
5. **不传 observations**：模型无状态，忘了把历史观察喂回去，模型每轮都「失忆」，反复调同一工具。
6. **硬编码工具名**：`if name == "lookup_product"` 分支写死——每加工具就改代码。用注册表（字典），新工具加一行就行。
7. **混淆「answer」和「tool」的终止语义**：`react_step` 不区分终止，但 `run_agent_loop` 要在 `type=="answer"` 时 return。终止逻辑在主循环，不在单步。
8. **生产用文本协议**：能用原生 tool use（§32.8）就别自己 parse 文本。文本解析是脆弱的（模型格式飘了就崩），结构化 API 才是正道。
9. **工具 description 写得太烂**：模型选工具全靠读 description。「查东西」这种描述会让模型乱调工具。写清「什么时候用 + 参数 + 返回」。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `make_registry` | 注册表 + 函数一等公民 + `__name__` | 🟢 |
| `execute_tool` | 查表调用 + EAFP + `**args` + stringify | 🟡 |
| `parse_action` | 文本协议解析 + `partition` + `json.loads` | 🟡 |
| `react_step` | 决策派发（Command 模式） | 🟢 |
| `run_agent_loop` | ReAct 主循环 + 终止 + 死循环防护 | 🔴 |

```bash
uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v
```

全绿 = 掌握 Ch32。

**实现提示**：

- `make_registry`：字典推导式，`f.__name__`。
- `execute_tool`：先 `in` 检查，再 `try` 调用，`except Exception` 兜底。注意 `**args`。
- `parse_action`：`strip()` + `startswith` + `partition("ARGS:")` + `json.loads`。
- `react_step`：`decision.get("type")` 分流，answer/tool/else 三路。tool 委托给 `execute_tool`，args 用 `.get("args", {})` 容错。
- `run_agent_loop`：`observations=[]` → for max_iters → decider → answer 判断 → react_step + append → 兜底。

---

## ✅ 自测

- [ ] 能说清 Agent 和 Ch28 单轮调用的本质区别（决策权在谁手里）
- [ ] 知道 ReAct 是 Reason+Act+Observation 的循环，能画出循环图
- [ ] 会用 `*funcs` + `f.__name__` + 字典推导式做注册表
- [ ] 理解 `execute_tool` 为什么把错误也返回成字符串（错误当数据）
- [ ] 会用 `partition` + `json.loads` 解析 `TOOL: name ARGS: {...}` 协议
- [ ] 理解 `max_iters` 为什么必须有（LLM 会死循环）
- [ ] 知道工具 schema 的作用（模型靠 description 选工具）
- [ ] 知道生产环境用原生 tool use，不用文本协议
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么 Agent 比单轮调用强？决策权的转移体现在哪？」— 重读 §32.1
2. 「如果模型陷入死循环反复调同一工具，你的代码会怎样？怎么防？」— 重读 §32.6 的 max_iters
3. 「execute_tool 为什么把异常也返回成字符串，而不是 raise？」— 重读 §32.3
4. 「原生 tool use 和文本协议（ReAct）各有什么优劣？生产选哪个？」— 重读 §32.4/§32.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步：Ch33 用 FastAPI 封装 AI 服务

会写 Agent 了。但 Agent 现在只能跑在脚本里——怎么把它变成一个生产级 API，让前端流式地看到 Agent 一步步思考的过程？下一章用 **FastAPI + SSE** 把 AI 能力封装成 `/chat` 流式接口，带并发限流和成本控制。
