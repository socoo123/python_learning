"""
Ch33 作业测试。运行: uv run pytest 05_ai_framework/ch33/test_ch33_assignment.py -v

用 FastAPI 的 TestClient（基于 httpx）测自己的 API，不用起服务。
**全部离线**：通过 app.dependency_overrides 注入假 LLM，不调真 SDK。

⚠️ 测试卫生：REQUEST_LEDGER / CHAT_CACHE / dependency_overrides 都是全局状态，
autouse fixture 在每个用例前后清理，保证用例互不污染（§33.8 的坑 ③④）。
"""
import pytest
from fastapi.testclient import TestClient

import ch33_assignment
from ch33_assignment import (
    CHAT_CACHE,
    RATE_LIMIT,
    REQUEST_LEDGER,
    EchoLLM,
    allow_request,
    app,
    chat_logic,
    chat_with_cache,
    estimate_tokens,
    get_llm,
)

client = TestClient(app)


# ---------- 假 LLM（测试专用，只暴露 ask 方法）----------
class _MockLLM:
    """假 LLM：返回 MOCK:{query}，并记录每次调用，方便断言「到底调没调 LLM」。"""

    def __init__(self):
        self.calls = []

    def ask(self, query: str) -> str:
        self.calls.append(query)
        return f"MOCK:{query}"


@pytest.fixture(autouse=True)
def _clean_global_state():
    """每个用例前后重置全局状态：限流账本、缓存、依赖覆盖（防用例互相污染）。"""
    REQUEST_LEDGER.clear()
    CHAT_CACHE.clear()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm():
    """注入假 LLM 并返回它（断言 mock_llm.calls 可验证 LLM 到底被调了几次）。"""
    fake = _MockLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    return fake


# ========== §33.3 get_llm（依赖）==========
class TestGetLlm:
    def test_default_returns_echo_llm(self):
        assert isinstance(get_llm(), EchoLLM)

    def test_default_llm_asks(self):
        assert get_llm().ask("在吗") == "echo:在吗"

    def test_dependency_overrides_replaces_it(self):
        # 核心机制：dependency_overrides 能换掉 get_llm 的返回值
        fake = _MockLLM()
        app.dependency_overrides[get_llm] = lambda: fake
        overridden = app.dependency_overrides[get_llm]()
        assert overridden is fake
        assert overridden.ask("q") == "MOCK:q"


# ========== §33.4 estimate_tokens（成本估算）==========
class TestEstimateTokens:
    def test_empty_string_minimum_one(self):
        # 边界：空文本保底 1（防漏账/除零）
        assert estimate_tokens("") == 1

    def test_single_char_minimum_one(self):
        # 边界：1 字符 // 2 = 0 → 保底 1
        assert estimate_tokens("好") == 1

    def test_two_chars_one_token(self):
        assert estimate_tokens("你好") == 1

    def test_seven_chars_three_tokens(self):
        assert estimate_tokens("echo:你好") == 3

    def test_eight_chars_four_tokens(self):
        assert estimate_tokens("机械键盘还有货吗") == 4

    def test_thirteen_chars_six_tokens(self):
        assert estimate_tokens("echo:机械键盘还有货吗") == 6

    def test_odd_length_floors(self):
        # 奇数长度向下取整：3→1，5→2（拦硬编码/错写成 ceil 的实现）
        assert estimate_tokens("abc") == 1
        assert estimate_tokens("abcde") == 2


# ========== §33.5 chat_logic（逻辑层，纯函数）==========
class TestChatLogic:
    def test_with_echo_llm(self):
        assert chat_logic(EchoLLM(), "你好") == {"reply": "echo:你好", "tokens": 3}

    def test_with_echo_llm_longer_query(self):
        assert chat_logic(EchoLLM(), "机械键盘还有货吗") == {
            "reply": "echo:机械键盘还有货吗",
            "tokens": 6,
        }

    def test_with_mock_llm(self):
        assert chat_logic(_MockLLM(), "hi") == {"reply": "MOCK:hi", "tokens": 3}

    def test_llm_received_exact_query(self):
        fake = _MockLLM()
        chat_logic(fake, "保修多久")
        assert fake.calls == ["保修多久"]

    def test_result_has_reply_and_tokens_keys(self):
        result = chat_logic(EchoLLM(), "x")
        assert set(result.keys()) == {"reply", "tokens"}


