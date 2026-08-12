# Ch19 · 数据库 ORM:SQLAlchemy 2.0

> **预计**:1 天 ｜ **前置**:Ch14(Pydantic)、Ch15(查询参数/分页)、Ch16(Depends)｜ **M3 第七章 · 重点**
> **目标**:用 **SQLAlchemy 2.0** 把「极客商城」从内存 dict 升级成真数据库。掌握三表建模(商品/用户/订单)、Session 写入三步、多条件查询 + 分页、**外键关系 + join 关联查询**、以及「下单扣库存」的**事务原子性**——全程对比 JPA/Hibernate。
> 本章主线:商城后台之前把商品存在内存 list 里,重启就没,更没法支持「用户下单扣库存」。你要建 **products / users / orders 三表**,实现商品的多条件分页查询、完整 CRUD,以及电商最核心的两个接口:**下单(校验 → 扣库存 → 写订单,要么全成要么全败)** 和 **查用户订单(带商品详情的关联查询)**。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。模型/engine/get_db 是脚手架(§19.2–§19.4,读懂即可);你填 8 个端点函数体,§19.5 对应查询题、§19.6 对应写入题、§19.7 对应关系与事务题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 engine / Session / SessionLocal 三件套各自的角色(对照 DataSource / EntityManager)
- 用 `Mapped[类型] + mapped_column(...)` 定义模型,用 `ForeignKey + relationship` 建一对多关系
- 用 `select() + where + order_by + offset/limit` 写多条件分页查询,用 `db.get` 按主键查
- 用 `add → commit → refresh` 三步写库;用**脏检查**改对象;`delete + commit` 删行
- 用 `scalar_one_or_none` 做唯一性检查(邮箱注册 409)
- 用 `select(A, B).join(...)` 做两表关联查询,说清 **N+1 问题**是什么、怎么避免
- 解释「commit 之前抛异常 = 什么都没写」,用它实现下单的事务原子性

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `list_products` | §19.5 | select + 多条件 where + order_by + **offset/limit 分页** |
| `get_product` | §19.5 | db.get 按主键查 + 404 |
| `create_product` | §19.6 | add → commit → refresh 三步写 |
| `update_product` | §19.6 | 脏检查:改字段 + commit(自动 UPDATE) |
| `delete_product` | §19.6 | db.get + delete + commit |
| `register_user` | §19.6 | scalar_one_or_none 唯一性检查 + 409 |
| `place_order` | §19.7 | 外键校验 + 扣库存 + **事务原子性**(本章重点) |
| `list_user_orders` | §19.7 | select(双模型).join 关联查询 + Row 元组解包 |

**脚手架**(不用填,读它理解):`engine`/`SessionLocal`(§19.2)、`User`/`Product`/`Order` 三表模型(§19.3)、`get_db` yield 依赖(§19.4)、`row_to_dict` 辅助函数、`health` 端点。

---

## ⏱️ 学习路径:费曼五步(约 90-120 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 JPA 直觉题,猜 SQLAlchemy 怎么答 | 本页 ① |
| ② 先动手 | 打开 `ch19_assignment.py`,**先读三表模型**,再试着写 | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「为什么要 commit」「下单为什么不会扣了库存却没写成订单」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。
> 本章作业形态:`填 FastAPI 端点函数体`(端点是同步 `def`,FastAPI 丢线程池跑,与同步 Session 绝配,见 §19.9)。

---

## ① 预览猜(2 分钟 · 激活你的 JPA 直觉)

先别看答案,凭 15 年 Java 经验猜:
1. JPA 的 `@Entity` + `@Id @GeneratedValue`。SQLAlchemy 2.0 怎么声明「这个类是表、这个属性是自增主键」?
2. `EntityManager.persist(p)` 之后,数据立刻进库了吗?SQLAlchemy 的 `db.add(p)` 呢?
3. JPA 里改了托管对象的字段,`transaction.commit()` 时自动发 UPDATE(脏检查)。SQLAlchemy 也有吗,还是得手写 UPDATE 语句?
4. 「下单:扣库存 + 写订单」两步,第 2 步失败会怎样?你需要手动回滚第 1 步吗?
5. `for order in orders: print(order.product.name)`——100 个订单会发几条 SQL?JPA 老手管这叫什么?

