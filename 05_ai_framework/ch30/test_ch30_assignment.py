"""
Ch30 作业测试。运行: uv run pytest 05_ai_framework/ch30/test_ch30_assignment.py -v
"""
from langchain_core.output_parsers import StrOutputParser

from ch30_assignment import (
    append_turn,
    as_runnable,
    build_chain,
    build_prompt,
    run_chain,
)


# ---------- build_prompt ----------
class TestBuildPrompt:
    def test_invoke_to_string(self):
        # PromptTemplate.invoke 返回 PromptValue,要 .to_string() 得到纯文本
        p = build_prompt("回答:{q}")
        assert p.invoke({"q": "你好"}).to_string() == "回答:你好"

    def test_format(self):
        # .format(...) 直接返回字符串
        assert build_prompt("{greeting},{name}").format(greeting="Hi", name="Bob") == "Hi,Bob"

    def test_returns_prompt_template(self):
        from langchain_core.prompts import PromptTemplate

        assert isinstance(build_prompt("x"), PromptTemplate)


# ---------- as_runnable ----------
class TestAsRunnable:
    def test_invoke(self):
        r = as_runnable(lambda s: s.upper())
        assert r.invoke("abc") == "ABC"

    def test_returns_runnable_lambda(self):
        from langchain_core.runnables import RunnableLambda

        assert isinstance(as_runnable(lambda x: x), RunnableLambda)

    def test_pipe_compose(self):
        # RunnableLambda 之间能用 | 串
        up = as_runnable(lambda s: s.upper())
        exclaim = as_runnable(lambda s: s + "!")
        chain = up | exclaim
        assert chain.invoke("hi") == "HI!"


# ---------- build_chain + run_chain ----------
class TestChain:
    def test_full_chain(self):
        p = build_prompt("Q:{q}")
        model = as_runnable(lambda s: f"A:{s}")
        chain = build_chain(p, model, StrOutputParser())
        assert run_chain(chain, {"q": "你好"}) == "A:Q:你好"

    def test_chain_without_parser(self):
        p = build_prompt("Q:{q}")
        model = as_runnable(lambda s: f"A:{s}")
        chain = build_chain(p, model, StrOutputParser())
        assert "Q:你好" in run_chain(chain, {"q": "你好"})

    def test_chain_is_runnable(self):
        from langchain_core.runnables import Runnable

        p = build_prompt("{q}")
        chain = build_chain(p, as_runnable(lambda s: s), StrOutputParser())
        assert isinstance(chain, Runnable)

    def test_model_echo(self):
        p = build_prompt("{q}")
        model = as_runnable(lambda s: f"<{s}>")
        chain = build_chain(p, model, StrOutputParser())
        assert run_chain(chain, {"q": "x"}) == "<x>"

    def test_multi_step_model(self):
        # model 内部做点处理(replace)
        p = build_prompt("翻译:{q}")
        model = as_runnable(lambda s: s.replace("翻译:", "[EN] "))
        chain = build_chain(p, model, StrOutputParser())
        assert run_chain(chain, {"q": "苹果"}) == "[EN] 苹果"


# ---------- append_turn ----------
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
        hist = []
        append_turn(hist, "u", "a")
        assert hist == []
