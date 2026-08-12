"""
Ch32 作业：Agent 开发（Tool Use / ReAct）。

学「Agent」——让 LLM 自己决定调哪个工具，在「思考→调工具→观察→再思考」的循环里解决问题。
核心：工具注册表、动作解析、单步执行、ReAct 主循环。

🎯 主线场景：电商「智能客服 Agent」——用户问「机械键盘还有货吗」「我的订单到哪了」，
Agent 自己决定先查商品、再查库存、最后给答复，全程不用你写 if/else 分支。

设计要点：本作业【不调真实 LLM】。decider（决策函数）用可注入的函数代替真模型——
只要签名是 decider(query, observations) -> dict，测试用 FakeDecider 离线跑。
真实用法（接 Anthropic / OpenAI 的 tool use）在 tutorial.md §32.8 有完整示例。

5 个函数。在每处 TODO 写实现，然后：

    uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v

全绿 = 你掌握了 Ch32。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:
- 工具就是普通函数（下方已备好三个业务工具：lookup_product / list_orders / check_stock），
  名字 = f.__name__，参数 = **kwargs。
- 决策（decision）是 dict，两种形态:
    {"type": "answer", "text": "最终答案文本"}           ← Agent 决定收尾
    {"type": "tool", "name": "工具名", "args": {...}}    ← Agent 决定调工具
- observations 是 list[str]，记录每一轮工具调用的观察结果（工具返回值的字符串）。
"""

import json

# ---------------------------------------------------------------------
# 业务数据层：电商后台的商品目录和订单簿（工具函数的数据源，无需修改）
# ---------------------------------------------------------------------

PRODUCT_CATALOG = {
    "机械键盘": {"sku": "KB-001", "price": 349, "stock": 12},
    "无线鼠标": {"sku": "MS-002", "price": 129, "stock": 0},
    "显示器": {"sku": "MN-003", "price": 899, "stock": 5},
}

ORDER_BOOK = {
    "u1001": [
        {"order_id": "A001", "item": "机械键盘", "status": "已发货", "amount": 349},
        {"order_id": "A002", "item": "无线鼠标", "status": "已完成", "amount": 129},
    ],
    "u1002": [
        {"order_id": "A003", "item": "显示器", "status": "待付款", "amount": 899},
    ],
}


# ---------------------------------------------------------------------
# 业务工具层：Agent 可登记使用的三个工具（已实现，直接拿去注册）
# ---------------------------------------------------------------------


def lookup_product(name: str) -> str:
    """按商品名查商品，返回一行描述；查不到返回提示。"""
    info = PRODUCT_CATALOG.get(name)
    if info is None:
        return f"未找到商品：{name}"
    return f"{name}（SKU {info['sku']}）：¥{info['price']}，库存 {info['stock']} 件"


def list_orders(user: str) -> str:
    """查某用户的全部订单，拼接成一行；没下过单返回提示。"""
    orders = ORDER_BOOK.get(user)
    if not orders:
        return f"{user} 没有订单记录"
    return "; ".join(
        f"{o['order_id']} {o['item']} {o['status']} ¥{o['amount']}" for o in orders
    )


def check_stock(sku: str) -> str:
    """按 SKU 查库存；SKU 不存在返回提示。"""
    for info in PRODUCT_CATALOG.values():
        if info["sku"] == sku:
            return f"{sku} 当前库存 {info['stock']} 件"
    return f"未知 SKU：{sku}"


# ========== §32.2 工具注册表：make_registry ==========


def make_registry(*funcs) -> dict:
    """
    【注册表 · §32.2】把多个工具函数打包成 {函数名: 函数} 的字典注册表。
    注册表就是 Agent 的「工具箱」——Agent 只能调这里登记过的工具。

    示例:
        reg = make_registry(lookup_product, check_stock)
        # -> {"lookup_product": <function lookup_product>, "check_stock": <function ...>}
        reg["lookup_product"]("机械键盘")   # "机械键盘（SKU KB-001）：¥349，库存 12 件"
        make_registry()                      # -> {}（一个工具都没登记）

    思路（对比 Java 的 Map<String, Tool> / Spring 的 @Bean 注册表）:
        Python 函数是一等公民，自带 __name__ 属性。字典推导式一步到位:
        return {f.__name__: f for f in funcs}

    为什么不用类/接口?
        Java 你可能写 interface Tool { String getName(); String run(args); } 再注册一堆 impl。
        Python 用 duck typing：只要是 callable、有 __name__，就能当工具。少写一层样板。
    """
    # TODO: 字典推导式 {f.__name__: f for f in funcs}
    ...


# ========== §32.3 执行工具：execute_tool ==========


