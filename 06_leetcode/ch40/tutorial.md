# Ch40 · 回溯 / 贪心 + 综合

> **预计**:1 天 ｜ **前置**:Ch34(刷题利器)、Ch38(树/DFS/BFS) ｜ **M6 收官**
> **目标**:拿下 LeetCode 两大思想——**回溯(Backtracking)** 与 **贪心(Greedy)**。回溯是 Ch38 DFS 的延伸:在树上「选→走→撤销」枚举所有解;贪心是另一条路:每步取局部最优,不回头。这是 M6 的收官章,也是 40 章学习项目的最后一站。

> 📐 **本教程的契约**:§40.2–§40.6 对应作业 5 个函数,纯 stdlib,不依赖任何外部库。

---

## 🗺️ 本章地图

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `permute(nums)` | §40.2 | 回溯 + used 标记(全排列 LC46) |
| `subsets(nums)` | §40.3 | 回溯 选/不选 + start 去重(子集 LC78) |
| `combination_sum(candidates, target)` | §40.4 | 回溯 + 排序剪枝 + 可重复选(组合总和 LC39) |
| `max_profit(prices)` | §40.5 | 贪心:维护历史最低(股票 LC121) |
| `can_jump(nums)` | §40.6 | 贪心:维护最远可达(跳跃游戏 LC55) |

> 三道回溯(全排列/子集/组合)+ 两道贪心(股票/跳跃)= 本章五题。回溯模板会了,子集/组合/排列就是**同一套骨架换收集时机和去重方式**。

---

## ⏱️ 学习路径:费曼五步(约 90 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜(先不看答案,猜一下)

1. 给 `[1,2,3]`,它的全排列有几个?你会怎么**系统地**枚举,保证不重不漏?(提示:递归 + 撤销)
2. 子集问题 `[1,2,3]` 有几个子集?它和全排列的**回溯区别**在哪——是叶子才收集,还是每个节点都收集?
3. 组合总和 `[2,3,6,7]` 凑 7,元素**可以重复用**。回溯时下一次递归传 `i` 还是 `i+1`?为什么?
4. 股票 `[7,1,5,3,6,4]` 只许一次交易,怎么**一次遍历**算出最大利润?需要嵌套循环吗?
5. 跳跃游戏 `[2,3,1,1,4]`,能不能不用 DFS、只维护一个「最远能到哪」的变量就判断能不能到末尾?

> 猜完再往下读。能猜对 3 个以上 = 你已经摸到门道了。

---

## §40.1 回溯是什么 + 贪心是什么 🟡

**回溯(Backtracking)** = DFS + 撤销选择。本质是「在一棵隐式的决策树上做 DFS,走到叶子收集答案,回退时撤销刚才的选择」。

```
做选择(path.append(x))
  → dfs() 往下走
撤销选择(path.pop())    ← 这一步就是「回溯」
```

**贪心(Greedy)** = 每一步都取**局部最优**,期望最终得到全局最优。不回溯、不枚举,通常 O(n) 一次遍历搞定。

| | 回溯 | 贪心 |
|---|------|------|
| 思想 | 穷举所有解(树形 DFS) | 每步取局部最优 |
| 复杂度 | 指数级(答案多) | 通常 O(n) |
| 何时用 | 要**所有方案**(排列/组合/子集) | 能证明「局部最优 = 全局最优」 |
| 模板 | `for: append; dfs; pop` | 维护一两个变量扫一遍 |

> 🟡 **Java 对比**:回溯的 append/pop 对应 Java 的 `list.add(x) ... dfs() ... list.remove(list.size()-1)`,最后一行那个 `remove(末尾)` 经常写漏 = bug。Python 的 `path.pop()` 默认弹末尾,语义更清晰。贪心两题 Java/Python 写法几乎一样,但 Python 的 `float('inf')` 比 Java 的 `Integer.MAX_VALUE` 直观。

> **本章为什么把回溯和贪心放一起**:它们是 LeetCode 的「两大枚举哲学」。回溯「全都要」,贪心「只选一个」。刷题时先想:这题要**所有方案**(回溯)还是**一个最优解**(贪心/DP)?想清楚方向再下笔。

