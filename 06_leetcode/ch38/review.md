# Ch38 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 二叉树 DFS 递归的通用模板是什么?base case 怎么写? | `if node is None: return <空答案>`;然后 `left=dfs(node.left)`, `right=dfs(node.right)`,最后 `return 合并(node, left, right)`。base case 返回「空」的答案:深度题 0、布尔题 True、找节点题 None | ⬜ |
| 2 | max_depth(LC104)怎么递推?base case 是什么? | `1 + max(左深度, 右深度)`;空树 `None` → 0。深度按节点数计,别忘了 `+ 1` | ⬜ |
| 3 | invert_tree(LC226)Python 怎么交换左右指针?是原地改还是新建树? | `root.left, root.right = root.right, root.left` 一行交换(Python 特有糖,Java 要三行 temp)。**原地修改**,返回的 root 和传入的是同一棵树(对象没换,结构变了) | ⬜ |
| 4 | is_valid_bst(LC98)为什么「只比直接孩子」是错的? | 因为孙子辈可能越界:如根 5 的右孩子 6 合法,但 6 的左孩子 3 < 5,3 跨过了根的下界。必须带上下界 (low, high) 收紧:走左 `(low, 父值)`,走右 `(父值, high)` | ⬜ |
| 5 | is_valid_bst 初始上下界为什么用 float('-inf')/float('inf') 而不是 INT_MIN/INT_MAX? | 节点值可能恰好等于 INT_MIN,用 INT_MIN 当界会误判。Python 的 ±inf 永远不会被任何节点值「撞穿」,比 Java 的整数边界更稳 | ⬜ |
| 6 | BST 里等值节点(两个相同值)合法吗?用开区间还是闭区间? | LeetCode 98 不允许等值(等值放哪边有歧义)。所以用开区间 `low < val < high`,等值 → False | ⬜ |
| 7 | level_order(LC102)为什么必须用 collections.deque 不能用 list? | `list.pop(0)` 是 O(n)(整个 list 往前挪),n 层退化到 O(n²)。`deque.popleft()` 和 `append()` 都是 O(1)。deque = Java 的 ArrayDeque | ⬜ |
| 8 | level_order「按层分组」的核心技巧是什么? | 每轮 while 开始先记 `level_size = len(queue)`(此时队列里正好是当前层所有节点),再 `for _ in range(level_size)` 弹完这一层、入队下一层。没有 level_size 会变扁平序列 | ⬜ |
| 9 | lowest_common_ancestor(LCA,LC236)什么时候当前节点就是 LCA? | 当左右子树递归**都返回非空**时——说明 p、q 分居当前节点两侧,当前节点就是最近分叉点(再往下只能找到一个) | ⬜ |
| 10 | LCA 里返回值的「含义重载」是什么?为什么绕? | 返回非 None = 「这棵子树至少包含 p 或 q 之一」,不区分是 p、是 q、还是 LCA。由调用方据「左右是否都非空」判断。这是 LCA 最绕的地方 | ⬜ |
| 11 | LCA 比较 p/q 用 `== val` 还是 `is`?为什么? | 用 `is`(对象引用同一性)。树里可能有重复值,按 val 比会定位错节点。p、q 是具体节点对象,必须按身份比 | ⬜ |
| 12 | 「节点是自己祖先」在 LCA 里怎么体现? | base case `root is p or root is q` 直接返回 root。所以 LCA(5, 5的孩子) = 5:5 向上汇报,孩子在 5 子树里,5 是最近的 | ⬜ |
| 13 | Python 树题默认递归深度上限是多少?退化链(全左/全右,深度=节点数)会怎样? | 默认上限 1000。退化链深度 = 节点数,大数据会 RecursionError 爆栈。解法:`import sys; sys.setrecursionlimit(10000)` 或改迭代 | ⬜ |
| 14 | DFS 题的空间复杂度是 O(h) 还是 O(n)?h 是什么? | O(h),h=树高(递归栈深度)。平衡树 h=log n,退化链 h=n。所以平衡 DFS 空间 O(log n),退化 O(n) | ⬜ |
| 15 | 这五题哪些用 DFS、哪些用 BFS? | max_depth/invert/is_valid_bst/LCA 都是 DFS;只有 level_order 是 BFS(deque 队列) | ⬜ |

## 🎓 费曼自检

- [ ] 能默写 DFS 后序通用模板,说清 base case 的作用?
- [ ] 能讲清 is_valid_bst「带上下界」为什么必要(孙子辈越界反例)?
- [ ] 能讲清 level_order 为什么必须 deque + level_size 切层?
- [ ] 能讲清 LCA 的「返回值重载」「左右分散→当前是 LCA」「节点是自己祖先」三件事?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