> 猜完带着验证心态进正文。第 2 题的「**add 只是暂存**」、第 4 题的「**commit 前抛异常 = 全没发生**」、第 5 题的「**N+1**」是本章最高频考点。

---

## §19.1 为什么用 ORM:从内存 dict 到真数据库(开胃 · 不出题)🟢

前几章商品存在内存 `list[dict]` 里——重启就没、没法并发安全地改、更别说「查张三的订单连带商品名」。真实后端要**持久化到关系型数据库**。

两条路,Java 你都走过:

| 路线 | Java 对应物 | Python 对应物 | 特点 |
|------|------------|--------------|------|
| 自己写 SQL | MyBatis / JdbcTemplate | SQLAlchemy **Core** | SQL 全控,结果得手映射对象 |
| 对象映射 | JPA / Hibernate | SQLAlchemy **ORM**(本章) | 类映射表,框架生成 SQL |

> 🟢 **关键认知**:SQLAlchemy 2.0 是 Python 的事实标准 ORM(地位 ≈ Hibernate)。它的 ORM 层 ≈ JPA,Core 层 ≈ MyBatis 的 SQL 构建器。本章只用 ORM 层。

### 本章的库表设计(三表一对多)

```text
users    ──< orders >──  products
 id           id           id
 name         user_id  ─┐  name
 email        product_id ┘ category
              quantity    price
              total_price stock
              status
```

一个用户有多个订单(1:N),一个商品出现在多个订单里(1:N),订单是连接表——这是电商最经典的建模样式。JPA 里你会写 `@ManyToOne` / `@OneToMany`,SQLAlchemy 对应物见 §19.3。

---

## §19.2 engine + Session:连接管理(对应:脚手架)🟡

### Java 对照最小例

```java
// DataSource:全局一个连接池
DataSource ds = new HikariDataSource(config);
// EntityManager:每请求/每事务一个,短命,跟踪你改了哪些对象
EntityManager em = entityManagerFactory.createEntityManager();
```

### Python 写法(作业里已写好,读懂)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:",                       # 连接串(生产换 postgresql://user:pass@host/db)
    connect_args={"check_same_thread": False},  # 坑①:SQLite 默认不许跨线程用连接
    poolclass=StaticPool,                       # 坑②:让所有连接共享同一份内存库
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

- **engine** = 连接池 + 驱动(= `DataSource`)。全局一个,所有请求共享。
- **Session** = 一次**工作单元**(Unit of Work):跟踪你 add/改了哪些对象,`commit()` 时统一落库(= `EntityManager`)。**每请求新建一个**,用完即关。
- **SessionLocal** 是 Session 的**工厂**(`sessionmaker` 的产物),`SessionLocal()` 产一个新 Session。

> 🟡 **两个配置项先记住结论**:`autoflush=False` = 查询前不自动把暂存改动刷进库(行为更可预测);`expire_on_commit=False` = commit 后对象属性**不过期**,能继续读(否则 commit 后再读 `p.name` 会触发一次 SELECT,测试里很烦)。

### SQLite 内存库的两个坑(本章用内存库跑测试,生产别用)

❌ **错误写法**(两个坑都踩):

```python
engine = create_engine("sqlite:///:memory:")
# 坑①:FastAPI 是多线程,SQLite 默认连接绑线程 → 跨线程用就 ProgrammingError
# 坑②::memory: 数据库是「连接级」的——建表用连接 A,查询用连接 B,B 里根本没有表!
```

✅ **正确写法**:`connect_args={"check_same_thread": False}`(允许多线程共享)+ `poolclass=StaticPool`(全池共用一个底层连接,大家看到同一份内存库)。**生产用 `sqlite:///./app.db` 或 Postgres 就没有这两个坑**。

---

## §19.3 模型定义:Mapped + ForeignKey + relationship(对应:脚手架)🔴

### Java 对照最小例

```java
@Entity @Table(name = "orders")
public class Order {
    @Id @GeneratedValue private Long id;
    @ManyToOne @JoinColumn(name = "user_id") private User user;   // 多对一
    private Integer quantity;
}
```

### Python 写法(SQLAlchemy 2.0,作业里已写好)

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):   # 所有模型的基类(2.0 现代写法)
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")  # 一对多(不建列!)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)      # ← 真外键列
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int]
    total_price: Mapped[float]
    status: Mapped[str] = mapped_column(default="created")
    user: Mapped[User] = relationship(back_populates="orders")       # 多对一导航属性
    product: Mapped[Product] = relationship(back_populates="orders")
