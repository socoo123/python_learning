"""
Ch25 作业测试。运行: uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v
"""
import io
import json

import pytest
from rich.console import Console
from typer.testing import CliRunner

from ch25_assignment import app, analyze, make_table, summarize_status, top_ips

runner = CliRunner()


# ---------- 共享小数据 ----------
def _small_logs() -> list[dict]:
    return [
        {"ip": "1.1.1.1", "method": "GET", "path": "/a", "status": 200},
        {"ip": "1.1.1.1", "method": "GET", "path": "/b", "status": 500},
        {"ip": "2.2.2.2", "method": "GET", "path": "/a", "status": 200},
    ]


# ---------- summarize_status ----------
class TestSummarizeStatus:
    def test_small(self):
        assert summarize_status(_small_logs()) == {200: 2, 500: 1}

    def test_real_access_logs(self):
        from conftest import load_mock_json

        logs = load_mock_json("access_logs.json")
        assert summarize_status(logs) == {200: 13, 201: 2, 401: 1, 404: 1, 500: 3}

    def test_empty(self):
        assert summarize_status([]) == {}

    def test_returns_plain_dict(self):
        # 不是 Counter 子类,而是普通 dict
        result = summarize_status(_small_logs())
        assert type(result) is dict

    def test_status_keys_are_int(self):
        result = summarize_status(_small_logs())
        for k in result:
            assert isinstance(k, int)


# ---------- top_ips ----------
class TestTopIps:
    def test_small_top2(self):
        assert top_ips(_small_logs(), n=2) == [("1.1.1.1", 2), ("2.2.2.2", 1)]

    def test_small_top1(self):
        assert top_ips(_small_logs(), n=1) == [("1.1.1.1", 2)]

    def test_real_top2(self):
        from conftest import load_mock_json

        logs = load_mock_json("access_logs.json")
        # 192.168.1.1(5 次)、10.0.0.5(3 次),前 2 无并列,结果确定
        assert top_ips(logs, n=2) == [("192.168.1.1", 5), ("10.0.0.5", 3)]

    def test_n_larger_than_unique(self):
        # n 超过 IP 种类数,返回全部(access_logs 有 8 个不同 IP)
        from conftest import load_mock_json

        logs = load_mock_json("access_logs.json")
        result = top_ips(logs, n=100)
        assert len(result) == 8
        # 第一个一定是访问最多的
        assert result[0] == ("192.168.1.1", 5)

    def test_descending_order(self):
        result = top_ips(_small_logs(), n=10)
        counts = [c for _, c in result]
        assert counts == sorted(counts, reverse=True)

    def test_returns_list_of_tuples(self):
        result = top_ips(_small_logs(), n=2)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2


# ---------- make_table ----------
class TestMakeTable:
    def test_column_count(self):
        table = make_table("Top", ["IP", "次数"], [["1.1.1.1", "5"]])
        assert len(table.columns) == 2

    def test_renders_title_and_headers(self):
        table = make_table("我的标题", ["IP", "次数"], [["1.1.1.1", "5"]])
        buf = io.StringIO()
        Console(file=buf, width=60).print(table)
        out = buf.getvalue()
        assert "我的标题" in out
        assert "IP" in out
        assert "次数" in out

    def test_renders_row_data(self):
        table = make_table("T", ["IP", "次数"], [["1.1.1.1", "5"], ["2.2.2.2", "3"]])
        buf = io.StringIO()
        Console(file=buf, width=60).print(table)
        out = buf.getvalue()
        assert "1.1.1.1" in out
        assert "2.2.2.2" in out
        assert "5" in out
        assert "3" in out

    def test_empty_rows(self):
        table = make_table("空", ["A", "B"], [])
        assert len(table.columns) == 2


# ---------- analyze 命令(CliRunner)----------
class TestAnalyzeCommand:
    def _write_logs(self, tmp_path) -> str:
        path = tmp_path / "logs.json"
        path.write_text(
            json.dumps(_small_logs()), encoding="utf-8"
        )
        return str(path)

    def test_json_format_exit_zero(self, tmp_path):
        path = self._write_logs(tmp_path)
        result = runner.invoke(app, ["analyze", path, "--format", "json"])
        assert result.exit_code == 0

    def test_json_format_output(self, tmp_path):
        path = self._write_logs(tmp_path)
        result = runner.invoke(app, ["analyze", path, "--format", "json", "--top", "2"])
        assert result.exit_code == 0
        # 输出是 JSON,能解析回来。⚠️ JSON 往返后:int key→str、tuple→list
        payload = json.loads(result.stdout)
        assert payload["status"] == {"200": 2, "500": 1}   # 状态码 key 变字符串
        assert payload["top_ips"] == [["1.1.1.1", 2], ["2.2.2.2", 1]]  # tuple 变 list

    def test_table_format_output(self, tmp_path):
        path = self._write_logs(tmp_path)
        result = runner.invoke(app, ["analyze", path, "--format", "table", "--top", "2"])
        assert result.exit_code == 0
        assert "1.1.1.1" in result.stdout

    def test_default_top_is_5(self, tmp_path):
        path = self._write_logs(tmp_path)
        result = runner.invoke(app, ["analyze", path, "--format", "json"])
        payload = json.loads(result.stdout)
        # 小数据只有 2 个 IP,默认 top=5 也只返回 2 个
        assert len(payload["top_ips"]) == 2

    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout
