"""
Ch37 作业:栈 / 队列 / 单调栈(LeetCode 高频 7 题)。

四大套路,梯度从 🟢 到 🔴:
  1. 配对/嵌套类   —— is_valid_parens(LC20)、remove_adjacent_duplicates(LC1047)
  2. 表达式求值    —— eval_rpn(LC150,含 Python 除法向零取整大坑)
  3. 辅助栈/O(1) 最值 —— make_min_stack_class(LC155)
  4. 队列          —— make_my_queue_class(LC232,双栈造队列)
  5. 单调栈        —— daily_temperatures(LC739)、trap(LC42 Hard)

Python 里 list 当栈(.append 入、.pop 出,均摊 O(1));队列用 collections.deque。
本章纯 stdlib。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch37/test_ch37_assignment.py -v

全绿 = 你掌握了 Ch37。每题 docstring 的【对应小节】指向 tutorial.md,卡住 → 回查对应 §。

约定:make_min_stack_class / make_my_queue_class 是工厂函数(Ch05 同模式)——
在函数体内定义类、返回类对象;测试先拿到类再实例化。
"""


# ========== §37.2 LC20 有效的括号 ==========


def is_valid_parens(s: str) -> bool:
    """
    【栈 · §37.2】LC20 有效的括号。给定只含 ()[]{} 的字符串,判断是否合法。
    合法 = 每个右括号都能和「最近的未匹配左括号」配对,且最终栈空。

    示例:
        is_valid_parens("()")      -> True
        is_valid_parens("()[]{}")  -> True
        is_valid_parens("{[]}")    -> True
        is_valid_parens("(]")      -> False
        is_valid_parens("([)]")    -> False  (交叉,栈顺序不对)
        is_valid_parens("")        -> True
        is_valid_parens("(")       -> False  (左括号没闭合)

    思路(栈 + dict 反向映射):
        1. 左括号 -> 入栈
        2. 右括号 -> 看栈顶是不是「它对应的左括号」;栈空或不匹配 -> False
        3. 走完字符串,栈必须为空(否则有左括号没闭合)

    技巧:pairs = {')': '(', ']': '[', '}': '{'} 一行表达配对表;
    三个失败点:右括号来栈空 / 栈顶不匹配 / 走完栈非空。
    """
    # TODO: 用栈 + 字典做括号配对
    ...


# ========== §37.3 LC1047 删除相邻重复项 ==========


def remove_adjacent_duplicates(s: str) -> str:
    """
    【栈 · §37.3】LC1047 删除字符串中所有相邻重复项(消消乐)。
    反复删除「相邻的两个相同字符」直到不能删,返回最终串。

    示例:
        remove_adjacent_duplicates("abbaca") -> "ca"   (删 bb -> aaca -> 删 aa)
        remove_adjacent_duplicates("azxxzy") -> "ay"
        remove_adjacent_duplicates("")       -> ""
        remove_adjacent_duplicates("aab")    -> "b"
        remove_adjacent_duplicates("abcba")  -> "abcba" (无相邻相同)

    思路(和 LC20 同一模式:「遇栈顶结算」):
        遍历每个字符:
          - 栈非空 且 栈顶 == 当前字符 -> 弹出栈顶(消掉一对)
          - 否则 -> 当前字符入栈等待
        最后 "".join(stack) 就是答案(栈里剩下的顺序即原顺序)

    提示:括号配对是「右括号 vs 栈顶左括号查 dict」,本题是「新字符 vs 栈顶同字符
    直接比」。骨架一模一样。
    """
    # TODO: 栈顶相同则弹,否则压;最后 "".join
    ...


# ========== §37.4 LC150 逆波兰表达式求值 ==========


def eval_rpn(tokens: list[str]) -> int:
    """
    【栈 · §37.4】LC150 逆波兰表达式求值(后缀表达式)。
    遇数字压栈;遇运算符弹出两个数运算后压回。除法向零取整。

    示例:
        eval_rpn(["2", "1", "+", "3", "*"])                 -> 9   ((2+1)*3)
        eval_rpn(["4", "13", "5", "/", "+"])                -> 6   (4 + 13/5)
        eval_rpn(["10","6","9","3","+","-11","*","/","*","17","+","5","+"]) -> 22
        eval_rpn(["18"])                                    -> 18
        eval_rpn(["6", "-132", "/"])                        -> 0   (向零!)

    思路:
        ops = {"+", "-", "*", "/"};栈存 int。
        遇运算符时:b = stack.pop(); a = stack.pop()
          —— 先弹的是【右】操作数!a - b / a / b 顺序别反。

    🔴 最大坑:除法要【向零取整】,写 int(a / b),
    不能写 a // b —— Python // 是向下取整,-6 // 132 == -1 而 int(-6/132) == 0。
    """
    # TODO: 数字入栈;运算符弹两个(先右后左);除法 int(a / b)
    ...


# ========== §37.5 LC155 最小栈 ==========


