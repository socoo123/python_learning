# Ch09 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `itertools.chain` 干嘛?比列表 `+` 好在哪? | 把多个可迭代对象首尾串联成**一条惰性流**。比 `+` 省内存(不建中间列表),且能拼任意可迭代对象(tuple/生成器都行)。手里是「列表的列表」用 `chain.from_iterable` | ⬜ |
| 2 | `itertools.groupby` 为什么【必须先排序】? | groupby 是**流式**的,只合并**相邻**的相同 key。不排序时 `[1,2,1]` 被切成三段。正确姿势:`sorted(同一 key 函数)` + `groupby`,两步缺一不可 | ⬜ |
| 3 | groupby 返回的 `g` 是什么?要注意什么? | `g` 是**迭代器**,用完即弃;外层循环一走它就空。要 `list(g)` 物化后再用 | ⬜ |
| 4 | `groupby` vs Ch08 `defaultdict(list)` 分组,怎么选? | 日常分组默认 **defaultdict**(任意顺序、不用排序);groupby 适合**数据已排序**(如按时间排好的日志)或**要 key 有序**的场景 | ⬜ |
| 5 | `combinations` / `permutations` / `product` 区别? | combinations=组合**不计顺序** C(n,r);permutations=排列**计顺序** P(n,r);product=笛卡尔积(a×b,**右边**跑最快,`repeat=n` 和自己做积) | ⬜ |
| 6 | `reduce(func, iterable, initial)` 三要素?initial 有何用? | func 接 (累积值, 当前元素);initial 是初始累积值,**空可迭代时返回它**。不传则用首元素当初始,空序列直接 TypeError。运算符函数在 `operator` 模块(add/mul) | ⬜ |
| 7 | 什么时候**不该**用 reduce? | 有现成函数就别用:`sum`/`max`/`min`/`math.prod`/`"".join`。reduce 留给「没有现成函数的自定义累积」(如 Σ price×stock、合并 dict) | ⬜ |
| 8 | 迭代器为什么不能 `stream[:n]`?无限流怎么取样? | 迭代器**没有切片**(TypeError);`list(stream)` 对无限流会卡死。用 `islice(stream, n)` 惰性取前 n 个,取到就停。判断:list 用 `[:n]`,迭代器/生成器用 islice | ⬜ |
| 9 | `@lru_cache` 怎么提速?两个适用条件? | 自动缓存「入参→返回值」,相同入参直接命中(递归 fib 从 O(2ⁿ)→O(n))。条件:① **纯函数**(不依赖时间/随机/外部状态);② **参数可哈希**(list/dict 当参数会 TypeError)。注意:**异常不被缓存** | ⬜ |
| 10 | `lru_cache(maxsize=...)` 参数?怎么看缓存有没有生效? | `maxsize=None` 不限容量;填数字则 LRU 淘汰最久未用。`f.cache_info()` 看 hits/misses,`f.cache_clear()` 清缓存(测试先 clear 再数,不依赖执行顺序) | ⬜ |
| 11 | `partial(func, *args)` 干嘛?和闭包怎么选? | 偏函数:**预先固定** func 的部分参数,生成新函数(柯里化替代)。`vip8 = partial(mul, 0.8)`。原函数「固定几个参数就行」用 partial 最省;要额外逻辑(校验/日志)回闭包 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「groupby 为何先排序、g 为何要 list() 物化、和 defaultdict 的取舍」?
- [ ] 能说清「lru_cache 提速原理 + 纯函数/可哈希两个条件 + cache_info 验证」?
- [ ] 能说清「迭代器 vs 列表:为什么 islice 能对无限流取样而 `[:n]` 不行」?
- [ ] 能默写 combinations / permutations / product 的区别?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
