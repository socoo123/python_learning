"""
Ch29 作业:Prompt 工程与结构化输出。

会调 LLM 了(Ch28),这章学「怎么问」+「怎么让它稳定返回结构化数据」。
核心:Prompt 模板填充、few-shot 示例、CoT;以及把 LLM 吐出的(可能带噪声的)
文本解析成【强类型 Pydantic 对象】,告别手写正则。

5 个函数,纯字符串 + pydantic,不调真实 LLM。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch29/test_ch29_assignment.py -v

全绿 = 你掌握了 Ch29。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import json
import re


# ========== §29.2 模板填充:fill_template ==========


def fill_template(template: str, **kwargs) -> str:
    """
    【模板 · §29.2】用 kwargs 填充 {占位符};缺失的占位符填空串(不报错)。

    示例:
        fill_template("你好 {name},你是 {role}", name="小明", role="学生")
            -> "你好 小明,你是 学生"
        fill_template("只有 {name}", name="A")   -> "只有 A"
        fill_template("缺失 {nope}")            -> "缺失 "   # 不抛 KeyError

    思路(format_map + 容错 dict;对比 Java MessageFormat):
        class _Safe(dict):
            def __missing__(self, k): return ""
        return template.format_map(_Safe(kwargs))
    """
    # TODO: format_map + __missing__ 返回 "" 的容错 dict
    ...


# ========== §29.3 few-shot:build_few_shot_prompt ==========


def build_few_shot_prompt(examples: list[tuple[str, str]], query: str) -> str:
    """
    【few-shot · §29.3】用 (输入, 输出) 示例 + 新 query 组装 few-shot prompt。
    让模型「照葫芦画瓢」。结尾留「输出:」让模型接。

    示例:
        build_few_shot_prompt([("苹果","水果"),("牛肉","肉类")], "胡萝卜")
            -> "输入:苹果\\n输出:水果\\n\\n输入:牛肉\\n输出:肉类\\n\\n输入:胡萝卜\\n输出:"

    思路:
        parts = []
        for inp, out in examples:
            parts.append(f"输入:{inp}\\n输出:{out}")
        parts.append(f"输入:{query}\\n输出:")
        return "\\n\\n".join(parts)
    """
    # TODO: 拼示例 + 结尾 query 的「输入:..\\n输出:」
    ...


# ========== §29.4 容错 JSON 提取:parse_json_lenient ==========


def parse_json_lenient(text: str) -> dict:
    """
    【容错 · §29.4】LLM 返回的文本常带噪声(前后解释文字、```json 围栏),从中抠出 JSON 解析。
    优先 ```json ... ``` 围栏;其次第一个 {...};都没有就 json.loads 整段(可能抛)。

    示例:
        parse_json_lenient('{"a": 1}')                  -> {"a": 1}
        parse_json_lenient('结果是:\\n```json\\n{"x": 2}\\n```')  -> {"x": 2}
        parse_json_lenient('前面 {"b": 3} 后面')         -> {"b": 3}

    思路(正则 + json.loads;对比手写正则 vs 结构化输出,见 §29.6):
        m = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```", text, re.S)
        if m: return json.loads(m.group(1))
        m = re.search(r"\\{.*\\}", text, re.S)
        return json.loads(m.group(0) if m else text)
    """
    # TODO: 先试 ```json 围栏,再试 {...},json.loads
    ...


# ========== §29.5 Pydantic 结构化:parse_structured ==========


def parse_structured(json_str: str, model_cls):
    """
    【结构化 · §29.5】把(带噪声的)JSON 文本解析成 Pydantic 模型实例,类型自动校验。
    model_cls 是 BaseModel 子类。解析或校验失败抛异常。

    示例:
        class Review(BaseModel): sentiment: str; score: int
        parse_structured('{"sentiment":"正面","score":5}', Review)
            -> Review(sentiment="正面", score=5)
        parse_structured('{"score":"不是数字"}', Review)   # 抛 ValidationError

    思路(Ch14 学过 Pydantic;先 parse_json_lenient 再 model_validate):
        data = parse_json_lenient(json_str)
        return model_cls.model_validate(data)
    """
    # TODO: parse_json_lenient 取 dict,再 model_cls.model_validate(data)
    ...


# ========== §29.6 CoT:build_cot_prompt ==========


def build_cot_prompt(question: str) -> str:
    """
    【CoT · §29.6】组装「思维链」prompt——要求模型先列推理步骤再给答案,提升复杂题准确率。

    示例:
        build_cot_prompt("小明有 3 个苹果...") -> 含 "一步步" 和原问题 + 要求列步骤

    思路(固定模板 + 占位):
        return (f"请【一步步思考】后回答下面的问题:\\n\\n{question}\\n\\n"
                f"先用 <推理> 标签列出推理步骤,再用 <答案> 标签给出最终答案。")
    """
    # TODO: 返回含「一步步思考」+ 问题 + 要求列步骤的 prompt
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(fill_template("你好 {name},你是 {role}", name="小明", role="学生"))
    print(build_few_shot_prompt([("苹果", "水果")], "胡萝卜"))
    print(parse_json_lenient('结果是:\n```json\n{"x": 2}\n```'))
