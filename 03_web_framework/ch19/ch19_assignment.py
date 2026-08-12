"""
Ch19 作业:数据库 ORM —— SQLAlchemy 2.0(declarative + Mapped/mapped_column + 关系查询)。

场景:「极客商城」电商后台。之前商品存在内存 list 里,重启就没,也没法支持
「用户下单扣库存」。现在升级成真数据库:products / users / orders 三表(一对多),
你要实现 8 个端点:

  ① list_products      —— 多条件过滤(类目/价格区间) + offset/limit 分页(§19.5)
  ② get_product        —— db.get 按主键查,查不到 404(§19.5)
  ③ create_product     —— add → commit → refresh 三步写(§19.6)
  ④ update_product     —— 脏检查:改字段 + commit(§19.6)
  ⑤ delete_product     —— delete + commit(§19.6)
  ⑥ register_user      —— scalar_one_or_none 查重 + 409(§19.6)
  ⑦ place_order        —— 校验 → 扣库存 → 写订单,一次 commit 保原子性(§19.7,重点)
  ⑧ list_user_orders   —— select(Order, Product).join(...) 关联查询(§19.7)

    uv sync --extra web
    uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

--- 关键设计(对比 Java) ---
- Base(DeclarativeBase) + Mapped/mapped_column  ≈ @Entity + @Column
- ForeignKey + relationship                      ≈ @JoinColumn + @ManyToOne/@OneToMany
- engine / Session / SessionLocal                ≈ DataSource / EntityManager / 工厂
- get_db() yield 依赖                            ≈ OpenEntityManagerInView(每请求一个 Session)
- select(...).where(...)                         ≈ JPQL / Criteria(参数化,防注入)
- add → commit → refresh                         ≈ persist → tx.commit → refresh
"""
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

# ---------- engine + SessionLocal(脚手架,见 §19.2)----------

# SQLite 内存库。两个坑必须同时解决:
#   ① check_same_thread=False:FastAPI 多线程请求复用同一 engine,必须关线程检查。
#   ② StaticPool::memory: 是「连接级」的,默认每个连接一份独立内存库。
#      StaticPool 强制全池共用同一个底层连接 → 建表和查询看到的是同一份数据。
# (生产环境用 sqlite:///./app.db 或 Postgres,无此问题;表结构演进用 Alembic。)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,  # True → 控制台打印生成的 SQL(调试用,看 ORM 偷偷干了什么)
)
# sessionmaker 是 Session 的「工厂」,每次调用产新 Session(= 每请求新建)。
# autoflush=False:查询前不自动刷暂存改动,行为可预测。
# expire_on_commit=False:commit 后对象属性不过期,可继续读(否则再读会触发 SELECT)。
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# ---------- 三表模型(脚手架,见 §19.3;读懂 ForeignKey 与 relationship 的分工)----------


class Base(DeclarativeBase):
    """所有模型的基类(SQLAlchemy 2.0 写法),metadata 收集全部表结构。"""


class User(Base):
    """用户表。一个用户有多个订单(1:N)。

    email 上的 unique=True 是「先查再插」之外的真正兜底(并发竞态时由 DB 拒绝)。
    orders = relationship(...) 是导航属性,不建列;靠 Order.user_id 外键反查。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Product(Base):
    """商品表(≈ Java @Entity)。

    Mapped[类型] + mapped_column(...) 是 2.0 的类型化列定义:
    primary_key/autoincrement → 自增主键;index=True → 建索引加速过滤。
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(index=True)
    price: Mapped[float]
    stock: Mapped[int]

    orders: Mapped[list["Order"]] = relationship(back_populates="product")

    def __repr__(self) -> str:  # 方便调试打印
        return f"<Product id={self.id} name={self.name!r}>"


class Order(Base):
    """订单表:users 与 products 之间的连接表(多对一 ×2)。

    user_id / product_id 才是真实的外键列(ForeignKey 建列);
    user / product 是导航属性(relationship 不建列,按外键捞对象)。
    status 用 mapped_column(default=...) 给插入默认值。
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int]
    total_price: Mapped[float]
    status: Mapped[str] = mapped_column(default="created")

    user: Mapped[User] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship(back_populates="orders")


# ---------- get_db yield 依赖(脚手架,见 §19.4,复用 Ch16 三段式)----------


def get_db():
    """每请求一个 Session,yield 后总关闭(即使端点抛异常)。

    Session 有状态(跟踪脏对象),全局共享会并发污染 → 每请求新建、用完即关。
    未 commit 的待办改动随 close 全部丢弃——这正是「下单中途抛异常 = 什么都没写」的原理。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- 辅助:ORM 对象 → dict(脚手架,供端点返回 JSON)----------


