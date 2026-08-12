# Ch38 · 二叉树 / DFS / BFS

> **预计**:1 天 ｜ **前置**:Ch34(Python 刷题利器)、Ch35(双指针/滑窗) ｜ **M6 高频区**
> **目标**:拿下二叉树这个 LeetCode 必考区。树题 90% 是**递归 DFS** 或**队列 BFS**——把两套「思维模板」练熟,7 道经典题全是套公式。

> 📐 **本教程的契约**:§38.2–§38.8 每节**精确对应**一道作业题(LC104 / 226 / 101 / 98 / 102 / 199 / 236),讲过的才考、考的必讲过。§38.1(两套模板 + 层序数组读法)/ §38.9(坑清单)讲透不出题。卡住时按对应表回查小节。
> **纯 stdlib**,只用到 `collections.deque`。

> 🎯 **Java 老手的直觉**:树 = 递归的天然主场。Java 里你写过 `int maxDepth(TreeNode root)` 一万遍;Python 版几乎一模一样,只是更短。本章重点不是「新算法」,是「**Python 怎么把树题写得又短又对**」+ 几个 BST / BFS 易错点。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:

- 默写 DFS 递归 / BFS 队列两套通用模板,说清每题的 base case 该返回什么
- 读懂 LeetCode 层序数组 `[3,9,20,None,None,15,7]`,自己构造测试树
- 用「1 + max(左, 右)」秒最大深度,说清为什么 base case 是「空树 = 0」
- 用元组交换 `a, b = b, a` **原地**翻转二叉树
- 用「双树镜像递归」判断对称树,说清为什么要**交叉比较**(左对右、右对左)
- 用「上下界区间收紧」验证 BST,说清为什么只比直接孩子会漏判孙子辈
- 用 `deque` + `level_size` 按层切分做层序遍历,并把同一技巧复用到右视图
- 用「左右分散 → 当前是 LCA」的后序思路解最近公共祖先,说清为什么用 `is` 不用 `==`

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | LeetCode | 核心知识点 | 难度 |
|--------|----------|----------|-----------|------|
| `max_depth` | §38.2 | LC104 | DFS 后序:`1 + max(左, 右)`,空树 = 0 | 🟢 |
| `invert_tree` | §38.3 | LC226 | DFS + 元组交换指针,原地修改 | 🟢 |
| `is_symmetric` | §38.4 | LC101 | DFS 双树镜像递归(交叉比较) | 🟢 |
| `is_valid_bst` | §38.5 | LC98 | DFS 带上下界 (low, high) 收紧 | 🟡 |
| `level_order` | §38.6 | LC102 | BFS:deque + level_size 按层切分 | 🟡 |
| `right_side_view` | §38.7 | LC199 | BFS 取每层末位(复用 level_size) | 🟡 |
| `lowest_common_ancestor` | §38.8 | LC236 | DFS 后序:左右分散 → 当前是 LCA | 🔴 |

> 标记说明:🟢 Java 老手秒懂;🟡 有差异/易错;🔴 思路较绕。

---

## ⏱️ 学习路径:费曼五步(约 90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(3 分钟) | 下面 ① 的 7 个问题,先凭 Java 经验猜 | 本页 ① |
| ② 先动手 | 打开 `ch38_assignment.py`,**先不看教程自己写** | assignment |
| ③ pytest 红绿 | `uv run pytest 06_leetcode/ch38/test_ch38_assignment.py -v` | test |
| ④ 费曼(5 分钟) | 大白话讲清「为什么空树=0」「为什么交叉比较」「为什么要带上下界」「level_size 怎么切层」「返回值重载」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(先合上教程想 1 分钟)

先别看答案,猜一猜(猜错记得更牢):

1. Java 写 `int maxDepth(TreeNode root)`,base case 返回 0。Python 的 base case 怎么写?(提示:`root is None`)
2. 交换两个变量 `a, b = b, a` —— 翻转二叉树交换 `node.left, node.right` 用这招吗?只交换根够不够?
3. 判断「对称树」= 判断左右两棵子树「完全相同」吗?(提示:镜像 ≠ 相同,那 t1 的左该对 t2 的哪边?)
4. 验证 BST,很多人第一反应是「左孩子 < 我 < 右孩子」。这够吗?(提示:孙子辈呢?)
5. 层序遍历用队列。Java 你用 `ArrayDeque`;Python 用什么?`list.pop(0)` 行不行?(提示:它是 O(n))
6. 右视图 = 「每层最右边的节点」。如果某层只在**左侧**有节点,从右边还看得到吗?(提示:右视图 ≠ 一路向右走)
7. 最近公共祖先:如果 `p` 在左子树、`q` 在右子树,谁是 LCA?(提示:就是当前节点)

