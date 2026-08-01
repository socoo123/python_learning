"""
Ch33 作业测试。运行: uv run pytest 05_ai_framework/ch33/test_ch33_assignment.py -v

用 FastAPI 的 TestClient(基于 httpx)测自己的 API,不用起服务。
**全部离线**:通过 app.dependency_overrides 注入假 LLM,不调真 SDK。
"""
import pytest
from fastapi.testclient import TestClient

import ch33_assignment
from ch33_assignment import ChatRequest, EchoLLM, app, chat_logic, get_llm, handle_health

client = TestClient(app)


# ---------- 假 LLM(测试专用,只暴露 ask 方法)----------
class _MockLLM:
    """假 LLM:返回 MOCK:{query},用于覆盖真 LLM。"""

    def __init__(self):
        self.calls = []          # 记录调用,方便断言

    def ask(self, query: str) -> str:
        self.calls.append(query)
        return f"MOCK:{query}"


@pytest.fixture
def mock_llm():
    """注入假 LLM 并在用例结束后清理 dependency_overrides(重要:避免污染其他用例)。"""
    fake = _MockLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.clear()        # teardown


# ========== §33.1 EchoLLM(默认离线 LLM)==========
class TestEchoLLM:
    def test_ask_returns_echo_prefix(self):
        assert EchoLLM().ask("你好") == "echo:你好"

    def test_ask_empty(self):
        assert EchoLLM().ask("") == "echo:"

    def test_ask_is_duck_typed(self):
        # 只要带 ask 方法就行——这就是后面能注入 _MockLLM 的基础
        e = EchoLLM()
        assert callable(e.ask)


# ========== §33.2 ChatRequest(Pydantic 校验)==========
class TestChatRequest:
    def test_valid_request(self):
        r = ChatRequest(query="hi")
        assert r.query == "hi"
        assert r.max_tokens == 1024       # 默认值

    def test_custom_max_tokens(self):
        r = ChatRequest(query="hi", max_tokens=512)
        assert r.max_tokens == 512

    def test_missing_query_raises(self):
        # Pydantic v2 抛 ValidationError
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(max_tokens=100)


# ========== §33.3 get_llm(依赖)==========
class TestGetLlm:
    def test_default_returns_echo_llm(self):
        llm = get_llm()
        assert isinstance(llm, EchoLLM)

    def test_default_llm_asks(self):
        # 默认实例能调 ask
        assert get_llm().ask("x") == "echo:x"

    def test_dependency_overrides_replaces_it(self):
        # 核心机制:dependency_overrides 能换掉 get_llm 的返回值
        fake = _MockLLM()
        app.dependency_overrides[get_llm] = lambda: fake
        try:
            # 模拟 FastAPI 调依赖的方式:直接 override 字典查
            overridden = app.dependency_overrides[get_llm]()
            assert overridden is fake
            assert overridden.ask("q") == "MOCK:q"
        finally:
            app.dependency_overrides.clear()


# ========== §33.4 chat_logic(核心逻辑,纯函数)==========
class TestChatLogic:
    def test_with_echo_llm(self):
        assert chat_logic(EchoLLM(), "你好") == {"reply": "echo:你好"}

    def test_with_mock_llm(self):
        assert chat_logic(_MockLLM(), "hi") == {"reply": "MOCK:hi"}

    def test_returns_dict_with_reply_key(self):
        result = chat_logic(EchoLLM(), "x")
        assert isinstance(result, dict)
        assert "reply" in result

    def test_llm_received_query(self):
        fake = _MockLLM()
        chat_logic(fake, "ping")
        assert fake.calls == ["ping"]     # 逻辑层确实把 query 传给了 llm


# ========== §33.5 GET /health ==========
class TestHealthEndpoint:
    def test_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_no_body_required(self):
        # 健康检查不该需要任何入参
        resp = client.get("/health")
        assert resp.status_code == 200


# ========== §33.5 POST /chat(集成,过 TestClient)==========
class TestChatEndpoint:
    def test_chat_with_mock_llm(self, mock_llm):
        # 注入假 LLM,POST /chat 应拿到 MOCK:hi
        resp = client.post("/chat", json={"query": "hi"})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "MOCK:hi"}

    def test_chat_passes_query_to_llm(self, mock_llm):
        client.post("/chat", json={"query": "你好"})
        assert mock_llm.calls == ["你好"]

    def test_chat_default_echo_llm_without_override(self):
        # 不覆盖 → 用默认 EchoLLM → echo:
        resp = client.post("/chat", json={"query": "x"})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "echo:x"}

    def test_missing_query_returns_422(self, mock_llm):
        # 缺必填字段 query → Pydantic 校验失败 → 422(不是 400)
        resp = client.post("/chat", json={})
        assert resp.status_code == 422

    def test_wrong_type_returns_422(self, mock_llm):
        # query 必须是 str,传 int → 422
        resp = client.post("/chat", json={"query": 123})
        assert resp.status_code == 422

    def test_extra_field_ignored(self, mock_llm):
        # 多余字段被忽略(默认 Pydantic 行为)
        resp = client.post("/chat", json={"query": "hi", "junk": 1})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "MOCK:hi"}

    def test_override_cleared_does_not_leak(self):
        # 验证 fixture teardown 干净:上一用例的 override 不该残留
        # 这条放在最后跑(类内顺序),此时 dependency_overrides 应为空
        assert get_llm not in app.dependency_overrides


# ========== §33.7 SSE 流式(进阶,可选——若实现则测)==========
class TestChatStreamEndpoint:
    def test_stream_returns_event_stream(self, mock_llm):
        resp = client.post("/chat/stream", json={"query": "hi"})
        # 流式响应的 content-type 是 text/event-stream
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_stream_body_has_data_chunks(self, mock_llm):
        resp = client.post("/chat/stream", json={"query": "hi"})
        # MockLLM 返回 "MOCK:hi",逐字 yield,每个 chunk 形如 "data: x\n\n"
        body = resp.text
        assert "data: " in body
        # 至少包含原文本里的每个字符(M/O/C/K/:/h/i 中的若干)
        assert "h" in body and "i" in body
