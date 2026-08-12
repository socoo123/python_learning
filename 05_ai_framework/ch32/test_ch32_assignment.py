"""
Ch32 作业测试。运行: uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v

全部用 FakeDecider 离线测，不调真实 LLM，不需要 API key。
主线场景：电商客服 Agent——查商品 / 查订单 / 查库存。
"""
import pytest

from ch32_assignment import (
    check_stock,
    execute_tool,
    list_orders,
    lookup_product,
    make_registry,
    parse_action,
    react_step,
    run_agent_loop,
)


# ---------- FakeDecider:模拟 LLM ----------
class FakeDecider:
    """按次序返回脚本化决策，模拟 LLM 的「思考」。

    script 是决策 dict 列表；每次 __call__ 弹一个。
    记录每次调用的 (query, observations 快照)，方便断言 Agent 喂回的观察。
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, query, observations):
        self.calls.append((query, list(observations)))
        if not self.script:
            return {"type": "answer", "text": "(脚本耗尽)"}
        return self.script.pop(0)


@pytest.fixture
def registry():
    """客服 Agent 的完整工具箱。"""
    return make_registry(lookup_product, list_orders, check_stock)


# ---------- make_registry ----------
class TestMakeRegistry:
    def test_registers_three_tools(self, registry):
        assert set(registry.keys()) == {"lookup_product", "list_orders", "check_stock"}

    def test_maps_name_to_function(self):
        reg = make_registry(lookup_product)
        assert reg == {"lookup_product": lookup_product}

    def test_empty_registry(self):
        assert make_registry() == {}

    def test_callable_via_name(self, registry):
        # 注册表里的函数能直接按名取出来调用
        assert "¥349" in registry["lookup_product"]("机械键盘")

    def test_lambda_gets_lambda_name(self):
        reg = make_registry(lambda x: x)
        assert "<lambda>" in reg


# ---------- execute_tool ----------
class TestExecuteTool:
    def test_lookup_product_found(self, registry):
        result = execute_tool("lookup_product", {"name": "机械键盘"}, registry)
        assert result == "机械键盘（SKU KB-001）：¥349，库存 12 件"

    def test_lookup_product_not_found(self, registry):
        # 工具正常返回「未找到」——这是业务结果，不是错误
        result = execute_tool("lookup_product", {"name": "辣条"}, registry)
        assert result == "未找到商品：辣条"

    def test_list_orders(self, registry):
        result = execute_tool("list_orders", {"user": "u1001"}, registry)
        assert result == "A001 机械键盘 已发货 ¥349; A002 无线鼠标 已完成 ¥129"

    def test_list_orders_unknown_user(self, registry):
        result = execute_tool("list_orders", {"user": "u9999"}, registry)
        assert result == "u9999 没有订单记录"

    def test_check_stock(self, registry):
        assert execute_tool("check_stock", {"sku": "MS-002"}, registry) == "MS-002 当前库存 0 件"

    def test_unknown_tool(self, registry):
        # 模型幻觉出注册表里没有的工具 → 兜住
        assert execute_tool("delete_db", {}, registry) == "错误:未知工具 delete_db"

    def test_missing_required_arg(self, registry):
        # list_orders 缺必填参数 user → TypeError → 错误串
        result = execute_tool("list_orders", {}, registry)
        assert result.startswith("错误:")

    def test_wrong_arg_type_returns_error(self):
        def div(a, b):
            return a / b

        reg = make_registry(div)
        result = execute_tool("div", {"a": 1, "b": 0}, reg)
        assert result.startswith("错误:")
        assert "division" in result

    def test_result_is_stringified(self):
        def get_price(name):
            return 349  # 返回 int

        reg = make_registry(get_price)
        result = execute_tool("get_price", {"name": "机械键盘"}, reg)
        assert result == "349"
        assert isinstance(result, str)


# ---------- parse_action ----------
class TestParseAction:
    def test_answer(self):
        assert parse_action("ANSWER: 机械键盘有货") == {
            "type": "answer",
            "text": "机械键盘有货",
        }

    def test_answer_strips_surrounding_spaces(self):
        # 整串前后空格 strip，答案内部空格保留
        assert parse_action("  ANSWER:   库存还有 12 件  ") == {
            "type": "answer",
            "text": "库存还有 12 件",
        }

    def test_tool_with_chinese_arg(self):
        result = parse_action('TOOL: lookup_product ARGS: {"name": "机械键盘"}')
        assert result == {
            "type": "tool",
            "name": "lookup_product",
            "args": {"name": "机械键盘"},
        }

    def test_tool_empty_args(self):
        result = parse_action("TOOL: list_all_products ARGS: {}")
        assert result == {"type": "tool", "name": "list_all_products", "args": {}}

    def test_tool_nested_args(self):
        result = parse_action('TOOL: search ARGS: {"q": "键盘", "opts": {"top": 3}}')
        assert result == {
            "type": "tool",
            "name": "search",
            "args": {"q": "键盘", "opts": {"top": 3}},
        }

    def test_tool_name_with_underscore_and_digits(self):
        result = parse_action('TOOL: check_stock_v2 ARGS: {"sku": "KB-001"}')
        assert result["name"] == "check_stock_v2"
        assert result["args"] == {"sku": "KB-001"}

    def test_unparseable_text(self):
        result = parse_action("今天天气不错")
        assert result == {"type": "error", "text": "无法解析:今天天气不错"}

    def test_empty_string(self):
        result = parse_action("")
        assert result["type"] == "error"

    def test_whitespace_only(self):
        result = parse_action("   \n  ")
        assert result["type"] == "error"


# ---------- react_step ----------
class TestReactStep:
    def test_answer_returns_text(self, registry):
        assert react_step({"type": "answer", "text": "有货，放心买"}, registry) == "有货，放心买"

    def test_tool_dispatch(self, registry):
        decision = {"type": "tool", "name": "check_stock", "args": {"sku": "MN-003"}}
        assert react_step(decision, registry) == "MN-003 当前库存 5 件"

    def test_tool_unknown_name(self, registry):
        decision = {"type": "tool", "name": "hack_db", "args": {}}
        assert react_step(decision, registry) == "错误:未知工具 hack_db"

    def test_tool_missing_args_key(self, registry):
        # 决策里没有 args 键 → 默认 {} → list_orders 缺参 → 错误串（容错，不炸）
        decision = {"type": "tool", "name": "list_orders"}
        result = react_step(decision, registry)
        assert result.startswith("错误:")

    def test_error_decision_passthrough(self, registry):
        # parse_action 解析失败产生的 error 决策：原文透传，让循环喂回模型纠错
        decision = {"type": "error", "text": "无法解析:嘿嘿"}
        assert react_step(decision, registry) == "无法解析:嘿嘿"

    def test_unknown_type(self, registry):
        result = react_step({"type": "????"}, registry)
        assert "未知" in result


# ---------- run_agent_loop ----------
class TestRunAgentLoop:
    def test_immediate_answer(self, registry):
        # 第 1 轮就给答案，不调任何工具（常见问题直接答）
        decider = FakeDecider([{"type": "answer", "text": "满 99 包邮"}])
        assert run_agent_loop(decider, registry, "包邮吗") == "满 99 包邮"
        assert len(decider.calls) == 1

    def test_stock_check_two_step(self, registry):
        # 主线场景：「机械键盘还有货吗」→ 查商品拿 SKU → 查库存 → 答复
        script = [
            {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}},
            {"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}},
            {"type": "answer", "text": "机械键盘有货，库存 12 件"},
        ]
        decider = FakeDecider(script)
        result = run_agent_loop(decider, registry, "机械键盘还有货吗")
        assert result == "机械键盘有货，库存 12 件"
        assert len(decider.calls) == 3

    def test_observations_passed_back(self, registry):
        # 验证工具结果 append 到 observations，且下一轮喂回 decider
        script = [
            {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}},
            {"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}},
            {"type": "answer", "text": "done"},
        ]
        decider = FakeDecider(script)
        run_agent_loop(decider, registry, "?")
        # 第 1 轮:还没有任何观察
        assert decider.calls[0][1] == []
        # 第 2 轮:看到查商品的结果
        assert decider.calls[1][1] == ["机械键盘（SKU KB-001）：¥349，库存 12 件"]
        # 第 3 轮:看到前两轮全部观察
        assert decider.calls[2][1] == [
            "机械键盘（SKU KB-001）：¥349，库存 12 件",
            "KB-001 当前库存 12 件",
        ]

    def test_query_passed_each_round(self, registry):
        script = [
            {"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}},
            {"type": "answer", "text": "ok"},
        ]
        decider = FakeDecider(script)
        run_agent_loop(decider, registry, "键盘有货吗")
        assert decider.calls[0][0] == "键盘有货吗"
        assert decider.calls[1][0] == "键盘有货吗"

    def test_order_query_chain(self, registry):
        # 另一条业务链：「我 u1001 的订单」→ 查订单 → 答复
        script = [
            {"type": "tool", "name": "list_orders", "args": {"user": "u1001"}},
            {"type": "answer", "text": "你有 2 个订单，A001 已发货"},
        ]
        decider = FakeDecider(script)
        result = run_agent_loop(decider, registry, "我 u1001 的订单到哪了")
        assert result == "你有 2 个订单，A001 已发货"
        assert decider.calls[1][1] == ["A001 机械键盘 已发货 ¥349; A002 无线鼠标 已完成 ¥129"]

    def test_tool_error_continues_loop(self, registry):
        # 第 1 轮幻觉出未知工具 → 错误串作为观察喂回 → 第 2 轮纠错成功 → 答复
        script = [
            {"type": "tool", "name": "find_keyboard", "args": {}},
            {"type": "tool", "name": "lookup_product", "args": {"name": "机械键盘"}},
            {"type": "answer", "text": "找到了"},
        ]
        decider = FakeDecider(script)
        assert run_agent_loop(decider, registry, "帮我找键盘") == "找到了"
        assert decider.calls[1][1] == ["错误:未知工具 find_keyboard"]

    def test_max_iters_exceeded(self, registry):
        # decider 一直查库存永不 answer → 超过 max_iters 兜底
        script = [{"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}}] * 100
        decider = FakeDecider(script)
        result = run_agent_loop(decider, registry, "?", max_iters=3)
        assert result == "未能在 max_iters 内得出答案"
        assert len(decider.calls) == 3

    def test_default_max_iters_is_5(self, registry):
        script = [{"type": "tool", "name": "check_stock", "args": {"sku": "KB-001"}}] * 100
        decider = FakeDecider(script)
        result = run_agent_loop(decider, registry, "?")
        assert result == "未能在 max_iters 内得出答案"
        assert len(decider.calls) == 5
