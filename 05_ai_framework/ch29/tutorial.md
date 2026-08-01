# Ch29 · Prompt 工程与结构化输出

> **预计**:0.5 天 ｜ **前置**:Ch28、Ch14(Pydantic)｜ **M5 第 2 章**
> **目标**:① 学会让模型更好作答的 Prompt 套路(模板、few-shot、CoT);② 让模型**稳定返回结构化数据**——用 Pydantic 把 LLM 吐出的(带噪声的)文本变成强类型对象,告别手写正则。

> 📐 **本教程的契约**:§29.2–§29.6 对应作业 5 个函数。纯字符串 + Pydantic,不调真实 LLM。

---

## 🗺️ 本章地图

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `fill_template` | §29.2 | str.format_map + 容错(缺失占位符不报错) |
| `build_few_shot_prompt` | §29.3 | few-shot:给示例让模型照做 |
| `parse_json_lenient` | §29.4 | 从带噪声文本抠 JSON(围栏/前后文) |
| `parse_structured` | §29.5 | JSON → Pydantic 模型(类型校验) |
| `build_cot_prompt` | §29.6 | CoT:要求先推理再答 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. 同一个 LLM,为什么换个问法答案质量差很多?「Prompt 工程」是玄学还是工程?
2. Java 里 `String.format("Hi %s", name)`,Python 怎么填模板?如果占位符没给值,Python 会怎样?
3. 模型有时把 JSON 包在 ```` ```json ```` 围栏里、前后还带解释文字,怎么稳定抠出 JSON?
4. 手写正则解析 LLM 输出很脆,有没有「强类型」的办法?(提示:Ch14 的 Pydantic)
5. 复杂数学题,怎么让模型别瞎猜答案?(CoT——让它先写推理过程)

---

## §29.1 为什么 Prompt 是工程 🟡

LLM 的输出质量,**强依赖你怎么问**。同样一个模型:
- 差的问法:`"分析这个评论"` → 模型返回一段散文,你想程序化处理很难。
- 好的问法:`"输出 JSON:{"sentiment": "正面/负面/中性", "score": 1-5}"` → 直接能解析。

Prompt 工程就是**用可复制的套路,稳定地把模型输出变成你能用的东西**。本教材的 5 个作业就是 5 个最常用的套路。

> 🟡 **Java 对比**:像 SQL——同一个数据库,写好 SQL 才出对的结果。Prompt 是「给 LLM 的 SQL」。

---

## §29.2 模板填充:fill_template(对应)🟢

Prompt 里常有可变部分(用户输入、上下文),用模板填充。Python 的 `str.format_map`:

```python
def fill_template(template: str, **kwargs) -> str:
    class _Safe(dict):
        def __missing__(self, k): return ""
    return template.format_map(_Safe(kwargs))
```

- `template.format_map(dict)`:用 dict 的键填 `{占位符}`。= Java `MessageFormat` / `String.format`。
- **为什么用 `_Safe`**:普通 `format` 遇到**没给的占位符会抛 `KeyError`**。Prompt 模板里常有可选字段,用 `_Safe.__missing__` 让缺失键返回 `""`,稳健。

> ✅ 做 `fill_template`:`format_map(_Safe(kwargs))`,`_Safe.__missing__` 返回 `""`。

---

## §29.3 few-shot:build_few_shot_prompt(对应)🟡

模型「照葫芦画瓢」能力极强——给它几个**输入→输出**示例,它就懂你要的格式/风格了。这叫 **few-shot**(对比 zero-shot 不给示例)。

```python
def build_few_shot_prompt(examples, query):
    parts = []
    for inp, out in examples:
        parts.append(f"输入:{inp}\n输出:{out}")
    parts.append(f"输入:{query}\n输出:")    # 留「输出:」让模型接
    return "\n\n".join(parts)
```

- 每个示例「输入:X\n输出:Y」对齐格式,模型学会映射规则。
- 结尾留 `输入:{query}\n输出:` **不写答案**——模型看到「输出:」就自动接着写(完形填空效应)。

> 🟡 few-shot 示例数量:1-3 个通常够;太多费 token 且可能过拟合示例风格。

> ✅ 做 `build_few_shot_prompt`:拼各示例的「输入/输出」对 + 结尾 `输入:{query}\n输出:`。

---

## §29.4 容错 JSON 提取:parse_json_lenient(对应)🔴

这是 LLM 工程里**最常踩的坑**。你让模型返回 JSON,它经常给你:
```
好的,这是分析结果:
```json
{"sentiment": "正面", "score": 5}
```
希望对你有帮助!
```

前后有解释文字、还包了 ```` ```json ```` 围栏。直接 `json.loads` 会失败。所以要**容错提取**:

```python
def parse_json_lenient(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)  # 先试围栏
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.S)                           # 再试裸 {...}
    return json.loads(m.group(0) if m else text)
```

- 先找 ```` ```json {...} ```` 围栏 → 取里面的 JSON。
- 没围栏就找第一个 `{...}`(贪婪到最后的 `}`)。
- `re.S`(`.` 匹配换行)让正则跨行匹配多行 JSON。
- **更稳的办法**:用 SDK 的「结构化输出/工具调用」强制模型返回合法 JSON(§29.5 + Ch32),从源头消除噪声。`parse_json_lenient` 是兜底。

> ✅ 做 `parse_json_lenient`:先正则匹配 ```` ```json ```` 围栏,再匹配 `{...}`,`json.loads`。

---

