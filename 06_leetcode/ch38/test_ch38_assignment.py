"""
Ch38 作业测试。运行:

    uv run pytest 06_leetcode/ch38/test_ch38_assignment.py -v

测试构造树用 build_tree(values)(按 LeetCode 层序,None 占位建树,读法见
tutorial §38.1);LCA 测试用 find_node(root, val) 按 val 拿到节点引用;
tree_to_level_list(root) 把树序列化回层序数组用于对比翻转结果。
这三个 helper 是测试工具,不算作业。

题目:LC104 / LC226 / LC101 / LC98 / LC102 / LC199 / LC236,每题一个
TestXxx 类,含正常 + 边界(空、单节点、斜链、LeetCode 官方示例)用例。
"""
from __future__ import annotations

import pytest

from ch38_assignment import (
    TreeNode,
    max_depth,
    invert_tree,
    is_symmetric,
    is_valid_bst,
    level_order,
    right_side_view,
    lowest_common_ancestor,
)


# ============================================================================
# helper:按 LeetCode 层序(None 占位)建树  ——  测试工具,非作业
# ============================================================================
def build_tree(values: list[int | None]) -> TreeNode | None:
    """
    按 LeetCode 层序数组建树,None 表示该位置无节点。

    例 build_tree([3, 9, 20, None, None, 15, 7]):
             3
            / \\
           9  20
              / \\
             15  7
    空数组 / [None] → None。
    """
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]
    i = 1
    for node in queue:  # 利用 list 边遍历边追加 = 层序展开
        if i >= len(values):
            break
        # 左孩子
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])  # type: ignore[arg-type]
            queue.append(node.left)
        i += 1
        # 右孩子
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])  # type: ignore[arg-type]
            queue.append(node.right)
        i += 1
    return root


def find_node(root: TreeNode | None, val: int) -> TreeNode | None:
    """按 val 在树里找节点(BST 性质不保证,用通用前序搜)。找不到返回 None。"""
    if root is None:
        return None
    if root.val == val:
        return root
    return find_node(root.left, val) or find_node(root.right, val)


def tree_to_level_list(root: TreeNode | None) -> list[int | None]:
    """把树序列化回 LeetCode 层序数组(带 None 占位),用于对比翻转结果。"""
    if root is None:
        return []
    out: list[int | None] = []
    queue: list[TreeNode | None] = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    # 去掉末尾连续的 None(LeetCode 惯例不写尾随 null)
    while out and out[-1] is None:
        out.pop()
    return out


# ============================================================================
# 1. LC104 · max_depth
# ============================================================================
class TestMaxDepth:
    def test_lc_example(self):
        #     3
        #    / \
        #   9  20
        #      / \
        #     15  7
        root = build_tree([3, 9, 20, None, None, 15, 7])
        assert max_depth(root) == 3

    def test_empty(self):
        assert max_depth(None) == 0

    def test_single_node(self):
        assert max_depth(TreeNode(1)) == 1

    def test_left_skewed(self):
        # 1 -> 2 -> 3(全左链,深度 3)
        root = TreeNode(1, TreeNode(2, TreeNode(3)))
        assert max_depth(root) == 3

    def test_right_skewed(self):
        # 1 -> 2 -> 3(全右链,深度 3)
        root = TreeNode(1, None, TreeNode(2, None, TreeNode(3)))
        assert max_depth(root) == 3

    def test_balanced_two_levels(self):
        #     1
        #    / \
        #   2   3
        root = build_tree([1, 2, 3])
        assert max_depth(root) == 2


# ============================================================================
# 2. LC226 · invert_tree
# ============================================================================
class TestInvertTree:
    def test_lc_example(self):
        #     4              4
        #    / \            / \
        #   2   7   ->    7    2
        #  / \ / \      / \   / \
        # 1 3 6  9     9  6  3  1
        root = build_tree([4, 2, 7, 1, 3, 6, 9])
        inverted = invert_tree(root)
        assert tree_to_level_list(inverted) == [4, 7, 2, 9, 6, 3, 1]

    def test_empty(self):
        assert invert_tree(None) is None

    def test_single_node(self):
        root = TreeNode(1)
        result = invert_tree(root)
        assert result is root and result.val == 1
        assert result.left is None and result.right is None

    def test_two_nodes(self):
        #   2    ->    2
        #  /          \
        # 1            1
        root = TreeNode(2, TreeNode(1))
        inverted = invert_tree(root)
        assert inverted.val == 2
        assert inverted.left is None
        assert inverted.right is not None and inverted.right.val == 1

    def test_in_place_modification(self):
        # 翻转应原地修改同一棵树,返回同一根对象(新建树的实现过不了这关)
        root = build_tree([1, 2, 3])
        result = invert_tree(root)
        assert result is root  # 同一根引用

    def test_unbalanced(self):
        #     1              1
        #    /               \
        #   2        ->       2
        #  /                   \
        # 3                     3
        root = build_tree([1, 2, None, 3])
        inverted = invert_tree(root)
        assert inverted.val == 1 and inverted.left is None
        assert inverted.right is not None and inverted.right.val == 2
        child = inverted.right
        assert child.left is None
        assert child.right is not None and child.right.val == 3


