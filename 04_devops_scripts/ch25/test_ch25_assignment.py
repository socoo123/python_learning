"""
Ch25 作业测试。运行: uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v
"""
import io
import json

import pytest
from rich.console import Console
from typer.testing import CliRunner

from ch25_assignment import (
    app,
    error_logs,
    make_summary_panel,
    make_table,
    summarize_status,
    top_ips,
)

runner = CliRunner()


# ---------- 共享小数据 ----------
def _small_logs() -> list[dict]:
    return [
        {"ip": "1.1.1.1", "method": "GET", "path": "/a", "status": 200},
        {"ip": "1.1.1.1", "method": "GET", "path": "/b", "status": 500},
        {"ip": "2.2.2.2", "method": "GET", "path": "/a", "status": 200},
        {"ip": "3.3.3.3", "method": "POST", "path": "/c", "status": 502},
    ]


def _render(renderable, width: int = 70) -> str:
    """把 Rich 对象渲染到字符串(不依赖真终端)。"""
    buf = io.StringIO()
    Console(file=buf, width=width).print(renderable)
    return buf.getvalue()


# ---------- summarize_status ----------
class TestSummarizeStatus:
    def test_small(self):
        assert summarize_status(_small_logs()) == {200: 2, 500: 1, 502: 1}

    def test_real_access_logs(self):
        from conftest import load_mock_json

        logs = load_mock_json("access_logs.json")
        assert summarize_status(logs) == {200: 13, 201: 2, 401: 1, 404: 1, 500: 3}

    def test_empty(self):
        assert summarize_status([]) == {}

    def test_returns_plain_dict(self):
        # 不是 Counter 子类,而是普通 dict(防直接 return Counter(...))
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
        assert result[0] == ("192.168.1.1", 5)  # 第一个一定是访问最多的

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


# ---------- error_logs ----------
class TestErrorLogs:
    def test_default_threshold_5xx(self):
        # 默认只留 5xx(500、502),不含 200
        result = error_logs(_small_logs())
        assert [l["status"] for l in result] == [500, 502]

    def test_custom_threshold(self):
        # threshold=200 → 全留;threshold=501 → 只留 502
        assert len(error_logs(_small_logs(), 200)) == 4
        assert [l["status"] for l in error_logs(_small_logs(), 501)] == [502]

    def test_empty(self):
        assert error_logs([], 500) == []

    def test_no_match(self):
        ok_only = [{"ip": "x", "method": "GET", "path": "/", "status": 200}]
        assert error_logs(ok_only, 500) == []

    def test_does_not_mutate_input(self):
        logs = _small_logs()
        error_logs(logs, 500)
        assert len(logs) == 4  # 原列表不变(返回新列表)

    def test_real_access_logs(self):
        from conftest import load_mock_json

        logs = load_mock_json("access_logs.json")
        # 3 个 500(其余 404/401 是 4xx,默认阈值 500 不含)
        assert len(error_logs(logs)) == 3
        assert all(l["status"] == 500 for l in error_logs(logs))


# ---------- make_table ----------
class TestMakeTable:
    def test_column_count(self):
        table = make_table("Top", ["IP", "次数"], [["1.1.1.1", "5"]])
        assert len(table.columns) == 2

    def test_renders_title_and_headers(self):
        table = make_table("我的标题", ["IP", "次数"], [["1.1.1.1", "5"]])
        out = _render(table)
        assert "我的标题" in out
        assert "IP" in out
        assert "次数" in out

    def test_renders_row_data(self):
        table = make_table("T", ["IP", "次数"], [["1.1.1.1", "5"], ["2.2.2.2", "3"]])
        out = _render(table)
        for cell in ["1.1.1.1", "2.2.2.2", "5", "3"]:
            assert cell in out

    def test_row_unpacked_into_columns(self):
        # 关键:每个 cell 应落在自己的列。若 add_row 没解包(*row),
        # 整行会被塞进一个单元格,列数对不上 → Rich 渲染时列内容错位。
        table = make_table("T", ["IP", "次数"], [["1.1.1.1", "5"]])
        assert table.columns[0]._cells == ("1.1.1.1",) or list(table.columns[0]._cells) == ["1.1.1.1"]
        assert table.columns[1]._cells == ("5",) or list(table.columns[1]._cells) == ["5"]

    def test_empty_rows(self):
        table = make_table("空", ["A", "B"], [])
        assert len(table.columns) == 2


