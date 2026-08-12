"""
Ch28 作业测试。运行: uv run pytest 05_ai_framework/ch28/test_ch28_assignment.py -v

全部用 FakeClient 离线测,不调真实 API,不需要 API key。
"""
import pytest

from ch28_assignment import (
    PRICING,
    build_messages,
    build_user_message,
    call_llm,
    estimate_cost,
    estimate_tokens,
    extract_text,
    generate_product_description,
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


# ---------- §28.2 extract_text ----------
class TestExtractText:
    def test_anthropic_blocks(self):
        assert extract_text(_Resp("你好")) == "你好"

    def test_multiple_blocks_joined(self):
        r = type("R", (), {"content": [_Block("指尖"), _Block("狂想")]})()
        assert extract_text(r) == "指尖狂想"

    def test_string_content(self):
        r = type("R", (), {"content": "plain"})()
        assert extract_text(r) == "plain"

    def test_string_response(self):
        assert extract_text("hi") == "hi"

    def test_dict_blocks(self):
        r = type("R", (), {"content": [{"type": "text", "text": "x"}, {"text": "y"}]})()
        assert extract_text(r) == "xy"

    def test_empty_block_text(self):
        assert extract_text(_Resp("")) == ""

    def test_mixed_object_and_dict_blocks(self):
        # 对象 block 和 dict block 混在一起也能拼
        r = type("R", (), {"content": [_Block("ab"), {"text": "cd"}]})()
        assert extract_text(r) == "abcd"


# ---------- §28.3 build_user_message ----------
class TestBuildUserMessage:
    def test_basic(self):
        assert build_user_message("你好") == {"role": "user", "content": "你好"}

    def test_empty_content(self):
        assert build_user_message("") == {"role": "user", "content": ""}

    def test_returns_new_dict_each_call(self):
        m1 = build_user_message("a")
        m2 = build_user_message("a")
        assert m1 is not m2  # 不是同一个对象

    def test_role_is_user_not_assistant(self):
        assert build_user_message("x")["role"] == "user"


# ---------- §28.4 call_llm ----------
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


# ---------- §28.5 estimate_tokens ----------
class TestEstimateTokens:
    def test_basic(self):
        assert estimate_tokens("hello world") == 2  # 11 // 4

    def test_short(self):
        assert estimate_tokens("hello") == 1  # 5 // 4

    def test_empty_is_at_least_one(self):
        assert estimate_tokens("") == 1

    def test_long(self):
        assert estimate_tokens("a" * 40) == 10

    def test_exact_multiple_of_four(self):
        assert estimate_tokens("abcd") == 1  # 4 // 4
        assert estimate_tokens("abcdefgh") == 2  # 8 // 4


# ---------- §28.5 estimate_cost ----------
class TestEstimateCost:
    def test_sonnet_pricing(self):
        # 50*3e-6 + 100*15e-6 = 0.00015 + 0.0015 = 0.00165
        cost = estimate_cost("claude-3-5-sonnet-20241022", 50, 100)
        assert cost == pytest.approx(0.00165)

    def test_haiku_cheaper_than_sonnet(self):
        same = (1000, 1000)
        assert estimate_cost("claude-3-haiku-20240307", *same) < estimate_cost(
            "claude-3-5-sonnet-20241022", *same
        )

    def test_zero_tokens_is_zero_cost(self):
        assert estimate_cost("claude-3-5-sonnet-20241022", 0, 0) == 0.0

    def test_output_more_expensive_than_input(self):
        # 同样 1000 token,输出比输入贵
        c_in = estimate_cost("claude-3-5-sonnet-20241022", 1000, 0)
        c_out = estimate_cost("claude-3-5-sonnet-20241022", 0, 1000)
        assert c_out > c_in

    def test_unknown_model_raises(self):
        with pytest.raises(KeyError):
            estimate_cost("no-such-model", 1, 1)

    def test_pricing_table_has_tuple_values(self):
        for model, prices in PRICING.items():
            assert isinstance(prices, tuple) and len(prices) == 2


# ---------- §28.6 build_messages ----------
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

    def test_multi_round_growth(self):
        # 模拟两轮对话:history 每轮 +2(user + assistant)
        h = []
        h = build_messages(h, "第1轮")
        assert len(h) == 1
        h = h + [{"role": "assistant", "content": "回复1"}]
        h = build_messages(h, "第2轮")
        assert len(h) == 3
        assert h[-1] == {"role": "user", "content": "第2轮"}


# ---------- §28.7 with_retry ----------
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
        # attempts=0 → 不调用,raise last(None) → 抛异常
        with pytest.raises(Exception):
            with_retry(lambda: 1, attempts=0)

    def test_attempts_count_exact(self):
        # 恰好 attempts 次全失败,调用次数 == attempts
        calls = {"n": 0}

        def always():
            calls["n"] += 1
            raise RuntimeError("x")

        with pytest.raises(RuntimeError):
            with_retry(always, attempts=4, errors=RuntimeError)
        assert calls["n"] == 4


# ---------- §28.8 generate_product_description(综合) ----------
class TestGenerateProductDescription:
    KB = {"name": "机械键盘", "category": "电脑外设", "price": 599.0}

    def test_returns_client_text(self):
        c = FakeClient("指尖机械狂想!")
        assert generate_product_description(c, self.KB, tone="活泼") == "指尖机械狂想!"

    def test_prompt_contains_product_info(self):
        c = FakeClient("ok")
        generate_product_description(c, self.KB, tone="文艺")
        prompt = c.calls[0]["messages"][0]["content"]
        assert "机械键盘" in prompt
        assert "电脑外设" in prompt
        assert "599" in prompt
        assert "文艺" in prompt

    def test_prompt_goes_to_user_message(self):
        c = FakeClient("ok")
        generate_product_description(c, self.KB)
        msg = c.calls[0]["messages"][0]
        assert msg["role"] == "user"

    def test_retries_on_transient_error(self):
        # 前 2 次抛错,第 3 次成功 → with_retry(attempts=3) 能扛住
        c = FakeClient("文案", raise_times=2, error=RuntimeError)
        assert generate_product_description(c, self.KB) == "文案"
        assert len(c.calls) == 3  # 调了 3 次

    def test_gives_up_after_3_failures(self):
        # 连续 5 次都失败 > attempts=3 → 抛异常
        c = FakeClient("x", raise_times=5, error=RuntimeError)
        with pytest.raises(RuntimeError):
            generate_product_description(c, self.KB)
