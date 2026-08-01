# Ch31 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | RAG 是什么?为什么比微调常用? | Retrieval-Augmented Generation:检索文档塞进 prompt 让 LLM 开卷考试。比微调便宜/即时/可溯源(改文档重建索引即可,不用重训) | ⬜ |
| 2 | RAG 管道几步? | 切片(chunk)→ 向量化(embed)→ 存向量库 → 检索 top-k → 拼上下文 → 喂 LLM 答 | ⬜ |
| 3 | chunk_text 的 overlap 干嘛? | 相邻块重叠 overlap 字符,防止句子从中间切断丢失上下文。step=size-overlap | ⬜ |
| 4 | 余弦相似度公式?值域? | cosθ = a·b/(|a||b|)。值域[-1,1]:1同向最似,0正交无关,-1反向。文本关心方向(语义)不关心长度,所以用余弦不用欧氏 | ⬜ |
| 5 | 零向量算相似度怎么办? | 防除零:if na and nb else 0.0。零向量和任何向量相似度定义为 0 | ⬜ |
| 6 | retrieve_top_k 怎么做? | [(cos_sim(q,v), text) for ...] → sort(reverse=True) → 取前 k 个文本。= Java stream sorted reversed limit | ⬜ |
| 7 | hash_embed 和真 embedding 区别? | hash_embed 是确定性假向量(md5 映射),相同文本相同向量但【不表达语义】。真实用 sentence-transformers/OpenAI,语义接近文本向量才接近 | ⬜ |
| 8 | 向量库选型?进阶? | Chroma(本地入门)/FAISS(快)/pgvector(同业务库)/Pinecone(托管)。进阶:rerank 精排、混合检索(关键字+向量)、引用溯源 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「RAG vs 微调 + 为什么 RAG 默认」?
- [ ] 能说清「余弦相似度 vs 欧氏距离」?
- [ ] 能说清「hash_embed 假向量 vs 真 embedding」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
