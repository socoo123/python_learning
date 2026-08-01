# Ch38 · 二叉树 / DFS / BFS

> **预计**:1 天 ｜ **前置**:Ch34(Python 刷题利器)、Ch37(栈/队列/deque) ｜ **M6 重点**
> **目标**:拿下二叉树这个 LeetCode 高频区。树的题 **90% 是递归(DFS)** 或 **队列(BFS)**——你只要把两种「思维模板」练熟,5 道经典题就是套公式。

> 📐 **本教程的契约**:§38.2–§38.6 对应作业 5 个函数,LeetCode 104 / 226 / 98 / 102 / 236。**纯 stdlib**,只用到 `collections.deque`。

> 🎯 **Java 老手的直觉**:树 = 递归的天然主场。Java 里你写过 `int maxDepth(TreeNode root)` 一万遍;Python 版几乎一模一样,只是语法更短。本章重点不是「新算法」,是「**Python 怎么把树题写得又短又对**」+ 几个 BST / BFS 易错点。

---

## 🗺️ 本章地图:作业↔知识点对应表

| 函数(作业) | 对应小节 | LeetCode | 核心知识点 | 难度标记 |
|------|----------|----------|-----------|---------|
| `max_depth` | §38.2 | LC104 | DFS 后序:`1 + max(左, 右)`,base case 空树=0 | 🟢 |
| `invert_tree` | §38.3 | LC226 | DFS 前序:递归翻左右 + 交换指针,原地修改 | 🟢 |
| `is_valid_bst` | §38.4 | LC98 | DFS 带上下界 `(low, high)` 区间收缩 | 🟡 |
| `level_order` | §38.5 | LC102 | BFS:`collections.deque`,按层切分技巧 | 🟡 |
| `lowest_common_ancestor` | §38.6 | LC236 | DFS 后序:左右分散→当前是 LCA,集中→递归一边 | 🔴 |

> 标记说明:🟢 Java 老手秒懂;🟡 有差异/易错;🔴 Python 特有或思路较绕。

---

## ⏱️ 学习路径:费曼五步(约 60-80 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2 分钟) | 下面 ① 的 5 个问题,先凭 Java 经验猜 | 本页 ① |
| ② 写 assignment | 打开 `ch38_assignment.py`,**先不看教程自己写** | assignment |
| ③ pytest 红绿 | `uv run pytest 06_leetcode/ch38/test_ch38_assignment.py -v` | test |
| ④ 费曼(5 分钟) | 大白话讲清「为什么 DFS 后序能算深度」「BST 为什么要带上下界」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 标复习日期 | review.md |

> 💡 **直接性**:别通读!先猜 ① → 去 ② 写作业 → 卡住才回查 §38.x。

---

## ① 预览猜(2 分钟 · 用 Java 经验猜 Python)

先别看答案,猜一猜(猜错记得更牢):

1. Java 写 `int maxDepth(TreeNode root)`,base case 返回 0。Python 的 base case 怎么写?(提示:`root is None`)
2. 交换两个变量 `a, b = b, a` —— 翻转二叉树交换 `node.left, node.right` 用这招吗?
3. 验证 BST,很多人第一反应是「左孩子 < 我 < 右孩子」。这够吗?(提示:孙子辈呢?)
4. 层序遍历用队列。Java 你可能用 `LinkedList<TreeNode>` 或 `ArrayDeque`。Python 用什么,`list` 行不行?(提示:`list.pop(0)` 是 O(n))
5. 最近公共祖先:如果 `p` 在左子树、`q` 在右子树,谁是 LCA?(提示:就是当前节点)

> 猜完带着验证心态进入下面的 §38.x。

---

## §38.1 二叉树的两种思维模板(讲透)🟢

树的所有遍历/统计题,归结起来就**两套模板**。先记住这两个,5 道题都是套:

### 模板 A:DFS 递归(自顶向下 + 自底向上)

```python
def dfs(node):
    if node is None:        # base case:空节点
        return ...           # 返回「空」的答案(0 / None / True)
    left = dfs(node.left)    # 递归左子树,拿到左子树的「答案」
    right = dfs(node.right)  # 递归右子树
    return 合并(node, left, right)  # 用左右答案合成当前答案
```

- 这是**后序**(先左右、后当前)——`max_depth`、`is_valid_bst`、`lowest_common_ancestor` 都用它。
- 也常见**前序**(先当前、后左右),如 `invert_tree`(先翻自己再翻孩子)。
- 关键问自己一句话:「**当前节点拿到的左、右子树答案,怎么合成当前答案?**」能答出,递归就写出来了。

