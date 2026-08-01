# Ch35 · 双指针 / 滑动窗口

> **预计**:1 天 ｜ **前置**:Ch34(Pythonic 刷题技巧)、Ch02(数据结构)｜ **M6 高频套路**
> **目标**:吃透数组/字符串题的两大杀手锏——**对撞双指针**(两端往中间逼)和**滑动窗口**(两指针夹一段区间)。配合 Python 的切片 + `set` / `Counter`,代码比 Java 短一半。
> 这是 LeetCode 中**出场频率最高**的两类手法:LC3 / LC11 / LC15 / LC76 / LC42(接雨水)/ LC209 / LC424 全是它的变体。

> 📐 **本教程的契约**:§35.2 讲对撞双指针原型,§35.3–§35.6 分别对应 4 道作业题。
> **纯 stdlib**(`set` / `collections.Counter`),不装任何外部库。

---

## 🗺️ 本章地图

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `two_sum_sorted` | §35.2 | 对撞双指针原型(辅助理解,非 LeetCode 题) |
| `max_area` | §35.3 | LC11 盛最多水的容器(对撞 + 贪心移动短板) |
| `length_of_longest_substring` | §35.4 | LC3 无重复字符最长子串(滑动窗口 + set) |
| `three_sum` | §35.5 | LC15 三数之和(排序 + 对撞 + 去重) |
| `min_window` | §35.6 | LC76 最小覆盖子串 Hard(滑动窗口 + Counter) |

---

## ⏱️ 学习路径:费曼五步(约 90 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜(先合上教程想 30 秒)

1. 「双指针」不是 C 的指针!是两个**下标**变量。为什么要用两个下标?用一层 for 不行吗?
2. 一个**有序**数组找两数之和等于 target,能不能不嵌套 for(O(n²))?两端往中间走行不行?
3. 盛水容器两块板,你只能拿掉一块——拿掉**高的**还是**矮的**?为什么?(短板决定水位)
4. 找「不含重复字符的最长子串」,左右两指针怎么配合?右指针扩张探索、左指针什么时候收缩?
5. 「最小覆盖子串」里 `need` 计数器什么时候是正、什么时候是负、什么时候是零?为什么还要一个 `missing` 总数?

> 想不出没关系——带着这些问题往下读,每读完一节回来对答案。

---

## §35.1 双指针到底在指什么 🟢

「双指针」= 两个下标变量在数组/字符串上**按某种规则移动**,把朴素 O(n²) 的双重 for 降成 O(n) 或 O(n²)→O(n²) 但常数更小。常见三种形态:

| 形态 | 两指针怎么走 | 典型题 |
|------|--------------|--------|
| **对撞**(相向) | 一头一尾,往中间逼 | LC11 盛水、LC15 三数之和、LC167 两数之和Ⅱ |
| **快慢**(同向) | 都从左出发,快指针跑前面探路、慢指针跟上 | LC27 移除元素、LC283 移动零 |
| **滑动窗口**(同向) | 两指针夹一段「窗口」[left,right],右扩左缩 | LC3 无重复子串、LC76 最小覆盖、LC209 长度最小子数组 |

> 🟢 **Java 老手秒懂**:Java 里就是 `int lo = 0, hi = n - 1; while (lo < hi) {...}`。逻辑完全一样,Python 只是语法更短。

> **为什么双指针能省时间**:朴素做法「枚举所有 (i,j) 对」是 O(n²);双指针**每次只动一个指针**,且每个元素至多被两端各访问一次 → **均摊 O(n)**。精髓在于「不回头」:一旦指针移动,之前的状态不再考虑(因为已经确定更优解不在这)。

---

## §35.2 对撞双指针原型:two_sum_sorted(讲透)🟡

> 这不是 LeetCode 题,是对撞双指针的**最小原型**。理解它,后面 LC11/LC15 一通百通。

**问题**:在一个**已排序**数组里,找两个数之和等于 target。

### 暴力 O(n²)(别这么写)

```python
for i in range(n):
    for j in range(i+1, n):
        if nums[i] + nums[j] == target:
            return [nums[i], nums[j]]
```

嵌套 for,数组一大就爆。

