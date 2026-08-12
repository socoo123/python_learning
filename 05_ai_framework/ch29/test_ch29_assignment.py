"""
Ch29 作业测试。运行: uv run pytest 05_ai_framework/ch29/test_ch29_assignment.py -v
"""
import pytest
from pydantic import ValidationError

from ch29_assignment import (
    ANALYSIS_INSTRUCTION,
    FEW_SHOT_EXAMPLES,
    ReviewAnalysis,
    analyze_review,
    build_analysis_prompt,
    build_cot_prompt,
    build_few_shot_prompt,
    fill_template,
    parse_json_lenient,
    parse_structured,
)


# ---------- §29.2 fill_template ----------
class TestFillTemplate:
    def test_basic(self):
        assert fill_template("你好 {name},你是 {role}", name="小明", role="学生") == "你好 小明,你是 学生"

    def test_missing_key_renders_empty(self):
        result = fill_template("商品:{sku}\n评论:{review}\n历史均分:{avg_score}",
                               sku="KB-001", review="手感绝了")
        assert result == "商品:KB-001\n评论:手感绝了\n历史均分:"

    def test_mixed_given_and_missing(self):
        assert fill_template("{a}-{b}-{c}", a="1", b="2") == "1-2-"

    def test_int_value_formatted(self):
        assert fill_template("评分:{score} 星", score=5) == "评分:5 星"

    def test_no_placeholders(self):
        assert fill_template("没有占位符") == "没有占位符"


# ---------- §29.3 build_few_shot_prompt ----------
class TestBuildFewShotPrompt:
    def test_two_examples_exact_string(self):
        result = build_few_shot_prompt([("苹果", "水果"), ("牛肉", "肉类")], "胡萝卜")
        assert result == "输入:苹果\n输出:水果\n\n输入:牛肉\n输出:肉类\n\n输入:胡萝卜\n输出:"

    def test_empty_examples(self):
        assert build_few_shot_prompt([], "香蕉") == "输入:香蕉\n输出:"

    def test_answer_slot_left_blank(self):
        result = build_few_shot_prompt([("手机很好用", '{"sentiment":"正面"}')], "差劲")
        assert result == '输入:手机很好用\n输出:{"sentiment":"正面"}\n\n输入:差劲\n输出:'


# ---------- §29.4 build_analysis_prompt ----------
class TestBuildAnalysisPrompt:
    def test_starts_with_instruction(self):
        result = build_analysis_prompt("屏幕效果惊艳")
        assert result.startswith(ANALYSIS_INSTRUCTION)

    def test_ends_with_query_and_blank_answer_slot(self):
        result = build_analysis_prompt("屏幕效果惊艳")
        assert result.endswith("输入:屏幕效果惊艳\n输出:")

    def test_contains_all_few_shot_examples(self):
        result = build_analysis_prompt("任意评论")
        for inp, out in FEW_SHOT_EXAMPLES:
            assert f"输入:{inp}\n输出:{out}" in result

    def test_instruction_and_examples_joined_by_blank_line(self):
        first_example = f"输入:{FEW_SHOT_EXAMPLES[0][0]}"
        assert ANALYSIS_INSTRUCTION + "\n\n" + first_example in build_analysis_prompt("x")


# ---------- §29.5 parse_json_lenient ----------
class TestParseJsonLenient:
    def test_plain_json(self):
        assert parse_json_lenient('{"a": 1}') == {"a": 1}

    def test_fenced_json_with_lang(self):
        text = '结果如下:\n```json\n{"x": 2, "y": 3}\n```\n完'
        assert parse_json_lenient(text) == {"x": 2, "y": 3}

    def test_fenced_json_without_lang(self):
        assert parse_json_lenient("```\n{\"k\": 9}\n```") == {"k": 9}

    def test_surrounding_text(self):
        assert parse_json_lenient('分析如下:{"b": 3}。以上供参考') == {"b": 3}

    def test_multiline_json_in_fence(self):
        text = '```json\n{\n  "sentiment": "正面",\n  "score": 5\n}\n```'
        assert parse_json_lenient(text) == {"sentiment": "正面", "score": 5}

    def test_nested_object_and_array(self):
        text = '噪声前缀 {"a": {"b": [1, 2]}, "c": "x"} 噪声后缀'
        assert parse_json_lenient(text) == {"a": {"b": [1, 2]}, "c": "x"}

    def test_fence_takes_priority_over_loose_braces(self):
        text = '说明 {"ignore": 0}\n```json\n{"real": 1}\n```'
        assert parse_json_lenient(text) == {"real": 1}

    def test_invalid_text_raises(self):
        with pytest.raises(Exception):
            parse_json_lenient("完全不是 json 的文字")


