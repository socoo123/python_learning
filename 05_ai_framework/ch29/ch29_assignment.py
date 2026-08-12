"""
Ch29 作业:Prompt 工程与结构化输出。

主线场景(极客商城评论分析器):运营要用 LLM 把用户评论批量分析成
{sentiment, score, pros, cons} 结构化结果入库。你要搭一条生产级管道:

    组装 Prompt(模板 + few-shot)→ 调 LLM(本章用 fake_llm 录制回放模拟)
    → 容错抠 JSON → Pydantic 强类型校验

7 个函数,纯字符串 + pydantic,不调真实 LLM。在每处 TODO 写实现,然后:

    uv sync --extra ai
    uv run pytest 05_ai_framework/ch29/test_ch29_assignment.py -v

全绿 = 你掌握了 Ch29。

每题 docstring 的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import json
import re

from pydantic import BaseModel


# ---------------------------------------------------------------------
# 脚手架(已写好,不用填;读它理解管道两端的数据长什么样)
# ---------------------------------------------------------------------


class ReviewAnalysis(BaseModel):
    """评论分析结果模型(Ch14 Pydantic 复用)。LLM 的 JSON 输出最终要变成它。"""

    sentiment: str  # "正面" / "负面" / "中性"
    score: int  # 1-5
    pros: list[str]  # 优点列表,没有则为 []
    cons: list[str]  # 缺点列表,没有则为 []


ANALYSIS_INSTRUCTION = (
    "你是电商评论分析助手。把用户评论分析成 JSON,格式:\n"
    '{"sentiment": "正面/负面/中性", "score": 1-5的整数, "pros": [优点列表], "cons": [缺点列表]}'
)

FEW_SHOT_EXAMPLES: list[tuple[str, str]] = [
    (
        "物流很快,键盘手感一流,就是贵了点",
        '{"sentiment": "正面", "score": 4, "pros": ["物流快", "手感好"], "cons": ["价格偏高"]}',
    ),
    (
        "用了一周就坏了,客服还推三阻四",
        '{"sentiment": "负面", "score": 1, "pros": [], "cons": ["质量差", "售后差"]}',
    ),
]

# 「录制好的」LLM 响应(类比 Java 的 WireMock):故意覆盖三种真实噪声——
# Markdown 围栏、前后夹解释文字、干净 JSON。你的解析必须三种都扛住。
FAKE_LLM_RESPONSES: dict[str, str] = {
    "屏幕效果惊艳,续航给力,值得推荐": (
        '好的,这是分析结果:\n```json\n'
        '{"sentiment": "正面", "score": 5, "pros": ["屏幕好", "续航强"], "cons": []}'
        '\n```\n希望对你有帮助!'
    ),
    "用了一个月就坏了,售后还不给换,气死": (
        '{"sentiment": "负面", "score": 1, "pros": [], "cons": ["质量差", "售后差"]}'
    ),
    "中规中矩,能用,价格还行": (
        '分析如下:{"sentiment": "中性", "score": 3, "pros": ["价格合理"], "cons": []}。以上供参考'
    ),
}

DEFAULT_RESPONSE = '{"sentiment": "中性", "score": 3, "pros": [], "cons": []}'


def fake_llm(prompt: str) -> str:
    """
    脚手架:模拟 Ch28 的 LLM 调用——prompt 里包含哪条已知评论,就返回它对应的
    录制响应(带噪声);都不包含则返回兜底的中性结果。真实项目里把这里换成
    Ch28 的 call_llm 即可,管道其余部分一行不动。
    """
    for review, response in FAKE_LLM_RESPONSES.items():
        if review in prompt:
            return response
    return DEFAULT_RESPONSE


# ========== §29.2 模板填充:fill_template ==========


def fill_template(template: str, **kwargs) -> str:
    """
    【模板 · §29.2】用 kwargs 填充模板里的 {占位符};**缺失的占位符填空串,不报错**。

    场景:Prompt 模板常有可选字段(有时有商品类目、有时没有),
    调用方少传一个字段不该让整个 Prompt 崩掉。

    示例:
        fill_template("你好 {name},你是 {role}", name="小明", role="学生")
            -> "你好 小明,你是 学生"
        fill_template("商品:{sku}\n评论:{review}\n历史均分:{avg_score}",
                      sku="KB-001", review="手感绝了")
            -> "商品:KB-001\n评论:手感绝了\n历史均分:"   # avg_score 缺失 → 空串
        fill_template("没有占位符")  -> "没有占位符"

    提示:普通 format 遇缺失键抛 KeyError。定义一个 dict 子类重写 __missing__
    返回 "",再用 template.format_map(该子类实例(kwargs))。
    """
    # TODO: dict 子类 __missing__ 返回 "" → format_map
    ...


# ========== §29.3 few-shot:build_few_shot_prompt ==========


def build_few_shot_prompt(examples: list[tuple[str, str]], query: str) -> str:
    """
    【few-shot · §29.3】用 (输入, 输出) 示例 + 待答 query 组装 few-shot prompt。
    模型「照葫芦画瓢」按示例格式续写,所以**结尾的答案位必须留空**。

    格式约定:每个示例为 "输入:{inp}\n输出:{out}",示例之间空行分隔,
    结尾追加 "输入:{query}\n输出:"(注意「输出:」后面什么都不写)。

    示例:
        build_few_shot_prompt([("苹果", "水果"), ("牛肉", "肉类")], "胡萝卜")
            -> "输入:苹果\n输出:水果\n\n输入:牛肉\n输出:肉类\n\n输入:胡萝卜\n输出:"
        build_few_shot_prompt([], "香蕉")  -> "输入:香蕉\n输出:"

    提示:循环拼 "输入:...\\n输出:..." 进 parts,结尾 append query 那行,
    用 "\\n\\n".join(parts)。
    """
    # TODO: 拼示例 + 结尾 query 的「输入:..\n输出:」(答案位留空)
    ...


# ========== §29.4 组装完整分析 Prompt:build_analysis_prompt ==========


def build_analysis_prompt(review_text: str) -> str:
    """
    【综合① · §29.4】把「指令 + few-shot 示例」拼成完整的评论分析 prompt。
    指令用常量 ANALYSIS_INSTRUCTION,示例用常量 FEW_SHOT_EXAMPLES。

    结构(顺序不能反):
        ANALYSIS_INSTRUCTION + "\n\n" + build_few_shot_prompt(FEW_SHOT_EXAMPLES, review_text)

    效果:
        build_analysis_prompt("屏幕效果惊艳") 的产物以
        "你是电商评论分析助手。..." 开头、以 "输入:屏幕效果惊艳\n输出:" 结尾,
        中间包含两条 FEW_SHOT_EXAMPLES 示例。

    提示:没有新语法——这题练的是「Prompt 组装收敛到一个函数」的工程习惯
    (单一事实来源,改格式只改一处)。复用上一题即可,一行搞定。
    """
    # TODO: ANALYSIS_INSTRUCTION + "\n\n" + build_few_shot_prompt(...)
    ...


# ========== §29.5 容错 JSON 提取:parse_json_lenient ==========


def parse_json_lenient(text: str) -> dict:
    """
    【容错 · §29.5】LLM 返回的文本常带噪声,从中稳定抠出 JSON 并解析成 dict。

    两级兜底(顺序不能反):
        1. 优先匹配 ```json ... ``` 围栏(语言标记 json 可有可无),取围栏内的 {...};
        2. 没围栏则匹配最外层 {...}(贪婪);
        3. 连 { 都没有 → 直接 json.loads(text),让它正常抛异常(失败就该抛,别吞)。

    示例:
        parse_json_lenient('{"a": 1}')                              -> {"a": 1}
        parse_json_lenient('结果:\\n```json\\n{"x": 2}\\n```\\n完')     -> {"x": 2}
        parse_json_lenient('```\\n{"k": 9}\\n```')                   -> {"k": 9}   # 无语言标记
        parse_json_lenient('分析如下:{"b": 3}。以上供参考')             -> {"b": 3}
        parse_json_lenient("完全不是 json")                          # 抛 JSONDecodeError

    提示(Ch10 正则):围栏用 r"```(?:json)?\\s*(\\{.*?\\})\\s*```"(.*? 非贪婪),
    裸 JSON 用 r"\\{.*\\}"(贪婪)。两个都要带 re.S——. 匹配换行才能抠多行 JSON。
    """
    # TODO: 先试围栏正则,再试 \{.*\},都没有就 json.loads(text) 抛错
    ...


# ========== §29.6 Pydantic 结构化:parse_structured ==========


def parse_structured(json_str: str, model_cls):
    """
    【结构化 · §29.6】把(带噪声的)JSON 文本解析成 Pydantic 模型实例。
    model_cls 是 BaseModel 子类。JSON 抠不出来或校验不过 → 抛异常。

    示例:
        parse_structured('{"sentiment":"正面","score":5,"pros":[],"cons":[]}', ReviewAnalysis)
            -> ReviewAnalysis(sentiment="正面", score=5, pros=[], cons=[])
        parse_structured('```json\\n{"sentiment":"负面","score":1,...}\\n```', ReviewAnalysis)
            -> ReviewAnalysis(...)   # 带围栏噪声也能解析(内部走了 parse_json_lenient)
        parse_structured('{"sentiment":"正面","score":"不是数字",...}', ReviewAnalysis)
            # 抛 ValidationError;缺字段同样抛。注意 score="5" 能转 int,不抛。

    提示(Ch14 学过):先用上一题 parse_json_lenient 抠出 dict,
    再 model_cls.model_validate(data)。= Jackson 的 readValue(json, Class)。
    """
    # TODO: parse_json_lenient 取 dict → model_cls.model_validate(data)
    ...


# ========== §29.7 CoT:build_cot_prompt ==========


def build_cot_prompt(question: str) -> str:
    """
    【CoT · §29.7】组装「思维链」prompt:要求模型**先列推理步骤、再给答案**,
    复杂推理题(数学/逻辑)准确率大幅提升。

    模板要素(缺一不可):
        ① 触发短语「一步步思考」;② 原问题;③ 输出格式要求——
           先用 <推理> 标签列步骤,再用 <答案> 标签给最终答案。

    示例:
        p = build_cot_prompt("3 件单价 47 元,满 100 减 20,实付多少?")
        # p 含 "一步步思考"、含原问题、含 "<推理>" 和 "<答案>" 标签

    提示:一个 f-string 多行拼接即可,字面不必与教程逐字相同,要素齐全就行。
    <推理>/<答案> 标签的好处:程序化抽取答案时正则一抠一个准。
    """
    # TODO: 返回含「一步步思考」+ 原问题 + <推理>/<答案> 标签要求的 prompt
    ...


# ========== §29.8 综合②:analyze_review ==========


def analyze_review(review_text: str) -> ReviewAnalysis:
    """
    【综合② · §29.8】评论情感分析器——把本章零件总装成一条管道:

        ① build_analysis_prompt(review_text)  组装 Prompt(指令 + few-shot)
        ② fake_llm(prompt)                    调 LLM(录制回放,响应带噪声)
        ③ parse_structured(raw, ReviewAnalysis) 容错抠 JSON + 强类型校验

    示例(录制响应见 FAKE_LLM_RESPONSES,断言前自己推一遍):
        analyze_review("屏幕效果惊艳,续航给力,值得推荐")
            -> ReviewAnalysis(sentiment="正面", score=5, pros=["屏幕好", "续航强"], cons=[])
        analyze_review("用了一个月就坏了,售后还不给换,气死")
            -> ReviewAnalysis(sentiment="负面", score=1, pros=[], cons=["质量差", "售后差"])
        analyze_review("没见过的评论")
            -> ReviewAnalysis(sentiment="中性", score=3, pros=[], cons=[])   # 兜底

    提示:就三行,但顺序错了测试会教你做人。想清楚:为什么换真实 LLM 时
    只需把 fake_llm 换成 Ch28 的 call_llm,其余一行不动?
    """
    # TODO: build_analysis_prompt → fake_llm → parse_structured(raw, ReviewAnalysis)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    result = analyze_review("屏幕效果惊艳,续航给力,值得推荐")
    print(f"情感:{result.sentiment}｜评分:{result.score}")
    print(f"优点:{result.pros}｜缺点:{result.cons}")
    print(build_cot_prompt("3 件单价 47 元,满 100 减 20,实付多少?"))