### 对撞双指针 O(n)

```python
def two_sum_sorted(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = nums[lo] + nums[hi]
        if s == target:
            return [nums[lo], nums[hi]]
        if s < target:   # 和太小 → 需要更大的数 → 左边进(因为右边已经最大)
            lo += 1
        else:            # 和太大 → 需要更小的数 → 右边退
            hi -= 1
    return None
```

**为什么对**:数组有序。`lo` 在小端、`hi` 在大端:
- 和太小,`hi` 已经是当前最大可能了,只能让 `lo` 往大走;
- 和太大,`lo` 已经是当前最小可能了,只能让 `hi` 往小走;
- 两指针每步逼进一步,**最多 n 步**收敛 → O(n)。

> 🟡 **Java 对比**:Java 一模一样 `int lo=0, hi=nums.length-1;`。差异只在 Python 用 `while lo < hi` 不用担心越界(`hi` 不会小于 0,因为循环条件守住了)。

> ⚠️ **前提是数组有序**!无序数组用这招会漏解——必须先 `sort()`(LC1 两数之和因为要返回原下标,只能用 HashMap)。这也是为什么 LC15 三数之和要先排序。

> ✅ **做 `two_sum_sorted`**:`lo,hi = 0, n-1`;小了 `lo+=1`、大了 `hi-=1`、等了返回。O(n)。

---

## §35.3 LC11 盛最多水的容器:max_area 🟡

**题面**:n 条竖线,第 i 条高度 `height[i]`,两线 + x 轴围成容器。求最大盛水量。盛水 = `宽 × min(两线高度)`(短板决定水位,水会从短板溢出)。

```
       8                8
       █▔▔▔▔▔▔▔▔▔▔▔▔▔▔█ ← 真实水位被短板(左边 1)卡住
   1   █     6         █   7
   █▔▔▔█▔▔▔▔▔▔▔▔▔▔▔▔▔▔█▔▔▔█
```

### 暴力 O(n²)

枚举所有 (i,j) 算面积取最大。n=10⁵ 直接超时。

### 对撞双指针 O(n)

```python
def max_area(height):
    lo, hi = 0, len(height) - 1
    area = 0
    while lo < hi:
        area = max(area, (hi - lo) * min(height[lo], height[hi]))
        if height[lo] < height[hi]:
            lo += 1          # 移动【短】的一边
        else:
            hi -= 1
    return area
```

**核心贪心:每次移动较短的一边。** 为什么?

面积 `= 宽 × min(h_lo, h_hi)`。每次循环**宽一定变小**(两指针在靠近)。要面积变大,**min(高度) 必须变大**才能扳回宽的损失。

- 若移动**长边**:宽变小,但 `min` 被短边卡死不变(短边还在),面积只会更小 → **毫无希望**。
- 若移动**短边**:宽变小,但 `min` 可能变大(新的一边可能更高)→ **有希望变大**。

所以只能移动短边。所有「移动长边」的情况都被证明不会更优,直接剪掉 → 每步排除一整批方案 → O(n)。

> 🟡 **Java 对比**:`Math.max` / `Math.min` 在 Python 是内置 `max` / `min`,且能一次比较多个值 `min(a, b, c)`。逻辑同构。

### 复杂度
- 时间 O(n):两指针合计最多走 n 步。
- 空间 O(1):只用几个变量。

> ⚠️ **常见坑**:
> 1. 用 `min` 不是 `max`——水位被**矮**板决定。
> 2. 别写成嵌套 for——那就是暴力。
> 3. 移动条件是 `height[lo] < height[hi]`(比高度)不是 `lo < hi`(那是循环条件)。

> ✅ **做 `max_area`**:对撞;每步 `area = max(area, 宽×min(h))`;移动**短**的一边。O(n) / O(1)。

---

## §35.4 LC3 无重复字符的最长子串:length_of_longest_substring 🔴

**题面**:给定字符串 `s`,找不含重复字符的**最长子串**的长度。
例:`"abcabcbb"` → 3(`"abc"`);`"pwwkew"` → 3(`"wke"`)。