---

## §40.2 全排列 permute(LC46)🟡

**题面**:给一个**无重复**数组,返回所有全排列。

### 为什么这么做

n 个位置,每个位置从还没用过的元素里挑一个 → 这就是一棵决策树,叶子是一个排列。用 `used[i]` 标记 `nums[i]` 是否已选,递归到底就收一个排列。

### Python 实现

```python
def permute(nums):
    n = len(nums)
    res, path = [], []
    used = [False] * n

    def dfs():
        if len(path) == n:               # 叶子:收集
            res.append(path.copy())      # ⚠️ 必须 copy,path 还会被改
            return
        for i in range(n):
            if used[i]:
                continue
            used[i] = True               # 做选择
            path.append(nums[i])
            dfs()
            path.pop()                   # 撤销选择
            used[i] = False

    dfs()
    return res
```

### Java 怎么写(对比)

```java
void dfs(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> res) {
    if (path.size() == nums.length) { res.add(new ArrayList<>(path)); return; } // copy
    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue;
        used[i] = true;
        path.add(nums[i]);
        dfs(nums, used, path, res);
        path.remove(path.size() - 1);   // 回溯:必须弹末尾
        used[i] = false;
    }
}
```

> 🟡 **差异点**:Python `path.copy()` 等价 Java `new ArrayList<>(path)`;Java 撤销要 `remove(size-1)`,Python `pop()` 默认弹末尾更省心。逻辑完全同构,Python 少写类型声明。

### 常见坑 ⚠️

1. **忘 copy**:叶子收集时直接 `res.append(path)`,后续 pop 会把已收的也改没——**这是回溯头号 bug**。永远是 `path.copy()` / `path[:]`。
2. **used 数组没初始化**:`[False]*n` 要建好,不能复用上一题的。
3. **撤销不配对**:`append` 之后 `dfs` 之后必须有 `pop`;`used=True` 之后必须有 `used=False`。成对写,缺一不可。

### 复杂度

- 时间 O(n · n!):n! 个排列,每个拷贝 O(n)。
- 空间 O(n):递归栈深 n + path + used。

> ✅ 做 `permute`:`used` 标记 + `append/pop` + `used=True/False` 配对 + 叶子 `path.copy()`。

---

## §40.3 子集 subsets(LC78)🟡

**题面**:给一个**无重复**数组,返回所有子集(含空集)。

### 为什么这么做

子集和全排列的**关键区别**:全排列只有叶子(长度=n)是答案;子集问题**每个节点都是答案**(长度 0、1、2、...、n 都算)。所以一进 dfs 先收,再继续选。

去重靠 **start 下标**:只往后选(`range(start, n)`,递归传 `i+1`),天然保证不重复选、不会出现 `[2,1]` 和 `[1,2]`。

### Python 实现

```python
def subsets(nums):
    res, path = [], []
    n = len(nums)

    def dfs(start):
        res.append(path.copy())          # ⭐ 每个节点都收(含空集)
        for i in range(start, n):
            path.append(nums[i])
            dfs(i + 1)                   # 只往后选 → 去重
            path.pop()

    dfs(0)
    return res
```

### Java 对比

逻辑同构,Java 写法几乎一一对应:`for (int i = start; i < n; i++) { path.add(nums[i]); dfs(i+1); path.remove(path.size()-1); }`。

> 🟡 **差异点**:无显著差异,Python 写起来更短。注意 `res.append(path.copy())` 在循环**之前**(进函数第一件事),保证空集 `[]` 也被收(第一次 dfs(0) 时 path 是空的)。

### 常见坑 ⚠️

1. **收集时机错**:把 `res.append(path.copy())` 写在 `if` 叶子条件里 → 漏掉非叶子的子集。子集问题**进函数就收**。
2. **传 i 而不是 i+1**:`dfs(i)` 会让同一元素被重复选(变成无限递归)。**子集是 i+1**(每个元素只选一次)——和 §40.4 组合总和的可重复选**正好相反**,别搞混。
3. **忘 copy**:同全排列。

### 复杂度

