# Ch31 · RAG 实战:向量检索

> **预计**:1 天 ｜ **前置**:Ch28、Ch29、Ch30 ｜ **M5 重点**
> **目标**:掌握 RAG(Retrieval-Augmented Generation)——让 LLM 基于**你的文档**回答,而不是它训练时的旧知识。这是企业落地 LLM 的头号场景(客服、知识库、文档问答)。

> 📐 **本教程的契约**:§31.2–§31.6 对应作业 5 个函数。**纯 Python + 假 embedding**,不用 torch。

---

## 🗺️ 本章地图

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `chunk_text` | §31.2 | 文档切片(滑动窗口 + overlap) |
| `cosine_similarity` | §31.3 | 余弦相似度(向量接近度) |
| `retrieve_top_k` | §31.4 | top-k 检索(按相似度排序) |
| `build_context` | §31.5 | 拼上下文喂 LLM |
| `hash_embed` | §31.6 | embedding 原理(假向量,真实换模型) |

---

## ⏱️ 学习路径:费曼五步(约 70 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. LLM 只记得训练时的知识,你的公司内部文档它根本没见过。怎么让它「知道」这些?
2. 一个 100 页的 PDF,能整个塞进 prompt 吗?(提示:上下文窗口 + token 成本)
3. 「语义搜索」和关键字搜索(SQL LIKE)有什么不同?怎么衡量两段话「意思接近」?
4. 向量的「余弦相似度」为什么能表示语义接近?cosθ=1 代表什么?
5. RAG 为什么比「微调模型」更常用?(便宜、可随时更新文档、可溯源)

---

## §31.1 RAG 是什么 + 为什么 🟡

LLM 的知识有**截止日期**,且没见过你的私有数据。两种办法让它用你的数据:

| 方式 | 做法 | 成本 | 何时用 |
|------|------|------|--------|
| **微调 fine-tune** | 拿你的数据重新训练模型权重 | 贵、慢、改数据要重训 | 风格/格式定制 |
| **RAG** ✅ | 检索你的文档,塞进 prompt 让模型「开卷考试」 | 便宜、即时、可溯源 | **知识更新(默认选这个)** |

RAG 流程(开卷考试):
```
用户提问
  → 把问题变向量(embedding)
  → 在你的文档向量库里找最相似的 top-k 段
  → 把这些段拼成「上下文」塞进 prompt
  → LLM 基于上下文回答(还能标注来源)
```

> 🟡 **Java 对比**:像 Elasticsearch 的语义版——但 ES 按关键字/词频,RAG 按「语义向量」找。RAG = 语义检索 + LLM 总结。

> **为什么 RAG 是默认**:文档更新只要重建索引(几分钟),不用重训模型(几天+贵);还能告诉用户「答案来自第 3 页」(可溯源,企业必备)。

---

## §31.2 文档切片:chunk_text(对应)🟡

文档太长塞不进 prompt(上下文窗口有限 + 贵)。先**切成小块**,只检索相关的几块:

```python
def chunk_text(text, size=100, overlap=20):
    if size <= 0:
        return []
    step = max(1, size - overlap)
    return [text[i : i + size] for i in range(0, len(text), step)]
```

- 按 `size` 字符切,步长 `step = size - overlap`。
- **overlap 重叠**:相邻块重叠 `overlap` 字符,防止「把一句话从中间切断」丢失上下文。
- 切多大是权衡:太大→检索不精(混入无关)、费 token;太小→丢失段落语义。通常 200-1000 token,按句子/段落切更好(这里按字符是简化)。

> ✅ 做 `chunk_text`:`step = max(1, size-overlap)`;`[text[i:i+size] for i in range(0,len,step)]`。

---

## §31.3 余弦相似度:cosine_similarity(对应)🔴

衡量两个向量「多接近」的标准方法——**余弦相似度**:两向量夹角的余弦。

```python
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
```

- `cosθ = a·b / (|a||b|)`——点积除以模长积。
- 值域 **[-1, 1]**:1=同向(最相似)、0=正交(无关)、-1=反向。
- **为什么用余弦不用欧氏距离**:文本向量关心「方向」(语义)不关心「长度」(词数)。两段意思相同但长短不同的话,余弦相似度仍高。
- 零向量防除零(`if na and nb else 0.0`)。

> 🔴 **Python 特有**:`sum(x*y for x,y in zip(a,b))` 生成器一行算点积,Java 要 for 循环或 Stream。数学公式直接翻译成代码。

> ✅ 做 `cosine_similarity`:点积 / (模×模),零向量返回 0.0。

---

## §31.4 top-k 检索:retrieve_top_k(对应)🟢

```python
def retrieve_top_k(query_vec, doc_vecs, k=3):
    scored = [(cosine_similarity(query_vec, v), t) for t, v in doc_vecs]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:k]]
```

- 给每个文档算与 query 的相似度 → 降序排 → 取前 k 个文本。
- = Java `stream.sorted(comparingDouble(...).reversed()).limit(k)`。

> ✅ 做 `retrieve_top_k`:`[(sim, t) for t,v in doc_vecs]` → `sort(reverse=True)` → 取前 k 的文本。