### 模板 B:BFS 队列(逐层处理)

```python
from collections import deque
queue = deque([root])
while queue:
    node = queue.popleft()   # O(1) 出队,千万别用 list.pop(0)!
    # 处理 node
    if node.left:  queue.append(node.left)
    if node.right: queue.append(node.right)
```

- `level_order` 用它。要「**按层分组**」时,加一个 `level_size = len(queue)` 技巧(§38.5 详解)。

> 🟢 **Java 对比**:DFS 模板 = Java `TreeNode` 递归,一模一样;BFS 模板 = Java `Queue<TreeNode> q = new ArrayDeque<>()` + `q.poll()` / `q.offer()`。Python 的 `deque` = Java 的 `ArrayDeque`,只是方法名不同(`popleft`↔`pollFirst`,`append`↔`addLast`)。

> **为什么 Python 递归特别顺手**:没有 Java 那套 `null` 检查噪音,`if node is None` 一行搞定 base case;返回值不用声明类型,`return 0` / `return None` 自由切换。代价是默认递归深度上限 1000(退化链会爆栈),LeetCode 大数据要 `sys.setrecursionlimit`,或改迭代。

---

## §38.2 max_depth:LC104 二叉树最大深度 🟢

```python
def max_depth(root):
    if root is None:
        return 0
    left = max_depth(root.left)
    right = max_depth(root.right)
    return 1 + max(left, right)
```

**为什么这么做**:一棵树的最大深度 = 1(自己)+ max(左子树深度, 右子树深度)。
- 空树深度 = 0(base case,递归必须有的「终止 + 最简答案」)。
- 非空:先算出左右子树各自的深度,取较大者 + 1 = 「从根走最深那条路」的层数。

```
        3                  max_depth(3)
       / \                 = 1 + max( max_depth(9), max_depth(20) )
      9  20                = 1 + max( 1, 1 + max( max_depth(15), max_depth(7) ) )
         / \               = 1 + max( 1, 1 + max(1, 1) )
        15  7              = 1 + max( 1, 2 )
                            = 3
```

> 🟢 **Java 秒懂**:`public int maxDepth(TreeNode root) { if (root == null) return 0; return 1 + Math.max(maxDepth(root.left), maxDepth(root.right)); }` —— Python 版只是 `null`→`None`、`Math.max`→`max`、不用写类型声明。

> **常见坑**:
> - base case 写成 `if root.left is None and root.right is None: return 1` —— 这是「叶子=1」,但漏了空树=0,且要写两个 base。统一用「空=0」更干净。
> - 忘了 `+ 1`:深度是**节点数**,空到根自己就 1 层,别漏。

**复杂度**:时间 O(n)(每节点访问一次);空间 O(h)(h=树高,递归栈深度。平衡 h=log n,退化链 h=n)。

> ✅ 做 `max_depth`:`if root is None: return 0` → `1 + max(左, 右)`。

---

## §38.3 invert_tree:LC226 翻转二叉树 🟢

```python
def invert_tree(root):
    if root is None:
        return None
    root.left = invert_tree(root.left)
    root.right = invert_tree(root.right)
    root.left, root.right = root.right, root.left   # 交换指针!
    return root
```

**为什么这么做**:翻转 = 把每个节点的左右子树互换。对每个节点:
1. 先递归翻它的左子树、右子树(让子树内部也翻转);
2. 再交换当前节点的 `left` / `right` 指针。

> 🟢 **Python 特有糖**:`a, b = b, a` 一行交换。Java 要写 `TreeNode t = l; l = r; r = t;` 三行。这是 Python 写树题最爽的一点。

> **关键认知**:这是**原地修改**——交换的是 `left`/`right` 引用,不新建节点;返回的 `root` 和传入的是**同一棵树**(结构变了,对象没换)。测试里 `assert result is root` 验证这点。

```
        4                 4                4
       / \               / \              / \
      2   7    交换根:  2   7   递归翻: 7   2
     / \ / \           / \ / \          / \ / \
    1 3 6  9          ... ...          9 6 3  1
```

> **前序 vs 后序**:`invert_tree` 你也可以先交换、再递归(前序),结果一样。这里先递归、再交换(后序交换)——只要「**交换指针**」和「**递归下钻**」都做了,顺序不影响最终结构。

> **常见坑**:
> - 只交换根,忘了递归子树 → 内层不翻。
> - 写成新建节点返回(以为要构造新树)——不用,原地改即可。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ 做 `invert_tree`:`if root is None: return None` → 递归翻左右 → `root.left, root.right = root.right, root.left` → 返回 root。

---

## §38.4 is_valid_bst:LC98 验证二叉搜索树 🟡

```python
def is_valid_bst(root):
    def validate(node, low, high):
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return validate(node.left, low, node.val) and \
               validate(node.right, node.val, high)
    return validate(root, float("-inf"), float("inf"))
```

**为什么这么做 —— 这是本章最易错的题**:

BST 定义:任意节点 x,**左子树所有值 < x.val**,**右子树所有值 > x.val**。注意是**所有**,不光是直接孩子。

❌ **错的写法**(只看一层):
```python
def bad(node):
    if node is None: return True
    if node.left and node.left.val >= node.val: return False
    if node.right and node.right.val <= node.val: return False
    return bad(node.left) and bad(node.right)
```
这种写法会**漏判孙子辈**。反例:
```
        5
       / \
      4   6       6 > 5 ✅, 4 < 5 ✅ —— 每个节点「直接孩子」都合法
         / \
        3   7     但 3 在 5 的【右子树】里,3 < 5,违反 BST!
```
6 自己合法,但 6 的左孩子 3 「跨过」了根 5 的下界——`bad` 检测不到。

✅ **对的写法(带上下界)**:给每个节点配一个合法区间 `(low, high)`:
- 根:区间 `(-∞, +∞)`(任意值都行)
- 走左子树:区间 `(low, 父值)` —— 整棵左子树所有值必须 `< 父值`(上界收紧)
- 走右子树:区间 `(父值, high)` —— 整棵右子树所有值必须 `> 父值`(下界收紧)

这样孙子辈天然被「祖辈的界」约束,3 在右子树会撞上 `low=5` 的下界 → False。

> 🟡 **Java 对比 / 差异**:Java 版用 `Long.MIN_VALUE` / `Long.MAX_VALUE` 当初始界,有溢出风险(节点值可能等于边界)。Python 用 `float("-inf")` / `float("inf")` —— **无穷大,永远不会被节点值「撞穿」**,比 Java 的 INT_MIN 方案更稳。

> **为什么是开区间 `low < node.val < high`**:BST 通常不允许等值(等值放哪边有歧义,LeetCode 98 明确不允许)。所以用 `<` 而非 `<=`。等值节点 → False。

> **常见坑**:
> - 只比直接孩子(见上 ❌)。
> - 用 `INT_MIN` 当初始下界,节点值恰好 `INT_MIN` 时误判。
> - 写成中序遍历判「是否严格递增」也行(中序遍历 BST 得升序),但带上下界更直观。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ 做 `is_valid_bst`:闭包 `validate(node, low, high)`,空=True,`low < val < high` 否则 False,左走 `(low, val)`、右走 `(val, high)`,初始 `(-∞, +∞)`。

---

## §38.5 level_order:LC102 二叉树层序遍历 🟡

```python
from collections import deque

def level_order(root):
    if root is None:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)          # ★ 按层切分的核心
        level_vals = []
        for _ in range(level_size):
            node = queue.popleft()        # ★ O(1),别用 list.pop(0)!
            level_vals.append(node.val)
            if node.left:  queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level_vals)
    return result
```

**为什么这么做**:

BFS(广度优先)用队列(FIFO):先进先出保证「同一层的节点在队列里连续排」。但题目要的不是「一条扁平序列」,是「**按层分组**」(`[[3],[9,20],[15,7]]`)。

**按层切分的技巧**:每轮 `while` 开始时,先记下 `level_size = len(queue)` —— 此时队列里**正好是当前层的所有节点**(上一轮把它们的父节点处理完,把它们都入队了)。然后 `for _ in range(level_size)` 刚好弹完这一层,期间入队的是**下一层**的节点,不会污染当前层。

```
初始 queue=[3]
轮1: level_size=1 → 弹 3,入队 9,20 → 本层 [3]      queue=[9,20]
轮2: level_size=2 → 弹 9(无孩子),弹 20(入 15,7) → 本层 [9,20]  queue=[15,7]
轮3: level_size=2 → 弹 15,弹 7(都无孩子) → 本层 [15,7]  queue=[]
结束 → [[3],[9,20],[15,7]]
```

> 🟡 **Python 特有 —— 一定要用 `deque`**:
> ```python
> queue = deque([root])
> node = queue.popleft()    # O(1) ✅
> ```
> 千万**别**用 `list.pop(0)` —— 那是 **O(n)**(整个 list 要往前挪)!对 n 层的树,总时间从 O(n) 退化到 O(n²)。这是本章最大的性能坑。
>
> `deque` = 双端队列,两端进出都 O(1)。Java 等价物:`ArrayDeque`(你刷题用过)。

> **Java 对比**:Java BFS 用 `Queue<TreeNode> q = new ArrayDeque<>(); q.offer(root); TreeNode n = q.poll();`。Python 的 `deque.append` = `offer`(入队尾),`deque.popleft` = `poll`(出队头)。语义一一对应。

> **常见坑**:
> - 用 `list.pop(0)` 当队列(O(n),慢)。
> - 没有 `level_size` 切分,结果变成扁平 `[3,9,20,15,7]`。
> - 忘了空树返回 `[]`(不是 `[[]]`)。

**复杂度**:时间 O(n);空间 O(n)(最宽一层节点数,平衡树约 n/2)。

> ✅ 做 `level_order`:`deque([root])` → 每轮 `level_size=len(queue)` → `for _ in range(level_size)` 弹出 + 收集 + 入孩子 → 每层 append 到 result。

---

## §38.6 lowest_common_ancestor:LC236 最近公共祖先 🔴

```python
def lowest_common_ancestor(root, p, q):
    if root is None or root is p or root is q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left is not None and right is not None:
        return root            # p、q 分居两侧 → 当前节点就是 LCA
    return left if left is not None else right
```

**为什么这么做 —— 后序 DFS 的妙用**:

定义:节点 x 是 p、q 的公共祖先,当且仅当 p、q 都在「以 x 为根的子树」里;「最近」= 最深的那个 x。**一个节点可以是自己的祖先**(比如 p 是 q 的祖先时,LCA 就是 p)。

后序 DFS(先看左右、再综合当前)的天然结构:
1. **base case**:当前是 `None` → 不是任何节点的祖先,返回 `None`;当前 `是 p 或 q` → 找到一个目标,把它「向上汇报」(返回当前节点)。
2. 递归左、右子树,各拿到一个结果(`left`、`right`):
   - **左右都非空** → p、q **分居**当前节点的两侧 → 当前节点就是 LCA(因为「最近」:再往下走只能找到一个)。
   - **只有一边非空** → p、q 都在那一边 → 答案在那边,递归结果就是 LCA。
   - **两边都空** → 这棵子树里没有 p/q → 返回 None。

```
        3                  求 LCA(5, 1):
       / \
      5   1                递归左(5 子树):命中 5,返回 5
     / \ / \               递归右(1 子树):命中 1,返回 1
    6 2 0 8                左右都非空 → 返回根 3 ✅(5、1 分居两侧)

    求 LCA(5, 4):4 在 5 的子树里
        3                   递归左(5 子树):命中 5 后继续找,左下找到 4
       /                    → 返回 5(汇报「找到了目标节点」)
      5                     递归右(1 子树):没找到,返回 None
       \                    左非空、右空 → 返回左 = 5 ✅(5 自己是祖先)
        4
```

> 🔴 **思路较绕的点**:
> - 「**返回值的含义是重载的**」:返回非 None,意思是「这棵子树里**至少包含 p 或 q 之一**」;至于包含的是 p、是 q、还是 LCA,由调用方根据「左右是否都非空」判断。这是这题最绕的地方。
> - 「**节点是自己的祖先**」:所以 base case `root is p or root is q` 直接返回 root。这也是为什么 `LCA(5, 4)` 能返回 5 —— 5 向上汇报,4 也在 5 子树里,5 自然是最近的。
> - 「**用对象引用相等(`is`)而不是 `val` 比较**」:树里可能有重复值,LCA 必须按**节点身份**定位 p、q。测试用 `find_node(root, val)` 拿到 p、q 的对象引用传入。

> 🟢 **Java 对比**:逻辑完全一样。Python 只是用 `is None` 替代 `== null`,用 `left is not None and right is not None` 替代 Java 的 `left != null && right != null`。

> **为什么是后序**:必须先知道「左子树有没有 p/q、右子树有没有 p/q」,才能判断当前节点是不是分叉点。前序(先看自己)做不到——因为「分散 vs 集中」的判断依赖子树的结果。

> **常见坑**:
> - 用 `node.val == p.val` 比较(重复值会错)。要用 `is`(对象同一性)。
> - 忘了「节点是自己祖先」的 base case,导致 `LCA(p, p的孩子)` 算错。
> - 左右都找到时不敢返回当前节点(怀疑「会不会有更深的」)——不会,再往下只能找到一个目标,这里就是最近的分叉。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ 做 `lowest_common_ancestor`:`if root is None or root is p or root is q: return root` → 递归左右 → 左右都非空返回 root → 否则返回非空那边。

---

## 📊 五道题复杂度一览

| 题 | 方法 | 时间 | 空间 | 关键 |
|----|------|------|------|------|
| max_depth | DFS 后序 | O(n) | O(h) | `1 + max(左, 右)` |
| invert_tree | DFS 前序/后序 | O(n) | O(h) | 原地交换 `a, b = b, a` |
| is_valid_bst | DFS 带界 | O(n) | O(h) | 区间 `(low, high)` 收紧 |
| level_order | BFS | O(n) | O(n) | `deque` + `level_size` 切层 |
| LCA | DFS 后序 | O(n) | O(h) | 左右分散→当前是 LCA |

> h = 树高。平衡 h = log n,退化链(全左/全右)h = n。LeetCode 退化链大数据要防递归爆栈:`import sys; sys.setrecursionlimit(10000)`。

---

## §38.7 Java 老手常踩的坑 ⚠️

1. **`list.pop(0)` 当队列**:O(n)!层序遍历务必用 `collections.deque` + `popleft()`。
2. **BST 只比直接孩子**:漏判孙子辈。必须带上下界 `(low, high)` 收紧。
3. **BST 初始界用 INT_MIN**:节点值可能更小。Python 用 `float('-inf')` 永不撞穿。
4. **LCA 用 val 比较**:重复值会错。用 `is`(对象引用)。
5. **递归爆栈**:Python 默认递归上限 1000,退化链(深度=节点数)会爆。大数据加 `sys.setrecursionlimit`。
6. **忘了 base case 的返回值**:DFS 模板里 `if node is None: return <空答案>` 是地基,漏了直接 NoneType 崩溃。

---

## 📝 本章作业

| 任务 | LeetCode | 知识点 | 难度 |
|------|----------|--------|------|
| `max_depth` | LC104 | DFS 后序 + base case | 🟢 |
| `invert_tree` | LC226 | DFS + 原地交换指针 | 🟢 |
| `is_valid_bst` | LC98 | DFS 带上下界(易错) | 🟡 |
| `level_order` | LC102 | BFS + deque + 按层切分 | 🟡 |
| `lowest_common_ancestor` | LC236 | DFS 后序 + 引用相等 | 🔴 |

> 🏗️ **scaffolding**:`ch38_assignment.py` 顶部已定义 `TreeNode` 类(= LeetCode 提交模板),**不擦、不算作业体**,5 道题和测试共用它。

```bash
uv run pytest 06_leetcode/ch38/test_ch38_assignment.py -v
```

全绿 = 你掌握了 Ch38。

---

## ✅ 自测

- [ ] 能默写出 DFS 后序的通用模板(base case + 左右递归 + 合成)?
- [ ] 知道为什么 `max_depth` 是 `1 + max(左, 右)`,base case 空树 = 0?
- [ ] 能说清 `is_valid_bst` 为什么不能只比直接孩子,必须带 `(low, high)` 区间?
- [ ] 知道 `level_order` 为什么必须用 `deque` 而不是 `list`,以及 `level_size` 怎么按层切分?
- [ ] 能讲清 `lowest_common_ancestor` 里「返回值重载」「节点是自己祖先」「左右分散→当前是 LCA」三件事?
- [ ] 5 个作业 pytest 全绿?

## 🎓 费曼挑战

1. 「**为什么 max_depth 用后序(先左右后自己)?**」能不能用前序写?(提示:前序要「自顶向下传当前深度」当参数,后序更自然)—— 重读 §38.2
2. 「**is_valid_bst 如果用 INT_MIN 当初始下界,什么 case 会出错?**」—— 重读 §38.4
3. 「**level_order 如果不记 level_size,直接 while queue: pop 一个处理一个,结果会怎样?**」—— 重读 §38.5
4. 「**lowest_common_ancestor 为什么必须用 `is` 比较 p/q,用 `val` 比较哪里会错?**」—— 重读 §38.6
5. 「**这五道题哪些是后序 DFS、哪些是 BFS、哪些是前序?为什么这道题用这个序?**」—— 重读全章

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch39 动态规划

树题练完递归直觉,接下来把递归用到「**最优化**」上 —— 动态规划(DP):`fib(n) = fib(n-1) + fib(n-2)` 这种「大问题 = 子问题组合」的递推。从记忆化搜索到状态转移方程,从自顶向下到自底向上。树的 DFS 是 DP 的热身。