# ============================================================================
# 3. LC101 · is_symmetric
# ============================================================================
class TestIsSymmetric:
    def test_lc_example_true(self):
        #        1
        #       / \
        #      2   2
        #     / \ / \
        #    3  4 4  3   -> True(同侧比较的实现会在这里误判 False)
        root = build_tree([1, 2, 2, 3, 4, 4, 3])
        assert is_symmetric(root) is True

    def test_lc_example_false(self):
        #     1
        #    / \
        #   2   2
        #    \   \
        #     3   3   -> False(两个 3 在同侧,都是右孩子)
        root = build_tree([1, 2, 2, None, 3, None, 3])
        assert is_symmetric(root) is False

    def test_empty(self):
        assert is_symmetric(None) is True

    def test_single_node(self):
        assert is_symmetric(TreeNode(1)) is True

    def test_mirror_positions_true(self):
        #     1
        #    / \
        #   2   2
        #    \ /
        #    3 3     -> True(2左.right=3 对 2右.left=3,交叉位置互为镜像)
        root = build_tree([1, 2, 2, None, 3, 3, None])
        assert is_symmetric(root) is True

    def test_structure_asymmetric_false(self):
        #     1
        #    / \
        #   2   2
        #  /   /
        # 2   2       -> False(2左有左孩子、2右有左孩子,位置不对称)
        root = build_tree([1, 2, 2, 2, None, 2, None])
        assert is_symmetric(root) is False

    def test_value_asymmetric_false(self):
        #     1
        #    / \
        #   2   2
        #  /     \
        # 3       4   -> False(位置对称但值 3 != 4)
        root = build_tree([1, 2, 2, 3, None, None, 4])
        assert is_symmetric(root) is False


# ============================================================================
# 4. LC98 · is_valid_bst
# ============================================================================
class TestIsValidBst:
    def test_valid_example(self):
        #     2
        #    / \
        #   1   3   -> True
        root = build_tree([2, 1, 3])
        assert is_valid_bst(root) is True

    def test_invalid_lc_example(self):
        #     5
        #    / \
        #   1   4
        #      / \
        #     3   6   -> False(右子树 3 < 根 5)
        root = build_tree([5, 1, 4, None, None, 3, 6])
        assert is_valid_bst(root) is False

    def test_empty(self):
        assert is_valid_bst(None) is True

    def test_single_node(self):
        assert is_valid_bst(TreeNode(1)) is True

    def test_left_grandchild_violation(self):
        # 经典坑:光比「左孩子<我<右孩子」会漏判这种
        #     5
        #    / \
        #   4   6
        #      / \
        #     3   7   -> False(3 在 5 的右子树但 3 < 5)
        root = build_tree([5, 4, 6, None, None, 3, 7])
        assert is_valid_bst(root) is False

    def test_right_grandchild_violation(self):
        #     5
        #    / \
        #   1   8
        #      / \
        #     6   4   -> False(4 在 5 的右子树但 4 < 5)
        root = build_tree([5, 1, 8, None, None, 6, 4])
        assert is_valid_bst(root) is False

    def test_valid_full_three_level(self):
        #        10
        #       /  \
        #      5    15
        #     / \   / \
        #    1   7 12 20   -> True
        root = build_tree([10, 5, 15, 1, 7, 12, 20])
        assert is_valid_bst(root) is True

    def test_duplicate_value_invalid(self):
        # BST 不允许等值;开区间 low < val < high,等值 -> False
        #     1
        #    / \
        #   1   1
        root = build_tree([1, 1, 1])
        assert is_valid_bst(root) is False

    def test_duplicate_left_child_invalid(self):
        #   1
        #  /    左孩子也是 1(等值)-> False(闭区间实现会误判 True)
        # 1
        root = TreeNode(1, TreeNode(1))
        assert is_valid_bst(root) is False

    def test_skewed_valid(self):
        # 全右链 1 -> 2 -> 3,合法 BST
        root = build_tree([1, None, 2, None, None, None, 3])
        assert is_valid_bst(root) is True

    def test_int_max_boundary(self):
        # 节点值恰好等于 int32 上限:用 INT_MAX 当初始界的实现会误判 False
        assert is_valid_bst(TreeNode(2**31 - 1)) is True

    def test_int_min_boundary(self):
        # 同理,int32 下限:用 INT_MIN 当初始下界的实现会误判 False
        assert is_valid_bst(TreeNode(-(2**31))) is True


