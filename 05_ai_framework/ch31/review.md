# Ch31 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | RAG 是什么?为什么知识更新默认选它不选微调? | Retrieval-Augmented Generation:检索你的文档塞进 prompt,让 LLM 开卷考试。比微调便宜/即时(改文档重建索引即可,不用重训)/可溯源 | ⬜ |
| 2 | RAG 管道几步? | 切(chunk)→ 嵌(embed)→ 存向量库 → 检(top-k)→ 拼上下文/prompt → 喂 LLM 答(带溯源) | ⬜ |
| 3 | chunk_text 为什么要 overlap?`step=max(1,...)` 防什么? | overlap 防一句话从中间切断丢上下文。`max(1, size-overlap)` 防 overlap≥size 时步长 ≤0 导致 range 报错/死循环 | ⬜ |
| 4 | 余弦相似度公式?值域?为什么不用欧氏距离? | cosθ = a·b/(|a‖b|),值域 [-1,1](1 同向/0 正交/-1 反向)。文本向量关心方向(语义)不关心长度(词数):[1,2]vs[2,4] 余弦 1.0、欧氏 2.236 | ⬜ |
| 5 | 零向量算余弦怎么办? | 零向量没有方向,防除零:`dot/(na*nb) if na and nb else 0.0`,约定相似度为 0 | ⬜ |
| 6 | retrieve_top_k 的元组排序陷阱?同分怎么办? | `[(文本,分数)].sort()` 不带 key 会按【文本字典序】排!必须 `key=lambda x: x[1], reverse=True`。list.sort 稳定排序,同分保持原顺序 | ⬜ |
| 7 | hash_embed 和真 embedding 的区别?维度有什么讲究? | hash_embed 是 md5 确定性假向量:相同文本相同向量,但【不表达语义】,只为离线跑通管道;真实用 sentence-transformers/OpenAI。query 和建库必须同模型同维度,否则 zip 对齐静默算错 | ⬜ |
| 8 | build_context 为什么要给片段编号 `[资料N]`? | LLM 回答能引用「据[资料2]…」= 可溯源(企业合规刚需)。`enumerate(chunks, 1)` 从 1 计数,`sep.join` 只在元素间加分隔符 | ⬜ |
| 9 | RAG prompt 必须写死哪条约束?为什么? | 「只基于资料回答,资料没有就说不知道」——不加约束,模型对资料外问题会瞎编(幻觉) | ⬜ |
| 10 | 为什么生产上「建索引」和「检索」要分离?本章为何合在一起? | 生产:离线建一次索引存向量库,在线只 embed query(每次重建是 O(N) 浪费)。本章合并进 search_knowledge_base 是教学简化,为一次调用看全管道 | ⬜ |
| 11 | rag_answer 的 llm 为什么做成注入的 callable? | 依赖注入(= Java 传 Function/策略接口):测试传 lambda 假模型(离线/免费/确定性,Ch30 FakeModel 同套路),生产传真 client,管道代码不动 | ⬜ |
| 12 | 向量库怎么选?进阶方向? | Chroma(本地入门)/FAISS(极致性能)/pgvector(与业务同库)/托管(省运维)。进阶:rerank 精排、BM25+向量混合检索、引用溯源、增量更新 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「RAG vs 微调 + 为什么 RAG 默认」?
- [ ] 能说清「余弦 vs 欧氏」并举数值例子?
- [ ] 能说清「hash_embed 假向量 vs 真 embedding + 维度一致性」?
- [ ] 能说清「为什么建索引和检索要分离」?
- [ ] 能说清「llm 注入 + 答案带 sources 溯源」的设计?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
