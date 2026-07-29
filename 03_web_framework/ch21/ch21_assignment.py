"""
Ch21 作业:认证授权 JWT。

五处填空:① hash_password / verify_password(bcrypt)
② create_access_token(jose.jwt.encode)③ 登录端点 POST /token(验密码、发 token)
④ get_current_user(依赖注入,decode 验 token)
⑤ 受保护端点 GET /me(依赖 get_current_user)。

    uv run pytest 03_web_framework/ch21/test_ch21_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

⚠️ 安全提示:SECRET_KEY 这里是演示硬编码,【生产从环境变量读,绝不硬编码】。
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

app = FastAPI(title="JWT 认证授权演示")


# ---------- 配置(演示用,生产从环境变量读)----------
SECRET_KEY = "demo-secret-key"          # ⚠️ 生产:os.environ["SECRET_KEY"],绝不硬编码
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ---------- 密码哈希上下文(已配好,了解即可)----------
#
# 设计说明:业界老教程常用 passlib 的 CryptContext(schemes=["bcrypt"]),
# 但 passlib 1.7.4 自 2020 年起未再更新,与新版 bcrypt(>=4.1)存在兼容性问题
# (passlib 内部探测 bug 在 bcrypt 5 上直接抛错)。因此本教程直接用官方 bcrypt 库。
# 若你的项目仍用 passlib,下面 hash_password / verify_password 两个函数的调用方式
# 几乎一致:pwd_context.hash(p) / pwd_context.verify(p, h) —— 换底层即可。
class CryptContext:
    """bcrypt 密码哈希的薄封装,对外只暴露 hash() / verify() 两个方法。
    对应 passlib.CryptContext 的最小子集,方便记忆。"""

    def hash(self, password: str) -> str:
        # bcrypt 要 bytes;gensalt() 生成随机盐(每次不同 → 同密码哈希也不同)
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False                      # 哈希串格式坏 → 验证失败,不抛异常


pwd_context = CryptContext()


# ---------- OAuth2 密码流 tokenUrl(已配好)----------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ---------- 用户存储(内存 demo。生产用数据库)----------
USERS: dict[str, dict] = {
    "alice": {"username": "alice", "hashed_password": pwd_context.hash("alice123")},
    "bob": {"username": "bob", "hashed_password": pwd_context.hash("bob456")},
}


# ---------- ① 密码哈希(已实现,读它理解 bcrypt)----------


def hash_password(password: str) -> str:
    """用 bcrypt 哈希明文密码(随机盐 → 同密码每次哈希不同)。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希串(bcrypt 内部重新算盐比对)。"""
    return pwd_context.verify(plain_password, hashed_password)


# ---------- ② 生成 JWT(你填)----------


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    【生成 JWT · §21.3】把用户信息编码成 JWT 字符串。

    思路:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})                 # 注入过期时间(标准 claim)
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    """
    # TODO: copy data → 算 expire → 注入 exp → jwt.encode
    ...


def authenticate_user(username: str, password: str) -> dict | None:
    """
    【辅助:验证用户】用户不存在或密码错返 None,否则返用户 dict。

    思路:
        user = USERS.get(username)
        if user is None or not verify_password(password, user["hashed_password"]):
            return None
        return user
    """
    # TODO: USERS.get → 不存在/密码错返 None,否则返 user
    ...


# ---------- ③ 登录端点:发 token(你填)----------


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    【登录发 token · §21.4】OAuth2 密码流:收 username/password,验密码,发 access_token。

    思路(失败 401,成功发 token):
        user = authenticate_user(form_data.username, form_data.password)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误", headers={"WWW-Authenticate": "Bearer"})
        token = create_access_token({"sub": user["username"]})   # sub 是标准 claim(主体)
        return {"access_token": token, "token_type": "bearer"}
    """
    # TODO: authenticate_user → None 则 401(带 WWW-Authenticate),否则 create_access_token 返 token
    ...


# ---------- ④ 依赖:解析+验证 token(你填)----------


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    【依赖注入鉴权 · §21.5】decode token,验证签名+过期,返回用户名。失败 401。

    思路:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])   # 自动验签名+exp
            username: str = payload.get("sub")
            if username is None or username not in USERS:
                raise HTTPException(401, "无效凭证", headers={"WWW-Authenticate": "Bearer"})
            return username
        except JWTError:                       # 过期/签名错/格式错都抛这个
            raise HTTPException(401, "无效凭证", headers={"WWW-Authenticate": "Bearer"})
    """
    # TODO: jwt.decode → 取 sub → 校验 → 返用户名;JWTError/无效 → 401
    ...


# ---------- ⑤ 受保护端点(你填)----------


@app.get("/me")
def read_current_user(current_user: str = Depends(get_current_user)):
    """
    【受保护端点 · §21.5】依赖 get_current_user 鉴权,返回当前登录用户名。

    思路:return {"user": current_user}
    """
    # TODO: return {"user": current_user}
    ...


# ---------- 公开端点(对比用,无需鉴权)----------


@app.get("/public")
def public():
    """公开端点,任何请求都能访问。对比 /me 必须带 token。"""
    return {"message": "公开数据"}