# ============================================================================
# 5. LC102 · level_order
# ============================================================================
class TestLevelOrder:
    def test_lc_example(self):
        #     3
        #    / \
        #   9  20
        #      / \
        #     15  7   -> [[3],[9,20],[15,7]]
        root = build_tree([3, 9, 20, None, None, 15, 7])
        assert level_order(root) == [[3], [9, 20], [15, 7]]

    def test_empty(self):
        assert level_order(None) == []

    def test_single_node(self):
        assert level_order(TreeNode(1)) == [[1]]

    def test_two_levels(self):
        #     1
        #    / \
        #   2   3
        root = build_tree([1, 2, 3])
        assert level_order(root) == [[1], [2, 3]]

    def test_left_skewed(self):
        # 1 -> 2 -> 3(全左链),每层一个节点
        root = TreeNode(1, TreeNode(2, TreeNode(3)))
        assert level_order(root) == [[1], [2], [3]]

    def test_complete_tree(self):
        #        1
        #       / \
        #      2   3
        #     / \ / \
        #    4  5 6  7
        root = build_tree([1, 2, 3, 4, 5, 6, 7])
        assert level_order(root) == [[1], [2, 3], [4, 5, 6, 7]]

    def test_result_type(self):
        root = build_tree([1, 2, 3])
        result = level_order(root)
        assert isinstance(result, list)
        assert all(isinstance(layer, list) for layer in result)


# ============================================================================
# 6. LC199 · right_side_view
# ============================================================================
class TestRightSideView:
    def test_lc_example(self):
        #     1
        #    / \
        #   2   3
        #    \   \
        #     5   4   -> [1,3,4](3 挡住 2,4 挡住 5)
        root = build_tree([1, 2, 3, None, 5, None, 4])
        assert right_side_view(root) == [1, 3, 4]

    def test_empty(self):
        assert right_side_view(None) == []

    def test_single_node(self):
        assert right_side_view(TreeNode(1)) == [1]

    def test_left_side_visible_when_right_missing(self):
        #     1
        #    / \
        #   2   3
        #  /
        # 4           -> [1,3,4](第 3 层只有左侧的 4,「一路贪右」实现会漏它)
        root = build_tree([1, 2, 3, 4])
        assert right_side_view(root) == [1, 3, 4]

    def test_left_skewed(self):
        # 全左链 1 -> 2 -> 3:每层唯一节点都看得到(贪右实现第一步就卡死)
        root = TreeNode(1, TreeNode(2, TreeNode(3)))
        assert right_side_view(root) == [1, 2, 3]

    def test_right_skewed(self):
        # 全右链 1 -> 2 -> 3
        root = TreeNode(1, None, TreeNode(2, None, TreeNode(3)))
        assert right_side_view(root) == [1, 2, 3]

    def test_complete_tree(self):
        #        1
        #       / \
        #      2   3
        #     / \ / \
        #    4  5 6  7   -> [1,3,7]
        root = build_tree([1, 2, 3, 4, 5, 6, 7])
        assert right_side_view(root) == [1, 3, 7]


# ============================================================================
# 7. LC236 · lowest_common_ancestor
# ============================================================================
class TestLowestCommonAncestor:
    def test_lc_example_split_at_root(self):
        #        3
        #       / \
        #      5   1
        #     / \ / \
        #    6  2 0  8
        #      / \
        #     7   4
        # p=5, q=1 -> LCA=3(分居根的两侧)
        root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p = find_node(root, 5)
        q = find_node(root, 1)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 3

    def test_one_is_ancestor_of_other(self):
        # 同一棵树:p=5, q=4。4 在 5 的子树里 → LCA=5(自己是自己的祖先)
        root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p = find_node(root, 5)
        q = find_node(root, 4)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 5

    def test_lca_in_left_subtree(self):
        # p=6, q=4 都在根的左子树里 → LCA=5
        root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p = find_node(root, 6)
        q = find_node(root, 4)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 5

    def test_lca_in_right_subtree(self):
        # p=0, q=8 都在根的右子树里 → LCA=1
        root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p = find_node(root, 0)
        q = find_node(root, 8)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 1

    def test_root_is_one_of_targets(self):
        # p=root(3), q=任意 → LCA=root(3)
        root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        q = find_node(root, 4)
        assert q is not None
        lca = lowest_common_ancestor(root, root, q)
        assert lca is not None and lca.val == 3

    def test_small_tree(self):
        #     1
        #    / \
        #   2   3
        # p=2, q=3 -> LCA=1
        root = build_tree([1, 2, 3])
        p = find_node(root, 2)
        q = find_node(root, 3)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 1

    def test_parent_child(self):
        #     1
        #    / \
        #   2   3
        # p=1(根), q=2(孩子) → LCA=1(根是孩子的祖先)
        root = build_tree([1, 2, 3])
        p = find_node(root, 1)
        q = find_node(root, 2)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 1

    def test_deep_left_chain(self):
        # 1 -> 2 -> 3(全左链):p=2, q=3 → LCA=2(2 是 3 的祖先)
        root = TreeNode(1, TreeNode(2, TreeNode(3)))
        p = find_node(root, 2)
        q = find_node(root, 3)
        assert p is not None and q is not None
        lca = lowest_common_ancestor(root, p, q)
        assert lca is not None and lca.val == 2
