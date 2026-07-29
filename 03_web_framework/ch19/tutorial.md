# Ch19 · 数据库 ORM:SQLAlchemy 2.0

> **预计**:1 天 ｜ **前置**:Ch16(依赖注入)｜ **重点**
> **目标**:用 **SQLAlchemy 2.0** 操作数据库,告别前几章的内存 dict 存储。掌握模型定义、Session、CRUD、查询——对比 JPA/Hibernate/MyBatis。这是真实后端的核心。

> 📐 **本教程的契约**:模型/engine/get_db 都已写好(读代码),你填 4 个 CRUD 端点的查询体(§19.5/§19.6)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业端点 | 对应小节 | 核心知识点 |
|----------|----------|-----------|
| `list_products` | §19.5 | select + where + order_by + execute/scalars/all |
| `get_product` | §19.5 | db.get 按主键查 + 404 |
| `create_product` | §19.6 | add + commit + refresh(三步写) |
| `delete_product` | §19.6 | db.get + delete + commit |

（engine/Session/模型/get_db 见 §19.2–§19.4,已写好）

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

① 预览猜 → ② 填 4 个端点 → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 你用过 JPA/Hibernate/MyBatis 哪个?Python 事实标准的 ORM 叫什么?
2. JPA 的 `@Entity` + `@Column`。SQLAlchemy 2.0 怎么定义模型?
3. JPA 的 `EntityManager` 管理持久化对象。SQLAlchemy 对应什么?它在 Web 里怎么「每请求一个」?
4. JPA `persist` 后要 `commit`。SQLAlchemy 写入分几步?
5. 为什么用 SQLite 内存库做测试?`check_same_thread=False` 和 `StaticPool` 解决什么?

---

## §19.1 为什么用 ORM

前几章商品存在内存 `dict`/`list` 里——服务重启就没了,也不能查询。真实后端要**持久化到数据库**。

两条路:
- **裸 SQL**(像 MyBatis):手写 SQL,灵活但要自己拼字符串、防注入、映射结果。
- **ORM**(像 JPA/Hibernate):用 Python 类映射表,框架自动生成 SQL。

Python 的 ORM 事实标准是 **SQLAlchemy**(2.0 是现代写法,全面类型注解)。

> 🟡 **Java 对比**:SQLAlchemy ≈ JPA/Hibernate(ORM,对象映射表);MyBatis 是「SQL mapper」(半自动,SQL 自己写),Python 对应物是 SQLAlchemy Core 或 SQLModel。本课程用 SQLAlchemy 2.0 ORM。

---

## §19.2 engine + Session:连接管理(对比 DataSource/EntityManager)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:",                              # 连接串(生产用 postgresql://...)
    connect_args={"check_same_thread": False},         # SQLite 特有:允许多线程共享
    poolclass=StaticPool,                              # 内存库共享同一连接(见下)
)
SessionLocal = sessionmaker(bind=engine, ...)          # Session 的工厂
```

- **engine** = 连接池 + DB 驱动(= Java `DataSource`)。全局一个。
- **Session** = 一次工作单元,跟踪你改了哪些对象,提交时统一写库(= `EntityManager`)。**每请求新建一个**(短命)。
- `SessionLocal` 是 Session 的**工厂**,每次调用 `SessionLocal()` 产新 Session。

### SQLite 内存库的两个坑(本章用,生产别用)

```python
"sqlite:///:memory:"                        # 内存库,进程退出就没
connect_args={"check_same_thread": False}   # 坑1:默认 SQLite 不让跨线程用
poolclass=StaticPool                        # 坑2::memory: 是「连接级」的,默认每连接独立内存库
```
两个坑都踩中才让 FastAPI(多线程)+ 内存库正常工作。**生产用文件库 `sqlite:///./app.db` 或 Postgres,无此问题**。

---

## §19.3 模型定义:DeclarativeBase + Mapped(对比 @Entity)

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):     # 所有模型的基类(2.0 写法)
    pass

class Product(Base):
    __tablename__ = "products"                            # 表名

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)         # index=True → 建索引
    category: Mapped[str] = mapped_column(index=True)
    price: Mapped[float]
    stock: Mapped[int]