- 时间 O(n · 2ⁿ):2ⁿ 个子集,每个拷贝 O(n)。
- 空间 O(n):递归栈 + path。

> ✅ 做 `subsets`:进 dfs 先收 `path.copy()` + `for i in range(start,n)` 只往后选 + `dfs(i+1)`。

---

## §40.4 组合总和 combination_sum(LC39)🟡

**题面**:候选**无重复**,每个可**无限次**使用,返回所有使和 = target 的组合。

### 为什么这么做

还是回溯骨架,但两个关键变化:

1. **可重复选** → 递归传 `i`(不是 `i+1`),允许下一层再选当前元素。去重靠「只往后选」(`range(start, n)`),保证 `[2,3]` 出现、`[3,2]` 不出现。
2. **剪枝** → 先排序 candidates,循环里一旦 `candidates[i] > remain`(还差这么多),后面更大的更不行,**直接 break**(不是 continue!)。

`remain` 是「还差多少凑够 target」。`remain == 0` 收答案;剪枝保证不会走到 remain < 0。

### Python 实现

```python
def combination_sum(candidates, target):
    res, path = [], []
    candidates = sorted(candidates)      # 排序 → 剪枝前提

    def dfs(start, remain):
        if remain == 0:
            res.append(path.copy())
            return
        for i in range(start, len(candidates)):
            cand = candidates[i]
            if cand > remain:
                break                    # 剪枝:后面更大,都不可能
            path.append(cand)
            dfs(i, remain - cand)        # ⭐ i 不是 i+1:可重复选
            path.pop()

    dfs(0, target)
    return res
```

### Java 对比

`for (int i = start; i < candidates.length; i++) { if (candidates[i] > remain) break; path.add(candidates[i]); dfs(i, remain - candidates[i]); path.remove(...); }`——结构完全一致。

> 🟡 **差异点**:`remain - cand` 是 Python 风格的减法传递;Java 一样。重点是 `dfs(i, ...)` 那个 `i` 别写成 `i+1`(写成 i+1 就退化成每个元素只能用一次的 LC40 组合总和 II 了)。

### 常见坑 ⚠️

1. **不排序就剪枝**:不排序时 `cand > remain` 不能 break(后面可能有更小的)→ 要么先排序,要么改成 continue + 不剪枝(但慢)。
2. **dfs 传 i+1**:变成「每个元素只能用一次」,答案错。**可重复 = 传 i**。
3. **target=0 的边界**:`remain==0` 立即收 `path.copy()`,此时 path 是空的 → 收 `[]`(空组合是合法答案)。测试里 `combination_sum([2,3], 0) == [[]]`。
4. **剪枝用 continue 而非 break**:break 才对(排序后后面更大),continue 会白跑。
5. **忘 copy**:老问题。

### 复杂度

- 时间:最坏指数级,取决于候选和 target;剪枝后实际很快。
- 空间 O(target / min(candidates)):递归深度。

> ✅ 做 `combination_sum`:排序 + `dfs(i, remain-cand)`(i 可重复)+ `if cand > remain: break`(剪枝)+ 叶子收 copy。

---

## §40.5 买卖股票最佳时机 max_profit(LC121)🟢(贪心)

**题面**:给股价数组,**只许一次交易**(先买后卖),求最大利润,不能赚返回 0。

### 为什么这么做(贪心)

每天当作「卖出日」,那能赚的就是 `今天价 - 之前最低价`。一次遍历,维护:

- `min_price`:到目前为止的**最低价**(最佳买入点);
- `best`:到目前为止的最大利润。

每个 price:用它当卖出算利润更新 best,再用它更新 min_price。**不需要嵌套循环**——因为我们只要「最优」,不要「所有方案」,所以贪心一次扫就够。

### Python 实现

```python
def max_profit(prices):
    best = 0
    min_price = float('inf')             # 🔴 Python 用 float('inf'),Java 是 MAX_VALUE
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > best:
            best = price - min_price
    return best
```

### Java 对比

```java
int best = 0, minPrice = Integer.MAX_VALUE;
for (int price : prices) {
    if (price < minPrice) minPrice = price;
    else if (price - minPrice > best) best = price - minPrice;
}
return best;
```

