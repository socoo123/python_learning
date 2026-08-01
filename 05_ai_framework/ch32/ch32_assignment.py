"""
Ch32 作业:Agent 开发(Tool Use / ReAct)。

学「Agent」——让 LLM 自己决定调哪个工具,在「思考→调工具→观察→再思考」的循环里解决问题。
核心:工具注册表、动作解析、单步执行、ReAct 主循环。

设计要点:本作业【不调真实 LLM】。decider(决策函数)用可注入的函数代替真模型——
只要签名是 decider(query, observations) -> dict,测试用 FakeDecider 离线跑。
真实用法(接 Anthropic / OpenAI 的 tool use)在 tutorial.md 里有完整示例。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v

全绿 = 你掌握了 Ch32。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:
- 工具就是普通函数:def add(a, b): return a + b。名字 = f.__name__,参数 = **kwargs。
- 决策(decision)是 dict,两种形态:
    {"type": "answer", "text": "最终答案文本"}           ← Agent 决定收尾
    {"type": "tool", "name": "工具名", "args": {...}}    ← Agent 决定调工具
- observations 是 list[str],记录每一轮工具调用的观察结果(工具返回值的字符串)。
"""


# ========== §32.2 工具注册表:make_registry ==========


def make_registry(*funcs) -> dict:
    """
    【注册表 · §32.2】把多个工具函数打包成 {函数名: 函数} 的字典注册表。
    注册表就是 Agent 的「工具箱」——Agent 只能调这里登记过的工具。

    示例:
        def add(a, b): return a + b
        def mul(a, b): return a * b
        reg = make_registry(add, mul)
        # -> {"add": <function add>, "mul": <function mul>}
        reg["add"](2, 3)   # 5

    思路(对比 Java 的 Map<String, Tool> / Spring 的 @Bean 注册表):
        Python 函数是一等公民,自带 __name__ 属性。字典推导式一步到位:
        return {f.__name__: f for f in funcs}

    为什么不用类/接口?
        Java 你可能写 interface Tool { String getName(); String run(args); } 再注册一堆 impl。
        Python 用 duck typing:只要是 callable、有 __name__,就能当工具。少写一层样板。
    """
    # TODO: 字典推导式 {f.__name__: f for f in funcs}
    ...


# ========== §32.3 执行工具:execute_tool ==========


def execute_tool(name: str, args: dict, registry: dict) -> str:
    """
    【执行 · §32.3】按名字查注册表调用工具,返回 str(观察结果)。
    三条路径:
      ① 正常:str(registry[name](**args))
      ② 未知工具:返回 "错误:未知工具 {name}"
      ③ 调用抛异常:返回 "错误:{e}"

    所有结果都 stringify,因为 Agent 循环里观察结果要塞回 prompt 喂给 LLM,必须是字符串。

    示例:
        reg = make_registry(lambda a, b: a + b)          # 注意 lambda 无 __name__?(有,<lambda>)
        def add(a, b): return a + b
        reg = make_registry(add)
        execute_tool("add", {"a": 2, "b": 3}, reg)        -> "5"
        execute_tool("nope", {}, reg)                     -> "错误:未知工具 nope"
        execute_tool("add", {"a": "x", "b": 1}, reg)      -> "错误:..."  (str+int 报错)

    思路(EAFP,先调再说,出问题 except 兜底):
        if name not in registry: return f"错误:未知工具 {name}"
        try:
            return str(registry[name](**args))     # **args 把 dict 展开成关键字参数
        except Exception as e:
            return f"错误:{e}"

    为什么返回 str 而不是原值?
        工具可能返回 int/float/list/dict……但 ReAct 循环要把观察结果拼进 prompt 喂给 LLM,
        LLM 只认文本。所以统一 str()。对比 Java:你也会把结果 JSON 序列化成字符串塞回 prompt。
    """
    # TODO: 未知工具检查;try registry[name](**args) → str;except 返回错误串
    ...


# ========== §32.4 解析动作:parse_action ==========


def parse_action(text: str) -> dict:
    """
    【解析 · §32.4】把 LLM 输出的「动作文本」解析成结构化决策 dict。两种格式:
      ① "ANSWER: 答案文本"          -> {"type": "answer", "text": "答案文本"}
      ② 'TOOL: 工具名 ARGS: {"a":1}' -> {"type": "tool", "name": "工具名", "args": {"a": 1}}

    这是 ReAct 的「Act」环节——LLM 用固定格式输出动作,我们解析后执行。
    真实场景里 LLM 输出可能不规整,这里假定格式正确(教学版);生产用 JSON Schema 强约束。

    示例:
        parse_action("ANSWER: 42")
            -> {"type": "answer", "text": "42"}
        parse_action('TOOL: add ARGS: {"a": 2, "b": 3}')
            -> {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}}
        parse_action("ANSWER: 不确定")     # 中文答案也行
            -> {"type": "answer", "text": "不确定"}
        parse_action("乱七八糟")            # 无法识别
            -> {"type": "error", "text": "无法解析:乱七八糟"}

    思路(字符串前缀分流 + json.loads 解析参数):
        import json
        text = text.strip()
        if text.startswith("ANSWER:"):
            return {"type": "answer", "text": text[len("ANSWER:"):].strip()}
        if text.startswith("TOOL:"):
            # "TOOL: add ARGS: {...}" 拆成 name 和 args_json 两段
            rest = text[len("TOOL:"):]              # " add ARGS: {...}"
            name_part, _, args_part = rest.partition("ARGS:")
            name = name_part.strip()
            args = json.loads(args_part.strip())   # dict
            return {"type": "tool", "name": name, "args": args}
        return {"type": "error", "text": f"无法解析:{text}"}

    为什么不用正则?
        partition + startswith 够用了,可读性比正则高。教学版优先简单。
        真实 SDK 的 tool use 用结构化 JSON(不是文本协议),根本不用解析——见 tutorial §32.7。
    """
    # TODO: strip;startswith("ANSWER:") → answer;startswith("TOOL:") → partition("ARGS:") + json.loads;else error
    ...


