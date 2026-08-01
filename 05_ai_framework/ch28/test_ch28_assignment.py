"""
Ch28 作业测试。运行: uv run pytest 05_ai_framework/ch28/test_ch28_assignment.py -v

全部用 FakeClient 离线测,不调真实 API,不需要 API key。
"""
import pytest

from ch28_assignment import (
    build_messages,
    call_llm,
    estimate_tokens,
    extract_text,
    with_retry,
)


# ---------- FakeClient:模拟 anthropic 客户端 ----------
class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text):
        self.content = [_Block(text)]


class _Messages:
    def __init__(self, parent):
        self.parent = parent

    def create(self, **kwargs):
        return self.parent._create(kwargs)


class FakeClient:
    """模拟 anthropic.Anthropic 客户端。raise_times:前 N 次抛 error。"""

    def __init__(self, text="ok", raise_times=0, error=RuntimeError):
        self._text = text
        self._raise_times = raise_times
        self._error = error
        self._n = 0
        self.calls = []
        self.messages = _Messages(self)

    def _create(self, kwargs):
        self.calls.append(kwargs)
        if self._n < self._raise_times:
            self._n += 1
            raise self._error("transient boom")
        return _Resp(self._text)


# ---------- extract_text ----------
class TestExtractText:
    def test_anthropic_blocks(self):
        assert extract_text(_Resp("你好")) == "你好"

    def test_multiple_blocks_joined(self):
        r = type("R", (), {"content": [_Block("a"), _Block("b")]})()
        assert extract_text(r) == "ab"

    def test_string_content(self):
        r = type("R", (), {"content": "plain"})()
        assert extract_text(r) == "plain"

    def test_string_response(self):
        assert extract_text("hi") == "hi"

    def test_dict_blocks(self):
        r = type("R", (), {"content": [{"type": "text", "text": "x"}, {"text": "y"}]})()
        assert extract_text(r) == "xy"

    def test_empty(self):
        assert extract_text(_Resp("")) == ""


# ---------- call_llm ----------
class TestCallLlm:
    def test_returns_text(self):
        c = FakeClient("pong")
        assert call_llm(c, "你是助手", "ping") == "pong"

    def test_passes_params(self):
        c = FakeClient("ok")
        call_llm(c, "S", "U", model="claude-X", max_tokens=512)
        kw = c.calls[0]
        assert kw["model"] == "claude-X"
        assert kw["system"] == "S"
        assert kw["max_tokens"] == 512
        assert kw["messages"] == [{"role": "user", "content": "U"}]

    def test_default_model(self):
        c = FakeClient("ok")
        call_llm(c, "S", "U")
        assert "claude" in c.calls[0]["model"]

    def test_propagates_error(self):
        c = FakeClient(raise_times=99)
        with pytest.raises(RuntimeError):
            call_llm(c, "S", "U")


# ---------- build_messages ----------
class TestBuildMessages:
    def test_appends_user(self):
        hist = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        assert build_messages(hist, "再来") == [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "再来"},
        ]

    def test_empty_history(self):
        assert build_messages([], "first") == [{"role": "user", "content": "first"}]

    def test_does_not_mutate_input(self):
        hist = [{"role": "user", "content": "hi"}]
        build_messages(hist, "second")
        assert hist == [{"role": "user", "content": "hi"}]


# ---------- estimate_tokens ----------
class TestEstimateTokens:
    def test_basic(self):
        assert estimate_tokens("hello world") == 2  # 11 // 4

    def test_short(self):
        assert estimate_tokens("hello") == 1  # 5 // 4

    def test_empty_is_at_least_one(self):
        assert estimate_tokens("") == 1

    def test_long(self):
        assert estimate_tokens("a" * 40) == 10

    def test_chinese_chars(self):
        # 中文字符也算长度;这里只验证单调性
        assert estimate_tokens("你好世界Python") == len("你好世界Python") // 4


# ---------- with_retry ----------
class TestWithRetry:
    def test_succeeds_first_try(self):
        assert with_retry(lambda: 42) == 42

    def test_retries_then_succeeds(self):
        state = {"n": 0}

        def flaky():
            state["n"] += 1
            if state["n"] < 3:
                raise ValueError("not yet")
            return "ok"

        assert with_retry(flaky, attempts=5, errors=ValueError) == "ok"
        assert state["n"] == 3

    def test_all_fail_raises(self):
        def always():
            raise ValueError("nope")

        with pytest.raises(ValueError):
            with_retry(always, attempts=3, errors=ValueError)

    def test_non_matching_error_not_retried(self):
        # errors=ValueError,但抛 TypeError → 不重试,直接抛
        calls = {"n": 0}

        def boom():
            calls["n"] += 1
            raise TypeError("wrong kind")

        with pytest.raises(TypeError):
            with_retry(boom, attempts=5, errors=ValueError)
        assert calls["n"] == 1  # 没重试

    def test_zero_attempts(self):
        # attempts=0 → 不调用,raise last(None)→ 抛异常
        with pytest.raises(Exception):
            with_retry(lambda: 1, attempts=0)
