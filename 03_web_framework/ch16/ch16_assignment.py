"""
Ch16 作业:依赖注入(Depends)—— FastAPI 最强大的设计之一。

场景:「极客商城」订单 API 2.0。架构组 Code Review 要求把横切关注点从端点里
抽出来,用依赖注入统一管理。你要亲手写 4 个依赖:
  ① get_db            —— yield 依赖:DB session,用完必须关闭(即使端点抛异常)
  ② get_current_user  —— Header 依赖:从 X-Token 解析当前用户,无效 → 401
  ③ get_pagination    —— 类依赖:page/size 打包成 Pagination(offset 一处定义)
  ④ require_admin     —— 嵌套依赖:在 get_current_user 之上查角色,非 admin → 403
再把它们注入 4 个端点:订单列表(按用户过滤+分页)、订单详情(越权 403)、
下单(201)、经营统计(仅 admin)。

    uv sync --extra web
    uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="极客商城 · 订单 API")


# ---------- 请求模型(脚手架:下单 body,框架自动 422)----------


class OrderCreate(BaseModel):
    """下单请求体。注意:没有 username——下单人身份只能来自服务端注入的 user(§16.7)。"""

    item: str = Field(min_length=1, max_length=50)
    amount: float = Field(gt=0)


# ---------- 数据与「数据库」模拟(脚手架,直接用)----------

ORDERS: list[dict] = [
    {"id": 1, "username": "alice", "item": "机械键盘", "amount": 599.0, "status": "paid"},
    {"id": 2, "username": "alice", "item": "无线鼠标", "amount": 159.0, "status": "shipped"},
    {"id": 3, "username": "bob", "item": "设计模式", "amount": 75.5, "status": "paid"},
    {"id": 4, "username": "bob", "item": "降噪耳机", "amount": 1299.0, "status": "pending"},
    {"id": 5, "username": "alice", "item": "Python编程", "amount": 89.0, "status": "paid"},
]
_next_order_id = 6

TOKENS: dict[str, dict] = {
    "tok-alice": {"username": "alice", "role": "user"},
    "tok-bob": {"username": "bob", "role": "user"},
    "tok-admin": {"username": "admin", "role": "admin"},
}

DB_AUDIT: list[str] = []  # 模拟 DB 连接日志:测试用它验证 session 的打开/关闭(§16.2)


# ---------- 依赖 1:DB session(yield 依赖)----------


def get_db():
    """
    【yield 依赖 · §16.2】模拟 DB session:每个请求一个,用完必须关闭。

    任务:三段式写法——
      ① yield 前:DB_AUDIT.append("open"),造 session dict {"queries": 0}
      ② try 里 yield session(端点注入拿到的就是它)
      ③ finally 里 DB_AUDIT.append("close")(模拟 session.close())

    示例(通过端点观察):
        GET /orders(带 token)一次   -> DB_AUDIT 增加 ["open", "close"]
        GET /orders/99999(端点抛 404)-> DB_AUDIT 依然增加 ["open", "close"]
        GET /orders 连发两次        -> ["open", "close", "open", "close"](每请求新建)

    提示:就是 Ch06 @contextmanager 的套路;清理必须放 finally,
         只写在 yield 后面的话,端点异常时执行不到。
    """
    # TODO: append("open") → try: yield {"queries": 0} → finally: append("close")
    ...


# ---------- 依赖 2:当前用户(Header 鉴权)----------


def get_current_user(x_token: str | None = Header(default=None)) -> dict:
    """
    【Header 依赖 · §16.3】从 X-Token 头解析当前用户(模拟鉴权)。

    任务:x_token 缺失或不在 TOKENS 表 -> raise HTTPException(401, "未授权");
         有效 -> return TOKENS[x_token](形如 {"username": "alice", "role": "user"})。

    示例:
        get_current_user(x_token="tok-alice") -> {"username": "alice", "role": "user"}
        get_current_user(x_token="tok-admin") -> {"username": "admin", "role": "admin"}
        get_current_user(x_token=None)        -> 抛 HTTPException,status_code == 401
        get_current_user(x_token="garbage")   -> 抛 HTTPException,status_code == 401

    提示:参数名 x_token 自动对应请求头 X-Token(下划线转连字符);
         依赖里抛 HTTPException 会「短路」——端点函数体根本不执行。
    """
    # TODO: 缺失/未知 token → raise HTTPException(401);有效 → return TOKENS[x_token]
    ...


# ---------- 依赖 3:分页参数(类依赖)----------


class Pagination:
    """把 page/size 打包,offset 计算一处定义(§16.4)。"""

    def __init__(self, page: int, size: int):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def get_pagination(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
) -> Pagination:
    """
    【类依赖 · §16.4】把查询参数 page/size 打包成 Pagination 对象。

    任务:返回 Pagination(page=page, size=size)。
         签名里的 Query 校验(page>=1、1<=size<=100)已给定,非法分页框架自动 422。

    示例:
        get_pagination(page=2, size=3) -> Pagination(page=2, size=3),.offset == 3
        get_pagination(page=1, size=10) -> .offset == 0
        GET /orders?page=0(带 token)   -> 422(框架校验,依赖函数体不执行)

    提示:依赖函数也能声明 Query/Header 参数,FastAPI 一并解析——
         这是依赖最顺手的地方:解析+校验+打包全在端点之外。
    """
    # TODO: return Pagination(page=page, size=size)
    ...


# ---------- 依赖 4:管理员权限(嵌套依赖)----------


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    【嵌套依赖 · §16.5】在「当前用户」之上再叠一层:不是 admin -> 403。

    任务:user["role"] != "admin" -> raise HTTPException(403, "需要管理员权限");
         否则 return user。注意签名:这个依赖自己又 Depends(get_current_user),
         FastAPI 自动解析整条链(先 401 后 403)。

    示例:
        require_admin(user={"username": "admin", "role": "admin"}) -> 原样返回
        require_admin(user={"username": "alice", "role": "user"})  -> 抛 403
        HTTP 层:X-Token: tok-admin -> 通过;tok-alice -> 403;无 token -> 401(上游短路)

    提示:401 = 没认证(你是谁?);403 = 已认证但没权限——别混。
    """
    # TODO: role != "admin" → raise HTTPException(403);否则 return user
    ...