> 「子串」= 连续;「子序列」= 可不连续(Ch39 动态规划那章)。这题要的是连续的。

### 暴力 O(n³) / O(n²)

枚举所有子串,每个检查是否含重复。超时。

### 滑动窗口 + set O(n)

```python
def length_of_longest_substring(s):
    chars = set()    # 窗口内已出现的字符
    left = 0         # 窗口左端(收缩用)
    best = 0
    for right, ch in enumerate(s):   # right = 窗口右端(扩张)
        while ch in chars:           # 右端字符与窗口内重复 → 左端收缩
            chars.remove(s[left])
            left += 1
        chars.add(ch)                # 现在窗口无重复,放入右端
        best = max(best, right - left + 1)
    return best
```

**窗口语义**:`s[left .. right]` 始终是一个**无重复字符**的子串。
- **右指针扩张**(`for right`):每步把 `s[right]` 想纳入窗口。
- **左指针收缩**(`while ch in chars`):如果 `s[right]` 已经在窗口里,说明重复了——左端不断吐出字符,直到把那个重复字符踢掉,窗口重新合法。
- **更新答案**:窗口合法后,`right - left + 1` 就是当前无重复子串长度,取 max。

**为什么是 O(n) 不是 O(n²)**?虽然有个 `while` 嵌在 `for` 里,看起来像 O(n²),但:
- `right` 只前进 n 次;
- `left` 在整个循环里**总共**也只前进不超过 n 次(每个字符至多被 `add` 和 `remove` 各一次)。

所以总操作数 ≤ 2n → **O(n)**。这是滑动窗口「均摊 O(1)」的精髓——别看嵌套,看每个元素的**总访问次数**。

> 🔴 **Python 特有**:
> - `enumerate(s)` 同时拿下标和字符,Java 要 `for (int i=0; i<n; i++) char ch = s.charAt(i);`。
> - `set` 的 `add` / `remove` / `in` 都是 O(1)(底层 hash 表),Java 用 `HashSet<Character>`。
> - `chars.remove(s[left])` 删的是**值**不是索引——和 Java `set.remove(obj)` 一致,但别和 `list.remove` 搞混(list 的 remove 是 O(n))。

### 复杂度
- 时间 O(n):见上,均摊。
- 空间 O(min(n, 字母表大小)):`set` 最坏装满整个字母表(ASCII 128 / Unicode 更大,但被 n 卡住)。

> ⚠️ **常见坑**:
> 1. 忘了 `while` 用 `if`:用 `if` 遇到 `"pwwkew"` 会在第二个 `w` 处只删一个字符,残留重复。
> 2. 把 `set` 换成 `list`:查找变 O(n),整体 O(n²)。
> 3. 返回的是**长度**不是子串本身。

> ✅ **做 `length_of_longest_substring`**:窗口 `set`;右扩 `for right`;冲突 `while ch in chars: remove s[left]; left+=1`;放 `add(ch)`;`best = max(best, 宽)`。O(n)。

---

## §35.5 LC15 三数之和:three_sum 🟡

**题面**:找所有**不重复**的三元组 `[a,b,c]` 使 `a+b+c == 0`。
例:`[-1,0,1,2,-1,-4]` → `[[-1,-1,2],[-1,0,1]]`。

### 难点 1:不能直接三重 for(O(n³))。

### 难点 2:去重——`[-1,0,1]` 可能出现很多次,结果里只能有一个。

### 解法:排序 + 固定一个 + 对撞双指针

```python
def three_sum(nums):
    nums.sort()
    res = []
    n = len(nums)
    for i in range(n - 2):
        # 去重 i:和上一个首数相同就跳过
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s == 0:
                res.append([nums[i], nums[lo], nums[hi]])
                # 去重 lo / hi:越过相邻相同值
                while lo < hi and nums[lo] == nums[lo + 1]:
                    lo += 1
                while lo < hi and nums[hi] == nums[hi - 1]:
                    hi -= 1
                lo += 1
                hi -= 1
            elif s < 0:
                lo += 1
            else:
                hi -= 1
    return res
```