def execute_tool(name: str, args: dict, registry: dict) -> str:
    """
    【执行 · §32.3】按名字查注册表调用工具，返回 str（观察结果）。
    三条路径:
      ① 正常: str(registry[name](**args))
      ② 未知工具: 返回 "错误:未知工具 {name}"
      ③ 调用抛异常: 返回 "错误:{e}"

    所有结果都 stringify，因为 Agent 循环里观察结果要塞回 prompt 喂给 LLM，必须是字符串。

    示例:
        reg = make_registry(lookup_product, list_orders)
        execute_tool("lookup_product", {"name": "机械键盘"}, reg)
            -> "机械键盘（SKU KB-001）：¥349，库存 12 件"
        execute_tool("delete_db", {}, reg)
            -> "错误:未知工具 delete_db"      （模型幻觉出不存在的工具，兜住）
        execute_tool("list_orders", {}, reg)
            -> "错误:..."                      （缺必填参数 user，抛 TypeError，兜住）

    思路（EAFP，先调再说，出问题 except 兜底）:
        if name not in registry: return f"错误:未知工具 {name}"
        try:
            return str(registry[name](**args))     # **args 把 dict 展开成关键字参数
        except Exception as e:
            return f"错误:{e}"

    为什么错误也返回字符串而不是抛异常?
        错误信息本身是有价值的观察——模型看到 "错误:未知工具 delete_db" 后，
        下一轮可能改调注册表里真实存在的工具。抛异常中断循环 = 剥夺模型自我纠正的机会。
        把错误当数据，而不是当炸弹——这是 Agent 设计的关键。
    """
    # TODO: 未知工具检查；try registry[name](**args) → str；except 返回错误串
    ...


# ========== §32.4 解析动作：parse_action ==========


def parse_action(text: str) -> dict:
    """
    【解析 · §32.4】把 LLM 输出的「动作文本」解析成结构化决策 dict。两种格式:
      ① "ANSWER: 答案文本"          -> {"type": "answer", "text": "答案文本"}
      ② 'TOOL: 工具名 ARGS: {"a":1}' -> {"type": "tool", "name": "工具名", "args": {"a": 1}}

    这是 ReAct 的「Act」环节——LLM 用固定格式输出动作，我们解析后执行。
    真实场景里 LLM 输出可能不规整，这里假定格式正确（教学版）；生产用原生 tool use（§32.8）。

    示例:
        parse_action("ANSWER: 机械键盘有货")
            -> {"type": "answer", "text": "机械键盘有货"}
        parse_action('TOOL: lookup_product ARGS: {"name": "机械键盘"}')
            -> {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}}
        parse_action('TOOL: list_orders ARGS: {"user": "u1001"}')
            -> {"type": "tool", "name": "list_orders", "args": {"user": "u1001"}}
        parse_action("今天天气不错")          # 无法识别
            -> {"type": "error", "text": "无法解析:今天天气不错"}

    思路（字符串前缀分流 + json.loads 解析参数）:
        text = text.strip()
        if text.startswith("ANSWER:"):
            return {"type": "answer", "text": text[len("ANSWER:"):].strip()}
        if text.startswith("TOOL:"):
            rest = text[len("TOOL:"):]              # " lookup_product ARGS: {...}"
            name_part, _, args_part = rest.partition("ARGS:")   # 只拆第一个 ARGS:
            return {"type": "tool",
                    "name": name_part.strip(),
                    "args": json.loads(args_part.strip())}
        return {"type": "error", "text": f"无法解析:{text}"}

    为什么用 partition 不用 split?
        partition("ARGS:") 只拆第一个分隔符，返回 (前, 分隔符, 后) 三段，稳定可控;
        args 的 JSON 里万一再有 "ARGS:" 字样也不受影响。split 会全拆，埋雷。
    """
    # TODO: strip；startswith("ANSWER:") → answer；startswith("TOOL:") → partition("ARGS:") + json.loads；else error
    ...


# ========== §32.5 单步执行：react_step ==========


def react_step(decision: dict, registry: dict) -> str:
    """
    【单步 · §32.5】执行一步决策，返回这一步的「输出」:
      ① decision["type"] == "answer" → 返回 decision["text"]（最终答案，由主循环判断终止）
      ② decision["type"] == "tool"   → 调 execute_tool 拿观察结果
      ③ 其他类型（error/未知）        → 返回错误提示串（让循环继续，LLM 下一轮纠错）

    这是 ReAct 的「执行」环节——把上一步解析出的决策落地。
    注意它不区分「这是最终答案」还是「工具观察」，都返回 str；由主循环 run_agent_loop 决定是否终止。

    示例（reg 已登记 lookup_product / list_orders）:
        react_step({"type": "answer", "text": "有货"}, reg)                 -> "有货"
        react_step({"type": "tool", "name": "lookup_product",
                    "args": {"name": "无线鼠标"}}, reg)
            -> "无线鼠标（SKU MS-002）：¥129，库存 0 件"
        react_step({"type": "error", "text": "无法解析:嘿嘿"}, reg)          -> "无法解析:嘿嘿"
        react_step({"type": "????"}, reg)                                    -> "未知决策类型:????"

    思路（if 分流，纯派发不复杂）:
        t = decision.get("type")
        if t == "answer":
            return decision["text"]
        if t == "tool":
            return execute_tool(decision["name"], decision.get("args", {}), registry)
        return decision.get("text", f"未知决策类型:{t}")

    为什么这一步要单独抽函数?
        单一职责：主循环只管「调度+收集观察」，执行细节委托给 react_step。
        对比 Java：这是 Command 模式的 execute()——decision 是 Command 对象，react_step 是执行器。
    """
    # TODO: type=="answer" 返回 text；=="tool" 调 execute_tool；else 返回错误串
    ...


