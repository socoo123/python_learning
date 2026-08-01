# 🧠 Ch36 · 哈希表 / 前缀和 —— 闪卡

> Ultralearning 原则七·记忆留存。**碎片化学习,不复习 ≈ 没学。**
> 用法:先看正面问题,**合上教程先回忆答案**,再翻背面核对。连续 2 次秒答标 ✅ 退役。
> 总览索引:[`../../REVIEW.md`](../../REVIEW.md)

---

## 🎴 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|------------|------------|------|
| 1 | 哈希表怎么把 O(n²) 降到 O(n)?一句话。 | 把「找一个东西在不在」从 O(n) 线性扫,换成 O(1) 哈希查询。**以查询换遍历。** | ⬜ |
| 2 | LC1 `two_sum` 的核心一行?为什么不能先全存 dict 再查? | 边扫边查:`if (target-num) in seen: return [seen[..], i]`。先全存会允许「同元素用两次」(如下标自己加自己),且要多一次下标判断。 | ⬜ |
| 3 | `group_anagrams` 用什么作 key?为什么? | `"".join(sorted(word))`——异位词的字符排序后序列相同。`defaultdict(list)` 聚合同 key 词。 | ⬜ |
| 4 | `defaultdict(list)` 替代了 Java 的什么样板? | `computeIfAbsent(k, k->new ArrayList<>())`。普通 dict 要先 `if k not in d: d[k]=[]` 再 append,defaultdict 自动建空 list。 | ⬜ |
| 5 | LC560 前缀和公式?为什么 dict 初始要塞 `{0:1}`? | `prefix[j]-prefix[i]=k` ⟺ `prefix[i]=prefix[j]-k`。`{0:1}` 表示空前缀出现过一次,**否则从下标 0 开始的子数组(整个前缀本身就是 k)会全部漏数。** | ⬜ |
| 6 | `subarray_sum` 为什么不能像 Ch35 滑动窗口? | nums 可含**负数**,前缀和不单调——缩窗不一定让和变小、扩窗不一定变大,滑窗失效。哈希前缀和是通用解。 | ⬜ |
| 7 | `subarray_sum` 一句话实现(关键三步)? | `{0:1}` 起手;每步 `cur+=num`;**先查** `count+=pc.get(cur-k,0)` **后登记** `pc[cur]=pc.get(cur,0)+1`。顺序不能反。 | ⬜ |
| 8 | LC128 `longest_consecutive` 为什么不排序?为什么只从「起点」数? | 排序 O(n log n),题目要 O(n)。只从 `n-1 not in set` 的元素开始数(它才是序列最小值),其它元素会被对应起点的 while 覆盖到,跳过避免重复——整体 O(n)。 | ⬜ |
| 9 | `longest_consecutive` 为什么是 O(n)?内层 while 不是 O(n) 吗? | 每个元素**最多被一个起点对应的 while 访问一次**(非起点都 `continue` 了),内层 while 总次数 ≤ n。O(n)+O(n)=O(n)。 | ⬜ |
| 10 | Python dict 安全取值 / 判键 / 自动默认值,分别怎么写? | 取值带默认:`d.get(k, default)`;判键:`k in d`;自动默认:`defaultdict(list/int)`。对应 Java `getOrDefault` / `containsKey` / `computeIfAbsent`。 | ⬜ |
| 11 | list 能当 dict 的 key 吗?异位词 key 怎么处理? | 不能,list 可变不可哈希。要 `"".join(sorted(word))` 拼成 str,或 `tuple(sorted(word))`。 | ⬜ |
| 12 | 这章四题里 dict 分别扮演什么角色? | two_sum:值→下标 map;group_anagrams:group-by 聚合;subarray_sum:频次表;longest_consecutive:set 成员查询。四种截然不同的用法。 | ⬜ |

---

## 🎙️ 费曼自检(对空气讲一遍)

合上教程,用自己的话讲清下面几点(讲不清就回去重读对应小节):

1. **哈希表降维套路**:拿 `two_sum` 当例子,讲清暴力 O(n²) 怎么变成 O(n),dict 里存什么、查什么。
2. **`{0:1}` 玄机**:为什么前缀和题必须预置 `{0:1}`?举 `nums=[5], k=5` 讲漏数的情况。
3. **`longest_consecutive` 的 O(n)**:为什么内层 while 不让复杂度退化成 O(n²)?

讲得磕巴 → 重读 §36.1 / §36.4 / §36.5。

---

## 📅 复习日程(间隔重复)

学完今天(记为 D0),按下面日期复习闪卡(2 分钟即可):

| 阶段 | 日期(自填) | 动作 | 完成 |
|------|------------|------|------|
| 首次 | D0(今天) | 学完做一遍闪卡,标初次掌握 | ⬜ |
| +1 天 | __________ | 先回忆再翻答案;秒答的标 ✅ | ⬜ |
| +3 天 | __________ | 同上;连续 2 次 ✅ 的卡退役 | ⬜ |
| +7 天 | __________ | 同上;剩下的精读对应 tutorial § | ⬜ |

> 退役的卡从上表移除,没掌握的卡继续滚动到下一周期。

---

## 🔗 相关章节

- 前置:Ch34(Python 刷题利器:`defaultdict`/`Counter`/`set`)、Ch35(双指针/滑动窗口——本章 §36.4 对比了为啥不能用滑窗)
- 下一章:Ch37(栈/队列/单调栈——另一种「维护顺序」的数据结构)
- 总览:[`../../REVIEW.md`](../../REVIEW.md)
