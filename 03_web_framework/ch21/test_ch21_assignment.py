"""
Ch21 作业测试。运行: uv run pytest 03_web_framework/ch21/test_ch21_assignment.py -v
"""
from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import JWTError, jwt

from ch21_assignment import (
    ALGORITHM,
    SECRET_KEY,
    USERS,
    admin_dashboard,  # noqa: F401  (路由注册到 app)
    app,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    login,  # noqa: F401
    public,  # noqa: F401
    read_current_user,  # noqa: F401
    register_user,
    require_admin,
    verify_password,
)

client = TestClient(app)


# ---------- 工具:拿 token ----------
def _login(username="alice", password="alice123") -> str:
    resp = client.post("/token", data={"username": username, "password": password})
    assert resp.status_code == 200, f"登录失败:{resp.text}"
    return resp.json()["access_token"]


# ---------- ① hash_password ----------
class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        """正常:以 $2 开头的 bcrypt 哈希串"""
        hashed = hash_password("alice123")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2")

    def test_hash_is_not_plaintext(self):
        """哈希串绝不含明文"""
        hashed = hash_password("alice123")
        assert hashed != "alice123"
        assert "alice123" not in hashed

    def test_same_password_different_hashes(self):
        """边界:同一明文两次哈希结果不同(随机盐),硬编码返回值过不了这关"""
        assert hash_password("same-pwd") != hash_password("same-pwd")


# ---------- ② verify_password ----------
class TestVerifyPassword:
    def test_correct_password_true(self):
        """正确明文 → True"""
        hashed = hash_password("s3cret!")
        assert verify_password("s3cret!", hashed) is True

    def test_wrong_password_false(self):
        """错误明文 → False(不抛异常)"""
        hashed = hash_password("s3cret!")
        assert verify_password("s3cret?", hashed) is False

    def test_broken_hash_returns_false(self):
        """边界:哈希串是垃圾字符串 → False 而不是抛异常"""
        assert verify_password("whatever", "不是哈希串") is False


# ---------- ③ register_user ----------
class TestRegisterUser:
    @pytest.fixture(autouse=True)
    def _restore_users(self):
        """每个测试后还原 USERS,避免注册的账号污染其他测试"""
        snapshot = {name: dict(u) for name, u in USERS.items()}
        yield
        USERS.clear()
        USERS.update(snapshot)

    def test_register_returns_public_info(self):
        """正常:返回用户名 + 默认角色 user,不泄露哈希"""
        result = register_user("carol", "carol888")
        assert result == {"username": "carol", "role": "user"}
        assert "password" not in result
        assert "hashed_password" not in result

    def test_register_with_admin_role(self):
        """指定角色:role='admin' 入库"""
        result = register_user("dave", "dave999", role="admin")
        assert result["role"] == "admin"
        assert USERS["dave"]["role"] == "admin"

    def test_register_stores_hash_not_plaintext(self):
        """入库的是哈希,且能被 authenticate_user 直接用(注册→登录闭环)"""
        register_user("carol", "carol888")
        stored = USERS["carol"]["hashed_password"]
        assert stored != "carol888"
        assert stored.startswith("$2")
        assert authenticate_user("carol", "carol888") is not None

    def test_register_duplicate_raises(self):
        """边界:重名 → ValueError"""
        with pytest.raises(ValueError, match="已被注册"):
            register_user("alice", "whatever")


# ---------- ④ create_access_token ----------
class TestCreateAccessToken:
    def test_token_is_three_segments(self):
        """JWT = header.payload.signature 三段,两个点"""
        token = create_access_token({"sub": "alice"})
        assert token.count(".") == 2
        assert len(token) > 30

    def test_claims_are_encoded(self):
        """sub / role / exp 都编进了 payload"""
        token = create_access_token({"sub": "alice", "role": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_input_dict_not_mutated(self):
        """边界:调用方的 dict 不被塞入 exp(要 copy)"""
        data = {"sub": "alice"}
        create_access_token(data)
        assert data == {"sub": "alice"}

    def test_expired_token_rejected_on_decode(self):
        """负的 expires_delta → 已过期 token,decode 直接抛 JWTError"""
        token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-10))
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ---------- ⑤ authenticate_user ----------
class TestAuthenticateUser:
    def test_valid_credentials_return_user(self):
        """正确账号密码 → 用户 dict(含 role)"""
        user = authenticate_user("alice", "alice123")
        assert user is not None
        assert user["username"] == "alice"
        assert user["role"] == "admin"

    def test_wrong_password_returns_none(self):
        """密码错 → None"""
        assert authenticate_user("alice", "WRONG") is None

    def test_unknown_user_returns_none(self):
        """边界:用户不存在 → None(与密码错同待遇,不暴露用户名是否存在)"""
        assert authenticate_user("nobody", "whatever") is None


