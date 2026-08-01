"""
Ch29 作业测试。运行: uv run pytest 05_ai_framework/ch29/test_ch29_assignment.py -v
"""
import pytest
from pydantic import BaseModel, ValidationError

from ch29_assignment import (
    build_cot_prompt,
    build_few_shot_prompt,
    fill_template,
    parse_json_lenient,
    parse_structured,
)


class Review(BaseModel):
    sentiment: str
    score: int


# ---------- fill_template ----------
class TestFillTemplate:
    def test_basic(self):
        assert fill_template("你好 {name},你是 {role}", name="小明", role="学生") == "你好 小明,你是 学生"

    def test_single(self):
        assert fill_template("只有 {name}", name="A") == "只有 A"

    def test_missing_key_is_empty(self):
        assert fill_template("缺失 {nope}") == "缺失 "

    def test_mixed(self):
        assert fill_template("{a}-{b}-{c}", a="1", b="2") == "1-2-"

    def test_no_placeholders(self):
        assert fill_template("没有占位符") == "没有占位符"


# ---------- build_few_shot_prompt ----------
class TestFewShot:
    def test_basic(self):
        result = build_few_shot_prompt([("苹果", "水果"), ("牛肉", "肉类")], "胡萝卜")
        assert "输入:苹果\n输出:水果" in result
        assert "输入:牛肉\n输出:肉类" in result
        assert result.endswith("输入:胡萝卜\n输出:")

    def test_single_example(self):
        result = build_few_shot_prompt([("苹果", "水果")], "香蕉")
        assert "输入:苹果\n输出:水果" in result
        assert result.endswith("输入:香蕉\n输出:")

    def test_empty_examples(self):
        result = build_few_shot_prompt([], "香蕉")
        assert result == "输入:香蕉\n输出:"

    def test_examples_separated_by_blank_line(self):
        result = build_few_shot_prompt([("a", "1"), ("b", "2")], "c")
        assert "\n\n输入:b" in result


# ---------- parse_json_lenient ----------
class TestParseJsonLenient:
    def test_plain_json(self):
        assert parse_json_lenient('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        text = '结果如下:\n```json\n{"x": 2, "y": 3}\n```\n完'
        assert parse_json_lenient(text) == {"x": 2, "y": 3}

    def test_fenced_without_lang(self):
        assert parse_json_lenient("```\n{\"k\": 9}\n```") == {"k": 9}

    def test_json_with_surrounding_text(self):
        assert parse_json_lenient('前面文字 {"b": 3} 后面文字') == {"b": 3}

    def test_nested(self):
        assert parse_json_lenient('{"a": {"b": 1}}') == {"a": {"b": 1}}

    def test_invalid_raises(self):
        with pytest.raises(Exception):
            parse_json_lenient("完全不是 json 的文字")


# ---------- parse_structured ----------
class TestParseStructured:
    def test_basic(self):
        r = parse_structured('{"sentiment":"正面","score":5}', Review)
        assert isinstance(r, Review)
        assert r.sentiment == "正面"
        assert r.score == 5

    def test_from_fenced(self):
        r = parse_structured('```json\n{"sentiment":"负面","score":2}\n```', Review)
        assert r.sentiment == "负面"

    def test_from_noisy_text(self):
        r = parse_structured('分析结果 {"sentiment":"中性","score":3} 以上', Review)
        assert r.score == 3

    def test_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            parse_structured('{"sentiment":"正面","score":"不是数字"}', Review)

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            parse_structured('{"sentiment":"正面"}', Review)  # 缺 score


# ---------- build_cot_prompt ----------
class TestCotPrompt:
    def test_contains_question(self):
        p = build_cot_prompt("小明有几个苹果?")
        assert "小明有几个苹果?" in p

    def test_asks_for_step_by_step(self):
        p = build_cot_prompt("x")
        assert "一步步" in p or "逐步" in p

    def test_asks_for_reasoning(self):
        p = build_cot_prompt("x")
        assert "推理" in p or "步骤" in p
