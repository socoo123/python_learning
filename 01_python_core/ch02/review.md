# Ch02 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 取列表前 3 个、最后 2 个、整体反转,各怎么写? | `a[:3]` / `a[-2:]` / `a[::-1]`(切片:左闭右开,可省略) | ⬜ |
| 2 | `products[0:100]` 列表只有 10 个元素会怎样? | 不报错,自动截到末尾——切片越界安全(Java subList 会抛异常) | ⬜ |
| 3 | `sorted(a)` 和 `a.sort()` 的区别?给别人用的函数里该用哪个? | `sorted` 返回新列表不改原列表;`.sort()` 原地排序返回 `None`。函数里用 `sorted`,不改调用方数据 | ⬜ |
| 4 | 按价格降序排商品 list[dict],一行怎么写? | `sorted(products, key=lambda p: p["price"], reverse=True)` | ⬜ |
| 5 | Python lambda 和 Java lambda 的关键区别? | Python lambda 只能写**单个表达式**,不能多行/有语句;复杂逻辑用 `def` | ⬜ |
| 6 | 函数怎么"返回多个值"?接收方怎么接? | `return x, y`(逗号打包成 tuple);接收方 `a, b = f()` 解包 | ⬜ |
| 7 | `(1)` 和 `(1,)` 分别是什么? | `(1)` 是 int(括号只是优先级);`(1,)` 才是单元素 tuple——**tuple 的灵魂是逗号** | ⬜ |
| 8 | dict 键不存在,`d[k]` 和 `d.get(k)` 分别怎样?什么场景用哪个? | `d[k]` 抛 `KeyError`;`d.get(k)` 返回 None、`d.get(k, 默认)` 返回默认值。契约必有的键用 `d[k]`,可有可无的用 `.get()` | ⬜ |
| 9 | Python dict 从 3.7 起保证什么?相当于 Java 哪个类? | **插入有序** = Java `LinkedHashMap`(不是无序 `HashMap`) | ⬜ |
| 10 | 字典推导式做 name→price 映射,骨架怎么写?同名键谁赢? | `{p["name"]: p["price"] for p in products}`;同名**后出现的覆盖先出现的** | ⬜ |
| 11 | 分组套路:`{类目: [商品...]}` 用普通 dict 怎么写?直接 `groups[k].append(p)` 为何不行? | 普通 dict 首次访问必 `KeyError`;用 `groups.setdefault(k, []).append(p)` 或 `defaultdict(list)` | ⬜ |
| 12 | `defaultdict(float)` 适合什么场景?返回前为什么要 `dict(...)`? | 分组累加聚合(缺键自动 0.0 直接 `+=`);转普通 dict 防止调用方误触发自动造键 | ⬜ |
| 13 | 空集合怎么创建?`{}` 是什么? | 空集合只能 `set()`;`{}` 是空 **dict**(经典坑) | ⬜ |
| 14 | 两个 set 求交集/并集/差集?改不改原集合?对比 Java? | `a & b` / `a \| b` / `a - b`,都返回新集合无副作用;Java `retainAll`/`addAll` 会**改掉原集合** | ⬜ |
| 15 | `min(products, key=lambda p: p["price"])` 返回什么?并列最小返回哪个? | 返回**整个元素**(商品 dict),不是最小值;并列返回**先出现的** | ⬜ |
| 16 | `def f(x=[])` 为什么是 bug?正确写法? | 默认值在函数**定义时只求值一次**,所有调用共享同一个 list。正确:`def f(x=None)` + `if x is None: x = []` | ⬜ |
| 17 | 可选参数 `min_price` 为什么用 `is not None` 判断而不用 `if min_price:`? | `0` 是 falsy——`if min_price:` 会把显式传 `0` 当成没传 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)
- [ ] 能说清「可变默认参数为何是 bug、根源在求值时机、怎么修」?
- [ ] 能说清「sorted 和 .sort() 都能排序,为什么公共函数里用 .sort() 是事故」?
- [ ] 能说清「dict 为何 3.7+ 有序、对应 Java 什么、为什么 HashMap 不是正确答案」?

## 📅 复习日程
- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
