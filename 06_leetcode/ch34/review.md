# Ch34 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Python 刷题为什么爽?(一句话) | stdlib 把高频样板封装成语义化一行(Counter/bisect/heapq/lru_cache),省掉 Java 手写 HashMap/二分/PriorityQueue/缓存的注意力,让你专注算法思路 | ⬜ |
| 2 | 统计字符频次 + 取前 3 怎么写? | `Counter(text).most_common(3)`。Counter 是 dict 子类,.most_common(k) 返回按次数降序的前 k 个 (元素,次数) 元组列表。Java 要 HashMap+sort | ⬜ |
| 3 | 第 k 大怎么写?返回的是单值还是列表? | `heapq.nlargest(k, nums)[-1]`。nlargest 返回【列表】(降序),`[-1]` 才是第 k 大那个单值。内部是 size=k 的小顶堆 O(n log k) | ⬜ |
| 4 | bisect_left 返回什么?统一了哪两种语义? | 返回升序数组里【第一个 >= target 的下标】。统一了「查找命中」和「找不到该插哪」两种情况——前提是数组【已升序】 | ⬜ |
| 5 | bisect_left vs bisect_right 区别? | 有重复元素时:left 返回最左 >=target(插到重复元素前),right 返回最右 >target。LC35 用 left。无重复时等价 | ⬜ |
| 6 | 去重保序怎么写?能用 set 吗? | 【不能】用 set(set 不保序)。用 `list(dict.fromkeys(items))`——dict key 去重且 3.7+ 保插入顺序。= Java LinkedHashSet | ⬜ |
| 7 | lru_cache 怎么用?做了什么? | `@lru_cache(maxsize=None)` 加在 def 上。自动把【参数→返回值】缓存,相同参数直接查表。maxsize=None 无限缓存。Java 要手写 HashMap 存取 | ⬜ |
| 8 | lru_cache 的两个限制? | ① 参数必须 hashable(list 不行,改 tuple);② 递归过深(>1000)仍栈溢出,那时改迭代 DP。它只解决「重复子问题」记忆化 | ⬜ |
| 9 | nlargest 何时用、何时改全排序? | k 远小于 n → nlargest(O(n log k) 省内存);k 接近 n → 直接 `sorted(nums,reverse=True)[k-1]` 常数更小 | ⬜ |
| 10 | stdlib 能替代算法思路吗? | 【不能】。stdlib 替代的是「样板」(统计/二分/去重/记忆化),真·算法题(双指针/DP/回溯)还得自己想——见 Ch35-40 | ⬜ |

## 🎓 费曼自检

- [ ] 能对 Java 老友说清「Python 刷题的爽点」并各举一例(Counter / bisect / lru_cache)?
- [ ] 能说清「为什么去重保序不能用 set,要用 dict.fromkeys」?
- [ ] 能说清「lru_cache 和 Java 手写 HashMap 缓存的对应 + lru_cache 的局限」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