# ========== §32.5 单步执行:react_step ==========


def react_step(decision: dict, registry: dict) -> str:
    """
    【单步 · §32.5】执行一步决策,返回这一步的「输出」:
      ① decision["type"] == "answer" → 返回 decision["text"](最终答案,循环到此终止)
      ② decision["type"] == "tool"   → 调 execute_tool 拿观察结果
      ③ 其他类型(error/未知)        → 返回错误提示串(让循环继续,LLM 下一轮纠错)

    这是 ReAct 的「执行」环节——把上一步解析出的决策落地。
    注意它不区分「这是最终答案」还是「工具观察」,都返回 str;由主循环 run_agent_loop 决定是否终止。

    示例:
        react_step({"type": "answer", "text": "42"}, reg)            -> "42"
        react_step({"type": "tool", "name": "add", "args": {"a":1,"b":2}}, reg)  -> "3"
        react_step({"type": "error", "text": "坏掉"}, reg)           -> "坏掉"
        react_step({"type": "????"}, reg)                             -> "未知决策类型:????"

    思路(if/elif/else 分流,纯派发不复杂):
        t = decision.get("type")
        if t == "answer":
            return decision["text"]
        if t == "tool":
            return execute_tool(decision["name"], decision.get("args", {}), registry)
        return decision.get("text", f"未知决策类型:{t}")

    为什么这一步要单独抽函数?
        单一职责:主循环只管「调度+收集观察」,执行细节委托给 react_step。
        对比 Java:这是 Command 模式的 execute()——decision 是 Command 对象,react_step 是执行器。
    """
    # TODO: type=="answer" 返回 text;=="tool" 调 execute_tool;else 返回错误串
    ...


# ========== §32.6 ReAct 主循环:run_agent_loop ==========


def run_agent_loop(decider, registry: dict, query: str, max_iters: int = 5) -> str:
    """
    【主循环 · §32.6】ReAct 核心循环:
        每轮让 decider(query, observations) 出一个决策 dict,
        是 answer 就返回 text(终止),
        是 tool 就 execute_tool 把结果 append 到 observations(下一轮喂回 decider),
        超过 max_iters 还没答案就返回兜底串。

    decider 签名:decider(query: str, observations: list[str]) -> dict
        它代表 LLM:看到问题 + 历史所有观察,决定下一步(调工具 / 给答案)。
        测试里用 FakeDecider 按次序返回脚本化决策;真实用法把 decider 接到 LLM 上(见 tutorial §32.7)。

    示例:
        # FakeDecider:第 1 次调工具,第 2 次给答案
        script = [
            {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}},
            {"type": "answer", "text": "结果是 5"},
        ]
        decider = FakeDecider(script)
        reg = make_registry(lambda a, b: a + b)   # 注意 lambda 名是 <lambda>,下面用具名函数
        def add(a, b): return a + b
        reg = make_registry(add)
        run_agent_loop(decider, reg, "2+3=?")     -> "结果是 5"

        # 死循环兜底:decider 一直不 answer
        loop = FakeDecider([{"type": "tool", "name": "add", "args": {"a":1,"b":1}}] * 100)
        run_agent_loop(loop, reg, "?", max_iters=2)  -> "未能在 max_iters 内得出答案"

    思路(while/for 循环 + 两类决策分流):
        observations = []
        for _ in range(max_iters):
            decision = decider(query, observations)         # LLM/脚本 决策
            if decision.get("type") == "answer":
                return decision["text"]                     # 终止,返回答案
            result = react_step(decision, registry)         # 执行(tool/error 都返回 str)
            observations.append(result)                     # 收集观察,下一轮可见
        return "未能在 max_iters 内得出答案"                  # 兜底,防死循环

    为什么有 max_iters?
        LLM 可能陷入「调工具→不满意→再调同一个工具」的死循环(模型犯傻)。
        max_iters 是硬上限,保证 Agent 一定会停。对比 Java:线程池的拒绝策略、超时熔断,同一思想。

    为什么 observations 每轮都全量传给 decider?
        和 Ch28 多轮对话同理:LLM 无状态,它要看到「问题 + 之前所有工具结果」才能决定下一步。
        observations 越长越贵(上下文窗口),所以复杂任务要配 Memory 截断(Ch30 讲过)。
    """
    # TODO: observations=[];for max_iters: decider 出决策;answer→return text;else react_step + append;越界兜底
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示用 FakeDecider(真实用法见 tutorial.md:接 anthropic/OpenAI 的 tool use)
    class FakeDecider:
        """按次序返回脚本化决策,模拟 LLM。"""

        def __init__(self, script):
            self.script = list(script)
            self.calls = []

        def __call__(self, query, observations):
            self.calls.append((query, list(observations)))
            return self.script.pop(0) if self.script else {"type": "answer", "text": "(空)"}

    def add(a, b):
        return a + b

    def mul(a, b):
        return a * b

    reg = make_registry(add, mul)
    print("注册表:", list(reg.keys()))

    script = [
        {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}},
        {"type": "tool", "name": "mul", "args": {"a": 5, "b": 4}},
        {"type": "answer", "text": "算完了"},
    ]
    decider = FakeDecider(script)
    print("Agent 结果:", run_agent_loop(decider, reg, "先加后乘"))
    print("decider 每轮看到的 observations:")
    for i, (q, obs) in enumerate(decider.calls):
        print(f"  轮{i}: observations={obs}")
