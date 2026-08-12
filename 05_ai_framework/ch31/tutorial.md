# Ch31 · RAG 实战:向量检索

> **预计**:1 天 ｜ **前置**:Ch28(LLM SDK)、Ch30(LCEL)｜ **M5 重点章**
> **目标**:掌握 RAG(Retrieval-Augmented Generation)——让 LLM 基于**你的文档**回答,而不是它训练时的旧知识。这是企业落地 LLM 的头号场景(客服、知识库、文档问答)。

> 📐 **本教程的契约**:§31.2–§31.9 每节对应一道作业题,卡住按「作业 ↔ 教程对应表」回查。**全程纯 Python + 确定性假向量**,不装 torch/sentence-transformers、不调真实 LLM;真实用法(Chroma + 真 embedding + 真模型)见 §31.10。
> 🎯 **主线场景**:你是「极客商城」AI 组工程师。Ch30 的客服机器人上线后被吐槽「一问三不知」——它没看过商品手册和售后政策,只能靠模型脑补,答错还理直气壮。老板要求:① 机器人必须**基于《商品知识库》回答**;② 答案**能溯源**到具体资料段落。你决定上 RAG。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 说清 RAG 是什么、为什么知识更新场景默认选 RAG 而不是微调
- 用滑动窗口 + overlap 给长文档切片,并知道 `max(1, ...)` 防什么坑
- 手算余弦相似度,说清为什么用余弦不用欧氏距离
- 理解 embedding = 「文本 → 向量」,以及 hash_embed 假向量的边界
- 实现 top-k 检索(排序 + 元组陷阱),拼带编号的上下文(可溯源)
- 把「切→嵌→检→拼→答」组装成完整 RAG 管道,LLM 用依赖注入便于测试

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `chunk_text` | §31.2 | 文档切片:滑动窗口 + overlap |
| `cosine_similarity` | §31.3 | 余弦相似度数学 + 零向量防除零 |
| `hash_embed` | §31.4 | embedding 原理(确定性假向量) |
| `retrieve_top_k` | §31.5 | top-k 检索:按相似度降序 |
| `build_context` | §31.6 | 拼带编号的上下文(可溯源) |
| `build_rag_prompt` | §31.7 | RAG prompt 模板 + 防幻觉约束 |
| `search_knowledge_base` | §31.8 | **综合①**:切→嵌→检 的检索管道 |
| `rag_answer` | §31.9 | **综合②**:全管道 + 注入 LLM + 返回来源 |

---