def make_min_stack_class():
    """
    【辅助栈 · §37.5】LC155 最小栈。push / pop / top / get_min 全部 O(1)。
    工厂函数模式(同 Ch05):在函数体内定义类 MinStack 并 return 它。

    难点:get_min O(1)。普通栈取最小要遍历 O(n)。
    解法:【辅助栈 mins】与主栈同步增减,栈顶始终是「到当前为止的最小值」。

    示例:
        MinStack = make_min_stack_class()
        ms = MinStack()
        ms.push(-2); ms.push(0); ms.push(-3)
        ms.get_min()  -> -3
        ms.pop()
        ms.top()      -> 0
        ms.get_min()  -> -2

    任务:类内四个方法:
        __init__(self):self.stack = []; self.mins = []
        push(self, val):主栈 append val;
                        辅助栈 append(val if 空 else min(val, self.mins[-1]))
        pop(self):主栈、辅助栈【同步】pop(别忘辅助栈!)
        top(self) -> int:return self.stack[-1]
        get_min(self) -> int:return self.mins[-1]

    为什么同步 pop 正确:辅助栈每层记录「到这层为止的最小值」,弹掉栈顶后,
    新栈顶正好是「到上一层为止的最小值」——两栈历史对齐。
    """
    # TODO: class MinStack(双栈同步) + return MinStack
    ...


# ========== §37.6 LC232 用栈实现队列 ==========


def make_my_queue_class():
    """
    【队列 · §37.6】LC232 用栈实现队列。只用两个栈(LIFO)拼出 FIFO 队列。
    工厂函数模式(同 Ch05):在函数体内定义类 MyQueue 并 return 它。

    核心:in_stack 收新元素(队尾),out_stack 出队(队头)。
    【只有 out_stack 空了】才把 in_stack 全倒过来(倒一次顺序翻正)。

    示例:
        MyQueue = make_my_queue_class()
        q = MyQueue()
        q.push(1); q.push(2); q.push(3)
        q.pop()    -> 1   (倒栈发生在这)
        q.push(4)
        q.pop()    -> 2   (out 不空,不倒,直接弹)
        q.peek()   -> 3
        q.empty()  -> False

    任务:类内方法:
        __init__(self):self.in_stack = []; self.out_stack = []
        push(self, x):in_stack.append(x)
        pop(self) -> int:先「out 空则倒」,再弹 out 栈顶
        peek(self) -> int:先「out 空则倒」,再看 out 栈顶
        empty(self) -> bool:两栈都空

    均摊 O(1) 论证:每个元素一生只「进 in、倒出、进 out、弹出」4 次,
    n 个元素 4n 次操作,摊到每次调用 O(1)。
    """
    # TODO: class MyQueue(双栈互倒,out 空才倒) + return MyQueue
    ...


# ========== §37.7 LC739 每日温度 ==========


def daily_temperatures(temps: list[int]) -> list[int]:
    """
    【单调栈 · §37.7】LC739 每日温度。
    返回数组 ans:ans[i] = 第 i 天之后第一个比 temps[i] 高的天,隔几天;没有则 0。

    示例:
        daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) -> [1, 1, 4, 2, 1, 1, 0, 0]
        daily_temperatures([30, 40, 50, 60])                 -> [1, 1, 1, 0]
        daily_temperatures([90, 80, 70, 60])                 -> [0, 0, 0, 0]
        daily_temperatures([30])                             -> [0]
        daily_temperatures([])                               -> []

    思路(单调递减栈,存【下标】):
        1. 栈里存「还没等到更高温的天的下标」,栈内温度保持单调递减
        2. 遍历每天 i:
             while 栈非空 且 temps[i] > temps[栈顶]:
                 j = 栈.pop()           # 第 j 天等到了,更高温是第 i 天
                 ans[j] = i - j
             栈.append(i)
        3. 留在栈里的永远没等到,ans 默认 0 即可

    提示:栈必须存【下标】不是温度——答案要算距离 i - j。
    均摊 O(n):每个下标入栈/出栈至多一次,while 总次数 ≤ n。
    """
    # TODO: 单调递减栈存下标
    ...


# ========== §37.8 LC42 接雨水(Hard) ==========


def trap(height: list[int]) -> int:
    """
    【双指针/单调栈 · §37.8】LC42 接雨水(Hard)。
    给定 n 个非负整数表示每根柱子高度,返回能接多少雨水。

    示例:
        trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) -> 6
        trap([4, 2, 0, 3, 2, 5])                   -> 9
        trap([3, 0, 3])                            -> 3
        trap([])                                   -> 0
        trap([1])                                  -> 0

    破题视角:每根柱子能接的水 = min(它左边最高, 它右边最高) - 它自身高度(取正)。

    思路 A(对撞双指针,O(n) 时间 O(1) 空间 —— 推荐,本作业用它):
        left/right 两个指针 + left_max/right_max 两侧最高:
            if height[left] < height[right]:
                # 左边矮,左侧水位由 left_max 决定(右侧必有更高挡着)
                left_max = max(left_max, height[left])
                ans += left_max - height[left]
                left += 1
            else:
                right_max = max(right_max, height[right])
                ans += right_max - height[right]
                right -= 1
        关键直觉:【矮的那侧定型】——另一侧一定有更高的柱子挡着,水位只看本侧 max。

    思路 B(单调栈,了解):单调递减栈存下标;新柱子更高则形成凹槽,
    弹出槽底,按 (min(左壁,右壁) - 底) × 宽 累加。
    """
    # TODO: 对撞双指针;矮侧定型
    ...