> 猜完带着验证心态进入下面的 §38.x。

---

## §38.1 两套思维模板 + 层序数组读法(讲透)🟢

树的所有遍历/统计题,归结起来就**两套模板**。先记住这两个,7 道题都是套。

### 模板 A:DFS 递归

```python
def dfs(node):
    if node is None:          # base case:空节点
        return ...            # 返回「空」的答案(0 / None / True)
    left = dfs(node.left)     # 递归左子树,拿到左子树的「答案」
    right = dfs(node.right)   # 递归右子树
    return 合并(node, left, right)   # 用左右答案合成当前答案
```

- 这是**后序**(先左右、后当前)——`max_depth`、`is_valid_bst`、`lowest_common_ancestor` 都用它。
- 也常见**前序**(先当前、后左右),如 `invert_tree`(先换自己再下钻)。
- 关键问自己一句话:「**当前节点拿到左、右子树的答案后,怎么合成当前答案?**」能答出,递归就写出来了。
- 双树题(`is_symmetric`)把模板升级成 `dfs(t1, t2)`,两个节点**结伴下钻**(§38.4)。

### 模板 B:BFS 队列(逐层处理)

```python
from collections import deque

queue = deque([root])
while queue:
    node = queue.popleft()    # O(1) 出队,千万别用 list.pop(0)!
    # 处理 node
    if node.left:  queue.append(node.left)
    if node.right: queue.append(node.right)
```

- `level_order`、`right_side_view` 用它。要「**按层分组**」时,加一个 `level_size = len(queue)` 技巧(§38.6 详解)。

> 🟢 **Java 对比**:DFS 模板 = Java `TreeNode` 递归,一模一样;BFS 模板 = `Queue<TreeNode> q = new ArrayDeque<>()` + `q.poll()` / `q.offer()`。Python 的 `deque` = Java 的 `ArrayDeque`,只是方法名不同(`popleft` ↔ `pollFirst`,`append` ↔ `addLast`)。

> **为什么 Python 递归特别顺手**:没有 `null` 检查噪音,`if node is None` 一行搞定 base case;返回值不用声明类型,`return 0` / `return None` 自由切换。代价是默认递归深度上限 1000(退化链会爆栈),LeetCode 大数据要 `import sys; sys.setrecursionlimit(10000)`,或改迭代。

### 读题必备:LeetCode 层序数组 ↔ 树

题面和测试都用**层序数组**描述一棵树:按层从左到右排,`None` 占位表示「该位置没有节点」:

```
[3, 9, 20, None, None, 15, 7]      读作:

        3                ← values[0] 是根
       / \
      9   20             ← values[1..2] 是 3 的左、右孩子
          / \
        15   7           ← 9 认领 values[3..4] = None,None(无孩子)
                         ← 20 认领 values[5..6] = 15,7
```

读法口诀:**数组按「层」被消耗**——从根开始,每个已建节点依次认领数组里下两个值当左右孩子,`None` 表示没有。测试文件里给了 `build_tree(values)` helper 把数组变成真树,你读测试时照着上面画一遍就懂了。

> 💡 自己构造边界用例(单节点、斜链)时,直接嵌套写更直观:`TreeNode(1, TreeNode(2), TreeNode(3))`,签名是 `TreeNode(val, left, right)`。

---

## §38.2 max_depth:LC104 二叉树最大深度 🟢

**题面**:给定根节点,返回二叉树的最大深度(根到最远叶子经过的**节点数**)。

**例**:
- `[3,9,20,None,None,15,7]` → `3`
- `[1,None,2]` → `2`(单链也算深度)
- `[1]` → `1`;`[]` → `0`

### ❌ 错误写法:base case 写成「叶子 = 1」

```python
def max_depth_bad(root):
    if root.left is None and root.right is None:   # 空树直接 AttributeError!
        return 1
    return 1 + max(max_depth_bad(root.left), ...)  # 对 None 孩子又没法递归
```

新手直觉是「叶子深度 1,往上累加」。这写法两个毛病:① 空树 `root.left` 直接炸;② 孩子可能是 `None`,还得层层特判,越写越乱。

### ✅ 正确写法:base case 是「空 = 0」

```python
def max_depth(root):
    if root is None:
        return 0
    left = max_depth(root.left)
    right = max_depth(root.right)
    return 1 + max(left, right)
```

**为什么「空 = 0」是对的**:把 `None` 也当成一棵(深度为 0 的)合法树,所有节点统一走同一套递归——叶子自然算出 `1 + max(0, 0) = 1`,根逐层 +1。**一个 base case 管所有情况**,不用特判叶子。