## ⏱️ 学习路径:费曼五步(约 70 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个问题,凭 Java 经验猜 | 本页 ① |
| ② 先动手 | 打开 `ch31_assignment.py`,**先试着写**(别通读教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「为什么用余弦不用欧氏距离」 | 本页 🎓 |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → 哪题卡了回对应 § 查 → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

1. LLM 只记得训练截止时的公开知识,你的《售后政策》它根本没读过。除了重新训练(微调),还有什么便宜办法让它「知道」?
2. 一份 100 页的商品手册,能整个塞进 prompt 吗?(提示:上下文窗口长度 + token 按量计费)
3. 「语义搜索」和 SQL `LIKE '%关键词%'` 有什么不同?用户问「电池耐用吗」,手册里写的是「5000mAh 大电池」——LIKE 能搜到吗?
4. 把两段话各变成一个向量,怎么用一个数衡量它们「意思多接近」?为什么用夹角余弦而不用直线距离?
5. 企业客服机器人的答案,为什么必须能点回「这句话来自哪份资料第几段」?

---

## §31.1 RAG 是什么 + 为什么 🟡

LLM 的知识有**截止日期**,且没见过你的私有数据。让它用你的数据,两条路:

| 方式 | 做法 | 成本 | 何时用 |
|------|------|------|--------|
| **微调 fine-tune** | 拿你的数据重训模型权重 | 贵、慢、改数据要重训 | 风格/格式定制 |
| **RAG** ✅ | 检索你的文档,塞进 prompt 让模型「开卷考试」 | 便宜、即时、可溯源 | **知识更新(默认选这个)** |

RAG 管道(开卷考试),**本章作业就是按这个顺序逐站实现**:

```
用户提问 query
  → ① 离线:文档切片(chunk)→ ② 每片向量化(embedding)→ 存入向量库
  → ③ 在线:query 也向量化 → 在库里找最相似的 top-k 片(retrieve)
  → ④ 把这些片拼成「上下文」塞进 prompt(build context/prompt)
  → ⑤ LLM 基于上下文回答(并标注来源)
```

> 🟡 **Java 对比**:像 Elasticsearch 的语义版——但 ES 按关键词/词频(BM25)匹配,RAG 按**语义向量**找。「电池耐用吗」匹配「5000mAh 大电池」,LIKE 做不到,向量做得到。

> **为什么 RAG 是默认**:文档更新只要重建索引(分钟级),不用重训模型(天级 + 贵);还能告诉用户「答案来自《售后政策》第 2 段」——**可溯源**,企业合规刚需。

---

## §31.2 文档切片:`chunk_text` 🟡

文档太长塞不进 prompt(窗口有限 + 贵),也**不利于检索精度**(一整篇里只有一段相关,其余都是噪声)。先切成小块,只检索相关的几块。

**Java 对照最小例**(滑动窗口切片):

```python
def chunk_text(text, size=100, overlap=20):
    if size <= 0:
        return []
    step = max(1, size - overlap)          # 关键!见下面的坑
    return [text[i : i + size] for i in range(0, len(text), step)]

chunk_text("abcdef", size=3, overlap=1)    # ["abc", "cde", "ef"]   step=2
chunk_text("abcdef", size=3, overlap=0)    # ["abc", "def"]         step=3
```

- 按 `size` 字符切,步长 `step = size - overlap`(Ch02 的切片 `text[i:i+size]` + `range` 步长)。
- **overlap 重叠**:相邻块重叠 `overlap` 字符,防止「把一句话从正中间切断」后两块都丢了完整语义。

**真实场景例**:切《售后政策》,overlap 让「保修」相关的句子在相邻两片里都完整出现:

```python
text = "支持7天无理由退货,整机保修2年。"
chunk_text(text, size=8, overlap=2)
# ["支持7天无理由退", "由退货,整机保修", "保修2年。"]
#   注意 "由退" 和 "保修" 在相邻片里重复出现 —— 切缝处不断句
```

❌ **错误写法(overlap ≥ size,range 步长 ≤ 0 直接炸)**:

```python
step = size - overlap                      # size=2, overlap=5 → step=-3
[text[i:i+size] for i in range(0, len(text), step)]   # ValueError: range() arg 3 must not be zero(或倒着走)
```

✅ **正确写法**:`step = max(1, size - overlap)`——overlap 再大也保证每次至少前进 1 格,不死循环不炸。

> ✅ 做 `chunk_text`:`size <= 0` 返回 `[]`;`step = max(1, size - overlap)`;列表推导切片。

---

## §31.3 余弦相似度:`cosine_similarity` 🔴

向量有了,怎么衡量「两片文本多接近」?标准答案:**余弦相似度**——两向量夹角的余弦。

**Java 对照最小例**(数学公式直接翻译成代码):

```python
import math

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))     # 点积 a·b
    na = math.sqrt(sum(x * x for x in a))      # 模长 |a|
    nb = math.sqrt(sum(y * y for y in b))      # 模长 |b|
    return dot / (na * nb) if na and nb else 0.0

cosine_similarity([1, 0], [1, 0])    # 1.0   同向 = 最相似
cosine_similarity([1, 0], [0, 1])    # 0.0   正交 = 无关
cosine_similarity([1, 0], [-1, 0])   # -1.0  反向
cosine_similarity([3, 4], [4, 3])    # 0.96  (点积 24,模长 5×5)
```

- 公式 `cosθ = a·b / (|a||b|)`,值域 **[-1, 1]**。
- **零向量防除零**:零向量没有方向,约定与任何向量相似度为 0(`if na and nb else 0.0`)。
- 🔴 `sum(x*y for x, y in zip(a, b))` 生成器一行算点积——Java 要 for 循环或 `IntStream.range` 累加。

**为什么用余弦不用欧氏距离**——这是 RAG 的核心直觉:

```python
# "电池耐用" 说一遍:[1, 2];说两遍(文本更长):[2, 4] —— 方向相同,长度不同
cosine_similarity([1, 2], [2, 4])     # 1.0  余弦:同一语义,满分
math.dist([1, 2], [2, 4])             # 2.236 欧氏:距离挺远,误判"不相似"
```

文本向量关心**方向**(语义)不关心**长度**(词数)。两段意思相同但一长一短的话,余弦仍给满分,欧氏却拉开距离。

❌ **错误写法(忘防除零)**:

```python
return dot / (na * nb)               # 传入 [0,0] → ZeroDivisionError
```

✅ **正确写法**:`return dot / (na * nb) if na and nb else 0.0`。

> ✅ 做 `cosine_similarity`:点积 / (模×模),零向量返回 0.0。

---

## §31.4 embedding:`hash_embed` 🟡

**embedding** = 把文本变成向量,让「语义接近」可计算。真实世界用专门模型:

```python
# 真实用法(要装 sentence-transformers,带 torch,约 2GB,本章不装):
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
vec = model.encode("苹果")            # 384 维 float;语义接近的文本,向量也接近
```

**本作业用确定性假向量 `hash_embed` 替代**——用 md5 把文本确定性映射成一个向量,只为离线跑通 RAG 全流程(测试可复现、不花钱、CI 能跑):

```python
import hashlib

def hash_embed(text, dim=16):
    vec = []
    for i in range(dim):
        b = hashlib.md5(f"{text}:{i}".encode()).digest()[0]   # 取哈希第 i 种子的首字节 0~255
        vec.append((b - 127.5) / 127.5)                        # 映射到 [-1.0, 1.0]
    return vec

hash_embed("苹果") == hash_embed("苹果")    # True  确定性:相同文本 → 相同向量
hash_embed("苹果") != hash_embed("香蕉")    # True  不同文本 → 不同向量
len(hash_embed("x", dim=8))                 # 8     维度可控
```

- `f"{text}:{i}"` 给每一维换不同的哈希输入,保证各维取值独立。
- `(b - 127.5) / 127.5`:字节 0 → -1.0,255 → +1.0,正好铺满 [-1, 1]。

❌ **错误认知(把 hash_embed 当真语义向量)**:

```python
# 「电池耐用吗」和「5000mAh 大电池」语义极近,但 hash_embed 给出的相似度 ≈ 随机!
# md5 是伪随机映射,语义接近 ≠ 向量接近。用它做真实检索,结果和瞎猜一样。
```

✅ **正确认知**:hash_embed 只保证「**相同文本 → 相同向量**」(确定性),不表达语义。它的用途是让 RAG 管道**离线可测**;上线时换成真 embedding 模型(§31.10),管道其余代码一行不动。

> ✅ 做 `hash_embed`:循环 `range(dim)`,每维 `md5(f"{text}:{i}")` 取首字节映射到 [-1, 1]。

---

## §31.5 top-k 检索:`retrieve_top_k` 🟢

向量库 = `[(文本, 向量), ...]`。检索 = 给每片算与 query 的相似度 → 降序 → 取前 k 片,**连分数一起返回**(调试、阈值过滤、展示「相关度」都要用):

**Java 对照最小例**:

```python
def retrieve_top_k(query_vec, doc_vecs, k=3):
    scored = [(t, cosine_similarity(query_vec, v)) for t, v in doc_vecs]
    scored.sort(key=lambda x: x[1], reverse=True)     # 按分数降序
    return scored[:k]                                  # [(文本, 分数), ...]

docs = [("苹果", [1, 0]), ("香蕉", [0, 1]), ("梨", [1, 1])]
retrieve_top_k([1, 0], docs, k=2)
# [("苹果", 1.0), ("梨", 0.7071...)]   苹果1.0 > 梨1/√2≈0.707 > 香蕉0.0
```

> 🟢 **Java 对比**:`list.stream().sorted(comparingDouble(score).reversed()).limit(k)`。Python 的 `list.sort` 是**稳定排序**——同分时保持原先后顺序(Java `Collections.sort` 同样稳定,`Arrays.sort` 对基本类型不稳定)。

❌ **错误写法(元组排序陷阱)**:

```python
scored = [("苹果", 1.0), ("梨", 0.707)]
scored.sort(reverse=True)            # ❌ 不带 key:按第 0 个元素(文本!)字典序排,不是按分数
```

✅ **正确写法**:`scored.sort(key=lambda x: x[1], reverse=True)`——元组默认按第 0 元素比,要按分数必须显式给 `key`。

**真实场景例**:知识库三篇文档(手机手册/耳机手册/售后政策)各成片,query 是「退货政策」的向量,top-2 命中的应该是售后政策那片,且分数排第一。

> ✅ 做 `retrieve_top_k`:`[(t, sim) for t, v in doc_vecs]` → `sort(key=..., reverse=True)` → 切片 `[:k]`。空库返回 `[]`,k 超过库存量就全返回。

---

## §31.6 拼上下文:`build_context` 🟢

检索到 top-k 片段后,拼成一段「参考资料」塞进 prompt。**给每片编号**,LLM 回答时就能引用「据[资料2]…」——这就是溯源的载体:

**Java 对照最小例**:

```python
def build_context(chunks, sep="\n\n"):
    return sep.join(f"[资料{i}] {c}" for i, c in enumerate(chunks, 1))

build_context(["片段A", "片段B"])     # "[资料1] 片段A\n\n[资料2] 片段B"
build_context([])                     # ""
```

- 🟡 `enumerate(chunks, 1)`:从 1 开始计数(Java 得手写 `for (int i = 0; ...)`);`str.join` 接受生成器,不必先物化成 list。
- 空列表 → `join` 自然返回 `""`,不用特判。

❌ **错误写法(手写循环拼接,结尾多一个分隔符)**:

```python
ctx = ""
for c in chunks:
    ctx += f"[资料] {c}" + "\n\n"     # 结尾多一个 "\n\n";且没编号,LLM 无法引用来源
```

✅ **正确写法**:`sep.join(...)` 只在元素**之间**加分隔符;`f"[资料{i}]"` 带上编号。

**真实场景例**:检索命中「售后政策」和「手机手册」两片,拼出:

```
[资料1] 《售后政策》:7 天无理由退货,15 天换货,整机保修 2 年。

[资料2] 《极客手机 X1 说明书》:5000mAh 电池,支持 65W 快充,IP68 防水。
```

> ✅ 做 `build_context`:`sep.join(f"[资料{i}] {c}" for i, c in enumerate(chunks, 1))`。

---

## §31.7 RAG prompt:`build_rag_prompt` 🟢

上下文塞进一个**带约束的模板**。关键认知:**不显式约束,模型会编**(幻觉)——资料里没有的信息,它也会理直气壮地瞎答。模板里必须写死「资料没有就说不知道」:

```python
RAG_TEMPLATE = (
    "你是极客商城的客服,只基于下面的资料回答用户问题;资料里没有的信息,就说「不知道」。\n\n"
    "{context}\n\n"
    "用户问题:{question}\n"
    "客服回答:"
)

def build_rag_prompt(question, context, template=RAG_TEMPLATE):
    return template.format(context=context, question=question)
```

> 🟢 **Java 对比**:`str.format` 按**名字**填占位符 ≈ `MessageFormat.format` / MyBatis 的 `#{}`;比 Java 的 `String.format("%s")` 按位置填更不易错。模板抽成模块常量 + `template` 参数带默认值——换模板不改调用方。

**真实场景例**:

```python
build_rag_prompt("支持退货吗", "[资料1] 《售后政策》:7 天无理由退货")
# 你是极客商城的客服,只基于下面的资料回答用户问题;资料里没有的信息,就说「不知道」。
#
# [资料1] 《售后政策》:7 天无理由退货
#
# 用户问题:支持退货吗
# 客服回答:
```

❌ **错误写法(prompt 不加约束)**:

```python
prompt = f"回答:{question}\n{context}"   # 模型遇到资料外的问题会自由发挥(幻觉)
```

✅ **正确写法**:模板里写死角色 + 「只基于资料」+「没有就说不知道」。

> ✅ 做 `build_rag_prompt`:一行 `template.format(context=context, question=question)`。

---

## §31.8 综合① 检索管道:`search_knowledge_base` 🟡

把前三站串起来:**切片 → 向量化 → top-k 检索**。输入原始文档列表,输出命中的 `[(片段, 分数)]`:

```python
def search_knowledge_base(query, documents, k=3, dim=16):
    # ① 每篇文档切片,汇成一个片段池(双层 for 推导 = Java flatMap)
    chunks = [c for doc in documents for c in chunk_text(doc)]
    # ② 每片向量化,组成「向量库」(这里用 list,真实用 Chroma/pgvector)
    doc_vecs = [(c, hash_embed(c, dim=dim)) for c in chunks]
    # ③ query 也向量化,检索 top-k
    return retrieve_top_k(hash_embed(query, dim=dim), doc_vecs, k=k)
```

- 🟡 `[c for doc in documents for c in chunk_text(doc)]`:双层 for 推导,**阅读顺序就是书写顺序**(先外层 doc 后内层 chunk)= Java `docs.stream().flatMap(d -> chunk(d).stream())`。
- query 和 chunk 必须**用同一个 embedding 函数、同一个维度**——否则向量不在同一空间,相似度毫无意义。

❌ **错误写法(query 和文档用不同维度/不同 embed)**:

```python
retrieve_top_k(hash_embed(query), doc_vecs)          # doc_vecs 若用 dim=384 建库,这里默认 16
                                                     # zip 对齐到短的算点积 → 分数全错还不报错!
```

✅ **正确写法**:建库和检索都走 `hash_embed(..., dim=dim)`,维度由一个参数统一下发。

> ⚠️ **教学简化,生产别这么干**:这里**每次查询都重建索引**(O(N) 重新 embed 全部文档)。生产是「离线建一次索引存向量库,在线只 embed query」——§31.10 会拆开。本章合并在一个函数里,是为了让你在一个调用里看全管道。

> ✅ 做 `search_knowledge_base`:严格按 切→嵌→检 三步**复用**前面的函数,别重写逻辑。

---

## §31.9 综合② 全管道:`rag_answer` 🔴

收尾综合:**完整 RAG 问答**——检索 → 拼上下文 → 拼 prompt → 调 LLM → 返回答案**和来源**:

```python
def rag_answer(query, documents, llm, k=3, dim=16):
    top = search_knowledge_base(query, documents, k=k, dim=dim)   # §31.8
    sources = [t for t, _ in top]                                 # 命中的片段 = 答案来源
    prompt = build_rag_prompt(query, build_context(sources))      # §31.6 + §31.7
    return llm(prompt), sources                                   # (回答, 来源) 可溯源
```

**`llm` 是个注入的 callable**(`Callable[[str], str]`,收 prompt 返回答案)——依赖注入模式:

> 🟡 **Java 对比**:`llm` 参数 = `Function<String,String>` / 策略接口。测试传 lambda 假模型(离线、免费、确定性),生产传真 client(§31.10)——和 Ch30 的 FakeModel 同一个套路,**可测试性**就这么来的。

**真实场景例**(CLI 问答 + 标注来源):

```python
answer, sources = rag_answer("支持退货吗", KNOWLEDGE_BASE, llm=call_claude)
print(answer)                     # "根据[资料1],支持 7 天无理由退货……"
for i, s in enumerate(sources, 1):
    print(f"  来源[{i}] {s[:30]}…")  # 把出处一起展示给用户,合规可溯源
```

一轮做五件事:检索 → 取片段文本 → 拼上下文 → 拼 prompt → 调 llm 并连同 sources 返回。**考的就是复用**,别自己重写任何一站的逻辑。

> ✅ 做 `rag_answer`:`search_knowledge_base` → `[t for t, _ in top]` → `build_context` → `build_rag_prompt` → `llm(prompt)`;返回 `(answer, sources)`。

---

## §31.10 真实用法示例(讲透,不出题)

把假向量、list 向量库、假 LLM 换成真家伙,**管道结构不变**:

```python
import chromadb
from openai import OpenAI

# ① 离线建索引(只做一次!):Chroma 自带 embedding,或显式用 OpenAI embedding
client = chromadb.PersistentClient(path="./chroma_db")
coll = client.get_or_create_collection("kb")
chunks = [c for doc in KNOWLEDGE_BASE for c in chunk_text(doc)]
coll.add(documents=chunks, ids=[f"chunk-{i}" for i in range(len(chunks))])

# ② 在线检索:只 embed query(Chroma 内部代劳),不再每次重建索引
def rag_answer_real(query):
    res = coll.query(query_texts=[query], n_results=3)
    sources = res["documents"][0]
    prompt = build_rag_prompt(query, build_context(sources))   # 本章函数直接用!
    answer = OpenAI().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content
    return answer, sources
```

- **索引/查询分离**:建库一次,查询千次——§31.8 的教学简化在真实代码里被拆开。
- 换真 embedding 后,「电池耐用吗」就能命中「5000mAh 大电池」了(真语义),hash_embed 做不到。
- API key 走环境变量(Ch28 铁律);`build_context` / `build_rag_prompt` 原样复用。

---

## §31.11 向量库选型 + 进阶(讲透,不出题)

| 向量库 | 场景 |
|--------|------|
| **Chroma** | 本地开发/入门,Python 友好,几行跑起来 |
| **FAISS** | Meta 出的纯检索库,极致性能,自己管存储 |
| **pgvector** | PostgreSQL 扩展,向量和业务数据同库,少一个组件 |
| 托管(Pinecone 等) | 省运维,花钱换省心 |

进阶方向(知道名字即可):**rerank**(先向量粗筛 top-20,再用专门模型精排 top-3)、**混合检索**(关键词 BM25 + 向量,各取所长)、**引用溯源**(记录每片来自哪份文档第几段——本章的 `[资料N]` 编号就是最小版)、**增量更新**(新文档只 embed 新增的片)。

---

## §31.12 Java 老手常踩的坑 ⚠️

1. **整个文档塞 prompt**:超窗口 + 贵 + 检索不精。先切片,只喂相关片段。
2. **用欧氏距离不用余弦**:文本向量关心方向不关心长度——`[1,2]` 和 `[2,4]` 余弦 1.0、欧氏 2.236,选错度量结果全拧。
3. **零向量不防除零**:`dot/(na*nb)` 遇到零向量直接 `ZeroDivisionError`,约定返回 0.0。
4. **切片 overlap ≥ size**:`range` 步长 ≤ 0 直接炸,`step = max(1, size - overlap)`。
5. **元组排序不给 key**:`[(文本, 分数)].sort()` 按文本字典序排!按分数必须 `key=lambda x: x[1]`。
6. **prompt 不加约束**:资料里没有的模型也敢编。写死「只基于资料,没有就说不知道」。
7. **query 和文档 embedding 不一致**:不同模型/不同维度 = 向量不在同一空间,分数全错且不报错。
8. **把 hash_embed 当真语义向量**:md5 是伪随机,语义接近 ≠ 向量接近。它只为离线跑通管道。
9. **不溯源**:企业场景答案必须能点回原文。检索结果带出片段、上下文编号 `[资料N]`。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `chunk_text` | 切片 + overlap | 🟡 |
| `cosine_similarity` | 余弦相似度数学 | 🔴 |
| `hash_embed` | embedding 原理(假向量) | 🟡 |
| `retrieve_top_k` | top-k 检索 + 元组排序 | 🟢 |
| `build_context` | 编号上下文(可溯源) | 🟢 |
| `build_rag_prompt` | 模板 + 防幻觉约束 | 🟢 |
| `search_knowledge_base` | **综合①**:切→嵌→检 | 🟡 |
| `rag_answer` | **综合②**:全管道 + 注入 LLM + 溯源 | 🔴 |

```bash
uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v
```

全绿 = 掌握 Ch31。

---

## ✅ 自测

- [ ] 能说清 RAG 是什么、为什么知识更新默认 RAG 而不是微调
- [ ] 会切片(滑动窗口 + overlap),说清 `max(1, ...)` 防什么
- [ ] 会手算余弦相似度,说清为什么用余弦不用欧氏
- [ ] 知道 hash_embed 只是确定性假向量,真实换 embedding 模型
- [ ] 会写 top-k 检索,不掉元组排序陷阱
- [ ] 知道上下文为什么要编号(溯源)、prompt 为什么要写「不知道」
- [ ] 能把「切→嵌→检→拼→答」组装成 `rag_answer`,llm 走依赖注入
- [ ] 8 个作业全绿

## 🎓 费曼挑战

1. 「RAG 和微调各适合什么?为什么 RAG 是默认?」— 重读 §31.1
2. 「为什么用余弦相似度不用欧氏距离?举个数值例子。」— 重读 §31.3
3. 「hash_embed 和真实 embedding 的区别?为什么不能用 hash_embed 做真实检索?」— 重读 §31.4
4. 「为什么说生产上建索引和检索要分离?本章为什么合在一起?」— 重读 §31.8
5. 「rag_answer 的 llm 参数为什么要注入?」— 重读 §31.9

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch32 Agent 开发

RAG 是「给 LLM 资料让它答」——还是被动的。接下来 Agent:让 LLM **自主决定调哪个工具**(查订单、查库存、算数),ReAct 循环「思考 → 调工具 → 观察 → 再思考」,从「被动答」到「主动干」。