```

- `Mapped[类型]` + `mapped_column(...)` 是 **2.0 类型化列定义**(`Mapped[int]` 表示这列是 int)。
- `primary_key=True` 主键;`autoincrement=True` 自增;`index=True` 建索引(加速查询)。
- 类 = 表,属性 = 列,实例 = 行。

> 🟡 **Java 对比**:= `@Entity @Table(name="products") class Product { @Id @GeneratedValue Integer id; @Column String name; ... }`。SQLAlchemy 2.0 的 `Mapped[]` 比 JPA 注解更类型安全(IDE/mypy 能查)。

### 建表

```python
Base.metadata.create_all(engine)    # 按所有模型定义建表(测试里用)
```

---

## §19.4 get_db:每请求一个 Session(yield 依赖,复用 Ch16)

```python
def get_db():
    db = SessionLocal()        # ① 新建 session(setup)
    try:
        yield db               # ② 端点拿到的就是它
    finally:
        db.close()             # ③ 请求结束总关闭(即使异常)

@app.get("/products")
def list_products(db: Session = Depends(get_db)):   # 注入 session
    ...
```

**这正是 Ch16 的 yield 依赖三段式**。每个 HTTP 请求新建一个 Session,请求结束关闭。= Java 的 `OpenEntityManagerInView` + `@Transactional`(每请求一个 EntityManager)。

> 🤯 **为什么每请求一个 Session**:Session 是有状态的(跟踪脏对象),并发请求共享会互相污染。每请求独立 + 用完即关,干净安全。

---

## §19.5 查询:select / where / get(对应:`list_products`、`get_product`)🔴

SQLAlchemy 2.0 用 **`select()`**(老版 `query()` 已废弃):

```python
from sqlalchemy import select

# 列表 + 过滤
def list_products(category, db):
    stmt = select(Product)                              # SELECT * FROM products
    if category:
        stmt = stmt.where(Product.category == category) # WHERE category = ?(参数化,防注入)
    stmt = stmt.order_by(Product.id)                    # ORDER BY id
    rows = db.execute(stmt).scalars().all()             # execute→Result;scalars()取 ORM 对象;all()列表
    return [product_to_dict(r) for r in rows]

# 按主键查(最直接)
def get_product(product_id, db):
    p = db.get(Product, product_id)    # SELECT ... WHERE id=? (= EntityManager.find)
    if p is None:
        raise HTTPException(404, "商品不存在")
    return product_to_dict(p)
```

### 关键 API

| 操作 | 写法 | Java 对应 |
|------|------|-----------|
| 查列表 | `db.execute(select(Product).where(...)).scalars().all()` | JPQL `entityManager.createQuery(...)` |
| 按主键 | `db.get(Product, id)` | `entityManager.find(Product.class, id)` |
| 过滤 | `.where(Product.category == category)` | JPQL `where p.category = ?1` |
| 排序 | `.order_by(Product.id)` | `order by p.id` |

### 为什么 `.execute(stmt).scalars().all()` 三连

- `db.execute(stmt)` 返回 `Result`(行的集合,每行是 Row 对象)。
- `.scalars()` 把每行「拆」成单个 ORM 对象(因为 select 单实体时,每行就一个 Product)。
- `.all()` 取成列表。

> ⚠️ **`Product.category == category` 不是比较,是构造 SQL**:ORM 拦截 `==`,生成参数化 SQL(`WHERE category = ?`,值后填)。**天然防 SQL 注入**(不用手拼字符串)。= JPA 的 Criteria API。

> ✅ 做 `list_products`/`get_product`:见上。

---

## §19.6 写入:add / commit / refresh / delete(对应:`create_product`、`delete_product`)🟡

```python
# 创建(三步:add → commit → refresh)
def create_product(payload, db):
    p = Product(name=payload.name, ...)   # 造对象(还没入库)
    db.add(p)        # ① 加入 session(= JPA persist,暂未写库)
    db.commit()      # ② 提交事务,真正写库(INSERT)
    db.refresh(p)    # ③ 刷新,拿回 DB 生成的自增 id
    return product_to_dict(p)

# 删除
def delete_product(product_id, db):
    p = db.get(Product, product_id)
    if p is None:
        raise HTTPException(404, "商品不存在")
    db.delete(p)     # 标记删除(= JPA remove)
    db.commit()      # 提交,真正 DELETE
    return {"deleted": product_id}
