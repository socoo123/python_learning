"""
Ch10 作业测试。运行: uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v

每个函数一个 TestXxx 类(命名 = Test + 函数名 PascalCase,web 端按类名单跑)。
覆盖:正常 case ≥ 2 + 边界 case(空输入 / 脏数据 / 极值)≥ 1,
另配「手工小数据」用例防止对着 mock 数据硬编码。

数据源:assets/mock_data/nginx_logs.txt(13 行,第 4/10 行是脏数据,11 行合法)。
"""
import pytest

from ch10_assignment import (
    build_report,
    extract_ips,
    format_top_table,
    is_valid_ip,
    mask_ip,
    parse_alert_codes,
    parse_log_line,
    parse_log_text,
    redact_phones,
)


@pytest.fixture
def nginx_text(mock_data_dir) -> str:
    """整份 nginx 日志原文(13 行,含 2 行脏数据)。"""
    return (mock_data_dir / "nginx_logs.txt").read_text(encoding="utf-8")


@pytest.fixture
def nginx_lines(nginx_text) -> list[str]:
    return nginx_text.splitlines()


# ---------- is_valid_ip:fullmatch + str 验范围 ----------
class TestIsValidIp:
    def test_valid(self):
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("8.8.8.8") is True
        assert is_valid_ip("0.0.0.0") is True

    def test_segment_over_255(self):
        # 形状合法但数值超界:正则验不出来,必须靠 split + all 分工
        assert is_valid_ip("256.1.1.1") is False
        assert is_valid_ip("1.2.3.300") is False

    def test_shape_wrong(self):
        assert is_valid_ip("1.2.3") is False
        assert is_valid_ip("1.2.3.4.5") is False
        assert is_valid_ip("abc") is False

    def test_trailing_space_rejected(self):
        # 用 search 做校验的典型漏网:尾部垃圾。fullmatch 才能拦住
        assert is_valid_ip("192.168.1.1 ") is False
        assert is_valid_ip(" 192.168.1.1") is False

    def test_empty(self):
        assert is_valid_ip("") is False


# ---------- extract_ips:findall ----------
class TestExtractIps:
    def test_two_ips(self):
        assert extract_ips("from 1.2.3.4 to 10.0.0.5") == ["1.2.3.4", "10.0.0.5"]

    def test_real_log_text(self, nginx_text):
        ips = extract_ips(nginx_text)
        assert len(ips) == 11                     # 2 行脏数据里没有 IP
        assert ips[0] == "192.168.1.1"
        assert ips.count("192.168.1.1") == 3      # findall 不去重,3 次访问占 3 位

    def test_no_ip(self):
        assert extract_ips("no ip here") == []

    def test_adjacent_punct(self):
        # \b 单词边界:紧贴标点也能干净取出
        assert extract_ips("ip=10.0.0.5;") == ["10.0.0.5"]


# ---------- parse_log_line:命名分组 + groupdict ----------
class TestParseLogLine:
    def test_first_line_full_dict(self, nginx_lines):
        assert parse_log_line(nginx_lines[0]) == {
            "ip": "192.168.1.1",
            "time": "10/Oct/2023:13:55:36 +0000",
            "method": "GET",
            "path": "/api/products",
            "status": 200,
            "bytes": 1234,
        }

    def test_status_and_bytes_are_int(self, nginx_lines):
        r = parse_log_line(nginx_lines[1])
        assert isinstance(r["status"], int) and r["status"] == 201
        assert isinstance(r["bytes"], int) and r["bytes"] == 567

    def test_delete_500(self, nginx_lines):
        r = parse_log_line(nginx_lines[2])
        assert r["method"] == "DELETE"
        assert r["path"] == "/api/orders/1"
        assert r["status"] == 500

    def test_root_path(self, nginx_lines):
        r = parse_log_line(nginx_lines[12])
        assert r["ip"] == "192.0.2.1"
        assert r["path"] == "/"

    def test_malformed_returns_none(self, nginx_lines):
        assert parse_log_line(nginx_lines[3]) is None    # 第 4 行脏数据
        assert parse_log_line(nginx_lines[9]) is None    # 第 10 行脏数据

    def test_empty_string_returns_none(self):
        assert parse_log_line("") is None

    def test_prefix_garbage_still_parses(self, nginx_lines):
        # 采集器加了行首前缀:search 能找到中段匹配;误用 match 的实现在这里现形
        r = parse_log_line("[req-abc] " + nginx_lines[0])
        assert r is not None
        assert r["ip"] == "192.168.1.1"
        assert r["status"] == 200


# ---------- mask_ip:sub + 命名反向引用 ----------
class TestMaskIp:
    def test_single(self):
        assert mask_ip("192.168.1.1") == "192.168.*.*"

    def test_keeps_first_two_segments(self):
        assert mask_ip("attack from 10.0.0.5 detected") == "attack from 10.0.*.* detected"

    def test_two_ips_in_sentence(self):
        assert mask_ip("1.2.3.4 and 10.20.30.40") == "1.2.*.* and 10.20.*.*"

    def test_log_line_rest_untouched(self, nginx_lines):
        masked = mask_ip(nginx_lines[0])
        assert "192.168.*.*" in masked
        assert "192.168.1.1" not in masked
        assert '"GET /api/products HTTP/1.1" 200 1234' in masked   # 其余部分原样

    def test_no_ip_unchanged(self):
        assert mask_ip("no ip here") == "no ip here"