```

逐参数对照:

| SQLAlchemy 2.0 | JPA | 作用 |
|----------------|-----|------|
| `class Base(DeclarativeBase)` | (无直接对应,≈ 元模型) | 收集所有模型的表结构元数据 |
| `__tablename__ = "orders"` | `@Table(name=...)` | 表名(**2.0 必填**,漏了就报错) |
| `Mapped[int]` | 字段类型 `Long` | 列的 Python 类型(IDE/mypy 可查) |
| `mapped_column(primary_key=True, autoincrement=True)` | `@Id @GeneratedValue` | 自增主键 |
| `mapped_column(unique=True, index=True)` | `@Column(unique=...)` + `@Index` | 唯一约束 / 索引 |
| `mapped_column(ForeignKey("users.id"))` | `@JoinColumn` | **外键列**(真实建列) |
| `relationship(back_populates=...)` | `@OneToMany` / `@ManyToOne` | **导航属性**(不建列,ORM 层面按外键找对象) |
| `mapped_column(default="created")` | 字段初始值 | 插入时不给值就用它 |

> 🔴 **Java 老手最容易混的一点**:`ForeignKey` 和 `relationship` 是**两层东西**。`user_id = mapped_column(ForeignKey(...))` 才是数据库里那列;`user = relationship(...)` 只是「按外键把 User 对象捞出来」的便捷导航,**不建任何列**。两者配合 = JPA 的 `@ManyToOne + @JoinColumn` 合体。

### 建表

```python
Base.metadata.create_all(engine)   # 按所有模型定义 CREATE TABLE(测试用;生产用 Alembic,§19.9)
```

❌ **错误写法 1**(用 1.x 老写法,2.0 项目里风格混用):

```python
from sqlalchemy import Column, Integer
id = Column(Integer, primary_key=True)   # 老写法,能跑但失去类型注解,2.0 项目别这么写
```

✅ **正确写法**:`id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)`。

❌ **错误写法 2**(以为 `relationship` 会建列):

```python
class Order(Base):
    user: Mapped[User] = relationship(...)   # 只写导航属性,没写 user_id 外键列 → 建表后没这列,关联报错
```

✅ **正确写法**:外键列(`user_id`)+ 导航属性(`user`)**都写**,靠 `back_populates` 互指。

---

## §19.4 get_db:每请求一个 Session(对应:脚手架,复用 Ch16)🟡

```python
def get_db():
    db = SessionLocal()      # ① setup:新建 Session
    try:
        yield db             # ② 端点注入拿到的就是它
    finally:
        db.close()           # ③ teardown:请求结束总关闭(即使端点抛异常)

@app.get("/products")
def list_products(db: Session = Depends(get_db)): ...
```

这正是 Ch16 的 **yield 依赖三段式**。每个 HTTP 请求拿一个**全新** Session,响应后关闭。

> 🤯 **为什么不能全局共享一个 Session**:Session 是**有状态**的——它跟踪脏对象、缓存查过的行。两个并发请求共用一个 Session,请求 A 读到一半的缓存会污染请求 B,还会把别人没 commit 的改动捎带提交。= Java 里你绝不会把 `EntityManager` 声明成单例 Bean,一个道理(Spring 的 `OpenEntityManagerInView` 也是「每请求一个 EntityManager」)。

❌ **错误写法**:

```python
db = SessionLocal()          # 模块级全局 Session,所有请求共享 → 并发污染 + 连接泄漏
@app.get("/products")
def list_products(): ...
```

✅ **正确写法**:`db: Session = Depends(get_db)`,让框架每请求注入新的。

---

## §19.5 查询:select / where / 分页 / db.get(对应:`list_products`、`get_product`)🔴

SQLAlchemy 2.0 用 **`select()`** 构造查询(1.x 的 `session.query(...)` 已淘汰,别在老博客上学它)。

### Java 对照最小例

```java
// JPQL:查图书类目、价格 80~100、按 id 排序、第 2 页每页 2 条
List<Product> list = em.createQuery(
    "SELECT p FROM Product p WHERE p.category = :c AND p.price BETWEEN :lo AND :hi ORDER BY p.id",
    Product.class)
    .setParameter("c", "图书").setParameter("lo", 80.0).setParameter("hi", 100.0)
    .setFirstResult(2).setMaxResults(2)      // offset / limit
    .getResultList();