**逐步推演** `[3,9,20,None,None,15,7]`(后序:先算完子树才算自己):

| 调用 | 计算 | 返回 |
|------|------|------|
| `max_depth(9)` | 1 + max(0, 0) | 1 |
| `max_depth(15)` | 1 + max(0, 0) | 1 |
| `max_depth(7)` | 1 + max(0, 0) | 1 |
| `max_depth(20)` | 1 + max(1, 1) | 2 |
| `max_depth(3)` | 1 + max(1, 2) | **3** |

> 🟢 **Java 秒懂**:`public int maxDepth(TreeNode root) { if (root == null) return 0; return 1 + Math.max(maxDepth(root.left), maxDepth(root.right)); }` —— Python 版只是 `null`→`None`、`Math.max`→`max`、不用声明返回类型。

> ⚠️ **常见坑**:
> 1. 忘了 `+ 1`:深度按**节点数**计,根自己就算一层。
> 2. 空树返回 1 → 全盘错;「空 = 0」是地基。
> 3. 退化链(全左/全右)深度 = n,LeetCode 大数据注意递归上限(§38.9 第 5 条)。

**复杂度**:时间 O(n)(每节点访问一次);空间 O(h)(递归栈,h = 树高;平衡 h=log n,退化链 h=n)。

> ✅ **做 `max_depth`**:`if root is None: return 0` → `1 + max(左, 右)`。

---

## §38.3 invert_tree:LC226 翻转二叉树 🟢

**题面**:把每个节点的左右子树互换,返回翻转后的根(**原地修改**)。

**例**:
- `[4,2,7,1,3,6,9]` → `[4,7,2,9,6,3,1]`
- `[2,1,3]` → `[2,3,1]`
- `[]` → `None`

### ❌ 错误写法一:只交换根,忘了递归

```python
def invert_bad(root):
    if root is None:
        return None
    root.left, root.right = root.right, root.left
    return root        # 内层子树一个没翻!
```

翻转是「**每个节点**都交换」,不是只换根。

### ❌ 错误写法二:新建节点返回(不是原地)

```python
def invert_bad2(root):
    if root is None:
        return None
    return TreeNode(root.val, invert_bad2(root.right), invert_bad2(root.left))
```

结构对,但开了新树——题目约定(和本章测试)要求**原地修改**:返回的必须是传入的那棵树。面试也常追问「O(1) 额外空间怎么做」。

### ✅ 正确写法:递归翻子树 + 元组交换指针

```python
def invert_tree(root):
    if root is None:
        return None
    left = invert_tree(root.left)          # 先递归翻好左右子树
    right = invert_tree(root.right)
    root.left, root.right = right, left    # 再交换当前节点的指针
    return root
```

> 🔴 **Python 特有糖**:`a, b = b, a` 一行交换(右边先打包成元组再解包)。Java 要 `TreeNode t = l; l = r; r = t;` 三行临时变量。这是 Python 写树题最爽的一点。

> **关键认知**:交换的是 `left` / `right` **引用**,不新建节点;返回的 `root` 和传入的是**同一棵树**(结构变了,对象没换)。测试里 `assert result is root` 验证的正是这点。

**逐步推演** `[2,1,3]`:

| 步骤 | 动作 | 树状态 |
|------|------|--------|
| invert(2) 先递归 invert(1) | 1 无孩子,原样返回 | 不变 |
| invert(2) 再递归 invert(3) | 3 无孩子,原样返回 | 不变 |
| invert(2) 交换左右指针 | `2.left, 2.right = 3, 1` | `[2,3,1]` ✅ |

> **前序 or 后序都行**:也可以先交换、再递归(前序)。只要「交换指针」和「递归下钻」都做了,顺序不影响最终结构——但注意前序版交换之后,要递归的是**交换后的**新 left / right。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ **做 `invert_tree`**:空返回 None → 递归翻左右 → `root.left, root.right = root.right, root.left` → 返回 root。

---

## §38.4 is_symmetric:LC101 对称二叉树 🟢

**题面**:判断一棵二叉树是否**轴对称**(以根的中轴为镜像)。

**例**:
- `[1,2,2,3,4,4,3]` → `True`

```
        1
       / \
      2   2
     / \ / \
    3  4 4  3      ← 左子树 (2,3,4) 与右子树 (2,4,3) 互为镜像
```

- `[1,2,2,None,3,None,3]` → `False`

```
        1
       / \
      2   2
       \   \
        3   3      ← 两个 3 在同侧(都是右孩子),不是镜像
```

- `[1]` → `True`(单节点恒对称);`[]` → `True`(空树)

### ❌ 错误写法:把「镜像」当成「相同」