## §29.5 Pydantic 结构化:parse_structured(对应)🟡

把抠出来的 JSON dict 变成**强类型对象**(Ch14 Pydantic),后续代码就有类型提示和自动校验,不用 `data["score"]` 到处写字符串键:

```python
def parse_structured(json_str, model_cls):
    data = parse_json_lenient(json_str)
    return model_cls.model_validate(data)
```

用法:
```python
from pydantic import BaseModel
class Review(BaseModel):
    sentiment: str
    score: int

r = parse_structured('```json\n{"sentiment":"正面","score":5}\n```', Review)
r.score        # 5,且 IDE 有类型提示
# 类型不对会抛 ValidationError:
parse_structured('{"score":"不是数字"}', Review)   # 抛错(score 要 int)
```

- `model_validate(data)`:Pydantic v2 的方法,把 dict 转成模型实例,**自动类型校验**(score 给字符串就抛 `ValidationError`)。
- 这比手写正则 / 手动取键**强太多**:类型安全 + 缺字段报错 + IDE 补全。

> 🟡 **Java 对比**:= Jackson `objectMapper.readValue(json, Review.class)`,带校验。Pydantic 是 Python 版的强类型反序列化。

> ✅ 做 `parse_structured`:`parse_json_lenient` 取 dict → `model_cls.model_validate(data)`。

---

## §29.6 CoT:build_cot_prompt(对应)🟢

复杂推理题(数学、逻辑),直接问模型可能瞎猜。**Chain-of-Thought (CoT)**:要求模型**先把推理过程写出来**,再给答案。推理步骤会让答案准确率大幅提升。

```python
def build_cot_prompt(question):
    return (
        f"请【一步步思考】后回答下面的问题:\n\n{question}\n\n"
        f"先用 <推理> 标签列出推理步骤,再用 <答案> 标签给出最终答案。"
    )
```

- 关键短语:「一步步思考」「Let's think step by step」——这句神奇地提升准确率(论文验证过)。
- 用 `<推理>` `<答案>` 标签结构化输出,方便你程序化抽取答案部分。

> 🔴 **新版模型**:Claude/GPT-4 有「extended thinking」内置 CoT,不用手写 prompt 也能推理。但理解 CoT 原理仍有用(老模型 / 控制成本时)。

> ✅ 做 `build_cot_prompt`:返回含「一步步思考」+ 问题 + 要求「先推理再答案」的模板。

---

## §29.7 真实组合示例(讲透)

```python
from pydantic import BaseModel

class Review(BaseModel):
    sentiment: str
    pros: list[str]
    cons: list[str]
    score: int

# 1. few-shot + 结构化要求 组合 prompt
prompt = build_few_shot_prompt(
    examples=[("手机很好用", '{"sentiment":"正面","pros":["流畅","续航"],"cons":[],"score":5}')],
    query=用户评论,
) + '\n请严格输出上述格式的 JSON。'

# 2. 调模型(Ch28)
text = call_llm(client, "你是评论分析助手", prompt)

# 3. 容错解析成强类型对象
review = parse_structured(text, Review)
print(review.sentiment, review.score)
```

模板 → few-shot → 调用 → 容错解析 → 强类型对象。这条链就是生产级 LLM 应用的标准管道。

---

## §29.8 Java 老手常踩的坑 ⚠️

1. **手写正则解析 LLM 输出**:脆、易碎。用 Pydantic 结构化(`model_validate`)或工具调用。
2. **直接 `json.loads` LLM 文本**:模型常带围栏/前后文,必崩。用 `parse_json_lenient` 兜底,或更好的——强制结构化输出。
3. **不给示例就想要特定格式**:zero-shot 格式不稳。关键格式给 few-shot。
4. **占位符没给值就崩**:用 `_Safe` 容错的 `format_map`,别让一个可选字段炸掉整个 prompt。
5. **复杂题不让模型推理**:CoT 提升准确率,别让模型直接猜答案。
6. **Prompt 写死在代码里散落**:集中管理(模板常量 / 文件),别到处拼字符串。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `fill_template` | format_map + 容错 | 🟢 |
| `build_few_shot_prompt` | few-shot 组装 | 🟡 |
| `parse_json_lenient` | 容错 JSON 提取 | 🔴 |
| `parse_structured` | Pydantic 结构化 | 🟡 |
| `build_cot_prompt` | CoT 模板 | 🟢 |

```bash
uv run pytest 05_ai_framework/ch29/test_ch29_assignment.py -v
```

全绿 = 掌握 Ch29。

---

## ✅ 自测

- [ ] 会用 `format_map` + `_Safe` 做容错模板填充
- [ ] 懂 few-shot 原理,能组装 few-shot prompt
- [ ] 能从带围栏/噪声的文本里容错抠 JSON
- [ ] 会用 Pydantic 把 JSON 变成校验过的强类型对象
- [ ] 知道 CoT 为什么提升准确率
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么直接 `json.loads` LLM 的输出会崩?怎么兜底?更好的办法是什么?」— 重读 §29.4/§29.5
2. 「few-shot 和 zero-shot 区别?为什么给示例格式更稳?」— 重读 §29.3
3. 「CoT 那句『一步步思考』为什么有用?」— 重读 §29.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch30 LangChain 基础

Prompt 和解析会了,但每次手拼「prompt → 调用 → 解析」很重复。LangChain 用 **LCEL**(`prompt | model | parser`)把这条链声明式拼起来,像 Unix 管道。
