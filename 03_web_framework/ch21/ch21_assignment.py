"""
Ch21 作业:认证授权 JWT —— 给「极客商城运营后台」加门禁。

场景:商城后台有两类员工——运营(alice,admin 角色)和客服(bob,user 角色)。
你要实现完整的「注册 → 登录发 JWT → 受保护接口验 token → 管理员专属接口」闭环。

你填十处(按依赖顺序,建议从上到下做):
  ① hash_password          —— bcrypt 哈希明文密码
  ② verify_password        —— bcrypt 验证明文 vs 哈希
  ③ register_user          —— 注册新账号:重名检查 + 哈希入库(复用 ①)
  ④ create_access_token    —— jose.jwt.encode 生成带 exp 的 JWT
  ⑤ authenticate_user      —— 登录前置:查用户 + 验密码(复用 ②)
  ⑥ login                  —— POST /token:OAuth2 密码流,验密码发 token(复用 ⑤④)
  ⑦ get_current_user       —— 鉴权依赖:decode 验签 + 查 exp,返回当前用户
  ⑧ read_current_user      —— GET /me:Depends(get_current_user) 受保护端点
  ⑨ require_admin          —— RBAC 依赖:嵌套 get_current_user,非 admin → 403
  ⑩ admin_dashboard        —— GET /admin/stats:管理员专属端点(复用 ⑨)

    uv sync --extra web
    uv run pytest 03_web_framework/ch21/test_ch21_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

⚠️ 安全提示:SECRET_KEY 这里演示硬编码,【生产从环境变量读,绝不硬编码】。
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

app = FastAPI(title="极客商城运营后台 · JWT 认证授权")

# ---------- 配置(演示用,生产从环境变量读)----------
SECRET_KEY = "demo-secret-key"          # ⚠️ 生产:os.environ["SECRET_KEY"],绝不硬编码
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ---------- 密码哈希上下文(已配好,了解即可)----------
#
# 设计说明:业界老教程常用 passlib 的 CryptContext(schemes=["bcrypt"]),
# 但 passlib 1.7.4 自 2020 年起未再更新,与新版 bcrypt(>=4.1)存在兼容性问题
# (passlib 内部探测 bug 在 bcrypt 5 上直接抛 ValueError)。因此本章直接用官方 bcrypt 库,
# 套一个与 passlib 同方法名的薄封装 —— 换底层时业务代码零改动。
class CryptContext:
    """bcrypt 密码哈希的薄封装,对外只暴露 hash() / verify() 两个方法。
    对应 passlib.CryptContext 的最小子集,方便记忆与迁移。"""

    def hash(self, password: str) -> str:
        # bcrypt 吃 bytes 不吃 str;gensalt() 生成随机盐(每次不同 → 同密码哈希也不同)
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False                      # 哈希串格式坏 → 验证失败,不抛异常


pwd_context = CryptContext()

# ---------- OAuth2 密码流:声明「登录入口是 POST /token」(已配好)----------
# oauth2_scheme 是个依赖:请求带 Authorization: Bearer <token> → 提取 token;
# 没带 → 自动 401 + WWW-Authenticate: Bearer 响应头。tokenUrl 主要给 Swagger UI 用。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------- 用户存储(内存 demo,生产换数据库。两个种子账号:运营 alice / 客服 bob)----------
USERS: dict[str, dict] = {
    "alice": {"username": "alice", "hashed_password": pwd_context.hash("alice123"), "role": "admin"},
    "bob": {"username": "bob", "hashed_password": pwd_context.hash("bob456"), "role": "user"},
}


# ---------- ① 密码哈希:bcrypt(§21.2)----------


def hash_password(password: str) -> str:
    """
    【bcrypt 哈希 · §21.2】把明文密码哈希成可入库的字符串。

    任务:return pwd_context.hash(password)

    示例:
        hash_password("alice123")   -> "$2b$12$KIXQ..."  (以 $2 开头的 bcrypt 串)
        hash_password("alice123")   -> 再调一次结果不同(随机盐:同密码 ≠ 同哈希)

    提示:一行 return。bcrypt 故意慢(cost=12 约 250ms),这是防暴力破解的设计。
    """
    # TODO: return pwd_context.hash(password)
    ...


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    【bcrypt 验证 · §21.2】验证明文密码是否匹配哈希串。

    任务:return pwd_context.verify(plain_password, hashed_password)

    示例:
        verify_password("alice123", hash_password("alice123"))  -> True
        verify_password("wrong",     hash_password("alice123")) -> False
        verify_password("x", "这不是哈希串")                      -> False(不抛异常)

    提示:一行 return。封装内部已把「哈希串格式坏」兜成 False。
    """
    # TODO: return pwd_context.verify(plain_password, hashed_password)
    ...