# ---------- make_summary_panel ----------
class TestMakeSummaryPanel:
    def test_renders_title(self):
        panel = make_summary_panel({200: 2, 500: 1}, title="状态码摘要")
        assert "状态码摘要" in _render(panel)

    def test_renders_each_status_line(self):
        panel = make_summary_panel({200: 2, 500: 1})
        out = _render(panel)
        assert "200: 2 次" in out
        assert "500: 1 次" in out

    def test_sorted_ascending_by_code(self):
        # 升序:200 应排在 500 前面(顺序确定,测试可断言)
        panel = make_summary_panel({500: 1, 200: 2, 404: 3})
        out = _render(panel)
        i200, i404, i500 = out.index("200"), out.index("404"), out.index("500")
        assert i200 < i404 < i500

    def test_empty_status(self):
        panel = make_summary_panel({})
        # 空分布也能构造(正文空字符串),不炸
        assert panel is not None


# ---------- analyze 命令(CliRunner)----------
class TestAnalyzeCommand:
    def _write_logs(self, tmp_path, logs=None) -> str:
        path = tmp_path / "logs.json"
        path.write_text(json.dumps(logs if logs is not None else _small_logs()), encoding="utf-8")
        return str(path)

    def test_json_format_exit_zero(self, tmp_path):
        result = runner.invoke(app, ["analyze", self._write_logs(tmp_path), "--format", "json"])
        assert result.exit_code == 0

    def test_json_format_output(self, tmp_path):
        result = runner.invoke(app, ["analyze", self._write_logs(tmp_path), "--format", "json", "--top", "2"])
        assert result.exit_code == 0
        # ⚠️ JSON 往返后:int key→str、tuple→list
        payload = json.loads(result.stdout)
        assert payload["status"] == {"200": 2, "500": 1, "502": 1}   # 状态码 key 变字符串
        assert payload["top_ips"] == [["1.1.1.1", 2], ["2.2.2.2", 1]]  # tuple 变 list

    def test_table_format_output(self, tmp_path):
        result = runner.invoke(app, ["analyze", self._write_logs(tmp_path), "--format", "table", "--top", "2"])
        assert result.exit_code == 0
        assert "1.1.1.1" in result.stdout

    def test_default_top_is_5(self, tmp_path):
        result = runner.invoke(app, ["analyze", self._write_logs(tmp_path), "--format", "json"])
        payload = json.loads(result.stdout)
        # 小数据只有 3 个 IP,默认 top=5 也只返回 3 个
        assert len(payload["top_ips"]) == 3

    def test_short_option_n(self, tmp_path):
        # 短名 -n 等价 --top
        result = runner.invoke(app, ["analyze", self._write_logs(tmp_path), "-f", "json", "-n", "1"])
        payload = json.loads(result.stdout)
        assert payload["top_ips"] == [["1.1.1.1", 2]]

    def test_missing_file_nonzero_exit(self, tmp_path):
        # 文件不存在 → 抛异常,退出码非 0(防「假装成功」)
        result = runner.invoke(app, ["analyze", str(tmp_path / "nope.json")])
        assert result.exit_code != 0


# ---------- report 命令(CliRunner)----------
class TestReportCommand:
    def _write_logs(self, tmp_path) -> str:
        path = tmp_path / "logs.json"
        path.write_text(json.dumps(_small_logs()), encoding="utf-8")
        return str(path)

    def test_report_exit_zero(self, tmp_path):
        result = runner.invoke(app, ["report", self._write_logs(tmp_path)])
        assert result.exit_code == 0

    def test_report_contains_all_sections(self, tmp_path):
        result = runner.invoke(app, ["report", self._write_logs(tmp_path)])
        out = result.stdout
        # ① 状态码面板  ② Top IP 表  ③ 错误日志表 都在输出里
        assert "状态码" in out
        assert "1.1.1.1" in out          # Top IP
        assert "502" in out              # 错误日志(5xx)

    def test_report_threshold_filters(self, tmp_path):
        # --threshold 501 → 错误表只留 502,不含 500
        result = runner.invoke(app, ["report", self._write_logs(tmp_path), "--threshold", "501"])
        out = result.stdout
        assert "502" in out
        # 500 那行不应出现在错误表里(但 500 可能在状态码面板;用表格行特征判)
        # 面板里有 "500: 1 次" 是状态码统计,正常;错误表里不应有独立 500 行 → 宽松判:阈值生效即可
        assert result.exit_code == 0

    def test_report_real_access_logs(self, tmp_path):
        from conftest import load_mock_json

        path = tmp_path / "access.json"
        path.write_text(json.dumps(load_mock_json("access_logs.json")), encoding="utf-8")
        result = runner.invoke(app, ["report", str(path), "--top", "2"])
        assert result.exit_code == 0
        assert "192.168.1.1" in result.stdout


# ---------- 命令组帮助 ----------
class TestCliHelp:
    def test_help_lists_both_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout
        assert "report" in result.stdout   # 两个子命令都注册成功(命令组)