# ========== §33.6 chat_with_cache（缓存）==========
class TestChatWithCache:
    def test_first_call_miss_calls_llm(self):
        fake = _MockLLM()
        result = chat_with_cache(fake, "你好", {})
        assert result == {"reply": "MOCK:你好", "tokens": 3, "cached": False}
        assert fake.calls == ["你好"]

    def test_second_call_hits_cache_without_llm(self):
        fake = _MockLLM()
        cache = {}
        chat_with_cache(fake, "你好", cache)
        result = chat_with_cache(fake, "你好", cache)
        assert result == {"reply": "MOCK:你好", "tokens": 3, "cached": True}
        # 关键断言：第二次没调 LLM（省钱就省在这）
        assert fake.calls == ["你好"]

    def test_cache_stores_pure_result_without_cached_flag(self):
        # 缓存里只存 {"reply","tokens"}，不含 cached 元信息
        fake = _MockLLM()
        cache = {}
        chat_with_cache(fake, "你好", cache)
        assert cache["你好"] == {"reply": "MOCK:你好", "tokens": 3}
        assert "cached" not in cache["你好"]

    def test_different_queries_miss_independently(self):
        fake = _MockLLM()
        cache = {}
        r1 = chat_with_cache(fake, "你好", cache)
        r2 = chat_with_cache(fake, "在吗", cache)
        assert r1["cached"] is False
        assert r2["cached"] is False
        assert fake.calls == ["你好", "在吗"]

    def test_empty_string_query_is_cacheable(self):
        # 边界：空 query 也是合法缓存键
        fake = _MockLLM()
        cache = {}
        chat_with_cache(fake, "", cache)
        result = chat_with_cache(fake, "", cache)
        assert result == {"reply": "MOCK:", "tokens": 2, "cached": True}
        assert fake.calls == [""]


# ========== §33.7 allow_request（限流）==========
class TestAllowRequest:
    def test_first_request_allowed_and_counted(self):
        ledger = {}
        assert allow_request(ledger, "u1001", 2) is True
        assert ledger == {"u1001": 1}

    def test_rejects_at_limit_and_stops_counting(self):
        ledger = {}
        assert allow_request(ledger, "u1001", 2) is True
        assert allow_request(ledger, "u1001", 2) is True
        assert allow_request(ledger, "u1001", 2) is False
        # 关键断言：被拒的请求不消耗配额（计数停在 limit）
        assert ledger == {"u1001": 2}

    def test_users_have_independent_quota(self):
        ledger = {}
        allow_request(ledger, "u1001", 1)
        assert allow_request(ledger, "u1001", 1) is False
        # 换个用户，独立配额
        assert allow_request(ledger, "u1002", 1) is True

    def test_zero_limit_rejects_everything(self):
        # 边界：limit=0 全拒，且不产生任何账目
        ledger = {}
        assert allow_request(ledger, "u1001", 0) is False
        assert ledger == {}

    def test_new_user_not_in_ledger_until_allowed(self):
        # dict.get 容错：新用户不 KeyError
        ledger = {}
        assert allow_request(ledger, "newcomer", 5) is True
        assert ledger["newcomer"] == 1


# ========== §33.8 GET /health ==========
class TestHandleHealth:
    def test_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_no_body_no_llm_required(self):
        # 健康检查零入参、零外部依赖（不注入任何 LLM 也该 200）
        resp = client.get("/health")
        assert resp.status_code == 200