> 🟢 **Java 秒懂**:完全同构。唯一小区别是无穷大:`float('inf')` vs `Integer.MAX_VALUE`。Python 的 `float('inf')` 参与减法不会溢出,Java 的 `MAX_VALUE` 减一下可能溢出(所以 Java 必须先比较再减,顺序敏感)。

### 常见坑 ⚠️

1. **min_price 初值用 0 或 prices[0]**:空数组会越界。用 `float('inf')`,空数组循环不进,直接返回 0。
2. **先更新 min 再算利润**:也能过,但语义上「今天买入今天卖出」利润 0 没意义。先算利润(用昨天的 min)再更新 min 更直观。
3. **想成能多次交易**:这是 LC121 只许一次,LC122 才允许多次,别混。
4. **返回负数**:题目要求不能赚返回 0,`best` 初值就是 0,自然不会负。

### 复杂度

- 时间 O(n),空间 O(1)。这就是贪心的力量——O(n) 搞定。

> ✅ 做 `max_profit`:一个 `min_price` + 一个 `best`,一次遍历更新。

---

## §40.6 跳跃游戏 can_jump(LC55)🟢(贪心)

**题面**:数组每个元素是该位置最多能跳几步,问能否从下标 0 跳到末尾。

### 为什么这么做(贪心)

关键洞察:**可达位置是一个连续区间 `[0, farthest]`**——能跳到位置 k,意味着 0..k 都能到(中间每一步都能落地)。所以维护一个 `farthest`(最远能到哪),扫一遍:

- 若 `i > farthest`:连位置 i 都到不了 → False。
- 否则更新 `farthest = max(farthest, i + nums[i])`。
- `farthest >= n-1` → True。

不用 DFS、不用记路径,一个变量扫一遍。这是贪心的典型:不关心「怎么跳最优」,只关心「能不能到」。

### Python 实现

```python
def can_jump(nums):
    farthest = 0
    n = len(nums)
    for i in range(n):
        if i > farthest:                 # 当前位置都够不到 → 死
            return False
        if farthest >= n - 1:            # 已能到末尾,提前收工
            return True
        farthest = max(farthest, i + nums[i])
    return farthest >= n - 1
```

### Java 对比

```java
int farthest = 0;
for (int i = 0; i < nums.length; i++) {
    if (i > farthest) return false;
    if (farthest >= nums.length - 1) return true;
    farthest = Math.max(farthest, i + nums[i]);
}
return farthest >= nums.length - 1;
```

> 🟢 **Java 秒懂**:结构完全一样。`range(n)` 对应 `for i=0..n-1`,无类型声明差异。

### 常见坑 ⚠️

1. **i > farthest 的判断顺序**:必须在更新 farthest **之前**判断——先确认能到 i,才能从 i 往前跳。
2. **空数组 / 单元素**:`can_jump([])` 空、`can_jump([0])` 单元素 0,都应 True(已在末尾)。循环里 `farthest=0 >= n-1=0` → True,或空数组直接走到 return。注意 `[0,1]` 第一格跳 0 步,到不了第二格 → False。
3. **没提前 return**:不加 `farthest >= n-1` 提前返回也能对,但会多扫,大用例慢。提前 return 是优化。
4. **混淆 LC45**:本题只要返回 bool(能不能),LC45 跳跃游戏 II 要返回**最少步数**(DP/贪心),别混。

### 复杂度

- 时间 O(n),空间 O(1)。

> ✅ 做 `can_jump`:维护 `farthest`,`i > farthest` 即 False,`farthest = max(farthest, i+nums[i])`,到末尾即 True。

---

## §40.7 回溯三兄弟对比(讲透)

| | 全排列 LC46 | 子集 LC78 | 组合总和 LC39 |
|---|---|---|---|
| 收集时机 | 叶子(`len==n`) | 每个节点 | `remain==0` |
| 下一层传 | i+1(每个用一次) | i+1(每个选一次) | **i**(可重复) |
| 去重方式 | used 数组 | start 下标 | start 下标 |
| 剪枝 | 无 | 无 | 排序 + break |
| 答案规模 | n! | 2ⁿ | 指数(取决于 target) |