```python
def mirror_bad(t1, t2):
    ...
    return (t1.val == t2.val
            and mirror_bad(t1.left, t2.left)     # 同侧比较 = 判「两树相同」
            and mirror_bad(t1.right, t2.right))
```

拿 `[1,2,2,3,4,4,3]` 试:左子树 `(2,3,4)`、右子树 `(2,4,3)` 并不**相同**,同侧比较返回 False——但它明明对称!**镜像 = 交叉比较**:t1 的左对 t2 的右,t1 的右对 t2 的左。

### ✅ 正确写法:双树交叉递归

```python
def is_symmetric(root):
    def mirror(t1, t2):
        if t1 is None and t2 is None:
            return True          # 都空:镜像
        if t1 is None or t2 is None:
            return False         # 一空一不空:结构不对称
        return (t1.val == t2.val
                and mirror(t1.left, t2.right)    # ★ 交叉!
                and mirror(t1.right, t2.left))
    return root is None or mirror(root.left, root.right)
```

**为什么这么做**:模板 A 的升级——单树递归是「一个节点下钻」,这题是「**两个节点结伴下钻**」。从根的左右孩子起步,每层都维持不变式「t1 和 t2 应互为镜像点」:值必须相等,且 t1 的**左**对应镜中 t2 的**右**(中轴翻转),反之亦然。

**逐步推演** `[1,2,2,3,4,4,3]`:

| 调用 | 值比较 | 交叉递归 | 返回 |
|------|--------|----------|------|
| `mirror(2左, 2右)` | 2 == 2 | `mirror(3,3)` ∧ `mirror(4,4)` | True |
| `mirror(3, 3)` | 3 == 3 | 孩子全空 → True ∧ True | True |
| `mirror(4, 4)` | 4 == 4 | 孩子全空 → True ∧ True | True |

> 🟢 **Java 对比**:Java `boolean isMirror(TreeNode t1, TreeNode t2)` 逻辑逐字同构。Python 里两个 None 分支可合并成 `if t1 is None or t2 is None: return t1 is t2`,更短(`None is None` 为 True)。

> ⚠️ **常见坑**:
> 1. 同侧比较(见上 ❌)——记口诀「**左对右,右对左**」。
> 2. base case 只写「都空 → True」,漏了「一空一不空 → False」→ `NoneType` 崩溃。
> 3. 想用层序遍历 + 每层判回文:`None` 占位会让回文判断很绕,递归才是正解。

**复杂度**:时间 O(n)(每对节点比一次);空间 O(h)。

> ✅ **做 `is_symmetric`**:闭包 `mirror(t1, t2)`——都 None→True;一个 None→False;值不等→False;否则 `mirror(t1.left, t2.right) and mirror(t1.right, t2.left)`。入口先判 root 空,再 `mirror(root.left, root.right)`。

---

## §38.5 is_valid_bst:LC98 验证二叉搜索树 🟡

**题面**:判断是否为合法**二叉搜索树**。BST 定义:任意节点 x,**左子树所有值 < x.val**,**右子树所有值 > x.val**(等值不允许)。

**例**:
- `[2,1,3]` → `True`
- `[5,1,4,None,None,3,6]` → `False`(右子树里的 3 < 根 5)
- `[1,1]` → `False`(等值不允许)
- `[2147483647]` → `True`(单节点值再大也合法——见下面 INT_MAX 坑)

### ❌ 错误写法:只比「直接孩子」

```python
def bad(node):
    if node is None:
        return True
    if node.left and node.left.val >= node.val:
        return False
    if node.right and node.right.val <= node.val:
        return False
    return bad(node.left) and bad(node.right)
```

这种写法**漏判孙子辈**。反例:

```
        5
       / \
      4   6       6 > 5 ✅, 4 < 5 ✅ —— 每个节点「直接孩子」都合法
         / \
        3   7     但 3 在 5 的【右子树】里,3 < 5,违反 BST!
```

6 自己合法,但 6 的左孩子 3「跨过」了根 5 的下界——`bad` 检测不到。

### ✅ 正确写法:DFS 带上下界 (low, high)

```python
def is_valid_bst(root):
    def validate(node, low, high):
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return (validate(node.left, low, node.val)
                and validate(node.right, node.val, high))
    return validate(root, float("-inf"), float("inf"))
```

**为什么这么做**:给每个节点配一个合法区间 `(low, high)`,递归时下传并收紧:

- 根:区间 `(-∞, +∞)`(任意值都行)
- 走左子树:区间 `(low, 父值)` —— 整棵左子树所有值必须 `< 父值`(上界收紧)
- 走右子树:区间 `(父值, high)` —— 整棵右子树所有值必须 `> 父值`(下界收紧)

这样孙子辈天然被「祖辈的界」约束:上面反例里的 3 在右子树会撞上 `low=5` 的下界 → False。

**逐步推演** `[5,4,6,None,None,3,7]`:

| 调用 | 区间 (low, high) | 判断 | 结果 |
|------|------------------|------|------|
| validate(5) | (-∞, +∞) | -∞ < 5 < +∞ | 继续 |
| validate(4) | (-∞, 5) | 4 < 5 ✅ | 继续(子树全空 → True) |
| validate(6) | (5, +∞) | 5 < 6 ✅ | 继续 |
| validate(3) | (5, 6) | 3 > 5?❌ | **False**(越下界) |

> 🟡 **Java 对比 / 差异**:Java 版常用 `Long.MIN_VALUE` / `Long.MAX_VALUE` 当初始界,有隐患——节点值**恰好等于边界**时(如单节点 `[2147483647]` = `Integer.MAX_VALUE`),开区间判断会把合法节点误判成 False。Python 用 `float("-inf")` / `float("inf")` 表示无界:**真·无穷大,任何节点值都撞不穿**,天然免疫这个坑。

> **为什么是开区间 `low < node.val < high`**:BST 不允许等值(等值放哪边有歧义,LC98 明确不允许)。所以用 `<` 而非 `<=`,等值节点 → False。

> **另一思路(了解即可)**:BST 的中序遍历结果严格递增,中序扫一遍判升序也行。但带上下界更直观、和模板 A 同构,面试首选。

> ⚠️ **常见坑**:
> 1. 只比直接孩子(见上 ❌)。
> 2. 初始界用 INT_MIN / INT_MAX,节点值恰好等于边界时误判。
> 3. 区间写成闭区间 `low <= val <= high` → 等值树 `[1,1]` 会误判 True。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ **做 `is_valid_bst`**:闭包 `validate(node, low, high)`——空 → True;`low < val < high` 否则 False;左走 `(low, val)`、右走 `(val, high)`;初始 `(-∞, +∞)`。

---

## §38.6 level_order:LC102 二叉树层序遍历 🟡

**题面**:自顶向下、逐层从左到右返回值,**每层一个 list**。

**例**:
- `[3,9,20,None,None,15,7]` → `[[3],[9,20],[15,7]]`
- `[1]` → `[[1]]`
- `[]` → `[]`(注意不是 `[[]]`)

### ❌ 错误写法一:没有 level_size,输出扁平

```python
while queue:
    node = queue.popleft()
    result.append(node.val)      # [3, 9, 20, 15, 7] —— 层界全丢
    ...
```

### ❌ 错误写法二:list 当队列

```python
queue = [root]
node = queue.pop(0)    # O(n)!整个 list 往前挪
```

层序遍历要弹 n 次,每次 O(n) → 整体 **O(n²)**。这是本章最大的性能坑。

### ✅ 正确写法:deque + level_size 按层切分

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
            node = queue.popleft()        # ★ O(1)
            level_vals.append(node.val)
            if node.left:  queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level_vals)
    return result
```

**为什么这么做**:BFS 用队列(FIFO),先进先出保证「同一层的节点在队列里连续排」。但题目要的不是一条扁平序列,是**按层分组**。

**按层切分的技巧**:每轮 `while` 开始时,先记 `level_size = len(queue)`——此时队列里**正好是当前层的所有节点**。然后 `for _ in range(level_size)` 刚好弹完这一层;期间入队的是**下一层**的节点,不会污染当前层。

**逐步推演** `[3,9,20,None,None,15,7]`:

| 轮 | level_size | 弹出(从左到右) | 本层收集 | 轮末队列 |
|----|-----------|----------------|----------|----------|
| 1 | 1 | 3 | `[3]` | [9, 20] |
| 2 | 2 | 9, 20 | `[9, 20]` | [15, 7] |
| 3 | 2 | 15, 7 | `[15, 7]` | [] |

→ `[[3],[9,20],[15,7]]` ✅

> 🟡 **Python 特有 —— 一定要用 `deque`**:`deque`(双端队列)两端进出都 O(1),= Java 的 `ArrayDeque`(你刷题用过)。`deque.append` = `offer`(入队尾),`deque.popleft` = `poll`(出队头),语义一一对应。普通 `list` 只有尾部操作是 O(1)。

> ⚠️ **常见坑**:
> 1. 用 `list.pop(0)` 当队列(O(n),慢)。
> 2. 没有 `level_size` 切分,结果变扁平 `[3,9,20,15,7]`。
> 3. 忘了空树返回 `[]`(不是 `[[]]`,也不是 None)。

**复杂度**:时间 O(n);空间 O(n)(最宽一层的节点数,平衡树约 n/2)。

> ✅ **做 `level_order`**:`deque([root])` → 每轮 `level_size = len(queue)` → `for _ in range(level_size)` 弹出 + 收集 + 入孩子 → 每层 append 到 result。空树 `[]`。

---

## §38.7 right_side_view:LC199 二叉树右视图 🟡

**题面**:从树的**右侧**看过去,从上到下能看到的节点值(= 每层最右边的那个节点)。

**例**:
- `[1,2,3,None,5,None,4]` → `[1,3,4]`

```
      1
     / \
    2   3
     \   \
      5   4      ← 第 2 层看到 3(挡住 2);第 3 层看到 4(挡住 5)
```

- `[1,2,3,4]` → `[1,3,4]`

```
      1
     / \
    2   3
   /
  4            ← 第 3 层只有 4(它在左侧!),照样看得到
```

- `[1,None,3]` → `[1,3]`;`[]` → `[]`

### ❌ 错误写法:以为「一路贪右」就是答案

```python
def rsv_bad(root):
    result = []
    while root:
        result.append(root.val)
        root = root.right if root.right else root.left   # 一路往右钻
    return result
```

拿 `[1,2,3,4]` 试:一路贪右走出 `[1,3]`,**漏了 4**——第 3 层右侧没人,从右边只能看到左侧的 4。「右视图」的真实定义是「**每层最后一个**」,不是「最右路径」。

### ✅ 正确写法:BFS 复用 level_size,取每层末位

```python
from collections import deque

def right_side_view(root):
    if root is None:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)          # 同一个按层切分技巧(§38.6)
        for i in range(level_size):
            node = queue.popleft()
            if i == level_size - 1:      # ★ 本层最后一个 = 从右侧能看到的
                result.append(node.val)
            if node.left:  queue.append(node.left)
            if node.right: queue.append(node.right)
    return result
```

**为什么这么做**:右视图 = 层序遍历的「每层只留最后一个」。§38.6 的 `level_size` 技巧原封不动搬过来,只在弹出本层第 `level_size - 1` 个(最后一个)节点时记录值——左到右入队保证了最后一个就是最右。

**逐步推演** `[1,2,3,None,5,None,4]`:

| 轮 | level_size | 弹出(从左到右) | 记录(i == 末位) |
|----|-----------|----------------|------------------|
| 1 | 1 | 1 | 1 |
| 2 | 2 | 2, 3 | 3 |
| 3 | 2 | 5, 4 | 4 |

→ `[1, 3, 4]` ✅

### 另解:DFS「先右后左 + 首访记录」(面试加分项)

```python
def right_side_view_dfs(root):
    result = []

    def dfs(node, depth):
        if node is None:
            return
        if depth == len(result):     # 该深度第一次被访问 → 就是该层最右
            result.append(node.val)
        dfs(node.right, depth + 1)   # 先右!保证每层首访的是最右节点
        dfs(node.left, depth + 1)

    dfs(root, 0)
    return result
```

`depth == len(result)` 是灵魂:访问到第 `depth` 层时,`result` 里已有 `depth` 个值 ⟺ 这一层还没人记录过;因为**先递归右子树**,每层首访者必是最右节点。若先左后右,就变成左视图了。

> 🟡 **Java 对比**:BFS 版同 §38.6,只是收集条件从「全收」变「`i == levelSize - 1` 才收」。DFS 版 Java 也常见,`depth == res.size()` 同一判断。

> ⚠️ **常见坑**:
> 1. 「一路贪右」漏掉左侧孤层(见上 ❌)。
> 2. BFS 忘了 `level_size` 切层,不知道谁是「每层最后」。
> 3. DFS 版先左后右 → 写成左视图。
> 4. 空树返回 `[]`。

**复杂度**:时间 O(n);空间 BFS O(n)(最宽一层),DFS O(h)。

> ✅ **做 `right_side_view`**:BFS 复用 `level_size`;弹到 `i == level_size - 1` 时收值;孩子照常入队。空树 `[]`。

---

## §38.8 lowest_common_ancestor:LC236 最近公共祖先 🔴

**题面**:找 p、q 在树中**离它们最近**的共同祖先节点。定义:节点 x 是 p、q 的公共祖先,当且仅当 p、q 都在「以 x 为根的子树」里;「最近」= 最深的那个 x。**一个节点可以是自己的祖先**(比如 p 是 q 的祖先时,LCA 就是 p)。题目保证 p、q 都在树中且互不相同。

**例**(树 `[3,5,1,6,2,0,8,None,None,7,4]`):

```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4
```

- p=5, q=1 → LCA=3(分居根的两侧)
- p=5, q=4 → LCA=5(4 在 5 的子树里,5 是自己的祖先)
- p=6, q=4 → LCA=5(都在左子树,分叉点是 5)

### ❌ 错误写法:忘了「命中汇报」的 base case

```python
def lca_bad(root, p, q):
    if root is None:
        return None
    # 漏了 root is p / root is q 就往下递归!
    left = lca_bad(root.left, p, q)
    right = lca_bad(root.right, p, q)
    ...
```

找到 p / q 时不向上汇报,`left` / `right` 永远 None,任何输入都返回 None。

### ✅ 正确写法:后序 DFS,左右都非空 → 当前是 LCA

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

1. **base case**:当前是 `None` → 不是任何节点的祖先,返回 None;当前**就是 p 或 q** → 找到一个目标,把它「向上汇报」(返回当前节点)。
2. 递归左、右子树,各拿到一个结果(`left`、`right`):
   - **左右都非空** → p、q **分居**当前节点两侧 → 当前节点就是 LCA(再往下走只能找到一个,所以这里是「最近」的分叉)。
   - **只有一边非空** → p、q 都在那一边 → 答案在那边,递归结果就是 LCA。
   - **两边都空** → 这棵子树里没有 p/q → 返回 None。

**逐步推演**(同一棵树):

| 求 | 左子树结果 | 右子树结果 | 结论 |
|----|-----------|-----------|------|
| LCA(5, 1) | 命中 5 | 命中 1 | 左右都非空 → 返回根 **3** |
| LCA(5, 4) | 5 的子树里先后命中 5 和 4 → 汇报 5 | None | 只有左非空 → 返回 **5** |

> 🔴 **思路较绕的点**:
> - 「**返回值的含义是重载的**」:返回非 None,意思是「这棵子树里**至少包含 p 或 q 之一**」;至于是 p、是 q、还是 LCA,由调用方根据「左右是否都非空」判断。这是本题最绕的地方。
> - 「**节点是自己的祖先**」:所以 base case `root is p or root is q` 直接返回 root。这就是 `LCA(5, 4)` 能返回 5 的原因——5 向上汇报,4 也在 5 的子树里。
> - 「**用对象引用相等(`is`)而不是 `val` 比较**」:树里可能有重复值,LCA 必须按**节点身份**定位 p、q。测试用 `find_node(root, val)` 先拿到 p、q 的对象引用再传入。

> 🟢 **Java 对比**:逻辑完全一样。Python 只是用 `is None` 替代 `== null`,用 `left is not None and right is not None` 替代 `left != null && right != null`。

> **为什么是后序**:必须先知道「左子树有没有 p/q、右子树有没有 p/q」,才能判断当前节点是不是分叉点。前序(先看自己)做不到——「分散 vs 集中」的判断依赖子树的结果。

> ⚠️ **常见坑**:
> 1. 用 `node.val == p.val` 比较(重复值会定位错节点)。要用 `is`。
> 2. 忘了「命中汇报」base case(见上 ❌)。
> 3. 左右都找到时不敢返回当前节点(怀疑「会不会有更深的」)——不会,再往下只能找到一个目标,这里就是最近的分叉。

**复杂度**:时间 O(n);空间 O(h)。

> ✅ **做 `lowest_common_ancestor`**:`if root is None or root is p or root is q: return root` → 递归左右 → 左右都非空返回 root → 否则返回非空那边。

---

## 📊 七道题复杂度一览

| 题 | 方法 | 时间 | 空间 | 关键 |
|----|------|------|------|------|
| max_depth | DFS 后序 | O(n) | O(h) | `1 + max(左, 右)`,空 = 0 |
| invert_tree | DFS | O(n) | O(h) | 原地交换 `a, b = b, a` |
| is_symmetric | DFS 双树 | O(n) | O(h) | 交叉比较:左对右、右对左 |
| is_valid_bst | DFS 带界 | O(n) | O(h) | 区间 (low, high) 收紧,±inf 无界 |
| level_order | BFS | O(n) | O(n) | deque + level_size 切层 |
| right_side_view | BFS / DFS | O(n) | O(n) / O(h) | 每层末位 / 先右后左首访 |
| LCA | DFS 后序 | O(n) | O(h) | 左右分散 → 当前是 LCA,`is` 比较 |

> h = 树高。平衡 h = log n,退化链(全左/全右)h = n。LeetCode 退化链大数据要防递归爆栈:`import sys; sys.setrecursionlimit(10000)`。

---

## §38.9 Java 老手常踩的坑 ⚠️

1. **`list.pop(0)` 当队列**:O(n)!层序 / 右视图务必用 `collections.deque` + `popleft()`。
2. **BST 只比直接孩子**:漏判孙子辈。必须带上下界 `(low, high)` 收紧。
3. **BST 初始界用 INT_MIN / INT_MAX**:节点值恰好等于边界时误判。Python 用 `float('-inf')` / `float('inf')` 永不撞穿。
4. **对称树同侧比较**:镜像是「左对右、右对左」**交叉**比;同侧比是「判相同」,不是镜像。
5. **递归爆栈**:Python 默认递归上限 1000,退化链(深度 = 节点数)大数据会 `RecursionError` → `sys.setrecursionlimit` 或改迭代。
6. **忘了 base case 的返回值**:DFS 模板里 `if node is None: return <空答案>` 是地基——深度题 0、布尔题 True、找节点题 None。漏了直接 NoneType 崩溃。
7. **右视图 = 一路贪右**:错。是「每层最后一个」;BFS 取 `i == level_size - 1`,DFS 先右后左 + `depth == len(result)`。
8. **LCA 用 `val` 比较**:重复值会定位错节点。必须按对象身份 `is` 比较。

---

## 📝 本章作业

| 任务 | LeetCode | 知识点 | 难度 |
|------|----------|--------|------|
| `max_depth` | LC104 | DFS 后序 + base case | 🟢 |
| `invert_tree` | LC226 | DFS + 元组交换,原地修改 | 🟢 |
| `is_symmetric` | LC101 | DFS 双树镜像,交叉比较 | 🟢 |
| `is_valid_bst` | LC98 | DFS 带上下界(易错) | 🟡 |
| `level_order` | LC102 | BFS + deque + 按层切分 | 🟡 |
| `right_side_view` | LC199 | BFS 取每层末位 | 🟡 |
| `lowest_common_ancestor` | LC236 | DFS 后序 + 引用相等 | 🔴 |

> 🏗️ **scaffolding**:`ch38_assignment.py` 顶部已定义 `TreeNode` 类(= LeetCode 提交模板),**不擦、不算作业体**,7 道题和测试共用它。测试里另有 `build_tree(values)` helper(§38.1 讲过读法),按层序数组建树。

```bash
uv run pytest 06_leetcode/ch38/test_ch38_assignment.py -v
```

全绿 = 你掌握了 Ch38。

---

## ✅ 自测

- [ ] 能默写 DFS 后序的通用模板(base case + 左右递归 + 合成)?
- [ ] 知道为什么 `max_depth` 是 `1 + max(左, 右)`,base case 空树 = 0?
- [ ] 能手推 `invert_tree([2,1,3])` 的递归 + 交换过程,说清为什么是原地修改?
- [ ] 能说清 `is_symmetric` 为什么必须「交叉比较」,同侧比较判的是什么?
- [ ] 能说清 `is_valid_bst` 为什么不能只比直接孩子,必须带 `(low, high)` 区间?初始界为什么用 ±inf?
- [ ] 知道 `level_order` 为什么必须用 `deque` 而不是 `list`,`level_size` 怎么按层切分?
- [ ] 能说清 `right_side_view` 为什么不是「一路贪右」,BFS 怎么取每层末位?
- [ ] 能讲清 `lowest_common_ancestor` 里「返回值重载」「节点是自己祖先」「左右分散 → 当前是 LCA」三件事?
- [ ] 7 个作业 pytest 全绿?

## 🎓 费曼挑战

1. 「**为什么 max_depth 用后序(先左右后自己)?能不能用前序写?**」(提示:前序要「自顶向下传当前深度」当参数,后序更自然)—— 重读 §38.2
2. 「**invert_tree 先交换再递归(前序)和先递归再交换(后序),为什么结果一样?**」—— 重读 §38.3
3. 「**is_symmetric 如果改成同侧比较,哪棵对称树会被误判?**」—— 重读 §38.4
4. 「**is_valid_bst 如果用 INT_MIN 当初始下界,什么 case 会出错?**」—— 重读 §38.5
5. 「**level_order 如果不记 level_size,直接 while queue 弹一个处理一个,结果会怎样?**」—— 重读 §38.6
6. 「**right_side_view 的 DFS 版为什么要先右后左?`depth == len(result)` 在判断什么?**」—— 重读 §38.7
7. 「**lowest_common_ancestor 为什么必须用 `is` 比较 p/q,用 `val` 比较哪里会错?**」—— 重读 §38.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch39 动态规划

树题练完递归直觉,接下来把递归用到「**最优化**」上 —— 动态规划(DP):`fib(n) = fib(n-1) + fib(n-2)` 这种「大问题 = 子问题组合」的递推。从 `@lru_cache` 记忆化搜索到状态转移方程,从自顶向下到自底向上。树的 DFS 就是 DP 的热身。