# ========== §33.8 POST /chat（综合：限流→缓存→逻辑）==========
class TestHandleChat:
    def test_chat_with_default_echo_llm(self):
        resp = client.post("/chat", json={"query": "你好"})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "echo:你好", "tokens": 3, "cached": False}

    def test_chat_with_mock_llm_override(self, mock_llm):
        resp = client.post("/chat", json={"query": "hi", "user": "u1001"})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "MOCK:hi", "tokens": 3, "cached": False}
        assert mock_llm.calls == ["hi"]

    def test_second_same_query_hits_cache(self, mock_llm):
        client.post("/chat", json={"query": "保修多久"})
        resp = client.post("/chat", json={"query": "保修多久"})
        assert resp.status_code == 200
        assert resp.json()["cached"] is True
        # 第二次没调 LLM
        assert mock_llm.calls == ["保修多久"]

    def test_fourth_request_returns_429(self, mock_llm):
        # RATE_LIMIT=3：前 3 次放行，第 4 次 429（缓存命中也照样计数）
        for i in range(RATE_LIMIT):
            resp = client.post("/chat", json={"query": f"q{i}"})
            assert resp.status_code == 200
        resp = client.post("/chat", json={"query": "刷接口"})
        assert resp.status_code == 429
        assert "频繁" in resp.json()["detail"]
        # 被拒的请求没有调 LLM
        assert len(mock_llm.calls) == RATE_LIMIT

    def test_rate_limit_counts_even_cache_hits(self, mock_llm):
        # 防御纵深：同一个 query 刷 3 次（后 2 次中缓存），第 4 次仍 429
        for _ in range(3):
            client.post("/chat", json={"query": "重复"})
        assert mock_llm.calls == ["重复"]  # 只真调了 1 次
        resp = client.post("/chat", json={"query": "重复"})
        assert resp.status_code == 429

    def test_different_users_independent_quota(self, mock_llm):
        for _ in range(RATE_LIMIT):
            client.post("/chat", json={"query": "q", "user": "u1001"})
        assert client.post("/chat", json={"query": "q2", "user": "u1001"}).status_code == 429
        # u1002 配额独立，还能聊
        resp = client.post("/chat", json={"query": "q", "user": "u1002"})
        assert resp.status_code == 200

    def test_missing_query_returns_422(self, mock_llm):
        resp = client.post("/chat", json={"user": "u1001"})
        assert resp.status_code == 422
        # 校验在限流之前：422 的请求不该消耗配额
        assert REQUEST_LEDGER == {}
        assert mock_llm.calls == []

    def test_wrong_type_query_returns_422(self):
        resp = client.post("/chat", json={"query": 123})
        assert resp.status_code == 422

    def test_extra_field_ignored(self, mock_llm):
        # 多余字段默认忽略（Pydantic 行为）
        resp = client.post("/chat", json={"query": "hi", "junk": 1})
        assert resp.status_code == 200
        assert resp.json()["reply"] == "MOCK:hi"

    def test_default_user_is_guest(self, mock_llm):
        # 不传 user → 按 "guest" 计数
        for _ in range(RATE_LIMIT):
            client.post("/chat", json={"query": "q"})
        assert REQUEST_LEDGER.get("guest") == RATE_LIMIT


# ========== §33.9 POST /chat/stream（SSE 流式）==========
class TestHandleChatStream:
    def test_content_type_is_event_stream(self, mock_llm):
        resp = client.post("/chat/stream", json={"query": "hi"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_body_is_char_by_char_sse_frames(self, mock_llm):
        resp = client.post("/chat/stream", json={"query": "hi"})
        body = resp.text
        # MOCK:hi 逐字成帧
        assert body.startswith("data: M\n\n")
        assert "data: h\n\n" in body
        assert "data: i\n\n" in body

    def test_body_ends_with_done_marker(self, mock_llm):
        resp = client.post("/chat/stream", json={"query": "hi"})
        assert resp.text.endswith("data: [DONE]\n\n")

    def test_frame_count_matches_text_length_plus_done(self, mock_llm):
        # "MOCK:hi" 7 字符 → 7 帧 + 1 帧 [DONE] = 8 条 "data: "
        resp = client.post("/chat/stream", json={"query": "hi"})
        assert resp.text.count("data: ") == len("MOCK:hi") + 1

    def test_stream_with_default_echo_llm(self):
        resp = client.post("/chat/stream", json={"query": "你好"})
        assert resp.status_code == 200
        # echo:你好 7 字符 → 8 帧
        assert resp.text.count("data: ") == 8
        assert "data: 你\n\n" in resp.text

    def test_stream_calls_llm_every_time(self, mock_llm):
        # 流式端点不走缓存：每次都实时生成
        client.post("/chat/stream", json={"query": "hi"})
        client.post("/chat/stream", json={"query": "hi"})
        assert mock_llm.calls == ["hi", "hi"]
