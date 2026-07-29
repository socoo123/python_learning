"""
Ch19 作业:数据库 ORM —— SQLAlchemy 2.0(declarative + Mapped/mapped_column)。

模型定义、engine、SessionLocal、get_db yield 依赖都已写好(读代码理解配置)。
你填四个 CRUD 端点的【查询体】,练习 SQLAlchemy 2.0 的查询语法 + 集成 FastAPI。

    uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

--- 关键设计(对比 Java) ---
- Product(Base)        ≈ @Entity 类  (declarative + Mapped/mapped_column ≈ @Column)
- engine               ≈ DataSource / DriverManager.getConnection
- Session              ≈ EntityManager  (工作单元,跟踪脏对象)
- get_db() yield 依赖  ≈ @Transactional + OpenEntityManagerInView(每请求一个 session)
- select(Product)      ≈ JPQL / Criteria API  (ORM 生成 SQL,参数化防注入)
"""
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

# ---------- engine + SessionLocal(全局共享,见 §19.2)----------

# SQLite 内存库。两个坑必须同时解决:
#   ① check_same_thread=False:FastAPI 多线程请求复用同一 engine,必须关线程检查。
#   ② StaticPool:默认每个连接拿到【独立的】内存库(:memory: 是连接级的)。
#      用 StaticPool 强制【所有连接共用同一个底层连接】→ 共享同一份内存库,
#      否则建表在 A 连接、查询在 B 连接,B 看不到表。
# (生产环境用文件库 sqlite:///./app.db 或 Postgres,无此问题。)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,  # True → 控制台打印生成的 SQL(调试用,看 ORM 偷偷干了什么)
)
# sessionmaker 是 Session 的「工厂」,每次调用产出新 Session(= 每请求新建)。
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# ---------- Declarative Base + 模型(见 §19.3,定义性代码保留)----------


class Base(DeclarativeBase):
    """所有模型的基类(SQLAlchemy 2.0 写法,继承 DeclarativeBase)。"""


class Product(Base):
    """商品模型(≈ Java @Entity)。

    Mapped[类型] + mapped_column(...) 是 2.0 的类型化列定义。
    - primary_key=True → 主键;autoincrement=True → 自增(整数主键默认自增)。
    - index=True → 该列建索引(加速按 category 过滤/排序)。
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(index=True)
    price: Mapped[float]
    stock: Mapped[int]

    def __repr__(self) -> str:  # 方便调试打印
        return f"<Product id={self.id} name={self.name!r}>"


# ---------- get_db yield 依赖(见 §19.4,复用 Ch16 模式)----------


def get_db():
    """每请求一个 Session,yield 后总关闭(即使端点抛异常)。

    = Ch16 的 yield 依赖三段式:setup → yield 值 → finally 清理。
    对应 Java 的 OpenEntityManagerInView + @Transactional:每请求一个 EntityManager。
    """
    db = SessionLocal()  # 新建 session
    try:
        yield db         # 端点拿到的就是这个 db
    finally:
        db.close()       # 总执行(请求结束,释放连接)


# ---------- 辅助:ORM 对象 → dict(供端点返回 HTTP JSON)----------


def product_to_dict(p: Product) -> dict:
    """把 ORM 对象的列转成 dict(去掉内部状态 _sa_instance_state)。"""
    return {c.name: getattr(p, c.name) for c in p.__table__.columns}


# ---------- 入参 schema(Pydantic,POST 用)----------


class ProductCreate(BaseModel):
    """创建商品的请求体(SQLAlchemy 模型是【出/入库】,Pydantic 是【入/出 HTTP】)。"""
    name: str
    category: str
    price: float
    stock: int


app = FastAPI(title="SQLAlchemy 2.0 CRUD 演示")


# ============================================================
# CRUD 端点(你填查询体)
# ============================================================


@app.get("/products")
def list_products(category: str | None = None, db: Session = Depends(get_db)):
    """
    【列表 + 过滤 · §19.5】返回商品列表,可选按 category 过滤。

    思路(SQLAlchemy 2.0 用 select(),不再用老的 query()):
        stmt = select(Product)
        if category:
            stmt = stmt.where(Product.category == category)   # ORM 参数化,防 SQL 注入
        stmt = stmt.order_by(Product.id)                       # 排序,保证顺序稳定
        rows = db.execute(stmt).scalars().all()                # execute→Result;scalars()拆 ORM 对象;all()取全列表
        return [product_to_dict(r) for r in rows]
    """
    # TODO: select + 可选 where + order_by + execute/scalars/all + 转 dict
    ...


@app.post("/products", status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """
    【创建 · §19.6】新增一个商品,返回 201 + 带新 id 的对象。

    思路(add → commit → refresh 三步):
        p = Product(name=payload.name, category=payload.category,
                    price=payload.price, stock=payload.stock)
        db.add(p)         # 加入 session(暂未写库,= JPA persist)
        db.commit()       # 提交事务,真正写库
        db.refresh(p)     # 刷新,拿回 DB 生成的自增 id
        return product_to_dict(p)
    """
    # TODO: 构造 Product → add → commit → refresh → 转 dict
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    【按主键查 + 404 · §19.5】查不到 → HTTPException(404)。

    思路:
        p = db.get(Product, product_id)   # 按主键查,最直接(= JPA EntityManager.find)
        if p is None:
            raise HTTPException(status_code=404, detail="商品不存在")
        return product_to_dict(p)
    """
    # TODO: db.get 按主键查;None 抛 404;否则转 dict
    ...


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    【删除 · §19.6】查不到 → 404;存在 → 删除并提交。

    思路:
        p = db.get(Product, product_id)
        if p is None:
            raise HTTPException(status_code=404, detail="商品不存在")
        db.delete(p)      # 标记删除(= JPA remove)
        db.commit()       # 提交事务真正删
        return {"deleted": product_id}
    """
    # TODO: db.get;None 抛 404;否则 delete + commit + 返回 {"deleted": id}
    ...