# ---------- ⑥ login(POST /token)----------
class TestLogin:
    def test_login_success_returns_token(self):
        """正确账号密码 → 200 + access_token + token_type=bearer"""
        resp = client.post("/token", data={"username": "alice", "password": "alice123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"].count(".") == 2

    def test_login_token_carries_role(self):
        """签发的 token 里带 sub 和 role(为 RBAC 铺路)"""
        token = _login("bob", "bob456")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "bob"
        assert payload["role"] == "user"

    def test_login_wrong_password_401(self):
        """密码错 → 401"""
        resp = client.post("/token", data={"username": "alice", "password": "WRONG"})
        assert resp.status_code == 401

    def test_login_unknown_user_401(self):
        """用户不存在 → 401(响应体与密码错一致,不区分)"""
        resp = client.post("/token", data={"username": "nobody", "password": "whatever"})
        assert resp.status_code == 401
        wrong_pwd = client.post("/token", data={"username": "alice", "password": "WRONG"})
        assert resp.json() == wrong_pwd.json()

    def test_login_401_has_bearer_challenge(self):
        """401 必须带 WWW-Authenticate: Bearer(OAuth2 规范)"""
        resp = client.post("/token", data={"username": "alice", "password": "WRONG"})
        assert resp.headers.get("www-authenticate", "").lower() == "bearer"

    def test_login_with_json_body_rejected(self):
        """边界:OAuth2 密码流吃表单不吃 JSON → 422"""
        resp = client.post("/token", json={"username": "alice", "password": "alice123"})
        assert resp.status_code == 422


# ---------- ⑦ get_current_user(直接传 token 调用,绕过 Depends)----------
class TestGetCurrentUser:
    def test_valid_token_returns_user(self):
        """有效 token → {"username", "role"}"""
        token = _login()
        user = get_current_user(token=token)
        assert user == {"username": "alice", "role": "admin"}

    def test_garbage_token_401(self):
        """乱写的 token → HTTPException(401)"""
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="not.a.valid.token")
        assert exc.value.status_code == 401

    def test_tampered_signature_401(self):
        """篡改签名 → 验签失败 → 401"""
        token = _login()
        tampered = token[:-2] + "XX"
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=tampered)
        assert exc.value.status_code == 401

    def test_expired_token_401(self):
        """过期 token → 401(decode 自动查 exp)"""
        token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-10))
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=token)
        assert exc.value.status_code == 401

    def test_token_of_deleted_user_401(self):
        """边界:token 合法但 sub 指向不存在的用户(账号被注销)→ 401"""
        token = create_access_token({"sub": "ghost"})
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=token)
        assert exc.value.status_code == 401


# ---------- ⑧ read_current_user(GET /me)----------
class TestReadCurrentUser:
    def test_me_with_valid_token(self):
        """带 token → 200 + 当前用户"""
        token = _login()
        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == {"username": "alice", "role": "admin"}

    def test_me_without_token_401(self):
        """不带 Authorization 头 → 401(oauth2_scheme 自动拦)"""
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_me_with_tampered_token_401(self):
        """篡改 token → 401"""
        token = _login()
        resp = client.get("/me", headers={"Authorization": f"Bearer {token[:-2]}XX"})
        assert resp.status_code == 401

    def test_me_wrong_scheme_401(self):
        """边界:Authorization 用 Basic 而非 Bearer → 401"""
        token = _login()
        resp = client.get("/me", headers={"Authorization": f"Basic {token}"})
        assert resp.status_code == 401


# ---------- ⑨ require_admin ----------
class TestRequireAdmin:
    def test_admin_passes(self):
        """admin → 原样放行"""
        user = {"username": "alice", "role": "admin"}
        assert require_admin(current_user=user) == user

    def test_non_admin_403(self):
        """普通用户 → HTTPException(403),不是 401"""
        with pytest.raises(HTTPException) as exc:
            require_admin(current_user={"username": "bob", "role": "user"})
        assert exc.value.status_code == 403


# ---------- ⑩ admin_dashboard(GET /admin/stats)----------
class TestAdminDashboard:
    def test_admin_can_access(self):
        """alice(admin)→ 200,返回总账号数 + 操作人"""
        token = _login("alice", "alice123")
        resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["admin"] == "alice"
        assert body["total_users"] == len(USERS)

    def test_normal_user_403(self):
        """bob(user)→ 403:已认证但权限不足"""
        token = _login("bob", "bob456")
        resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_no_token_401(self):
        """不带 token → 401(在 get_current_user 层就被拦,走不到 require_admin)"""
        resp = client.get("/admin/stats")
        assert resp.status_code == 401


# ---------- 公开端点对比 ----------
class TestPublicEndpoint:
    def test_public_no_auth_needed(self):
        """公开端点无需 token"""
        resp = client.get("/public")
        assert resp.status_code == 200
        assert "message" in resp.json()
