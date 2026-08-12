# Ch19 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | engine / Session / SessionLocal 各是什么?对应 Java? | engine=连接池(=DataSource,全局一个);Session=工作单元,跟踪脏对象(=EntityManager,每请求新建);SessionLocal=Session 工厂(sessionmaker 产物) | ⬜ |
| 2 | SQLAlchemy 2.0 怎么定义模型类?对应 Java? | `class X(Base): __tablename__=...; 字段: Mapped[类型] = mapped_column(...)`,Base 继承 DeclarativeBase。= @Entity + @Column;Mapped[int] 类型化列 | ⬜ |
| 3 | ForeignKey 和 relationship 的分工? | ForeignKey 建真实外键列(=@JoinColumn);relationship 是导航属性、不建列(=@ManyToOne/@OneToMany),靠 back_populates 互指。两个都要写 | ⬜ |
| 4 | 查询三连 `execute().scalars().all()` 各干嘛?少一步呢? | execute→Result 行集;scalars() 把每行拆成单个 ORM 对象;all() 取列表。少了拿到的不是「对象列表」 | ⬜ |
| 5 | 取结果的 API 怎么选:列表 / 0或1行 / 按主键? | 列表 `.scalars().all()`;0或1行 `.scalar_one_or_none()`(唯一性检查);按主键 `db.get(Model, id)`(=em.find) | ⬜ |
| 6 | `db.add(p)` 后数据入库了吗?完整写入几步? | 没入,add 只是暂存待办。三步:add → commit(事务里真 INSERT)→ refresh(拿回 DB 自增 id)。忘 commit = 数据悄丢 | ⬜ |
| 7 | 改对象字段怎么写库?要写 UPDATE 吗? | 不用。db.get 拿回的是托管对象,改属性被脏检查跟踪,`db.commit()` 时自动发 UPDATE(= JPA dirty checking) | ⬜ |
| 8 | `Product.category == x` 是比较吗?为什么防注入? | 不是,是构造 WHERE 表达式。ORM 生成参数化 SQL(`WHERE category = ?`,值后填),不拼字符串 → 天然防注入 | ⬜ |
| 9 | offset/limit 分页公式?为什么必须先 order_by? | `offset((page-1)*size).limit(size)`(page 从 1 起)。不排序每页顺序不稳定,分页失去意义 | ⬜ |
| 10 | 下单「扣库存 + 写订单」怎么保证原子性?要手写 rollback 吗? | 两步都只是 Session 待办,最后一次 commit 同事务发出;commit 前抛异常 → 待办随 close 全丢弃,不用手写 rollback。忌拆两次 commit | ⬜ |
| 11 | 多实体查询 `select(Order, Product).join(...)` 能加 `.scalars()` 吗?怎么取结果? | 不能!scalars() 会把每行第二个实体悄悄丢掉。直接 `.all()` → 每行 (Order, Product) 元组,`for o, p in rows` 解包 | ⬜ |
| 12 | 什么是 N+1?本章两种解法? | 查 N 个订单后循环访问 `o.product`,懒加载每趟发 1 条 SQL → 1+N 条。解法:显式 join 一次查全 / `selectinload` 预加载(≈ JOIN FETCH) | ⬜ |
| 13 | get_db 为什么必须每请求一个 Session? | Session 有状态(脏对象跟踪+缓存),跨请求共享会并发污染。yield 依赖三段式:新建 → 注入 → finally 关闭 | ⬜ |
| 14 | SQLite 内存库的两个坑及解法?生产表结构变更用什么? | ① check_same_thread=False(多线程)② StaticPool(共享同一份内存库)。生产用 Alembic 迁移(=Flyway),create_all 不会 ALTER | ⬜ |

## 🎓 费曼自检

- [ ] 能讲清「add → commit → refresh」各自干了什么、忘一步的后果?
- [ ] 能讲清「commit 前抛异常 = 什么都没写」,并用它设计下单接口?
- [ ] 能讲清多实体 join 为什么不加 scalars、N+1 怎么避免?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