Product one = em.find(Product.class, 3L);    // 按主键
```

### Python 写法(三连:`execute → scalars → all`)

```python
from sqlalchemy import select

stmt = select(Product)                                  # SELECT products.*
stmt = stmt.where(Product.category == "图书")            # 链式加条件 = WHERE ... AND ...
stmt = stmt.where(Product.price >= 80.0).where(Product.price <= 100.0)
stmt = stmt.order_by(Product.id)                        # ORDER BY id
stmt = stmt.offset((page - 1) * size).limit(size)       # 分页:page=2,size=2 → OFFSET 2 LIMIT 2
rows = db.execute(stmt).scalars().all()                 # → [Product, Product]
```

**为什么是三连**:`db.execute(stmt)` 返回 `Result`(行的集合);`.scalars()` 把每行「拆」出单个 ORM 对象(单实体查询时每行就一个 Product);`.all()` 取成 list。三步各管一段,少一步拿到的都不是「商品对象列表」。

### 真实场景例(电商后台商品列表:类目 + 价格区间 + 分页)

作业 `list_products` 的查询参数全是可选的,给了才加条件——**stmt 是不可变拼接,每次 `stmt = stmt.where(...)` 生成新语句**:

```python
def list_products(category=None, min_price=None, max_price=None, page=1, size=10, db=...):
    stmt = select(Product)
    if category is not None:
        stmt = stmt.where(Product.category == category)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    stmt = stmt.order_by(Product.id).offset((page - 1) * size).limit(size)
    return [row_to_dict(p) for p in db.execute(stmt).scalars().all()]
```

用本章测试种子数据(6 个商品:键盘 599、鼠标 159、Python编程 89、设计模式 75.5、重构 99、耳机 1299)手算验证:

```text
GET /products?category=图书                    → 3 本(id 3/4/5)
GET /products?min_price=80&max_price=100       → Python编程(89)、重构(99)…… 还有设计模式(75.5)?不,75.5<80 → 2 本
GET /products?size=2&page=2                    → 第 2 页:id [3, 4]
GET /products?category=图书&size=2&page=2      → 图书里第 2 页:[重构](id 5)
```

> 🟡 **分页公式**:`offset = (page - 1) * size`(page 从 1 开始,符合前端习惯)。这是 Ch15 学过的分页参数落到 SQL 的样子:`OFFSET ? LIMIT ?`。

### 按主键查:`db.get`,最直接

```python
p = db.get(Product, 3)     # SELECT ... WHERE id = 3;查不到返回 None(= EntityManager.find)
if p is None:
    raise HTTPException(status_code=404, detail="商品不存在")
