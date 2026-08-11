"""
Ch10 作业:正则表达式与字符串处理。

场景:你是电商平台值班运维,拿到导出的 nginx 访问日志
(assets/mock_data/nginx_logs.txt,13 行样本,含 2 行脏数据),
安全团队要一份**审计快报**:校验白名单 IP → 从全文提取 IP → 结构化解析每一行
→ 对外分享前脱敏(IP + 手机号)→ 解析告警规则配置 → 排版 Top-N 表 → 汇总快报。

9 个任务,从单个 re 函数一路递进到大综合。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v

全绿 = 你掌握了 Ch10。

约定:
- nginx_logs.txt 每行形如:
    192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234
- 模块级的 LOG_RE / IP_RE 是【脚手架】,已按 §10.4 的拆解编译好,直接用,不用改。
- 每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
  (提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import re
from collections import Counter

# ========== 脚手架:两条「大件」正则(§10.3/§10.4 讲透,直接用)==========

# nginx 访问日志:IP - - [时间] "方法 路径 HTTP/x.x" 状态码 字节数
# (?P<名>...) 命名分组;(?:...) 非捕获分组;[^\]]+ 抓 ] 之前的所有字符;\S+ 非空白
LOG_RE = re.compile(
    r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) - - \[(?P<time>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d{3}) (?P<bytes>\d+)'
)

# IP 地址:4 段 1~3 位数字用点连。\b 单词边界防从长串中间切开;
# (?:...) 只分组不捕获——否则 findall 返回值会变形(§10.3 陷阱)
IP_RE = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')


# ========== §10.2 search / match / fullmatch ==========


def is_valid_ip(ip: str) -> bool:
    """
    【fullmatch · §10.2】校验配置中心拉下来的白名单条目是不是合法 IPv4。

    任务:整串形状必须是「4 段 1~3 位数字用点连」,且每段数值 ≤ 255。
         两段式分工:正则验形状,str 方法验范围。

    示例:
        is_valid_ip("192.168.1.1")   -> True
        is_valid_ip("256.1.1.1")     -> False   (形状合法但 256 超界)
        is_valid_ip("192.168.1.1 ")  -> False   (尾部空格,形状就不合法)
        is_valid_ip("1.2.3")         -> False

    提示:
      ① re.fullmatch(r'\\d{1,3}(?:\\.\\d{1,3}){3}', ip) 返回 None → 形状不合法。
         fullmatch 自带整串锚定,不用再写 ^...$。别用 search,它会放过前后垃圾。
      ② 形状合法后再 ip.split('.') + all(int(seg) <= 255 ...) 验范围。
    """
    # TODO: fullmatch 验形状 → split + all 验范围
    ...


# ========== §10.3 findall + 非捕获分组 ==========


def extract_ips(text: str) -> list[str]:
    """
    【findall · §10.3】从任意文本(告警邮件、聊天记录、整份日志)捞出所有 IP。

    任务:返回所有 IP 字符串的列表,按出现顺序,重复不去重。

    示例:
        extract_ips("from 1.2.3.4 to 10.0.0.5")  -> ["1.2.3.4", "10.0.0.5"]
        extract_ips("no ip here")                -> []

    提示:对预编译的 IP_RE 调 .findall(text),一行返回。
         IP_RE 里用了 (?:...)——删掉 ?: 再跑测试,亲眼看看返回值怎么变形。
    """
    # TODO: IP_RE.findall(text)
    ...


# ========== §10.4 命名分组 + groupdict ==========


def parse_log_line(line: str) -> dict | None:
    """
    【命名分组 · §10.4】解析一行 nginx 日志,提取 6 个字段成 dict。

    任务:合法行返回 {"ip","time","method","path","status","bytes"},
         status 和 bytes 转成 int(正则抓到的永远是字符串);非法行返回 None。

    示例:
        parse_log_line('192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234')
            -> {"ip": "192.168.1.1", "time": "10/Oct/2023:13:55:36 +0000",
                "method": "GET", "path": "/api/products", "status": 200, "bytes": 1234}
        parse_log_line("this line is malformed")   -> None

    提示:m = LOG_RE.search(line)(用 search,容忍采集器加的行首前缀)
         → m 为 None 返回 None → d = m.groupdict() 一次拿全
         → d["status"]、d["bytes"] 各包一层 int() → 返回 d。
    """
    # TODO: search + 判空 + groupdict + 两个 int 转换
    ...


# ========== §10.5 sub:反向引用 ==========


def mask_ip(text: str) -> str:
    """
    【sub + 反向引用 · §10.5】日志对外分享前脱敏:IP 保留前两段,后两段打码。

    任务:文本里每个 IP a.b.c.d 换成 a.b.*.*,其余内容原样保留。

    示例:
        mask_ip("attack from 192.168.1.1")        -> "attack from 192.168.*.*"
        mask_ip("1.2.3.4 and 10.0.0.5")           -> "1.2.*.* and 10.0.*.*"

    提示:模式里把「前两段」捕获成【命名分组】(如 (?P<net>...)),
         替换串用反向引用 r'\\g<net>.*.*' 拼回。反向引用在替换串里,替换串也要带 r。
         别用 \\1——后面跟数字时有歧义(§10.5),\\g<名字> 永远无歧义。
    """
    # TODO: re.sub(前两段命名分组的 IP 模式, r'\g<名字>.*.*', text)
    ...


# ========== §10.5 sub:函数替换 ==========


def redact_phones(text: str) -> str:
    """
    【sub + 函数替换 · §10.5】客服系统展示前,手机号中间四位打码。

    任务:每个 11 位手机号(1 开头、第二位 3-9)换成「前 3 位 + **** + 后 4 位」,
         其余内容原样保留。

    示例:
        redact_phones("call 13812345678")              -> "call 138****5678"
        redact_phones("a:13900001111 b:15800002222")   -> "a:139****1111 b:158****2222"
        redact_phones("code 12345")                    -> "code 12345"   (不是手机号,不动)

    提示:模式 \\b1[3-9]\\d{9}\\b(\\b 防 14 位长串误伤)。
         替换内容要「算」出来 → 第二参给 lambda m: ...(m.group() 是匹配到的整串,
         切片拼首尾即可)。复习 §10.5 形态 3。
    """
    # TODO: re.sub(手机号模式, lambda m: m.group() 切片拼接, text)
    ...


# ========== §10.6 re.split ==========


def parse_alert_codes(rule: str) -> list[int]:
    """
    【re.split · §10.6】解析监控系统的告警规则配置(运维手写,分隔符随缘)。

    任务:rule 里的状态码用逗号/分号/空白混合分隔,解析成 int 列表(按出现顺序)。

    示例:
        parse_alert_codes("500, 502;503")   -> [500, 502, 503]
        parse_alert_codes("500,502,")       -> [500, 502]   (尾部空串过滤掉)
        parse_alert_codes("")               -> []

    提示:re.split(r'[,;\\s]+', ...) 一次认三种分隔符;列表推导里 int(s)
         并用 if s 过滤空串碎片。想想为什么 str.split 干不了这活(§10.6)。
    """
    # TODO: re.split + 列表推导 int(s) + if s 过滤
    ...


# ========== §10.7 str 方法 vs 正则 ==========


def parse_log_text(text: str) -> list[dict]:
    """
    【splitlines + 逐行正则 · §10.7】整份日志文本 → 结构化条目列表,脏行跳过。

    任务:按行切分(text.splitlines(),\\n/\\r\\n 都认),逐行用 LOG_RE 解析,
         非法行静默跳过;返回的每个 dict 同 parse_log_line 的契约
         (status/bytes 为 int)。

    示例(nginx_logs.txt 共 13 行,第 4/10 行是脏数据):
        entries = parse_log_text(text)
        len(entries)      -> 11
        entries[0]["ip"]  -> "192.168.1.1"
        parse_log_text("") -> []

    提示:for line in text.splitlines(): 里做 §10.4 那套
         (search → None 则 continue → groupdict → 两个 int → append)。
         按行切是 str 的活,行内解析才是正则的活。
    """
    # TODO: splitlines → 逐行 search + 判空 + groupdict + int 转换 → 收集
    ...


# ========== §10.8 f-string 高级:对齐 ==========


def format_top_table(rows: list[tuple[str, int]], title: str) -> str:
    """
    【f-string 对齐 · §10.8】把 Top-N 数据 [(名字, 次数), ...] 渲染成对齐的表。

    任务:第一行 "== {title} ==",之后每行 "{名次}. {名字}{次数}" ——
         名次从 1 开始;名字列左对齐宽 16;次数列右对齐宽 5。
         行间用 "\\n" 连接,末尾不加换行。空 rows 只输出标题行。

    示例:
        format_top_table([("192.168.1.1", 3), ("10.0.0.5", 2)], "Top IP")
        ->
        == Top IP ==
        1. 192.168.1.1         3
        2. 10.0.0.5            2

    提示:f-string 格式说明 {name:<16} 左对齐宽 16、{count:>5} 右对齐宽 5;
         enumerate(rows, 1) 从 1 编号;"\\n".join(lines) 收尾。
    """
    # TODO: 标题行 + 循环拼对齐行 + "\n".join
    ...


# ========== §10.9 综合:审计快报 ==========


def build_report(text: str) -> str:
    """
    【综合 · §10.9】原始日志文本 → 排版好的审计快报(全链路:解析+统计+排版)。

    任务:解析 text(脏行跳过),统计后用 f-string 排版,返回如下 8 行文本
         (对 nginx_logs.txt 的真实结果):

        ===== 日志审计快报 =====
        有效请求: 11 条 (丢弃脏数据 2 行)
        错误率: 45.5% (5/11)
        状态码分布: 200×5 201×1 401×1 404×1 500×2 502×1
        Top 3 IP:
        1. 192.168.1.1         3
        2. 10.0.0.5            2
        3. 8.8.8.8             2

    约定:
      - 错误 = status >= 400;错误率 f-string 用 :.1%(空文本防除零,按 0.0% 输出)
      - 状态码分布按状态码数值升序,格式 "状态×次数" 空格相连
      - Top 3 用 Counter.most_common(3)(Ch08),行格式同 §10.8:
        f"{rank}. {ip:<16}{count:>5}"

    提示:splitlines → LOG_RE 逐行解析(§10.4 套路)→ Counter 两个统计
         → 列表拼各行 → "\\n".join。结构照 §10.9,注意每行文案测试会逐个验。
    """
    # TODO: 解析 → Counter 统计 → f-string 排版(防除零)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch10/ch10_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path

    log_path = Path(__file__).parent / ".." / ".." / "assets" / "mock_data" / "nginx_logs.txt"
    text = log_path.read_text(encoding="utf-8")

    print(build_report(text))
    print()
    print("白名单校验:", is_valid_ip("192.168.1.1"), is_valid_ip("256.1.1.1"))
    print("全文 IP 数:", len(extract_ips(text)))
    print("脱敏分享:", mask_ip(text.splitlines()[0]))
    print("手机号打码:", redact_phones("客户电话 13812345678,备用 13900001111"))
    print("告警规则:", parse_alert_codes("500, 502;503"))
