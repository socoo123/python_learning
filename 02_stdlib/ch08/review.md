# Ch08 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `Counter` 替代了 Java 什么?`c[不存在的键]` 返回什么? | 替代手写 `Map + getOrDefault` 计数循环。不存在的键返回 **0**(不抛 KeyError,这是特性)。一行 `Counter(可迭代对象)` 完成计数 | ⬜ |
| 2 | `most_common(n)` 返回什么? | 前 n 个 `(元素, 次数)` 元组的列表,按次数降序。Top-N 排行榜一行搞定 | ⬜ |
| 3 | `defaultdict(list)` 为何能自动建空列表?和 `setdefault` 区别? | 遇到不存在的键时【调用工厂 list()】造默认值。比 setdefault 优雅:工厂写在声明处一次,后面每次访问都自动,不用每处写 `d.setdefault(k,[])` | ⬜ |
| 4 | 为什么队列用 `deque` 不用 `list`?`maxlen` 干嘛? | `list.pop(0)` 是 **O(n)**(整体搬移);`deque.popleft()` 是 **O(1)**。`maxlen=n` 让 deque 定长,满了自动挤掉最旧的 → 滚动窗口 | ⬜ |
| 5 | `namedtuple` 对应 Java 什么?可变吗? | = Java `record`。**不可变**(改字段抛 AttributeError),可按字段名访问(`log.ip`)也可索引(`log[0]`),可哈希能当字典键 | ⬜ |
| 6 | Counter 还能做算术吗? | 能:`c1 + c2` 计数相加,`c1 - c2` 相减(负数会被丢掉)。两个 Counter 直接 +/- | ⬜ |
| 7 | `defaultdict` 的工厂怎么写?`defaultdict([])` 对吗? | **错**!写 `defaultdict(list)`(传工厂函数 list),不是 `defaultdict([])`(传一个固定 list,所有键共享同一个——可变默认坑)。同理 `defaultdict(int)`→默认0,`defaultdict(set)`→默认空set | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「Counter/defaultdict 各替代 Java 什么、为何更简洁」?
- [ ] 能说清「为什么队列必须用 deque,maxlen 如何实现滚动窗口」?
- [ ] 能说清「namedtuple 不可变、可按名访问、对应 Java record」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
