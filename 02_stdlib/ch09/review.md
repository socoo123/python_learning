# Ch09 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `itertools.chain` 干嘛?比列表 `+` 好在哪? | 把多个可迭代对象首尾串联成一条流。比 `+` 省内存(不创建中间列表),且能拼任意可迭代对象 | ⬜ |
| 2 | `itertools.groupby` 为什么【必须先排序】? | groupby 只合并【相邻】的相同 key(它是流式的)。不排序,[1,2,1] 会被切成三段。正确做法:`sorted()` 再 `groupby`。日常分组用 defaultdict 更稳 | ⬜ |
| 3 | `combinations(items, r)` 和 `permutations` 区别? | combinations = 组合(不计顺序),C(n,r) 个;permutations = 排列(计顺序),P(n,r) 个。LeetCode 回溯题常用 | ⬜ |
| 4 | `reduce(func, iterable, initial)` 三个参数?initial 有何用? | func 接 (累积值, 当前元素);initial 是初始累积值,空可迭代时返回它(乘法传 1,加法传 0)。不传则用首元素当初始,空序列报错 | ⬜ |
| 5 | `@lru_cache` 怎么提速?有什么适用条件? | 自动缓存「入参→结果」,相同入参直接命中。把递归 fib 从 O(2ⁿ) 降到 O(n)。**只适合纯函数**,且参数必须【可哈希】(list/dict 不行)。`cache_info()` 看命中 | ⬜ |
| 6 | groupby 返回的 group 是什么?要注意什么? | group 是【迭代器】,用完即弃。要反复用得先 `list(g)` 物化 | ⬜ |
| 7 | `partial(func, *args)` 干嘛? | 偏函数:固定 func 的部分参数,生成新函数。= 柯里化替代。如 `double = partial(mul, 2)` | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「groupby 为何要先排序、和 defaultdict 分组的取舍」?
- [ ] 能说清「lru_cache 提速原理 + 适用条件」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