```

### 单行或空:`scalar_one_or_none`(注册查邮箱用)

```python
exists = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
# 恰好一行 → User 对象;没有 → None;多于一行 → 报错(配合 unique 约束,不可能发生)
```

| 取结果 API | 适用 |
|-----------|------|
| `.scalars().all()` | 列表(0~N 行) |
| `.scalar_one_or_none()` | 0 或 1 行(唯一性检查) |
| `db.get(Model, pk)` | 按主键,0 或 1 行 |

### ❌ → ✅ 对照

❌ **错误写法 1**(三连只写一半):

```python
rows = db.execute(stmt)                 # 这是 Result,不是列表!for 循环拿到的是 Row 元组
return rows                             # FastAPI 序列化失败或得到奇怪嵌套
```

✅ **正确写法**:`db.execute(stmt).scalars().all()`。

❌ **错误写法 2**(手拼 SQL,注入警告):

```python
db.execute(text(f"SELECT * FROM products WHERE category = '{category}'"))
# category = "'; DROP TABLE products;--" → 删表。MyBatis 里 ${} 的同款事故
```

✅ **正确写法**:`Product.category == category` 不是 Python 比较!ORM 拦截 `==` 生成**参数化** SQL(`WHERE category = ?`,值单独传给驱动)——**天然防注入**,≈ JPA 的 Criteria API。

> ✅ 做 `list_products`:照抄上面真实场景例的结构(可选参数 → 条件拼接 → order_by → offset/limit)。做 `get_product`:`db.get` + None → 404。

---

## §19.6 写入:add / commit / refresh / 脏检查 / delete(对应:`create_product`、`update_product`、`delete_product`、`register_user`)🟡

### Java 对照最小例

```java
em.getTransaction().begin();
Product p = new Product("降噪耳机", 1299.0);
em.persist(p);                    // 暂存,还没 INSERT
p.setPrice(1199.0);               // 托管对象改字段 → 脏检查,commit 时自动 UPDATE
em.getTransaction().commit();     // 此刻才真正写库
em.refresh(p);                    // 拿回 DB 生成的值
em.remove(p);                     // 删除
```

### 创建三步:add → commit → refresh

```python
p = Product(name="降噪耳机", category="影音设备", price=1299.0, stock=80)
db.add(p)         # ① 放进 Session「待办」——此刻【没有发任何 SQL】
db.commit()       # ② 提交事务:把待办统一落库(INSERT)
db.refresh(p)     # ③ 重查一次,把 DB 生成的自增 id 填回 p
return row_to_dict(p)             # 现在才有 p.id
```

> 🔴 **`add` 只是暂存,`commit` 才真写**。这是 ORM 的工作单元模式:攒一批改动,一次事务提交。忘了 `commit`,请求结束 Session 一关,数据**悄无声息地丢**——这是 Java 老手转过来最常踩的坑,没有之一。

### 修改:脏检查(改字段 + commit,不用写 UPDATE)

```python
p = db.get(Product, product_id)
if p is None:
    raise HTTPException(status_code=404, detail="商品不存在")
p.name = payload.name          # 直接改对象属性
p.price = payload.price
db.commit()                    # Session 跟踪到 p「脏了」,commit 时自动生成 UPDATE
```

> 🤯 **Java 对比**:这就是 JPA 的 dirty checking + flush。`db.get` 拿回来的对象是**托管状态**,改属性会被跟踪;`commit` 时 ORM 比对出变化,只 UPDATE 变了的行。因为脚手架设了 `expire_on_commit=False`,commit 后 `p` 的属性仍然可读,直接 return。

### 删除:get + delete + commit

```python
p = db.get(Product, product_id)
if p is None:
    raise HTTPException(status_code=404, detail="商品不存在")
db.delete(p)      # 标记删除(= em.remove)
db.commit()       # 提交,真正 DELETE
return {"deleted": product_id}
```

### 真实场景例(注册:唯一性检查 + 409)

「邮箱已注册」是写入类接口的标配业务校验——**先查再插**:

```python
def register_user(payload, db):
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail="邮箱已注册")   # 409 Conflict
    u = User(name=payload.name, email=payload.email)
    db.add(u); db.commit(); db.refresh(u)
    return row_to_dict(u)
```

> 🟡 **注意**:先查再插在**并发**下有竞态(两个请求同时查都为空、同时插)。真正的兜底是列上的 `unique=True` 约束(§19.3 已建)+ 捕获 `IntegrityError`。本章作业只要求先查再插,知道有这回事即可。

### ❌ → ✅ 对照

❌ **错误写法 1**(add 之后忘 commit):

```python
db.add(p)
return row_to_dict(p)    # 请求正常返回,但数据根本没进库!下个请求查不到
```

✅ **正确写法**:`db.add(p); db.commit(); db.refresh(p)` 三步齐全。

❌ **错误写法 2**(忘 refresh 就拿 id):

```python
db.add(p); db.commit()
return {"id": p.id}      # expire_on_commit=False 时 p.id 其实还在……但新建对象 commit 后 id 由 DB 生成,
                         # 不 refresh 就依赖配置行为,换配置就炸。显式 refresh 最稳
```

✅ **正确写法**:新建后 `db.refresh(p)` 再读 `p.id`。

> ✅ 做 `create_product` / `update_product` / `delete_product` / `register_user`:创建三步、改字段+commit、delete+commit、先查再插+409。

---

## §19.7 关系查询与事务:join / N+1 / 原子提交(对应:`place_order`、`list_user_orders`)🔴

本章最有业务感的两题。**下单**和**查订单带商品详情**,单表 CRUD 都搞不定。

### 下单:事务原子性(commit 前抛异常 = 什么都没写)

业务规则:校验用户存在 → 校验商品存在 → 校验库存够 → **扣库存 + 写订单,两步必须同生共死**:

```python
def place_order(payload, db):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="库存不足")     # ← 在任何改动之前抛出

    product.stock -= payload.quantity              # 脏检查:commit 时 UPDATE products
    order = Order(user_id=user.id, product_id=product.id, quantity=payload.quantity,
                  total_price=round(product.price * payload.quantity, 2))
    db.add(order)                                  # commit 时 INSERT orders
    db.commit()                                    # ★ UPDATE + INSERT 在同一事务,要么都成要么都败
    db.refresh(order)
    return row_to_dict(order)