---

## §31.5 拼上下文:build_context(对应)🟢

```python
def build_context(chunks, sep="\n\n"):
    return sep.join(chunks)
```

把检索到的片段拼成一段「参考资料」,塞进 prompt:
```
基于以下资料回答问题:
{context}

问题:{query}
```
LLM 就基于 context 回答(开卷考试)。

> ✅ 做 `build_context`:`sep.join(chunks)`。

---

## §31.6 embedding:hash_embed(对应)🟡

**embedding** = 把文本变成向量(让「语义接近」可计算)。真实用专门模型(`sentence-transformers` 本地,或 OpenAI/Anthropic embedding API):

```python
# 真实(要装 sentence-transformers,~torch,很重):
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
vec = model.encode("苹果")        # 384 维向量,语义接近的文本向量接近
```

本作业用**确定性假向量** `hash_embed`(md5 映射)替代——只为跑通 RAG 流程,不表达真实语义:

```python
def hash_embed(text, dim=16):
    vec = []
    for i in range(dim):
        b = hashlib.md5(f"{text}:{i}".encode()).digest()[0]
        vec.append((b - 127) / 127.0)
    return vec
```

- 相同文本 → 相同向量(确定性);不同文本 → 不同向量。
- **它不表达语义**(md5 是随机的),真实检索要用真 embedding 模型(语义接近的文本向量才接近)。

> ✅ 做 `hash_embed`:循环 dim,每维 `md5(f"{text}:{i}")[0]` 映射到 -1..1。

---

## §31.7 完整 RAG 管道(讲透)

```python
# 1. 离线建库:文档切片 → 向量化 → 存(这里用 list,真实用 Chroma/pgvector)
docs = "你的长文档..."
chunks = chunk_text(docs, size=200, overlap=30)
embed = lambda t: hash_embed(t)          # 真实换 SentenceTransformer
doc_vecs = [(c, embed(c)) for c in chunks]

# 2. 在线检索回答
def rag_answer(query):
    qvec = embed(query)
    top = retrieve_top_k(qvec, doc_vecs, k=3)
    context = build_context(top)
    prompt = f"基于以下资料回答:\n{context}\n\n问题:{query}"
    return call_llm(client, "你是文档助手", prompt)   # Ch28
```

切→嵌→存→检→拼→答。这就是 RAG。真实工程还要:向量库(Chroma/pgvector/FAISS)、重排序(rerank)、引用溯源、增量更新。

---

## §31.8 向量库选型 + 进阶(讲透不出题)

| 向量库 | 场景 |
|--------|------|
| **Chroma** | 本地开发/入门,Python 友好 |
| **FAISS** | Meta 出的,纯检索库,快 |
| **pgvector** | PostgreSQL 扩展,和业务数据同库 |
| 托管(Pinecone 等) | 省运维 |

进阶:**rerank**(检索 top-20 后用专门模型精排 top-3)、**混合检索**(关键字 + 向量)、**引用溯源**(记录每段来自哪个文档第几页)。

---

## §31.9 Java 老手常踩的坑 ⚠️

1. **整个文档塞 prompt**:超窗口 + 贵。要切片 + 检索相关段。
2. **用欧氏距离不用余弦**:文本向量关心方向不关心长度,用余弦。
3. **切片无 overlap**:句子从中间断,语义丢失。加 overlap。
4. **chunk 太大/太小**:太大检索不精,太小丢段落语义。按句子/段落切更好。
5. **hash_embed 当真 embedding 用**:它不表达语义(随机),只为跑流程。真实用 embedding 模型。
6. **不溯源**:企业场景答案要能点回原文(哪段来的)。记录来源。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `chunk_text` | 切片 + overlap | 🟡 |
| `cosine_similarity` | 向量相似度数学 | 🔴 |
| `retrieve_top_k` | top-k 排序检索 | 🟢 |
| `build_context` | 拼上下文 | 🟢 |
| `hash_embed` | embedding 原理(假向量) | 🟡 |

```bash
uv run pytest 05_ai_framework/ch31/test_ch31_assignment.py -v
```

全绿 = 掌握 Ch31。

---

## ✅ 自测

- [ ] 能说清 RAG 是什么、为什么比微调更常用
- [ ] 会切片(滑动窗口 + overlap)
- [ ] 会算余弦相似度,知道为什么用余弦不用欧氏
- [ ] 能组装「切→嵌→检→拼」的 RAG 管道
- [ ] 知道 hash_embed 只是假向量,真实用 embedding 模型
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「RAG 和微调各适合什么?为什么 RAG 是默认?」— 重读 §31.1
2. 「为什么用余弦相似度不用欧氏距离?」— 重读 §31.3
3. 「hash_embed 和真实 embedding 的区别?为什么不能用 hash_embed 做真实检索?」— 重读 §31.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch32 Agent

RAG 是「给 LLM 资料让它答」。接下来 Agent——让 LLM **自主调工具**(查数据库、调 API、算数),ReAct 循环:思考→调工具→观察→再思考。从「被动答」到「主动干」。
