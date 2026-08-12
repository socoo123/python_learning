# Ch38 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 二叉树 DFS 递归的通用模板是什么?base case 怎么写? | `if node is None: return <空答案>`;然后 `left=dfs(node.left)`、`right=dfs(node.right)`,最后 `return 合并(node, left, right)`。base case 返回「空」的答案:深度题 0、布尔题 True、找节点题 None | ⬜ |
| 2 | LeetCode 层序数组 `[3,9,20,None,None,15,7]` 怎么读? | 按层从左到右,None 占位表示无节点。从根开始,每个已建节点依次认领数组下两个值当左右孩子 → 3 的孩子是 9、20;9 的孩子是 None、None;20 的孩子是 15、7 | ⬜ |
| 3 | max_depth(LC104)怎么递推?base case 是什么?为什么不能用「叶子=1」当 base? | `1 + max(左深度, 右深度)`;空树 `None` → 0。用「叶子=1」当 base:空树 `root.left` 直接炸,还得特判孩子;「空=0」一个 base 管所有情况 | ⬜ |
| 4 | invert_tree(LC226)Python 怎么交换左右指针?是原地改还是新建树? | `root.left, root.right = root.right, root.left` 一行交换(Python 特有糖,Java 要三行 temp)。**原地修改**,返回的 root 和传入的是同一棵树(对象没换,结构变了) | ⬜ |
| 5 | invert_tree 只交换根、不递归子树,会出什么错? | 内层子树一个没翻——翻转是「每个节点」都交换。先交换再递归(前序)或先递归再交换(后序)都对 | ⬜ |
| 6 | is_symmetric(LC101)为什么要「交叉比较」?同侧比较判的是什么? | 镜像 = t1 的左对 t2 的右、t1 的右对 t2 的左(中轴翻转)。同侧比较判的是「两树相同」,会把对称树 `[1,2,2,3,4,4,3]` 误判成 False | ⬜ |
| 7 | is_symmetric 的 mirror(t1, t2) base case 有哪些?漏一个会怎样? | 都 None → True;一空一不空 → False;值不等 → False;否则交叉递归。漏了「一空一不空」会 NoneType 崩溃 | ⬜ |
| 8 | is_valid_bst(LC98)为什么「只比直接孩子」是错的? | 孙子辈可能越界:根 5 的右孩子 6 合法,但 6 的左孩子 3 < 5,跨过了根的下界。必须带上下界 (low, high) 收紧:走左 `(low, 父值)`,走右 `(父值, high)` | ⬜ |
| 9 | is_valid_bst 初始上下界为什么用 float('-inf')/float('inf') 而不是 INT_MIN/INT_MAX? | 节点值可能恰好等于 INT_MAX(如 `[2147483647]`),开区间会把它误判。Python 的 ±inf 是真·无穷大,任何节点值都撞不穿 | ⬜ |
| 10 | BST 里等值节点合法吗?区间该开还是闭? | LC98 不允许等值(等值放哪边有歧义)。开区间 `low < val < high`,等值 → False;写成 `<=` 会把 `[1,1]` 误判 True | ⬜ |
| 11 | level_order(LC102)为什么必须用 collections.deque 不能用 list? | `list.pop(0)` 是 O(n)(整个 list 往前挪),弹 n 次退化到 O(n²)。`deque.popleft()` 和 `append()` 都 O(1)。deque = Java 的 ArrayDeque | ⬜ |
| 12 | level_order「按层分组」的核心技巧是什么?少了它会怎样? | 每轮 while 开始先记 `level_size = len(queue)`(此时队列里正好是当前层),再 `for _ in range(level_size)` 弹完本层、入队下一层。少了它结果变扁平序列 | ⬜ |
| 13 | right_side_view(LC199)为什么不是「一路贪右」?正确做法是什么? | 反例 `[1,2,3,4]`:第 3 层只有左侧的 4,贪右会漏。正解:BFS 复用 level_size,弹到 `i == level_size - 1` 时收值(每层最后一个) | ⬜ |
| 14 | right_side_view 的 DFS 版怎么写?两个关键点? | 先右后左递归;`depth == len(result)` 时收值(该深度首访即最右,因为先递归右)。先左后右就变成左视图 | ⬜ |
| 15 | lowest_common_ancestor(LC236)什么时候当前节点就是 LCA? | 左右子树递归**都返回非空**时——p、q 分居当前节点两侧,当前节点就是最近分叉点(再往下只能找到一个) | ⬜ |
| 16 | LCA 里返回值的「含义重载」是什么? | 返回非 None = 「这棵子树里至少包含 p 或 q 之一」,不区分是 p、是 q、还是 LCA。由调用方据「左右是否都非空」判断。这是 LCA 最绕的地方 | ⬜ |
| 17 | LCA 比较 p/q 用 `== val` 还是 `is`?「节点是自己祖先」怎么体现? | 用 `is`(对象引用同一性)——树里可能有重复值,按 val 比会定位错节点。base case `root is p or root is q` 直接返回 root,所以 LCA(5, 5的后代) = 5 | ⬜ |
| 18 | Python 树题默认递归深度上限是多少?退化链会怎样?怎么解决? | 默认上限 1000。退化链(全左/全右)深度 = 节点数,大数据会 RecursionError 爆栈。`import sys; sys.setrecursionlimit(10000)` 或改迭代 | ⬜ |
| 19 | DFS 题的空间复杂度是 O(h) 还是 O(n)?h 是什么? | O(h),h=树高(递归栈深度)。平衡树 h=log n,退化链 h=n | ⬜ |
| 20 | 本章 7 题哪些用 DFS、哪些用 BFS? | DFS:max_depth / invert_tree / is_symmetric / is_valid_bst / LCA;BFS:level_order / right_side_view(deque 队列) | ⬜ |

## 🎓 费曼自检

- [ ] 能默写 DFS 后序 / BFS 队列两套模板,说清各题 base case 返回什么?
- [ ] 能讲清 is_symmetric「交叉比较」为什么必要(同侧比较的反例)?
- [ ] 能讲清 is_valid_bst「带上下界」为什么必要(孙子辈越界反例),±inf 为什么比 INT_MIN 稳?
- [ ] 能讲清 level_order / right_side_view 为什么必须 deque + level_size 切层?
- [ ] 能讲清 LCA 的「返回值重载」「左右分散 → 当前是 LCA」「节点是自己祖先」三件事?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