```

> 🔴 **为什么这样是原子的**:`product.stock -= ...`(UPDATE)和 `db.add(order)`(INSERT)都只是 Session 里的**待办**,`db.commit()` 把它们包在**一个事务**里发出。commit 成功 = 两个都落库;commit 前任何一步抛异常(比如库存不足),Session 随请求关闭时**未提交的待办全部丢弃**——库存一分没扣,订单一行没有。这正是你需要的行为,**不用手写 rollback**。
> = Java:`@Transactional` 方法里抛 RuntimeException → 整体回滚。SQLAlchemy 更直白:没 commit 就等于没发生。

❌ **错误写法**(先 commit 一半):

```python
product.stock -= payload.quantity
db.commit()                      # 库存扣了!
db.add(order); db.commit()       # 万一这步炸了 → 库存没了订单没有,数据不一致
```

✅ **正确写法**:所有改动攒着,**最后只 commit 一次**。

❌ **错误写法 2**(校验顺序颠倒,先扣库存再发现用户不存在):

```python
product.stock -= payload.quantity
user = db.get(User, payload.user_id)
if user is None:
    raise HTTPException(404, ...)   # 抛是抛了,本次请求确实没 commit……
                                    # 但逻辑已乱,若哪天中间夹了个 commit 就直接事故。先校验、后动手
```

✅ **正确写法**:**所有校验在前,所有改动在后**(validate-then-mutate)。

### 关联查询:`select(双模型).join(...)`

「张三的订单列表,每条带商品名」需要 orders ⋈ products:

```python
rows = db.execute(
    select(Order, Product)                                   # 选两个模型
    .join(Product, Order.product_id == Product.id)           # INNER JOIN ON ...
    .where(Order.user_id == user_id)
    .order_by(Order.id)
).all()                                                      # ★ 注意:这里没有 .scalars()
return [{"order_id": o.id, "product_name": p.name, "quantity": o.quantity,
         "total_price": o.total_price, "status": o.status} for o, p in rows]   # 按元组解包
```

> 🔴 **多实体 select 别加 `.scalars()`**:`select(Order, Product)` 每行是 `(Order, Product)` 二元组,`.all()` 后直接 `for o, p in rows` 解包。加 `.scalars()` 会把每行的 Product **悄悄丢掉**,只剩 Order——这是多表查询最常见的错。

> 🟡 **Java 对比**:≈ JPQL `SELECT o, p FROM Order o JOIN Product p ON o.productId = p.id WHERE o.userId = :uid`,结果 `List<Object[]>`。`.join(Product, on条件)` 显式给 ON 条件;若模型里建了 relationship,也可以 `.join(Order.product)` 让 ORM 自己推 ON。

### N+1 问题:relationship 遍历的代价(JPA 老熟人)

有 `relationship` 导航属性,理论上可以这样拿商品名:

```python
orders = db.execute(select(Order).where(Order.user_id == user_id)).scalars().all()
for o in orders:
    print(o.product.name)    # 懒加载:每访问一次 o.product,发一条 SELECT!
