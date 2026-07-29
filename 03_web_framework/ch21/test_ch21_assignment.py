"""
Ch21 作业测试。运行: uv run pytest 03_web_framework/ch21/test_ch21_assignment.py -v
"""
from fastapi.testclient import TestClient

from ch21_assignment import (
    create_access_token,
    app,
    hash_password,
    verify_password,
)


client = TestClient(app)


# ---------- 密码哈希 ----------
class TestPasswordHashing:
    def test_hash_and_verify_ok(self):
        """正确明文 → verify 返 True"""
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self):
        """错误明文 → verify 返 False(不抛异常)"""
        hashed = hash_password("secret123")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_not_plaintext(self):
        """哈希串不等于明文(bcrypt 带 salt,每次结果不同)"""
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        # 同一明文两次哈希结果不同(salt 随机)
        assert hash_password("secret123") != hashed

    def test_hash_has_bcrypt_prefix(self):
        """bcrypt 哈希串以 $2 开头"""
        assert hash_password("x").startswith("$2")


# ---------- 生成 JWT ----------
class TestCreateToken:
    def test_token_is_three_segments(self):
        """JWT 由 header.payload.signature 三段组成(用 . 分隔)"""
        token = create_access_token({"sub": "alice"})
        assert token.count(".") == 2          # 三段 → 两个点
        assert len(token) > 30

    def test_token_contains_subject(self):
        """sub claim 编进了 token(解出来能对上)"""
        from jose import jwt
        from ch21_assignment import SECRET_KEY, ALGORITHM

        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"
        assert "exp" in payload               # 过期时间也进去了


# ---------- 登录端点 POST /token ----------
class TestLogin:
    def test_login_success_returns_token(self):
        """正确账号密码 → 200 + access_token + token_type bearer"""
        resp = client.post(
            "/token",
            data={"username": "alice", "password": "alice123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert "access_token" in body
        assert body["access_token"].count(".") == 2

    def test_login_wrong_password_401(self):
        """密码错 → 401"""
        resp = client.post(
            "/token",
            data={"username": "alice", "password": "WRONG"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user_401(self):
        """用户不存在 → 401"""
        resp = client.post(
            "/token",
            data={"username": "nobody", "password": "whatever"},
        )
        assert resp.status_code == 401

    def test_login_401_has_bearer_challenge(self):
        """401 响应带 WWW-Authenticate: Bearer(OAuth2 规范)"""
        resp = client.post(
            "/token",
            data={"username": "alice", "password": "WRONG"},
        )
        assert resp.headers.get("www-authenticate", "").lower() == "bearer"


# ---------- 受保护端点 GET /me ----------
class TestProtectedEndpoint:
    def _get_token(self, username="alice", password="alice123"):
        resp = client.post("/token", data={"username": username, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    def test_me_with_valid_token(self):
        """带正确 token → 200 + 当前用户名"""
        token = self._get_token()
        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user"] == "alice"

    def test_me_without_token_401(self):
        """不带 Authorization 头 → 401"""
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_me_with_bad_token_401(self):
        """乱写的 token → 401(decode 失败)"""
        resp = client.get("/me", headers={"Authorization": "Bearer not.a.valid.token"})
        assert resp.status_code == 401

    def test_me_with_tampered_token_401(self):
        """签名被篡改 → 401"""
        token = self._get_token()
        # 篡改最后一段(signature)
        tampered = token[:-2] + "XX"
        resp = client.get("/me", headers={"Authorization": f"Bearer {tampered}"})
        assert resp.status_code == 401

    def test_me_wrong_scheme_401(self):
        """Authorization 用非 Bearer scheme → 401"""
        token = self._get_token()
        resp = client.get("/me", headers={"Authorization": f"Basic {token}"})
        assert resp.status_code == 401


# ---------- 公开端点对比 ----------
class TestPublicEndpoint:
    def test_public_no_auth_needed(self):
        """公开端点无需 token"""
        resp = client.get("/public")
        assert resp.status_code == 200
        assert "message" in resp.json()
