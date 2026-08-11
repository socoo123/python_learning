# Ch03 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 列表推导式骨架?三部分的书写顺序和执行顺序? | `[表达式 for 变量 in 序列 if 条件]`。书写顺序 = 执行顺序:先 for,再 if 过滤,最后算表达式 | ⬜ |
| 2 | 推导式里「过滤 if」和「三元 if-else」位置有何不同? | 过滤 if 在 `for` **后**(决定要不要这个元素);三元 `x if c else y` 在 `for` **前**(每个元素都要,只换算法)。混了 = SyntaxError | ⬜ |
| 3 | `for-else` 的 else 什么时候执行?空循环呢? | 循环**没被 break/return 打断**(完整跑完)时执行;空循环一次没进也算「完整跑完」→ 进 else。和 if-else 毫无关系,更像「nobreak」 | ⬜ |
| 4 | 用 for-else 写「找第一条 ERROR,找不到返回 None」的结构? | `for line in logs: if "ERROR" in line: return line` + `else: return None` | ⬜ |
| 5 | enumerate 拿「索引+元素」,序号从 1 开始怎么写? | `enumerate(seq, start=1)`(start 默认 0)。别写 `for i in range(len(xs))`,那是 C/Java 遗风 | ⬜ |
| 6 | `zip(['a','b','c'], [1,2])` 结果?zip 返回的是什么类型? | `[('a',1),('b',2)]`——**按最短的截断**,静默丢数据。返回**迭代器**,要 `list(...)` 物化 | ⬜ |
| 7 | `first, *rest = xs` 做了什么?为什么迭代器只能这样拆? | first 拿第 1 个,rest 收「剩下全部」成 list。迭代器**没有下标、不能切片**(`it[0]` TypeError),但能星号解包。空序列解包会 ValueError,先判空 | ⬜ |
| 8 | Iterable vs Iterator?`iter()`/`next()`/到头分别对应 Java 什么? | Iterable = 能被遍历(≈ Java `Iterable`);Iterator = 游标(≈ `Iterator`)。`iter(x)` ≈ `x.iterator()`,`next(it)` ≈ `it.next()`,到头抛 `StopIteration` ≈ `hasNext()` 返回 false | ⬜ |
| 9 | 迭代器能遍历几次?`list(it)` 之后再 `list(it)` 呢? | **只能一次**,游标不回退。`list(it)` 物化后原迭代器已空,再 `list(it)` 是 `[]` | ⬜ |
| 10 | 函数体里有 `yield`,这个函数变成了什么?调用它会执行函数体吗? | 变成**生成器函数**。调用它**不执行函数体**,只返回生成器对象(可暂停的机器);`next()`/`for`/`list()` 才驱动它运转到下一个 yield | ⬜ |
| 11 | 生成器里 `yield` 和 `return` 的区别?写错了会怎样? | `yield` = 产出并暂停,下次继续;`return` = 彻底结束函数。生成器里误写 return → 只能交出第一个值,后面的全丢 | ⬜ |
| 12 | 生成器表达式 vs 列表推导式?`sum(1 for x in xs if c)` 里的括号去哪了? | `()` 是**惰性**生成器(边算边给,内存恒定),`[]` 立刻物化成列表。函数调用的括号里,生成器表达式作唯一参数可**省掉自己的 ()** | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「yield 让函数变成可暂停的机器,所以能流式处理 GB 级文件」?
- [ ] 能说清「for-else 的 else 是 nobreak,空循环也进 else」?
- [ ] 能说清「迭代器一次性,list(it) 物化是放弃惰性换随机访问」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