```

10 个订单 = 1 条查订单 + 10 条查商品 = **11 条 SQL**。这就是 N+1——你在 Hibernate 里见过一模一样的(`LazyInitializationException` 之外的隐蔽性能杀手)。

| 方案 | SQL 数 | 写法 |
|------|--------|------|
| 懒加载遍历 | 1 + N | `o.product.name`(隐式,危险) |
| **显式 join**(本章作业方案) | 1 | `select(Order, Product).join(...)` |
| 预加载 | 2(批量 IN) | `select(Order).options(selectinload(Order.product))` |

❌ **错误写法**:循环里 `o.product.name` 懒加载,N+1。

✅ **正确写法**:要展示字段就**显式 join 一次查全**(作业 `list_user_orders` 的做法);要保留 ORM 对象导航就用 `selectinload` 预加载(了解即可)。

### 多对多(了解 · 不出题)

商品 ↔ 标签这种多对多,需要第三张**关联表**(association table):`product_tags(product_id, tag_id)`,然后 `relationship(secondary=product_tags)`。概念和 JPA `@ManyToMany @JoinTable` 一致,本章用不到,见到认识即可。

> ✅ 做 `place_order`:校验(用户→商品→库存)→ 扣库存 → 造 Order → **一次 commit** → refresh。做 `list_user_orders`:先 `db.get(User, ...)` 404 → `select(Order, Product).join(...)` → `for o, p in rows` 解包拼 dict。

---

## §19.8 测试隔离:autouse fixture + 内存库(脚手架 · 了解)🟢

测试不能互相污染数据。测试文件里的方案(**已写好**):

```python
@pytest.fixture(autouse=True)      # 每个 test 自动套用,不用逐个声明
def reset_db():
    Base.metadata.drop_all(engine)     # 清掉上个 test 的表
    Base.metadata.create_all(engine)   # 建全新空表
    yield
    Base.metadata.drop_all(engine)
```

每个 test 看到的都是空库,需要数据时用 `SessionLocal` 直接塞(绕过 HTTP,准备前置数据)或走 POST 接口。测试断言也可以直接用 `SessionLocal` 查库验证「真的写进去了」——比如下单后验证库存行真的变了。

> 🟢 **Java 对比**:≈ `@Sql` 清库脚本 / `@DirtiesContext`,但 pytest 的 autouse fixture 更轻。生产环境的表结构演进别用 `create_all`,用 **Alembic**(§19.9)。

---

## §19.9 延伸阅读:异步 SQLAlchemy + Alembic(了解 · 不出题)🟢

**异步 SQLAlchemy**:本章端点是 `def`(同步),FastAPI 丢线程池跑,和同步 Session 是**安全组合**(Ch18 §18.7 的取舍)。高并发场景可换 `create_async_engine` + `AsyncSession`(配 asyncpg 驱动),端点随之改 `async def`、处处 `await db.execute(...)`。2.0 的同步/异步 API 几乎同构,先把同步练熟。

**Alembic**(= Java 的 Flyway/Liquibase,已在 web extras 里):

```bash
alembic init migrations            # 初始化迁移目录
alembic revision --autogenerate -m "add orders table"   # 对比模型与库,自动生成迁移脚本
alembic upgrade head               # 执行迁移(= flyway migrate)
```

`create_all` 只会「从无到有建表」,不会给已有表加列;生产上表结构变更一律走 Alembic 版本化迁移。

---

## §19.10 Java 老手常踩的坑 ⚠️

1. **add 后忘 commit**:数据没进库,请求还正常返回,最隐蔽。三步:`add → commit → refresh`。
2. **Session 全局共享**:并发污染。每请求一个(`Depends(get_db)`)。
3. **`execute` 后忘 `.scalars().all()`**:拿到的是 `Result` 不是对象列表。
4. **多实体 select 加 `.scalars()`**:`select(Order, Product).join(...)` 加 scalars 会丢掉 Product,只剩 Order。
5. **`Product.category == x` 当布尔值用**:它是构造 WHERE 子句的表达式,不是比较结果(同时这也解释了为什么 ORM 天然防注入)。
6. **以为 `relationship` 建列**:不建。外键列要单独写 `mapped_column(ForeignKey(...))`。
7. **下单分两次 commit**:第一次 commit 成功、第二次失败 → 库存扣了订单没有。所有改动攒到最后一次 commit。
8. **循环里访问 `o.product`**:N+1。要么显式 join,要么 `selectinload`。
9. **SQLite 内存库不配 StaticPool**:建表和查询落在不同连接,表「时隐时现」。
10. **生产用 `create_all` 演进表结构**:它不会 ALTER。用 Alembic。

---

## §19.11 速查:SQLAlchemy 2.0 ↔ JPA 对照

| SQLAlchemy 2.0 | JPA / Hibernate | 说明 |
|----------------|-----------------|------|
| `engine` | `DataSource` | 连接池,全局一个 |
| `Session` | `EntityManager` | 工作单元,每请求一个 |
| `sessionmaker(...)` | `EntityManagerFactory` | Session 工厂 |
| `Mapped[int] + mapped_column(...)` | `@Column` + 字段类型 | 类型化列定义 |
| `mapped_column(ForeignKey(...))` | `@JoinColumn` | 外键列 |
| `relationship(...)` | `@OneToMany` / `@ManyToOne` | 导航属性,不建列 |
| `select(X).where(...)` | JPQL / Criteria | 参数化,防注入 |
| `.order_by / .offset / .limit` | `ORDER BY` / `setFirstResult` / `setMaxResults` | 排序分页 |
| `db.get(X, id)` | `em.find(X.class, id)` | 按主键 |
| `.scalars().all()` | `.getResultList()` | 取对象列表 |
| `.scalar_one_or_none()` | `.getSingleResult()`(不抛版) | 0 或 1 行 |
| `db.add(p)` | `em.persist(p)` | 暂存,未写库 |
| `db.commit()` | `transaction.commit()` | 事务提交,真正落库 |
| `db.refresh(p)` | `em.refresh(p)` | 拿回 DB 生成值 |
| `db.delete(p)` | `em.remove(p)` | 删除 |
| 改字段 + commit(脏检查) | dirty checking + flush | 自动 UPDATE |
| `selectinload` | `JOIN FETCH` | 预加载,治 N+1 |
| Alembic | Flyway / Liquibase | 版本化迁移 |
| `create_all` | `hbm2ddl.auto=create` | 仅测试用 |

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `list_products` | 多条件 where + order_by + offset/limit 分页 | 🔴 |
| `get_product` | db.get 按主键 + 404 | 🟢 |
| `create_product` | add → commit → refresh | 🟡 |
| `update_product` | 脏检查改字段 + commit | 🟡 |
| `delete_product` | delete + commit | 🟢 |
| `register_user` | scalar_one_or_none 唯一性检查 + 409 | 🟡 |
| `place_order` | 外键校验 + 扣库存 + 事务原子性(重点) | 🔴 |
| `list_user_orders` | join 关联查询 + 元组解包 | 🔴 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v
```