**思路拆解**:
1. **排序** O(n log n):排序后就能用对撞双指针,且三元组天然升序(便于去重)。
2. **固定第一个数 `nums[i]`**:剩下的两数之和要等于 `-nums[i]` → 退化成 §35.2 的 `two_sum_sorted`。
3. **对撞找后两个数**:`lo = i+1`, `hi = n-1`,和为负 `lo++`、和为正 `hi--`、等于 0 收录。
4. **去重(两处)**:
   - **固定 i 的去重**:`if i>0 and nums[i]==nums[i-1]: continue`——同首数的三元组上一轮 i 已经找全,这轮跳过。
   - **找到一组后的去重**:lo/hi 各自越过相邻重复值,否则下一轮又会找到一模一样的三元组。

**为什么排序能简化去重**?排序后相同值相邻,一次 `while` 就能跳过一串重复。不排序的话得用 `set` 去重(把三元组 freeze 成 tuple 塞 set),慢且丑。

> 🟡 **Java 对比**:Java 同款逻辑,只是 `List<List<Integer>>` 比 Python `list[list[int]]` 啰嗦。Python 的 `res.append([a,b,c])` 直接加 list,Java 要 `Arrays.asList(a,b,c)` 或 `new ArrayList<>(){...}`。

### 复杂度
- 时间 O(n²):外层 i 走 n 次,内层对撞 O(n),合计 O(n²)。排序 O(n log n) 被吸收。
- 空间 O(log n):排序的栈空间(Python `sort` 是 Timsort)。结果数组不算。

> ⚠️ **常见坑**:
> 1. **只去重 i 不去重 lo/hi**:会塞进 `[[-1,0,1],[-1,0,1]]` 重复。
> 2. **去重 i 写成 `nums[i]==nums[i+1]`**:这会漏解——比如 `[-2,0,0,2,2]`,i=0 时 `nums[0]==nums[1]`?不,正确写法是和 `i-1` 比(跳过本轮重复,不是预判下轮)。
> 3. **忘记排序**:对撞双指针依赖有序,不排序直接错。
> 4. **边界 `range(n-2)`**:不足 3 个数直接不进循环,返回 `[]`。

> ✅ **做 `three_sum`**:`sort`;固定 i(去重 `nums[i]==nums[i-1]` 跳过);对撞 lo/hi;命中后两边都去重再 `lo++ hi--`。O(n²)。

---

## §35.6 LC76 最小覆盖子串(Hard):min_window 🔴

**题面**:在 `s` 中找涵盖 `t` 所有字符(含重复)的**最短**子串;没有返回 `""`。
例:`min_window("ADOBECODEBANC", "ABC")` → `"BANC"`。

> 这是滑动窗口的**巅峰题**,LeetCode 标 Hard。但拆开看,就是 LC3 的升级版——LC3 窗口要「无重复」,这题窗口要「涵盖 t」。

### 暴力 O(n² × 检查)

枚举所有子串,每个检查是否涵盖 t,取最短。n=10⁵ 必爆。

### 滑动窗口 + Counter O(|s|+|t|)

```python
from collections import Counter

def min_window(s, t):
    if not t or not s:
        return ""
    need = Counter(t)      # 各字符还需多少个(>0 缺, <=0 不缺/超了)
    missing = len(t)       # 总缺口(= sum(need.values()) 的快表)
    left = 0
    start, length = 0, len(s) + 1   # 最优窗口记录,length 初值设成「找不到」的哨兵
    for right, ch in enumerate(s):
        # 1) 右扩:把 s[right] 纳入窗口
        if need[ch] > 0:           # 这个字符是 t 需要的 → 补一个缺口
            missing -= 1
        need[ch] -= 1              # 不管需不需要都 -1(负数=窗口里这种字符超了)
        # 2) 已满足(t 全覆盖)→ 左缩到「刚不满足」为止,沿途更新最短
        while missing == 0:
            if right - left + 1 < length:
                start, length = left, right - left + 1
            need[s[left]] += 1     # 左端字符要出窗口
            if need[s[left]] > 0:  # 出窗口后这种字符变成「缺」了 → 缺口 +1
                missing += 1
            left += 1
    return s[start:start+length] if length <= len(s) else ""
```

**两个 Counter 技巧(Java 老手重点理解)**:

`need[c]` 的值有三种语义:
- **> 0**:t 还需要 c 这个字符 `need[c]` 个(缺口);
- **== 0**:刚好(窗口里 c 的数量 = t 需要的);
- **< 0**:窗口里 c **超了**(多出来的 c 是「冗余」,左缩时可以放心丢)。

**`missing` 是什么**?它是「还差的总字符数」= `sum(need[c] for c in need if need[c]>0)`。但每次 while 都算 sum 太慢,所以用一个整数计数器**增量维护**:
- 右扩时,若 `need[ch] > 0`(这个字符还缺),`missing -= 1`;
- 左缩时,若出窗口后 `need[s[left]] > 0`(变成缺了),`missing += 1`。

`missing == 0` 就代表窗口已涵盖 t。**为什么 `need[ch] > 0` 才减 missing**?因为只有「真正补上缺口」才算数;如果 `need[ch] <= 0`(窗口里 c 已经够了甚至超了),再来一个 c 不减少缺口,missing 不动。

**窗口怎么收缩**:`missing == 0` 时,窗口是「合法的」(涵盖 t)。但可能太长,试着把左端丢出去看还能不能合法。丢 `s[left]`:
- `need[s[left]] += 1`(它要离开窗口,需求 +1);
- 如果 `need[s[left]]` 从 0 变 1 → 刚好变成「缺」了 → `missing += 1`(窗口不再合法);
- 如果还是 ≤ 0 → 这种字符本来就有冗余,丢了也不影响合法性,继续缩。
- 收缩途中,每次窗口合法都更新一次最短。

**`length = len(s)+1` 哨兵**:如果整个循环没找到合法窗口,`length` 还是 `len(s)+1 > len(s)`,最后 `if length <= len(s)` 判否,返回 `""`。

> 🔴 **Python 特有**:
> - `Counter(t)` 一行统计 t 各字符频次,Java 要 `Map<Character,Integer> need = new HashMap<>(); for(char c:t.toCharArray()) need.merge(c,1,Integer::sum);`。
> - `need[ch]` 访问不存在的 key **返回 0 而不报错**(Counter 特性,普通 dict 会 KeyError)——这非常关键,代码里 `need[ch]` 直接读 s 的任意字符都安全。**Java 的 `HashMap.get` 返回 null 会 NPE**,必须用 `getOrDefault(c, 0)`。
> - 切片 `s[start:start+length]` 一行取子串,Java 要 `s.substring(start, start+length)`。

### 复杂度
- 时间 O(|s| + |t|):right 走 |s| 次,left 总共也走不超过 |s| 次;建 Counter 是 |t|。
- 空间 O(|t|):Counter 存 t 的不同字符数。

> ⚠️ **常见坑**:
> 1. **用普通 dict 不用 Counter**:`need[ch]` 访问不存在 key 直接 KeyError。Counter 自动补 0。
> 2. **`missing` 维护错**:只在 `need[ch] > 0` 时减——否则缺口算多。
> 3. **左缩条件写 `while` 不是 `if`**:要一直缩到「刚不满足」,if 只缩一次会漏最短。
> 4. **哨兵 length 初值设错**:设成 `len(s)` 会误判——找不到时返回了整个 s。要 `len(s)+1`,最后用 `if length <= len(s)` 区分。
> 5. **返回 `s[left:right]`**:left/right 是循环结束后的值,不是最优窗口。要单独记 `start/length`。

> ✅ **做 `min_window`**:`need=Counter(t)`,`missing=len(t)`;右扩(`need[ch]>0` 才减 missing,然后 `need[ch]-=1`);`missing==0` 时左缩(出窗口 `need+=1`,变正则 `missing+=1`),沿途记最短。哨兵 `length=len(s)+1`。O(|s|+|t|)。

---

## §35.7 滑动窗口的「通用模板」(讲透,通用套路)

LC3 和 LC76 都是滑动窗口,可以抽象成**同一个模板**:

```python
def sliding_window(s):
    window = ...           # 窗口状态:set / Counter / 变量
    left = 0
    best = ...
    for right in range(len(s)):
        c = s[right]
        # 1) 右扩:把 c 纳入窗口
        window.add(c)  # 或 window[c] += 1
        # 2) 窗口不合法时,左缩到合法
        while 窗口不合法(c):
            d = s[left]
            window.remove(d)  # 或 window[d] -= 1
            left += 1
        # 3) 更新答案(此时窗口合法)
        best = 更新(best, right - left + 1)
    return best
```

三步:**右扩 → 不合法就左缩 → 更新**。LC3 的「合法」是「无重复」,LC76 的「合法」是「涵盖 t」。记住这个模板,LC209 / LC424 / LC1004 都是换「合法」的定义。

> 🧠 **判断该不该用滑动窗口的口诀**:**「求连续子数组/子串的极值,且窗口有单调性(右扩使某条件变差,左缩使某条件变好)」** → 用滑动窗口。

---

## §35.8 Java 老手常踩的坑 ⚠️

1. **「双指针」当 C 的指针**:Python/Java 里都是**下标整数**,不是内存指针。别被名字吓到。
2. **对撞双指针用在无序数组上**:LC15 必须先 `sort()`;不排序对撞毫无意义。
3. **滑动窗口用 `if` 收缩而不是 `while`**:`if` 只删一个字符,残留重复/缺口。必须 `while` 缩到合法。
4. **用 `list` 当窗口状态**:`in` / `remove` 是 O(n),整体退化 O(n²)。窗口状态要用 `set` / `Counter`(hash,O(1))。
5. **去重漏掉一处**:LC15 有**两处**去重(固定 i 的 + 命中后 lo/hi 的),漏一处就有重复三元组。
6. **min_window 的 `missing` 维护**:只在 `need[ch] > 0` 时减 missing——负数代表冗余,不减缺口。
7. **返回值用循环结束的 left/right**:滑动窗口答案要单独用变量记录最优(如 `start/length` / `best`),循环结束的指针位置不是答案。
8. **Counter vs dict**:Counter 访问不存在的 key 返回 0(安全);dict 会 KeyError。窗口题用 Counter 省心。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `two_sum_sorted` | 对撞双指针原型 | 🟡 |
| `max_area` | LC11 盛水容器(对撞 + 移动短板) | 🟡 |
| `length_of_longest_substring` | LC3 无重复子串(滑动窗口 + set) | 🔴 |
| `three_sum` | LC15 三数之和(排序 + 对撞 + 去重) | 🟡 |
| `min_window` | LC76 最小覆盖子串 Hard(滑动窗口 + Counter) | 🔴 |

```bash
uv run pytest 06_leetcode/ch35/test_ch35_assignment.py -v
```

全绿 = 掌握 Ch35 的双指针 / 滑动窗口套路。

---

## ✅ 自测

- [ ] 能说清「对撞 / 快慢 / 滑动窗口」三种双指针形态各适合什么题
- [ ] 能解释 LC11 为什么「移动短边」(贪心正确性证明)
- [ ] 能徒手写 LC3 的滑动窗口,并解释为什么是 O(n) 不是 O(n²)
- [ ] 能说清 LC15 的**两处**去重各干嘛
- [ ] 能解释 LC76 的 `need[c]` 正/零/负三种语义,以及 `missing` 为什么不能用 sum 替代
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「LC11 盛水容器为什么移动短边?移动长边会怎样?」— 重读 §35.3
2. 「LC3 的滑动窗口嵌了 while,为什么是 O(n)?」— 重读 §35.4
3. 「LC15 不排序能做吗?为什么要排序?两处去重各自的作用?」— 重读 §35.5
4. 「LC76 的 `need[c]` 为负数代表什么?`missing` 为什么不直接 sum?」— 重读 §35.6
5. 「什么样的问题该用滑动窗口?」— 重读 §35.7 口诀

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch36 哈希表 / 前缀和

双指针/滑动窗口玩的是「下标」。下一章换武器——**哈希表**(`dict` / `Counter`)用 O(1) 查找把两数之和、字母异位词分组、和为 K 的子数组一网打尽;再加**前缀和**把子数组和问题降到 O(n)。从「指针夹逼」到「哈希映射」。