> 一张表记三题。回溯骨架是同一个:`for + append + dfs + pop`,区别只在「何时收」「传 i 还是 i+1」「怎么剪枝」。

---

## §40.8 回溯 vs 贪心 vs DP(讲透,选型指南)

刷到一道「最优化 / 枚举」题,先分方向:

| 题目要求 | 选型 | 典型 |
|---|---|---|
| 要**所有方案**(列举) | **回溯** | 全排列、子集、组合、N 皇后 |
| 要**一个最优解**,且能证明局部最优=全局最优 | **贪心** | 股票、跳跃、区间调度 |
| 要**一个最优解**,但局部最优≠全局最优,有重叠子问题 | **DP** | Ch39 爬楼梯、零钱兑换、LIS |

> 股票 LC121 和跳跃 LC55 都能用 DP/暴力解,但贪心把它们压到 O(n)/O(1)。能用贪心别用 DP——更简洁。但贪心需要「证明」局部最优=全局最优,证明不了就只能 DP。

---

## §40.9 Java 老手常踩的坑 ⚠️(本章汇总)

1. **回溯忘 copy**:`res.append(path)` 直接收引用,后面 pop 全没。永远 `path.copy()` / `path[:]`。
2. **撤销不配对**:`append`/`pop`、`used=True`/`used=False` 必须成对,漏一个 = 答案乱。
3. **子集传 i、组合传 i 搞反**:子集每个选一次 → `dfs(i+1)`;组合总和可重复 → `dfs(i)`。**死记这张表**。
4. **组合不排序就剪枝**:不排序时 `cand > remain` 只能 continue 不能 break。先 sorted。
5. **贪心初值用 0**:股票 `min_price=0` 会把所有正价当「不便宜」;用 `float('inf')`。
6. **跳跃判断顺序错**:先 `if i > farthest` 再更新 farthest,反了就漏判。
7. **把「要所有方案」当「要最优」做**:全排列用贪心?不存在;股票用回溯?太慢。先想清楚要什么。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `permute` | 回溯 + used 标记 | 🟡 |
| `subsets` | 回溯 选/不选 + start 去重 | 🟡 |
| `combination_sum` | 回溯 + 排序剪枝 + 可重复选 | 🟡 |
| `max_profit` | 贪心(维护历史最低) | 🟢 |
| `can_jump` | 贪心(维护最远可达) | 🟢 |

```bash
uv run pytest 06_leetcode/ch40/test_ch40_assignment.py -v
```

全绿 = 掌握 Ch40 = **M6 毕业 = 40 章全栈学习项目通关** 🎉。

---

## ✅ 自测

- [ ] 能默写回溯三行骨架:`for + append + dfs + pop`
- [ ] 能说清「子集为什么进函数就收,全排列等叶子才收」
- [ ] 能说清「组合总和为什么传 i 不传 i+1」+「为什么要排序才能剪枝」
- [ ] 能用 O(n)/O(1) 写出股票和跳跃两道贪心
- [ ] 能判断一道新题该用回溯 / 贪心 / DP(§40.8 选型表)
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么子集每个节点都收集,全排列只收集叶子?」— 重读 §40.3 vs §40.2
2. 「`dfs(i)` 和 `dfs(i+1)` 的区别,什么时候用哪个?」— 重读 §40.7 对比表
3. 「跳跃游戏为什么能用贪心?『局部最优=全局最优』在哪?」— 重读 §40.6(可达区间连续)
4. 「回溯 / 贪心 / DP 各适合什么题?给一道新题你怎么选?」— 重读 §40.8

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ M6 毕业 + 项目收官

40 章走完:从 Ch01 的 `if __name__=='__main__'` 到 Ch40 的回溯贪心,你已经能用 Python 写语言核心(M1)、玩转标准库(M2)、搭 FastAPI 服务(M3)、写运维脚本(M4)、调 LLM/搭 RAG/Agent(M5)、Pythonic 刷 LeetCode(M6)。下一步:把这些拼成一个**属于自己的项目**(比如一个带 AI 的 Web 服务),在实战里把六块肌肉连起来。🎓