# ---------- 端点:把依赖注入进来 ----------


@app.get("/orders")
def list_orders(
    pagination: Pagination = Depends(get_pagination),
    user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    """
    【注入三个依赖 · §16.6】当前用户的订单列表(分页)。

    任务:
      ① db["queries"] += 1(用一下 session,模拟查询)
      ② 只留当前用户的订单:[o for o in ORDERS if o["username"] == user["username"]]
      ③ 切片:my[pagination.offset : pagination.offset + pagination.size]
      ④ 返回 {"items": 切片结果, "total": 过滤后总数, "page": ..., "size": ...}

    示例(种子:alice 有 id=1/2/5,bob 有 id=3/4):
        GET /orders(tok-alice)              -> total == 3,items 全是 alice 的
        GET /orders?page=2&size=2(tok-alice)-> items 只有 [id=5],total 仍是 3
        GET /orders(tok-bob)                -> total == 2
        GET /orders(无 token)               -> 401,函数体不执行

    提示:注入的 pagination/user/db 就是普通对象,直接用;鉴权不是摆设——
         user 必须参与过滤,否则 bob 能看到 alice 的订单(水平越权)。
    """
    # TODO: db 计数 → 按 user 过滤 → offset 切片 → 返回 dict(items/total/page/size)
    ...


@app.get("/orders/{order_id}")
def get_order(
    order_id: int,
    user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    """
    【404 vs 403 · §16.6】查单个订单:不存在 404,是别人的 403。

    任务:
      ① db["queries"] += 1
      ② 按 id 找订单,找不到 -> HTTPException(404, "订单不存在")
      ③ 订单的 username != 当前用户 -> HTTPException(403, "无权查看他人订单")
      ④ 返回订单 dict

    示例:
        GET /orders/1(tok-alice)    -> 200,item == "机械键盘"
        GET /orders/1(tok-bob)      -> 403(订单是 alice 的)
        GET /orders/99999(tok-alice)-> 404
        GET /orders/1(无 token)     -> 401(依赖先短路)

    提示:先 404 再 403(不存在的订单不暴露归属);
         查找用 next((o for o in ORDERS if o["id"] == order_id), None)。
    """
    # TODO: db 计数 → 404 守卫 → 403 守卫 → return order
    ...


@app.post("/orders", status_code=201)
def create_order(
    body: OrderCreate,
    user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    """
    【POST + session 写入 · §16.7】下单:注入 session 完成写入,201 返回新订单。

    任务:
      ① global _next_order_id
      ② db["queries"] += 1(写入也走 session)
      ③ 造订单 {"id": _next_order_id, "username": user["username"],
                "item": body.item, "amount": body.amount, "status": "pending"}
      ④ append 到 ORDERS,id 自增,返回新订单

    示例:
        POST /orders(tok-bob){"item": "显示器", "amount": 899}
            -> 201,{"id": 6, "username": "bob", "item": "显示器", "amount": 899.0, "status": "pending"}
        POST /orders(无 token)     -> 401(依赖短路,不会写入)
        POST amount=-1             -> 422(OrderCreate 的 Field(gt=0),函数体不执行)

    提示:给 _next_order_id 赋值前必须 global(Ch14 的老朋友);
         username 只能来自注入的 user,绝不信客户端自报家门。
    """
    # TODO: global → db 计数 → 造订单 dict → append → id 自增 → return
    ...


@app.get("/admin/stats")
def admin_stats(admin: dict = Depends(require_admin)):
    """
    【综合 · §16.8】全站经营统计,仅管理员可见(复用 require_admin)。

    任务:返回三个键——
      - total_orders: 订单总数
      - total_amount: 总金额 sum(amount),round(..., 2)
      - by_status: 各状态订单数,如 {"paid": 3, "shipped": 1, "pending": 1}

    示例(种子 5 单:599 + 159 + 75.5 + 1299 + 89):
        GET /admin/stats(tok-admin)
            -> {"total_orders": 5, "total_amount": 2221.5,
                "by_status": {"paid": 3, "shipped": 1, "pending": 1}}
        GET /admin/stats(tok-alice) -> 403;无 token -> 401

    提示:参数 admin 函数体里用不到——注入它就是为了鉴权这个「副作用」;
         by_status 逐单累计:d[s] = d.get(s, 0) + 1。
    """
    # TODO: 累计 by_status → 返回 dict(total_orders/total_amount/by_status)
    ...