期望:45 个全绿。

---

## ✅ 自测清单

- [ ] 能说清 engine / Session / SessionLocal 各是什么、对应 Java 什么
- [ ] 能写 `Mapped[int] = mapped_column(primary_key=True)`,并说清 `ForeignKey` 与 `relationship` 的区别
- [ ] 能用 `select + where(多条件) + order_by + offset/limit` 写分页查询,三连取结果
- [ ] 知道 `add` 只是暂存、`commit` 才真写、`refresh` 拿自增 id
- [ ] 能解释脏检查:为什么改完字段只要 `commit` 就有 UPDATE
- [ ] 能用 `scalar_one_or_none` 做唯一性检查并返回 409
- [ ] 能解释下单的原子性:commit 前抛异常为什么等于什么都没写
- [ ] 能写 `select(A, B).join(...)`,知道多实体查询**不加** `.scalars()`
- [ ] 能说清 N+1 是什么、两种解法(join / selectinload)
- [ ] 45 个测试全绿

---

## 🎓 费曼挑战(合上教程讲清「为什么」)

1. **「`db.add(p)` 之后数据到底在哪?为什么要 `commit`?为什么还要 `refresh`?」**
   — 卡壳重读 §19.6。(关键词:工作单元、暂存待办、事务、自增 id 由 DB 生成)

2. **「下单扣库存为什么不用手写 `db.rollback()` 也能保证不出错?如果分成两次 commit 会出什么事?」**
   — 卡壳重读 §19.7。(关键词:未 commit = 未发生、单事务、数据不一致)

3. **「`Product.category == category` 明明是 `==`,为什么说它不是比较、还天然防 SQL 注入?」**
   — 卡壳重读 §19.5。(关键词:表达式对象、参数化、值后填)

4. **「`for o in orders: o.product.name` 100 个订单发几条 SQL?怎么用一条 SQL 搞定?」**
   — 卡壳重读 §19.7。(关键词:N+1、懒加载、显式 join)

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch19 掌握后,进 **Ch20 · 测试 API 进阶**(fixtures + parametrize + 覆盖率 + 依赖覆盖)——你已经见过 autouse fixture 隔离数据库,下一章把这套测试功夫练到专业级。
