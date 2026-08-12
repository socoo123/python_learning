"""
Ch30 作业测试。运行: uv run pytest 05_ai_framework/ch30/test_ch30_assignment.py -v

全程离线:model 步用 RunnableLambda 包普通函数(FakeModel),不调真实 LLM。
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from ch30_assignment import (
    append_turn,
    as_runnable,
    batch_run,
    build_chain,
    build_prompt,
    chat_once,
    format_history,
    run_chain,
)


def make_echo_chain(template: str = "Q:{q}", fn=lambda s: f"A:{s}"):
    """搭一条 FakeModel 链:prompt 渲染 → to_text → fn → StrOutputParser。"""
    return build_chain(build_prompt(template), as_runnable(fn), StrOutputParser())


# ---------- §30.2 build_prompt ----------
class TestBuildPrompt:
    def test_invoke_to_string(self):
        # invoke 返回 PromptValue 对象,.to_string() 得到纯文本
        p = build_prompt("回答:{q}")
        assert p.invoke({"q": "你好"}).to_string() == "回答:你好"

    def test_format_returns_str(self):
        # .format(...) 直接返回字符串
        assert build_prompt("{greeting},{name}").format(greeting="Hi", name="Bob") == "Hi,Bob"

    def test_returns_prompt_template(self):
        assert isinstance(build_prompt("x"), PromptTemplate)

    def test_invoke_is_not_str(self):
        # 关键认知:invoke 返回 PromptValue,不是 str(蒙 str 会挂)
        result = build_prompt("{q}").invoke({"q": "hi"})
        assert not isinstance(result, str)


# ---------- §30.3 as_runnable ----------
class TestAsRunnable:
    def test_invoke(self):
        assert as_runnable(lambda s: s.upper()).invoke("abc") == "ABC"

    def test_returns_runnable_lambda(self):
        assert isinstance(as_runnable(lambda x: x), RunnableLambda)

    def test_pipe_compose(self):
        # 包成 Runnable 后就能用 | 串联
        chain = as_runnable(lambda s: s.upper()) | as_runnable(lambda s: s + "!")
        assert chain.invoke("hi") == "HI!"


# ---------- §30.4 build_chain ----------
class TestBuildChain:
    def test_full_chain(self):
        chain = make_echo_chain()
        assert chain.invoke({"q": "你好"}) == "A:Q:你好"

    def test_chain_is_runnable(self):
        assert isinstance(make_echo_chain(), Runnable)

    def test_model_receives_plain_str(self):
        # 没有 to_text 适配时 FakeModel 会收到 PromptValue 对象 repr;有了则收到纯文本
        seen = []
        chain = make_echo_chain("{q}", lambda s: seen.append(s) or "ok")
        chain.invoke({"q": "x"})
        assert seen == ["x"]

    def test_multi_step_model(self):
        # model 内部做点处理(replace),验证数据真的流过了 model 步
        chain = make_echo_chain("翻译:{q}", lambda s: s.replace("翻译:", "[EN] "))
        assert chain.invoke({"q": "苹果"}) == "[EN] 苹果"


# ---------- §30.5 run_chain ----------
class TestRunChain:
    def test_basic(self):
        assert run_chain(make_echo_chain(), {"q": "你好"}) == "A:Q:你好"

    def test_multi_variables(self):
        chain = make_echo_chain("{a}+{b}", lambda s: f"[{s}]")
        assert run_chain(chain, {"a": "1", "b": "2"}) == "[1+2]"

    def test_accepts_any_runnable(self):
        # run_chain 只要求「能 invoke 的 Runnable」——单个 RunnableLambda 也行
        assert run_chain(as_runnable(lambda n: n * 2), 3) == 6


# ---------- §30.6 batch_run ----------
class TestBatchRun:
    def test_batch_three_in_order(self):
        chain = make_echo_chain("问:{q}", lambda s: f"答:{s}")
        inputs = [{"q": "a"}, {"q": "b"}, {"q": "c"}]
        assert batch_run(chain, inputs) == ["答:问:a", "答:问:b", "答:问:c"]

    def test_empty_inputs(self):
        assert batch_run(make_echo_chain(), []) == []

    def test_single_input(self):
        chain = make_echo_chain("{review}", lambda s: f"已分析:{s}")
        assert batch_run(chain, [{"review": "物流很快"}]) == ["已分析:物流很快"]


# ---------- §30.7 append_turn ----------
class TestAppendTurn:
    def test_empty(self):
        assert append_turn([], "你好", "你好呀") == [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
        ]

    def test_appends_to_history(self):
        hist = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
        result = append_turn(hist, "q2", "a2")
        assert len(result) == 4
        assert result[-2] == {"role": "user", "content": "q2"}
        assert result[-1] == {"role": "assistant", "content": "a2"}

    def test_does_not_mutate_input(self):
        hist = [{"role": "user", "content": "q1"}]
        append_turn(hist, "u", "a")
        assert hist == [{"role": "user", "content": "q1"}]


# ---------- §30.7 format_history ----------
class TestFormatHistory:
    def test_empty(self):
        assert format_history([]) == ""

    def test_one_turn(self):
        hist = [{"role": "user", "content": "有货吗"}, {"role": "assistant", "content": "有的"}]
        assert format_history(hist) == "用户:有货吗\n客服:有的\n"

    def test_two_turns(self):
        hist = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]
        assert format_history(hist) == "用户:q1\n客服:a1\n用户:q2\n客服:a2\n"


# ---------- §30.8 chat_once(综合) ----------
def repeat_question_model():
    """FakeModel:复读 prompt 里最后一个「用户问:」之后的那一行。"""
    return as_runnable(lambda s: "亲," + s.rsplit("用户问:", 1)[-1].splitlines()[0])


class TestChatOnce:
    def test_first_turn(self):
        answer, hist = chat_once(repeat_question_model(), "有货吗", [])
        assert answer == "亲,有货吗"
        assert hist == [
            {"role": "user", "content": "有货吗"},
            {"role": "assistant", "content": "亲,有货吗"},
        ]

    def test_history_is_in_prompt(self):
        # 第二轮:历史必须渲染进 prompt(模型才能「看到」之前聊过什么)
        seen = []
        model = as_runnable(lambda s: seen.append(s) or "收到")
        hist = [{"role": "user", "content": "Q1"}, {"role": "assistant", "content": "A1"}]
        answer, hist2 = chat_once(model, "Q2", hist)
        assert answer == "收到"
        assert "用户:Q1" in seen[0]
        assert "客服:A1" in seen[0]
        assert "用户问:Q2" in seen[0]
        assert len(hist2) == 4

    def test_multi_turn_accumulates(self):
        # 连聊两轮,历史逐轮累积,回答始终复读当前问题
        model = repeat_question_model()
        a1, h1 = chat_once(model, "有货吗", [])
        a2, h2 = chat_once(model, "发什么快递", h1)
        assert a1 == "亲,有货吗"
        assert a2 == "亲,发什么快递"
        assert [m["role"] for m in h2] == ["user", "assistant", "user", "assistant"]

    def test_does_not_mutate_history(self):
        hist = [{"role": "user", "content": "Q1"}]
        chat_once(repeat_question_model(), "Q2", hist)
        assert hist == [{"role": "user", "content": "Q1"}]