# ========== §32.6 ReAct 主循环：run_agent_loop ==========


def run_agent_loop(decider, registry: dict, query: str, max_iters: int = 5) -> str:
    """
    【主循环 · §32.6】ReAct 核心循环:
        每轮让 decider(query, observations) 出一个决策 dict，
        是 answer 就返回 text（终止），
        是 tool 就 react_step 执行、把观察 append 到 observations（下一轮喂回 decider），
        超过 max_iters 还没答案就返回兜底串。

    decider 签名: decider(query: str, observations: list[str]) -> dict
        它代表 LLM：看到问题 + 历史所有观察，决定下一步（调工具 / 给答案）。
        测试里用 FakeDecider 按次序返回脚本化决策；真实用法把 decider 接到 LLM 上（§32.8）。

    示例（FakeDecider 按脚本出牌；reg 登记了 lookup_product / check_stock）:
        # 场景：用户问「机械键盘还有货吗」——Agent 先查商品拿 SKU，再查库存，最后答复
        script = [
            {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}},
            {"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}},
            {"type": "answer", "text": "机械键盘有货，库存 12 件"},
        ]
        run_agent_loop(FakeDecider(script), reg, "机械键盘还有货吗")
            -> "机械键盘有货，库存 12 件"
        # 第 2 轮 decider 看到的 observations = ["机械键盘（SKU KB-001）：¥349，库存 12 件"]
        # 第 3 轮看到 [...上一条..., "KB-001 当前库存 12 件"]

        # 死循环兜底：decider 一直调工具永不 answer
        loop = FakeDecider([{"type": "tool", "name": "check_stock",
                             "args": {"sku": "KB-001"}}] * 100)
        run_agent_loop(loop, reg, "?", max_iters=2)  -> "未能在 max_iters 内得出答案"

    思路（for 循环 + 两类决策分流）:
        observations = []
        for _ in range(max_iters):
            decision = decider(query, observations)         # LLM/脚本 决策（Reason）
            if decision.get("type") == "answer":
                return decision["text"]                     # 终止，返回答案
            result = react_step(decision, registry)         # 执行（Act）
            observations.append(result)                     # 收集观察（Observation）
        return "未能在 max_iters 内得出答案"                  # 兜底，防死循环

    为什么有 max_iters?
        LLM 可能陷入「调工具→不满意→再调同一个工具」的死循环（模型犯傻）。
        max_iters 是硬上限，保证 Agent 一定会停。对比 Java：线程池的拒绝策略、HTTP 超时熔断，同一思想。

    为什么 observations 每轮都全量传给 decider?
        和 Ch28 多轮对话同理：LLM 无状态，它要看到「问题 + 之前所有工具结果」才能决定下一步。
        observations 越长越贵（上下文窗口），复杂任务要配 Memory 截断/摘要（Ch30 讲过）。
    """
    # TODO: observations=[]；for max_iters: decider 出决策；answer→return text；else react_step + append；越界兜底
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示用 FakeDecider（真实用法见 tutorial.md §32.8：接 anthropic/OpenAI 的 tool use）
    class FakeDecider:
        """按次序返回脚本化决策，模拟 LLM。"""

        def __init__(self, script):
            self.script = list(script)
            self.calls = []

        def __call__(self, query, observations):
            self.calls.append((query, list(observations)))
            if not self.script:
                return {"type": "answer", "text": "(脚本耗尽)"}
            return self.script.pop(0)

    reg = make_registry(lookup_product, list_orders, check_stock)
    print("客服 Agent 已上线，可用工具:", list(reg.keys()))

    # 用户问:「机械键盘还有货吗」→ Agent 自主决定:先查商品 → 再查库存 → 给答复
    script = [
        {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}},
        {"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}},
        {"type": "answer", "text": "机械键盘有货，库存 12 件，¥349"},
    ]
    decider = FakeDecider(script)
    print("用户:", "机械键盘还有货吗")
    print("Agent:", run_agent_loop(decider, reg, "机械键盘还有货吗"))
    print("decider 每轮看到的 observations:")
    for i, (q, obs) in enumerate(decider.calls):
        print(f"  轮{i}: observations={obs}")
