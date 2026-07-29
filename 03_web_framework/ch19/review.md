# Ch19 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | engine / Session / SessionLocal 各是什么?对应 Java? | engine=连接池(=DataSource);Session=工作单元跟踪脏对象(=EntityManager,每请求新建);SessionLocal=Session 的工厂。sessionmaker(bind=engine) 造工厂 | ⬜ |
| 2 | SQLAlchemy 2.0 模型怎么定义?对应 Java? | `class X(DeclarativeBase): __tablename__=...; 字段: Mapped[类型] = mapped_column(...)`。= @Entity + @Column。Mapped[int] 类型化列 | ⬜ |
| 3 | 查列表三连 `execute().scalars().all()` 各干嘛? | execute(stmt)→Result 行集;scalars() 把每行拆成 ORM 对象(select 单实体时);all() 取成列表。少一步都拿不到对象列表 | ⬜ |
| 4 | `db.add(p)` 后数据入库了吗?完整写入几步? | 没入。add 只暂存(=JPA persist)。三步:add → commit(真写 INSERT)→ refresh(拿自增 id)。忘 commit 数据丢 | ⬜ |
| 5 | `Product.category == category` 是比较吗?为什么防注入? | 不是比较,是构造 WHERE 子句。ORM 拦截 == 生成参数化 SQL(WHERE category = ?,值后填),不用手拼字符串 → 天然防注入 | ⬜ |
| 6 | 按主键查最快的方法?对应 Java? | `db.get(Product, id)`(= EntityManager.find)。无需 select/where | ⬜ |
| 7 | get_db 为什么用 yield 依赖?每请求一个 Session 的原因? | 复用 Ch16 三段式(setup/yield/teardown)。Session 有状态(跟踪脏对象),跨请求共享会并发污染 → 每请求新建、用完即关 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「add/commit/refresh 各干了什么、为何要 refresh」?
- [ ] 能说清「ORM == 构造 SQL + 防注入原理」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
