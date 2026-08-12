# Ch34 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Python 刷题为什么爽?(一句话) | stdlib 把高频样板(Counter/heapq/bisect/lru_cache…)封装成语义化一行,省掉 Java 手写 HashMap/堆/二分/缓存的样板,让你专注算法思路 | ⬜ |
| 2 | 统计频次 + 取前 k 怎么写?平局怎么排? | `Counter(x).most_common(k)`;Counter 是 dict 子类,most_common 返回 (元素,次数) 元组降序列表,平局按【首次出现顺序】(3.7+ 保证),空输入返回 [] | ⬜ |
| 3 | defaultdict(int) 凭什么免判空?int 是什么角色? | 缺 key 时自动调【工厂函数】 int() 得 0 并存入,所以能直接 +=。要传类型本身(defaultdict(int)),不是实例。分组列表用 defaultdict(list) | ⬜ |
| 4 | defaultdict 使用收尾要注意什么? | 读不存在的 key 也会【创建】它;返回/交给下游前 `dict(totals)` 转回普通 dict,把自动建 key 的副作用关住 | ⬜ |
| 5 | 第 k 大怎么写?返回单值还是列表?何时该全排序? | `heapq.nlargest(k, nums)[-1]`——返回【降序列表】,[-1] 才是第 k 大。k≪n 用 nlargest(O(n log k) 省内存);k≈n 用 sorted(reverse=True)[k-1] 常数更小 | ⬜ |
| 6 | 为什么队列别用 list.pop(0)?定长滑窗怎么写? | pop(0) 头部删除 O(n)(整体搬移);队列用 deque,定长用 deque(maxlen=n)——满了 append 自动踢最旧,Java ArrayDeque 没有这语义 | ⬜ |
| 7 | bisect_left 返回什么?统一了哪两种语义?前提? | 升序数组里【第一个 >= target 的下标】;统一「命中」和「该插哪」。前提:数组【已升序】,bisect 不检查 | ⬜ |
| 8 | bisect_left vs bisect_right? | 有重复时:left 最左 >=target(插到重复元素前,LC35 用它);right 最右 >target。无重复等价 | ⬜ |
| 9 | 「分数降序、同分名字升序」一行怎么写?原理? | `sorted(records, key=lambda r: (-r[1], r[0]))`。key 元组【逐元素】比较;数值键取负把降序转升序。字符串键不能取负(TypeError),字符串降序靠 sorted 稳定性排两次(先次键后主键) | ⬜ |
| 10 | sorted() 和 list.sort() 的区别? | sorted() 返回【新列表】;list.sort() 原地排返回 None——`xs = xs.sort()` 会把 xs 变成 None | ⬜ |
| 11 | 前缀和一行怎么写?两个坑? | `list(accumulate(nums))`。坑:① 返回【迭代器】要 list() 物化;② 做区间和时用 initial=0 补前导 0 可省端点特判。func=operator.mul 变前缀积 | ⬜ |
| 12 | 数组右轮转 k 位一行怎么写?两个前置步骤? | `nums[-k:] + nums[:-k]`(= Java 三次反转)。前置:① `if not nums: return []` 挡空(否则 k%0 崩);② `k %= len(nums)` 归一。k=0 时 -0==0 碰巧对,别依赖 | ⬜ |
| 13 | lru_cache 怎么用?两个限制? | `@lru_cache(maxsize=None)` 紧贴 def(带括号),自动缓存 参数→返回值。限制:① 参数必须 hashable(list 崩,改 tuple);② 递归 >1000 仍栈溢出,那时改迭代 DP | ⬜ |
| 14 | 一趟扫描求 min/max 的哨兵怎么初始化?空数组? | `min_val = float('inf')`、`max_val = float('-inf')`(≈ Integer.MAX_VALUE 但和 int 混比自如)。别用 0 当哨兵(负数数组全错);空数组先特判,别把 inf 泄漏给调用方 | ⬜ |
| 15 | stdlib 能替代算法思路吗? | 不能。stdlib 替代的是「样板」(统计/分组/二分/去重/记忆化),双指针/DP/回溯的思路还得自己想——Ch35-40 | ⬜ |

## 🎓 费曼自检

- [ ] 能对 Java 老友说清「Python 刷题的爽点」并各举一例(Counter / defaultdict / deque(maxlen) / bisect / lru_cache)?
- [ ] 能说清「defaultdict 的工厂函数机制」和「为什么返回前要 dict() 转回」?
- [ ] 能说清「key 元组多键排序」的原理,以及「字符串降序为什么不能取负、怎么办」?
- [ ] 能说清「lru_cache 和 Java 手写 HashMap 缓存的对应 + 它的两个局限」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
