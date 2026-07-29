"""
Ch10 作业测试。运行: uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v
"""
import pytest

from ch10_assignment import parse_nginx_log, extract_ips, redact_phones, split_on
from conftest import load_mock_json


@pytest.fixture
def nginx_logs():
    return load_mock_json("nginx_logs.json")


# ---------- parse_nginx_log:re + 命名分组 ----------
class TestParseNginxLog:
    def test_valid_get(self, nginx_logs):
        r = parse_nginx_log(nginx_logs[0])
        assert r["ip"] == "192.168.1.1"
        assert r["method"] == "GET"
        assert r["path"] == "/api/products"
        assert r["status"] == 200

    def test_status_is_int(self, nginx_logs):
        r = parse_nginx_log(nginx_logs[0])
        assert isinstance(r["status"], int)

    def test_delete_500(self, nginx_logs):
        r = parse_nginx_log(nginx_logs[2])
        assert r["method"] == "DELETE"
        assert r["status"] == 500

    def test_has_time_field(self, nginx_logs):
        r = parse_nginx_log(nginx_logs[1])
        assert "10/Oct/2023" in r["time"]

    def test_malformed_returns_none(self, nginx_logs):
        assert parse_nginx_log(nginx_logs[4]) is None
        assert parse_nginx_log(nginx_logs[5]) is None

    def test_empty_string_returns_none(self):
        assert parse_nginx_log("") is None


# ---------- extract_ips:re.findall ----------
class TestExtractIps:
    def test_find_two(self):
        assert extract_ips("from 1.2.3.4 to 10.0.0.5") == ["1.2.3.4", "10.0.0.5"]

    def test_single(self):
        assert extract_ips("ip=192.168.1.1") == ["192.168.1.1"]

    def test_none(self):
        assert extract_ips("no ip here") == []

    def test_in_sentence(self):
        result = extract_ips("client 8.8.8.8 connected via 1.1.1.1")
        assert result == ["8.8.8.8", "1.1.1.1"]


# ---------- redact_phones:re.sub ----------
class TestRedactPhones:
    def test_basic(self):
        assert redact_phones("call 13812345678") == "call ***"

    def test_multiple(self):
        assert redact_phones("a:13900001111 b:15800002222") == "a:*** b:***"

    def test_no_phone_unchanged(self):
        assert redact_phones("no phone here") == "no phone here"

    def test_keeps_short_numbers(self):
        # 短数字(不是 11 位手机号)不替换
        assert redact_phones("code 12345") == "code 12345"


# ---------- split_on:re.split ----------
class TestSplitOn:
    def test_comma(self):
        assert split_on("a,b,c") == ["a", "b", "c"]

    def test_mixed_seps(self):
        assert split_on("a,b;c") == ["a", "b", "c"]

    def test_single(self):
        assert split_on("solo") == ["solo"]

    def test_custom_sep(self):
        assert split_on("a|b|c", seps=r"\|") == ["a", "b", "c"]