# ---------- redact_phones:sub + 函数替换 ----------
class TestRedactPhones:
    def test_basic(self):
        assert redact_phones("call 13812345678") == "call 138****5678"

    def test_multiple(self):
        assert redact_phones("a:13900001111 b:15800002222") == "a:139****1111 b:158****2222"

    def test_no_phone_unchanged(self):
        assert redact_phones("no phone here") == "no phone here"

    def test_short_number_untouched(self):
        assert redact_phones("code 12345") == "code 12345"

    def test_long_digit_string_untouched(self):
        # 14 位长串不是手机号:\b 边界让它整体失配;去掉 \b 会误打码前 11 位
        assert redact_phones("id 13812345678901") == "id 13812345678901"


# ---------- parse_alert_codes:re.split ----------
class TestParseAlertCodes:
    def test_mixed_separators(self):
        assert parse_alert_codes("500, 502;503") == [500, 502, 503]

    def test_newline_tab(self):
        assert parse_alert_codes("500\n502\t503") == [500, 502, 503]

    def test_trailing_separator(self):
        # Python re.split 保留尾部空串(Java split 会丢)——实现里要过滤
        assert parse_alert_codes("500,502,") == [500, 502]

    def test_leading_separator(self):
        assert parse_alert_codes(",500") == [500]

    def test_single_code(self):
        assert parse_alert_codes("503") == [503]

    def test_empty(self):
        assert parse_alert_codes("") == []


# ---------- parse_log_text:splitlines + 逐行正则 ----------
class TestParseLogText:
    def test_count_valid(self, nginx_text):
        assert len(parse_log_text(nginx_text)) == 11    # 13 行 - 2 行脏数据

    def test_first_entry(self, nginx_text):
        entries = parse_log_text(nginx_text)
        assert entries[0]["ip"] == "192.168.1.1"
        assert entries[0]["path"] == "/api/products"
        assert entries[0]["status"] == 200

    def test_dirty_lines_skipped_not_shifting_order(self, nginx_text):
        # 第 4 行脏数据被跳过后,第 4 个条目是原第 5 行的 /admin 404
        entries = parse_log_text(nginx_text)
        assert entries[3]["ip"] == "172.16.0.3"
        assert entries[3]["path"] == "/admin"
        assert entries[3]["status"] == 404

    def test_all_fields_typed(self, nginx_text):
        entries = parse_log_text(nginx_text)
        assert all(isinstance(e["status"], int) for e in entries)
        assert all(isinstance(e["bytes"], int) for e in entries)

    def test_empty_text(self):
        assert parse_log_text("") == []

    def test_garbage_only(self):
        assert parse_log_text("garbage\nmore garbage") == []

    def test_no_trailing_newline(self, nginx_lines):
        text = nginx_lines[0] + "\n" + nginx_lines[1]   # 末尾无换行
        assert len(parse_log_text(text)) == 2


# ---------- format_top_table:f-string 对齐 ----------
class TestFormatTopTable:
    def test_two_rows_exact(self):
        result = format_top_table([("192.168.1.1", 3), ("10.0.0.5", 2)], "Top IP")
        assert result == (
            "== Top IP ==\n"
            "1. 192.168.1.1         3\n"
            "2. 10.0.0.5            2"
        )

    def test_three_rows_with_tie(self):
        rows = [("192.168.1.1", 3), ("10.0.0.5", 2), ("8.8.8.8", 2)]
        result = format_top_table(rows, "Top IP")
        assert result.splitlines()[3] == "3. 8.8.8.8             2"

    def test_empty_rows_title_only(self):
        assert format_top_table([], "Top IP") == "== Top IP =="

    def test_single_row(self):
        assert format_top_table([("8.8.8.8", 5)], "X") == "== X ==\n1. 8.8.8.8             5"


# ---------- build_report:综合全链路 ----------
class TestBuildReport:
    def test_real_log_file_exact(self, nginx_text):
        assert build_report(nginx_text) == (
            "===== 日志审计快报 =====\n"
            "有效请求: 11 条 (丢弃脏数据 2 行)\n"
            "错误率: 45.5% (5/11)\n"
            "状态码分布: 200×5 201×1 401×1 404×1 500×2 502×1\n"
            "Top 3 IP:\n"
            "1. 192.168.1.1         3\n"
            "2. 10.0.0.5            2\n"
            "3. 8.8.8.8             2"
        )

    def test_handmade_text_exact(self):
        # 手工小数据,防止对着 mock 答案硬编码
        text = (
            '1.1.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /a HTTP/1.1" 200 100\n'
            "bad line\n"
            '2.2.2.2 - - [10/Oct/2023:13:55:37 +0000] "GET /b HTTP/1.1" 500 200'
        )
        assert build_report(text) == (
            "===== 日志审计快报 =====\n"
            "有效请求: 2 条 (丢弃脏数据 1 行)\n"
            "错误率: 50.0% (1/2)\n"
            "状态码分布: 200×1 500×1\n"
            "Top 3 IP:\n"
            "1. 1.1.1.1             1\n"
            "2. 2.2.2.2             1"
        )

    def test_empty_text(self):
        result = build_report("")
        assert result.startswith("===== 日志审计快报 =====")
        assert "有效请求: 0 条 (丢弃脏数据 0 行)" in result
        assert "错误率: 0.0% (0/0)" in result
