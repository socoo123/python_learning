"""
Ch32 作业测试。运行: uv run pytest 05_ai_framework/ch32/test_ch32_assignment.py -v

全部用 FakeDecider 离线测,不调真实 LLM,不需要 API key。
"""
import pytest

from ch32_assignment import (
    execute_tool,
    make_registry,
    parse_action,
    react_step,
    run_agent_loop,
)


# ---------- 工具函数(测试用) ----------
def add(a, b):
    return a + b


def mul(a, b):
    return a * b


def greet(name):
    return f"hi {name}"


def boom(x):
    raise ValueError("炸了")


# ---------- FakeDecider:模拟 LLM ----------
class FakeDecider:
    """按次序返回脚本化决策,模拟 LLM 的「思考」。

    script 是决策 dict 列表;每次 __call__ 弹一个。
    记录每次调用的 (query, observations 快照),方便断言 Agent 喂回的观察。
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, query, observations):
        self.calls.append((query, list(observations)))
        if not self.script:
            return {"type": "answer", "text": "(脚本耗尽)"}
        return self.script.pop(0)


# ---------- make_registry ----------
class TestMakeRegistry:
    def test_basic(self):
        reg = make_registry(add, mul)
        assert reg == {"add": add, "mul": mul}

    def test_empty(self):
        assert make_registry() == {}

    def test_callable_via_name(self):
        reg = make_registry(add)
        assert reg["add"](2, 3) == 5

    def test_three_funcs(self):
        reg = make_registry(add, mul, greet)
        assert set(reg.keys()) == {"add", "mul", "greet"}

    def test_lambda_gets_lambda_name(self):
        reg = make_registry(lambda x: x)
        assert "<lambda>" in reg


# ---------- execute_tool ----------
class TestExecuteTool:
    def test_normal_call(self):
        reg = make_registry(add)
        assert execute_tool("add", {"a": 2, "b": 3}, reg) == "5"

    def test_string_result(self):
        reg = make_registry(greet)
        assert execute_tool("greet", {"name": "zy"}, reg) == "hi zy"

    def test_unknown_tool(self):
        reg = make_registry(add)
        assert execute_tool("nope", {}, reg) == "错误:未知工具 nope"

    def test_exception_returns_error_string(self):
        reg = make_registry(boom)
        result = execute_tool("boom", {"x": 1}, reg)
        assert result.startswith("错误:")
        assert "炸了" in result

    def test_wrong_arg_types(self):
        reg = make_registry(add)
        # add("x", 3) → str + int 报错,被 except 兜住
        result = execute_tool("add", {"a": "x", "b": 3}, reg)
        assert result.startswith("错误:")

    def test_no_args(self):
        def hi():
            return "hi"

        reg = make_registry(hi)
        assert execute_tool("hi", {}, reg) == "hi"

    def test_returns_string_even_for_float(self):
        def half(x):
            return x / 2

        reg = make_registry(half)
        assert execute_tool("half", {"x": 5}, reg) == "2.5"


# ---------- parse_action ----------
class TestParseAction:
    def test_answer(self):
        assert parse_action("ANSWER: 42") == {"type": "answer", "text": "42"}

    def test_answer_chinese(self):
        assert parse_action("ANSWER: 不确定") == {"type": "answer", "text": "不确定"}

    def test_answer_with_spaces(self):
        # 前后空格要 strip,答案本身保留
        assert parse_action("  ANSWER:   hello world  ") == {
            "type": "answer",
            "text": "hello world",
        }

    def test_tool(self):
        result = parse_action('TOOL: add ARGS: {"a": 2, "b": 3}')
        assert result == {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}}

    def test_tool_empty_args(self):
        result = parse_action('TOOL: listall ARGS: {}')
        assert result == {"type": "tool", "name": "listall", "args": {}}

    def test_tool_nested_args(self):
        result = parse_action('TOOL: search ARGS: {"q": "py", "opts": {"n": 5}}')
        assert result == {
            "type": "tool",
            "name": "search",
            "args": {"q": "py", "opts": {"n": 5}},
        }

    def test_unparseable(self):
        result = parse_action("乱七八糟")
        assert result["type"] == "error"
        assert "乱七八糟" in result["text"]

    def test_empty_string(self):
        result = parse_action("")
        assert result["type"] == "error"


# ---------- react_step ----------
class TestReactStep:
    def test_answer_returns_text(self):
        reg = make_registry(add)
        assert react_step({"type": "answer", "text": "42"}, reg) == "42"

    def test_tool_calls_execute(self):
        reg = make_registry(add)
        decision = {"type": "tool", "name": "add", "args": {"a": 1, "b": 2}}
        assert react_step(decision, reg) == "3"

    def test_tool_unknown(self):
        reg = make_registry(add)
        decision = {"type": "tool", "name": "nope", "args": {}}
        assert react_step(decision, reg) == "错误:未知工具 nope"

    def test_tool_missing_args_key(self):
        # 没有 args 键也要容错(用默认 {})
        reg = make_registry(greet)
        # greet 需要 name,缺参会报错 → 返回错误串
        decision = {"type": "tool", "name": "greet"}
        result = react_step(decision, reg)
        assert result.startswith("错误:")

    def test_error_decision_passthrough(self):
        reg = make_registry(add)
        decision = {"type": "error", "text": "坏掉了"}
        assert react_step(decision, reg) == "坏掉了"

    def test_unknown_type(self):
        reg = make_registry(add)
        decision = {"type": "????"}
        result = react_step(decision, reg)
        assert "未知" in result


# ---------- run_agent_loop ----------
class TestRunAgentLoop:
    def test_immediate_answer(self):
        # 第 1 轮就给答案,不调任何工具
        decider = FakeDecider([{"type": "answer", "text": "直接答"}])
        reg = make_registry(add)
        assert run_agent_loop(decider, reg, "问题") == "直接答"
        assert len(decider.calls) == 1

    def test_one_tool_then_answer(self):
        script = [
            {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}},
            {"type": "answer", "text": "结果是 5"},
        ]
        decider = FakeDecider(script)
        reg = make_registry(add)
        assert run_agent_loop(decider, reg, "2+3=?") == "结果是 5"
        assert len(decider.calls) == 2

    def test_observations_passed_back(self):
        # 验证工具结果被 append 到 observations,且下一轮喂回 decider
        script = [
            {"type": "tool", "name": "add", "args": {"a": 1, "b": 1}},
            {"type": "tool", "name": "mul", "args": {"a": 2, "b": 3}},
            {"type": "answer", "text": "done"},
        ]
        decider = FakeDecider(script)
        reg = make_registry(add, mul)
        run_agent_loop(decider, reg, "?")
        # 第 2 轮 decider 应该看到上一轮的观察 "2"
        assert decider.calls[1][1] == ["2"]
        # 第 3 轮看到 ["2", "6"]
        assert decider.calls[2][1] == ["2", "6"]

    def test_query_passed_each_round(self):
        script = [{"type": "answer", "text": "ok"}]
        decider = FakeDecider(script)
        run_agent_loop(decider, make_registry(), "你好")
        assert decider.calls[0][0] == "你好"

    def test_max_iters_exceeded(self):
        # decider 一直调工具,永远不 answer → 超过 max_iters 兜底
        script = [{"type": "tool", "name": "add", "args": {"a": 1, "b": 1}}] * 100
        decider = FakeDecider(script)
        reg = make_registry(add)
        result = run_agent_loop(decider, reg, "?", max_iters=3)
        assert result == "未能在 max_iters 内得出答案"
        assert len(decider.calls) == 3

    def test_default_max_iters_is_5(self):
        script = [{"type": "tool", "name": "add", "args": {"a": 1, "b": 1}}] * 100
        decider = FakeDecider(script)
        reg = make_registry(add)
        result = run_agent_loop(decider, reg, "?")
        assert result == "未能在 max_iters 内得出答案"
        assert len(decider.calls) == 5

    def test_multi_tool_chain(self):
        # 先加,再乘,最后答
        script = [
            {"type": "tool", "name": "add", "args": {"a": 2, "b": 3}},   # 5
            {"type": "tool", "name": "mul", "args": {"a": 5, "b": 4}},   # 20
            {"type": "answer", "text": "20"},
        ]
        decider = FakeDecider(script)
        reg = make_registry(add, mul)
        assert run_agent_loop(decider, reg, "2+3然后*4") == "20"

    def test_tool_error_continues_loop(self):
        # 工具调用失败返回错误串,循环继续,LLM 下轮纠错
        script = [
            {"type": "tool", "name": "nope", "args": {}},                # 未知工具
            {"type": "answer", "text": "算了不调了"},
        ]
        decider = FakeDecider(script)
        reg = make_registry(add)
        assert run_agent_loop(decider, reg, "?") == "算了不调了"
        # 第 2 轮 decider 看到错误观察
        assert decider.calls[1][1] == ["错误:未知工具 nope"]