def row_to_dict(obj) -> dict:
    """把 ORM 对象的列转成 dict(按 __table__.columns 取,丢掉内部状态)。"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


# ---------- 入参 schema(Pydantic 负责【入 HTTP】,SQLAlchemy 模型负责【出入库】)----------


class ProductCreate(BaseModel):
    """创建/更新商品的请求体。Field 校验复用 Ch14:price>0、stock>=0,违反 → 422。"""

    name: str
    category: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class UserCreate(BaseModel):
    name: str
    email: str


class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = Field(gt=0)


app = FastAPI(title="极客商城 · SQLAlchemy 2.0")


# ============================================================
# 商品:列表(过滤+分页)/ 详情 / 创建 / 更新 / 删除
# ============================================================


@app.get("/products")
def list_products(
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    【多条件查询 + 分页 · §19.5】商品列表:可选类目过滤、价格区间、分页。

    任务:
      ① stmt = select(Product)
      ② 三个可选参数各给才拼条件:stmt = stmt.where(Product.category == category)
         (min_price → Product.price >= min_price;max_price → <=)
      ③ stmt = stmt.order_by(Product.id)             —— 排序稳定,分页才有意义
      ④ stmt = stmt.offset((page - 1) * size).limit(size)
      ⑤ db.execute(stmt).scalars().all() → [row_to_dict(p) for p in rows]

    示例(测试种子:键盘599/鼠标159/Python编程89/设计模式75.5/重构99/耳机1299):
        GET /products                          -> 全部 6 个,id 升序
        GET /products?category=图书            -> 3 本(id 3/4/5)
        GET /products?min_price=80&max_price=100 -> [Python编程(89), 重构(99)]
        GET /products?size=2&page=2            -> 第 2 页:id [3, 4]
        GET /products?size=2&page=4            -> []

    提示:`Product.category == category` 不是比较,是构造参数化 WHERE(防注入,§19.5);
         分页公式 offset = (page - 1) * size;页码/页大小的范围校验 Query(ge=1) 已帮你写好。
    """
    # TODO: select → 按可选参数拼 where → order_by(Product.id) → offset/limit → execute().scalars().all()
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    【按主键查 + 404 · §19.5】商品详情。

    任务:
      ① p = db.get(Product, product_id)     —— 按主键查(= EntityManager.find)
      ② p is None → raise HTTPException(status_code=404, detail="商品不存在")
      ③ 否则 return row_to_dict(p)

    示例:
        GET /products/1   -> 200 {"id": 1, "name": "机械键盘", ...}
        GET /products/999 -> 404 {"detail": "商品不存在"}

    提示:按主键查用 db.get 最直接,不必 select().where();None 判断用 is None。
    """
    # TODO: db.get 按主键;None → 404;否则 row_to_dict
    ...


@app.post("/products", status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """
    【创建 · §19.6】新增商品,返回 201 + 带自增 id 的对象。

    任务(add → commit → refresh 三步):
      ① p = Product(name=payload.name, category=payload.category,
                    price=payload.price, stock=payload.stock)
      ② db.add(p)      —— 暂存到 Session,此刻【没有发 SQL】
      ③ db.commit()    —— 提交事务,真正 INSERT
      ④ db.refresh(p)  —— 重查一次,把 DB 生成的自增 id 填回 p
      ⑤ return row_to_dict(p)

    示例:
        POST /products {"name":"降噪耳机","category":"影音设备","price":1299.0,"stock":80}
            -> 201 {"id": 1, "name": "降噪耳机", ...}
        POST 缺 price / price=-1  -> 422(Pydantic Field 校验,框架自动)

    提示:最常见的坑是 add 之后忘 commit——数据根本没进库(§19.6 坑 1)。
    """
    # TODO: 构造 Product → add → commit → refresh → row_to_dict
    ...


@app.put("/products/{product_id}")
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    """
    【更新:脏检查 · §19.6】全量更新商品的 4 个字段(id 不变)。

    任务:
      ① p = db.get(Product, product_id);None → 404
      ② 把 payload 的 name/category/price/stock 逐个赋给 p(直接改属性)
      ③ db.commit()   —— Session 跟踪到 p「脏了」,commit 时自动生成 UPDATE
      ④ return row_to_dict(p)

    示例:
        种子商品 1 是机械键盘 599.0
        PUT /products/1 {"name":"机械键盘","category":"电脑外设","price":499.0,"stock":100}
            -> 200 {"id": 1, "price": 499.0, "stock": 100, ...}
        GET /products/1 -> price 已是 499.0(真的写进去了)
        PUT /products/999 -> 404

    提示:不用写任何 UPDATE 语句——db.get 拿回的对象是「托管状态」,
         改属性会被脏检查跟踪(= JPA dirty checking);不用 refresh,commit 后属性仍可读。
    """
    # TODO: db.get → None 抛 404 → 逐字段赋值 → commit → row_to_dict
    ...


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    【删除 · §19.6】查不到 → 404;存在 → 删除并提交。

    任务:
      ① p = db.get(Product, product_id);None → 404
      ② db.delete(p)    —— 标记删除(= em.remove)
      ③ db.commit()     —— 提交,真正 DELETE
      ④ return {"deleted": product_id}

    示例:
        DELETE /products/1   -> 200 {"deleted": 1};之后 GET /products/1 -> 404
        DELETE /products/999 -> 404

    提示:删两次同一个 id,第二次必须是 404(测试会连删两次验证)。
    """
    # TODO: db.get → None 抛 404 → delete → commit → {"deleted": product_id}
    ...