# ---------- ② 注册:重名检查 + 哈希入库(§21.2,复用 ①)----------


def register_user(username: str, password: str, role: str = "user") -> dict:
    """
    【注册新账号 · §21.2】运营给新同事开后台账号:重名报错,否则哈希入库。

    任务:
      ① username 已在 USERS → raise ValueError(f"用户名 {username} 已被注册")
      ② 否则把 {"username": username, "hashed_password": hash_password(password), "role": role}
         存进 USERS[username]
      ③ 返回 {"username": username, "role": role}(绝不返回哈希/明文)

    示例:
        register_user("carol", "carol888")            -> {"username": "carol", "role": "user"}
        register_user("dave", "dave999", role="admin") -> {"username": "dave", "role": "admin"}
        register_user("alice", "xxx")                 -> 抛 ValueError(已存在)

    提示:入库的必须是 hash_password(password) 的哈希串,明文落库 = 重大安全事故(§21.2)。
    """
    # TODO: 重名 → ValueError;否则 USERS[username] = {...哈希入库...} → 返回 {"username","role"}
    ...


# ---------- ③ 生成 JWT(§21.3)----------


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    【生成 JWT · §21.3】把用户信息编码成 JWT 字符串,默认 30 分钟过期。

    任务:
      ① to_encode = data.copy()(别改调用方的 dict)
      ② expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
      ③ to_encode.update({"exp": expire})            —— 注入标准过期 claim
      ④ return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    示例:
        create_access_token({"sub": "alice", "role": "admin"})  -> "eyJhbGciOi...三段点分串"
        jwt.decode(上面的token, SECRET_KEY, algorithms=[ALGORITHM])["sub"] -> "alice"
        create_access_token({"sub": "x"}, timedelta(seconds=-1)) -> 已过期的 token(decode 即抛 JWTError)

    提示:datetime.now(timezone.utc) 必须带时区;naive datetime 会埋过期判定的坑(§21.3)。
    """
    # TODO: copy data → 算 expire(aware UTC)→ update({"exp": expire}) → jwt.encode(..., SECRET_KEY, algorithm=ALGORITHM)
    ...


# ---------- ④ 登录前置:验证账号密码(§21.4,复用 ②)----------


def authenticate_user(username: str, password: str) -> dict | None:
    """
    【验证账号密码 · §21.4】用户不存在或密码错 → None;否则返回用户 dict。

    任务:
      ① user = USERS.get(username)
      ② user is None 或 verify_password(password, user["hashed_password"]) 为 False → return None
      ③ 否则 return user

    示例:
        authenticate_user("alice", "alice123") -> {"username": "alice", "role": "admin", ...}
        authenticate_user("alice", "WRONG")    -> None
        authenticate_user("nobody", "xxx")     -> None

    提示:用户不存在和密码错都返 None —— 对外只报「用户名或密码错误」,
         不区分哪种错,避免暴露「哪些用户名已注册」(§21.4)。
    """
    # TODO: USERS.get → 不存在/密码错返 None,否则返 user
    ...


# ---------- ⑤ 登录端点:发 token(§21.4,复用 ④③)----------


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    【登录发 token · §21.4】OAuth2 密码流:收表单 username/password,验密码,发 JWT。

    任务:
      ① user = authenticate_user(form_data.username, form_data.password)
      ② user is None → raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="用户名或密码错误",
             headers={"WWW-Authenticate": "Bearer"},      # OAuth2 规范要求的挑战头
         )
      ③ token = create_access_token({"sub": user["username"], "role": user["role"]})
      ④ return {"access_token": token, "token_type": "bearer"}

    示例(TestClient 视角):
        POST /token  data={"username":"alice","password":"alice123"} -> 200 + access_token
        POST /token  data={"username":"alice","password":"WRONG"}    -> 401

    提示:OAuth2 密码流规定用表单(application/x-www-form-urlencoded)提交,不是 JSON;
         form_data.username / form_data.password 直接取。
    """
    # TODO: authenticate_user → None 则 401(带 WWW-Authenticate: Bearer);
    #       否则 create_access_token({"sub","role"}) → 返回 {"access_token","token_type":"bearer"}
    ...


