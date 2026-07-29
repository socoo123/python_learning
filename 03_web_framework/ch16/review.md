# Ch16 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `Depends(f)` 怎么工作?和 Spring @Autowired 异同? | 端点声明 `param=Depends(f)`,FastAPI 调 f 把返回值注入 param。同:都是 DI。异:FastAPI 函数级、无 IoC 容器、默认每请求新建(适合 session);Spring 注入单例 bean | ⬜ |
| 2 | 三种依赖模式各是什么? | ① 函数依赖(返值注入)② 类依赖(打包多参数,返对象)③ yield 依赖(setup/yield值/teardown,需清理的资源) | ⬜ |
| 3 | yield 依赖如何保证 DB session 关闭?对应 Ch06 什么? | yield 前=获取资源,yield 值=注入,yield 后放 finally=清理(总执行,即使异常)。= Ch06 的 @contextmanager 三段套路 | ⬜ |
| 4 | `Depends(get_current_user)` 还是 `Depends(get_current_user())`? | **前者**(不调)!Depends 接收函数本身,FastAPI 负责调用。后者会立刻调用一次,错 | ⬜ |
| 5 | 鉴权依赖(get_current_user)为什么能在多端点复用?抛 401 会怎样? | 同一依赖函数多个端点 Depends,鉴权逻辑只写一处。依赖里 raise HTTPException(401) 会【短路】:端点不执行,直接返 401 | ⬜ |
| 6 | `Header(default=None)` 怎么用?x_token 对应哪个头? | 从请求头提取值。参数名 x_token → 自动找 X-Token 头(下划线转连字符)。default=None 表示可选 | ⬜ |
| 7 | 依赖默认是单例吗? | **不是**,默认每次请求新建(适合 DB session)。要单例用 `Depends(f, use_cache=True)` | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Depends 的工作机制 + vs Spring @Autowired」?
- [ ] 能说清「yield 依赖保证清理,对应 @contextmanager」?
- [ ] 能说清「鉴权依赖复用 + 401 短路」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