# ============================================================
# 用户:注册(唯一性检查)
# ============================================================


@app.post("/users", status_code=201)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    【唯一性检查 + 写入 · §19.6】注册新用户;邮箱已存在 → 409。

    任务:
      ① exists = db.execute(select(User).where(User.email == payload.email))
                    .scalar_one_or_none()     —— 恰好一个 → User;没有 → None
      ② exists 非 None → raise HTTPException(status_code=409, detail="邮箱已注册")
      ③ u = User(name=payload.name, email=payload.email)
      ④ add → commit → refresh → return row_to_dict(u)

    示例:
        POST /users {"name":"张三","email":"zhangsan@example.com"}
            -> 201 {"id": 1, "name": "张三", "email": "zhangsan@example.com"}
        再 POST 同邮箱 -> 409 {"detail": "邮箱已注册"}
        同 name 不同 email -> 201(唯一约束在 email 上,不在 name)

    提示:scalar_one_or_none 与 scalars().all() 的分工见 §19.5;
         「先查再插」在并发下有竞态,真正兜底是列上 unique=True(§19.6 有讲)。
    """
    # TODO: scalar_one_or_none 查邮箱 → 已存在抛 409 → 构造 User → add/commit/refresh → row_to_dict
    ...


# ============================================================
# 订单:下单(事务原子性)/ 用户订单列表(join 关联查询)
# ============================================================


@app.post("/orders", status_code=201)
def place_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    【下单:事务原子性 · §19.7 —— 本章重点】校验 → 扣库存 → 写订单,一次 commit。

    任务(顺序不能乱:先全部校验,再动手改):
      ① user = db.get(User, payload.user_id);None → 404 "用户不存在"
      ② product = db.get(Product, payload.product_id);None → 404 "商品不存在"
      ③ product.stock < payload.quantity → 400 "库存不足"
         (此刻还没改任何数据,抛出 = 什么都不写)
      ④ product.stock -= payload.quantity   —— 脏检查,commit 时 UPDATE
      ⑤ order = Order(user_id=user.id, product_id=product.id, quantity=payload.quantity,
                      total_price=round(product.price * payload.quantity, 2))
      ⑥ db.add(order); db.commit(); db.refresh(order)
         —— UPDATE(扣库存) + INSERT(订单) 在同一事务,要么都成要么都败
      ⑦ return row_to_dict(order)

    示例(设计模式 price=75.5, stock=200):
        POST /orders {"user_id": 1, "product_id": 4, "quantity": 2}
            -> 201 {"id": 1, "user_id": 1, "product_id": 4, "quantity": 2,
                    "total_price": 151.0, "status": "created"}
            且商品 4 库存变 198(GET /products/4 可查)
        quantity=201(超库存) -> 400,且库存不变、订单表无新行(原子性,测试会验证)

    提示:千万别把扣库存和写订单分成两次 commit(§19.7 ❌ 写法);
         status 不用传,模型上有 default="created"。
    """
    # TODO: 校验用户/商品/库存 → 扣库存 → 造 Order → 一次 commit → refresh → row_to_dict
    ...


@app.get("/users/{user_id}/orders")
def list_user_orders(user_id: int, db: Session = Depends(get_db)):
    """
    【join 关联查询 · §19.7】查某用户的订单列表,每条带商品名。

    任务:
      ① user = db.get(User, user_id);None → 404 "用户不存在"
      ② rows = db.execute(
             select(Order, Product)                                  # 选两个模型
             .join(Product, Order.product_id == Product.id)          # INNER JOIN ON ...
             .where(Order.user_id == user_id)
             .order_by(Order.id)
         ).all()      —— ★ 多实体查询不加 .scalars()!每行是 (Order, Product) 元组
      ③ return [{"order_id": o.id, "product_id": p.id, "product_name": p.name,
                 "quantity": o.quantity, "total_price": o.total_price,
                 "status": o.status} for o, p in rows]

    示例(张三下了两单:设计模式×2、Python编程×1):
        GET /users/1/orders -> 200 [
            {"order_id": 1, "product_id": 4, "product_name": "设计模式",
             "quantity": 2, "total_price": 151.0, "status": "created"},
            {"order_id": 2, "product_id": 3, "product_name": "Python编程",
             "quantity": 1, "total_price": 89.0, "status": "created"}]
        GET /users/2/orders -> 200 [](用户存在但没下单)
        GET /users/999/orders -> 404

    提示:别在循环里写 o.product.name(懒加载 N+1,§19.7);
         若给多实体 select 加了 .scalars(),每行的 Product 会被悄悄丢掉。
    """
    # TODO: db.get(User) → None 抛 404 → select(Order, Product).join(...).where(...).order_by(...)
    #       → .all()(不加 scalars)→ for o, p in rows 拼 dict
    ...


@app.get("/health")
def health():
    """健康检查(脚手架)。"""
    return {"status": "ok"}