# ---------- ⑥ 鉴权依赖:解析 + 验证 token(§21.5)----------


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    【鉴权依赖 · §21.5】decode token(自动验签名 + 查 exp),返回当前用户 dict;失败 401。

    任务:
      ① try: payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      ② username = payload.get("sub");为 None 或不在 USERS → 抛 401(带 WWW-Authenticate: Bearer)
      ③ return {"username": username, "role": USERS[username]["role"]}
      ④ except JWTError → 同样抛 401(过期 / 签名错 / 格式错都会被 decode 抛成 JWTError)

    示例:
        get_current_user(有效token)            -> {"username": "alice", "role": "admin"}
        get_current_user("乱写的token")         -> 抛 HTTPException(401)
        get_current_user(已过期token)          -> 抛 HTTPException(401)

    提示:except JWTError 里 raise ... from None,别把原始异常链暴露给客户端。
         依赖里 raise HTTPException 会让 FastAPI 短路 —— 端点函数根本不会执行。
    """
    # TODO: try jwt.decode → 取 sub → None/不在 USERS 则 401 → 返回 {"username","role"};
    #       except JWTError → 401 (from None)
    ...


# ---------- ⑦ 受保护端点:看当前登录用户(§21.5,复用 ⑥)----------


@app.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    """
    【受保护端点 · §21.5】返回当前登录用户信息。鉴权全靠依赖,函数体只有一行。

    任务:return current_user

    示例(TestClient 视角):
        GET /me  带 Authorization: Bearer <有效token> -> 200 {"username":"alice","role":"admin"}
        GET /me  不带 token / token 被篡改 / 已过期     -> 401

    提示:函数体真的只有 return current_user —— 鉴权逻辑全在 get_current_user 里,
         依赖链短路,这个函数体只在 token 合法时才会执行(§21.5)。
    """
    # TODO: return current_user
    ...


# ---------- ⑧ RBAC:管理员专属依赖 + 端点(§21.5,复用 ⑥)----------


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    【RBAC 授权依赖 · §21.5】在 get_current_user 之上再叠一层:非 admin → 403。

    任务:
      ① current_user["role"] != "admin" → raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
      ② 否则 return current_user

    示例:
        require_admin({"username": "alice", "role": "admin"}) -> 原样返回
        require_admin({"username": "bob", "role": "user"})    -> 抛 HTTPException(403)

    提示:401 = 没认证(你是谁?);403 = 已认证但没权限(我知道你是谁,但你不够格)。
         依赖嵌套依赖:require_admin → get_current_user → oauth2_scheme,逐层加码。
    """
    # TODO: role != "admin" → HTTPException(403);否则 return current_user
    ...


@app.get("/admin/stats")
def admin_dashboard(admin: dict = Depends(require_admin)):
    """
    【管理员专属端点 · §21.5】运营周报要看后台概览:总账号数 + 谁在看。

    任务:return {"total_users": len(USERS), "admin": admin["username"]}

    示例(TestClient 视角):
        GET /admin/stats  带 alice(admin) 的 token -> 200 {"total_users": 2, "admin": "alice"}
        GET /admin/stats  带 bob(user) 的 token    -> 403
        GET /admin/stats  不带 token               -> 401(在 get_current_user 那层就被拦了)

    提示:函数体一行 return。一层依赖管「你是谁」,一层依赖管「你够不够格」—— 组合而非 if 堆叠。
    """
    # TODO: return {"total_users": len(USERS), "admin": admin["username"]}
    ...


# ---------- 公开端点(对比用,已实现)----------


@app.get("/public")
def public():
    """公开端点,任何请求都能访问。对比 /me 与 /admin/stats 必须带 token。"""
    return {"message": "商城公告:618 大促筹备中"}
