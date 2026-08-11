# Ch08 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `Counter` 替代了 Java 什么?`c[不存在的键]` 返回什么? | 替代手写 `Map + getOrDefault + merge` 计数循环。缺键返回 **0**(不抛 KeyError,类型级特性)。一行 `Counter(可迭代对象)` 完成计数 | ⬜ |
| 2 | `Counter` 的三种创建方式? | ① 可迭代对象 `Counter("aabbb")` ② dict `Counter({200: 13})` ③ 关键字 `Counter(ok=13)` | ⬜ |
| 3 | `most_common(n)` 返回什么?并列时谁排前? | 前 n 个 `(元素, 次数)` **元组列表**,次数降序;**并列按首次出现顺序**(dict 插入有序 + 稳定排序)。`most_common(1)[0]` 取冠军 | ⬜ |
| 4 | `Counter` 减法的关键规则?实战用途? | `today - yesterday` **丢弃 ≤0 的键**(好转/持平的指标直接消失,不是 0 不是负数)。配缺键返 0 读取仍安全。实战:今日 vs 昨日对比,差集里每个键都是「恶化的指标」 | ⬜ |
| 5 | `defaultdict(list)` 为什么能自动建空列表?为什么不能写 `defaultdict([])`? | 缺键时**调用工厂** `list()` 造新实例。`defaultdict([])` 传的是**固定实例**,所有缺键共享同一个 list(可变默认坑)。同理 `int`→0、`set`→空集合 | ⬜ |
| 6 | `defaultdict(list)` vs Ch02 的 `setdefault`,好在哪? | 工厂在**声明处写一次**,之后每次访问都自动;setdefault 每个访问点都要重复 `d.setdefault(k, [])` | ⬜ |
| 7 | 分完组为什么要 `dict(groups)` 转回普通 dict? | ① 防止下游误访问缺键时**悄悄建空键**污染数据;② 普通 dict 便于 JSON 序列化/打印 | ⬜ |
| 8 | `defaultdict(set)` 的典型场景?收集用什么方法? | 按 key 收集**去重**元素,如接口 UV 统计 `{路径: {IP 集合}}`。set 用 `.add()`(不是 append);收尾 `{k: len(v) for ...}` 转计数 | ⬜ |
| 9 | 为什么队列必须用 `deque` 不用 `list`? | `list.pop(0)` 是 **O(n)**(整体搬移),循环里 O(n²);`deque.popleft()` **O(1)**。但 deque 下标访问 O(n),随机索引用 list | ⬜ |
| 10 | `deque(maxlen=n)` 的行为?`append` vs `appendleft` 各挤哪端? | 定长队列,满了自动挤掉**另一端**:append 进右挤左(时间正序滚动窗口);appendleft 进左挤右(最新在前的错误栈)。数据不足 n 保留全部 | ⬜ |
| 11 | `namedtuple` 对应 Java 什么?可变吗?dict 怎么转? | = Java `record`。**不可变**(改字段抛 AttributeError,要「改」用 `_replace` 返新实例)。dict 键名一致时 `AccessLog(**d)` 一行解包转换 | ⬜ |
| 12 | namedtuple 的「tuple 本质」带来哪两个特性? | ① 索引访问 + 和等值 tuple 判等(`log == ("1.2.3.4", ...)`);② **可哈希**,能当 dict 键 / 进 set 去重 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「Counter/defaultdict 各替代 Java 什么、为何更简洁」?
- [ ] 能说清「Counter 减法丢键规则 + 为什么这对恶化检测正合适」?
- [ ] 能说清「maxlen 滚动窗口原理、appendleft 为什么让最新在前」?
- [ ] 能说清「namedtuple 不可变 → 可哈希 → 能当键」这条链?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