```

### 关键:**`add` 只是暂存,`commit` 才真写**

`db.add(p)` 把对象放进 session 的「待办」,**不立刻执行 SQL**。`db.commit()` 提交事务,这时才真正 `INSERT`。这是 ORM 的「工作单元」模式——攒一批改动,一次提交(= JPA 的 dirty checking + flush + commit)。

- `db.refresh(p)`:commit 后,DB 生成了自增 id,但 Python 对象 `p` 还没有。refresh 重新查一次,把 id 填进 `p`。
- 改对象:`p.price = 99; db.commit()`(session 跟踪到 p 变脏,commit 时 UPDATE)。

> 🟡 **Java 对比**:`add`=`persist`,`commit`=`transaction.commit`,`refresh`=`refresh`,`delete`=`remove`。几乎一一对应。

> ✅ 做 `create_product`/`delete_product`:见上三步/四步。

---

## §19.7 测试隔离:drop/create_all

测试不能让数据互相污染。本作业用 **autouse fixture** 每个 test 前 drop+create 建空表:

```python
@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(engine)     # 先清
    Base.metadata.create_all(engine)   # 建空表
    yield                              # 跑 test
    Base.metadata.drop_all(engine)     # 收尾
```

每个 test 看到的是干净表,互不影响。生产用 **Alembic** 做数据库迁移(= Java Flyway/Liquibase),不用 create_all。

---

## §19.8 同步 vs 异步 SQLAlchemy(呼应 Ch18)

本章用**同步** SQLAlchemy(`create_engine` + `Session`)。端点是 `def`(同步),FastAPI 会丢线程池跑(Ch18 §18.7)——同步 DB 驱动**别**放进 `async def` 端点。

如果追求极致并发,用**异步** SQLAlchemy(`create_async_engine` + `AsyncSession`,配 asyncpg 驱动),端点 `async def`。生产选择:
- 大多数项目:同步 SQLAlchemy + `def` 端点(简单,够用)。
- 高并发 IO 密集:异步 SQLAlchemy + `async def`(复杂,要全程 async)。

> 本章选同步,因为简单且 SQLAlchemy 2.0 同步/异步 API 几乎一样,先掌握同步。

---

## §19.9 Java 老手常踩的坑 ⚠️

1. **`add` 后忘 `commit`**:数据没真写库。`add` 只是暂存。
2. **忘 `refresh` 拿自增 id**:commit 后 Python 对象没 id,要 refresh。
3. **`execute` 后忘 `scalars().all()`**:`execute` 返回 Result,要 `.scalars().all()` 才是 ORM 对象列表。
4. **`==` 当比较用**:`Product.category == x` 在 ORM 里是构造 WHERE 子句,不是比较。判断值用 `==`(Python 对象层面)或 `is`。
5. **Session 跨请求共享**:并发污染。每请求一个(get_db)。
6. **SQLite 内存库的 StaticPool**:生产别用内存库,数据会丢。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `list_products` | select + where + order_by | 🟡 |
| `get_product` | db.get 按主键 + 404 | 🟢 |
| `create_product` | add + commit + refresh | 🟡 |
| `delete_product` | delete + commit | 🟡 |

```bash
uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v
```
期望:16 个全绿。

---

## ✅ 自测

- [ ] 能说清 engine/Session/SessionLocal 各是什么,对应 Java 什么
- [ ] 能用 `select().where().order_by()` + `execute().scalars().all()` 查列表
- [ ] 知道 `add` 只是暂存,`commit` 才真写,`refresh` 拿自增 id
- [ ] 能解释 get_db yield 依赖为何保证每请求独立 Session(复用 Ch16)
- [ ] 16 个作业全绿

## 🎓 费曼挑战

1. 「为什么 `db.add(p)` 后还要 `db.commit()`?中间发生了什么?」— 重读 §19.6
2. 「`db.execute(select(Product).where(Product.category==c))` 为什么天然防 SQL 注入?」— 重读 §19.5

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch19 掌握后,进 **Ch20 · 测试 API 进阶**(fixtures + parametrize + 覆盖率 + 依赖覆盖)——给前几章的 API 写专业测试。