# ---------- §29.6 parse_structured ----------
class TestParseStructured:
    def test_basic(self):
        r = parse_structured('{"sentiment":"正面","score":5,"pros":["快"],"cons":[]}', ReviewAnalysis)
        assert isinstance(r, ReviewAnalysis)
        assert r.sentiment == "正面"
        assert r.score == 5
        assert r.pros == ["快"]
        assert r.cons == []

    def test_from_fenced_noisy_text(self):
        r = parse_structured('```json\n{"sentiment":"负面","score":2,"pros":[],"cons":["吵"]}\n```',
                             ReviewAnalysis)
        assert r.sentiment == "负面"
        assert r.cons == ["吵"]

    def test_numeric_string_coerced_to_int(self):
        r = parse_structured('{"sentiment":"中性","score":"5","pros":[],"cons":[]}', ReviewAnalysis)
        assert r.score == 5  # 能转则转,不抛

    def test_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            parse_structured('{"sentiment":"正面","score":"不是数字","pros":[],"cons":[]}',
                             ReviewAnalysis)

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            parse_structured('{"sentiment":"正面","pros":[],"cons":[]}', ReviewAnalysis)  # 缺 score

    def test_list_field_given_string_raises(self):
        with pytest.raises(ValidationError):
            parse_structured('{"sentiment":"正面","score":4,"pros":"好用","cons":[]}',
                             ReviewAnalysis)


# ---------- §29.7 build_cot_prompt ----------
class TestBuildCotPrompt:
    def test_contains_question(self):
        p = build_cot_prompt("3 件单价 47 元,满 100 减 20,实付多少?")
        assert "3 件单价 47 元,满 100 减 20,实付多少?" in p

    def test_asks_for_step_by_step(self):
        assert "一步步" in build_cot_prompt("x")

    def test_has_reasoning_and_answer_tags(self):
        p = build_cot_prompt("x")
        assert "<推理>" in p
        assert "<答案>" in p


# ---------- §29.8 analyze_review ----------
class TestAnalyzeReview:
    def test_fenced_noisy_response(self):
        r = analyze_review("屏幕效果惊艳,续航给力,值得推荐")
        assert isinstance(r, ReviewAnalysis)
        assert r.sentiment == "正面"
        assert r.score == 5
        assert r.pros == ["屏幕好", "续航强"]
        assert r.cons == []

    def test_clean_json_response(self):
        r = analyze_review("用了一个月就坏了,售后还不给换,气死")
        assert r.sentiment == "负面"
        assert r.score == 1
        assert r.pros == []
        assert r.cons == ["质量差", "售后差"]

    def test_surrounding_text_response(self):
        r = analyze_review("中规中矩,能用,价格还行")
        assert r.sentiment == "中性"
        assert r.score == 3
        assert r.pros == ["价格合理"]
        assert r.cons == []

    def test_unknown_review_gets_default(self):
        r = analyze_review("这条评论没被录制过")
        assert r.sentiment == "中性"
        assert r.score == 3
        assert r.pros == []
        assert r.cons == []

    def test_pipeline_uses_few_shot_prompt(self):
        # 管道第一步必须拼出完整分析 prompt:fake_llm 靠「评论文本出现在 prompt 里」匹配,
        # 若没走 build_analysis_prompt(或把评论丢了),会落入兜底分支,上面用例就会挂。
        # 这里再显式断言一次:兜底响应 ≠ 围栏噪声响应的解析结果。
        r_known = analyze_review("屏幕效果惊艳,续航给力,值得推荐")
        r_unknown = analyze_review("这条评论没被录制过")
        assert r_known.score == 5
        assert r_unknown.score == 3
