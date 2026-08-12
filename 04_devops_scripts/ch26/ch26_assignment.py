"""
Ch26 作业:定时任务与日志分析 —— schedule + 聚合告警。

监控告警的核心 pipeline:① 解析日志流 → ② 按分钟聚合 5xx → ③ 超阈值筛分钟 →
④ 生成结构化告警(dict)→ ⑤ 格式化成报告 → ⑥ 定时跑。
schedule 库做进程内定时(= Java ScheduledExecutorService);聚合用纯正则 + dict。

7 个函数。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch26/test_ch26_assignment.py -v

全绿 = 你掌握了 Ch26。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

日志行格式约定(server.log 一行一条):
    "2026-07-24T10:00:01 500 GET /api/orders"
     └── 时间戳 ──┘ └状态┘ └方法┘ └─路径─┘
    分钟 = 时间戳前 16 个字符("2026-07-24T10:00")。
"""
import re

# 预编译正则(Ch10 学过:compile 复用,性能好)。匹配「时间戳 状态码」。
# 时间戳:YYYY-MM-DDTHH:MM:SS(第 1 组);状态码:3 位数字(第 2 组)。
_TS_STATUS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\d{3})")


# ========== §26.2 正则提取:extract_ts_status ==========


def extract_ts_status(line: str) -> tuple[str, int] | None:
    """
    【正则 · §26.2】从一行日志提取 (分钟级时间戳, 状态码),非法行返回 None。

    示例:
        extract_ts_status("2026-07-24T10:00:01 500 GET /api")
            -> ("2026-07-24T10:00", 500)        # 分钟=时间戳前16字符
        extract_ts_status("2026-07-24T10:00:59 200 GET /")
            -> ("2026-07-24T10:00", 200)        # 同一分钟,秒不同分钟相同
        extract_ts_status("乱七八糟") -> None      # 脏数据不抛异常

    思路(用模块顶部的 _TS_STATUS_RE):
        m = _TS_STATUS_RE.search(line)            # search:任意位置找(match 只从开头)
        if not m:
            return None                            # 非法行返回 None,上游跳过
        ts, status = m.group(1), int(m.group(2))  # group(1)=时间戳 group(2)=状态码
        return ts[:16], status                     # ts[:16] 截到分钟
    """
    # TODO: _TS_STATUS_RE.search → 没匹配返 None → m.group(1)、int(m.group(2)) → ts[:16] 截到分钟
    ...


# ========== §26.3 聚合:count_5xx_per_minute ==========


def count_5xx_per_minute(lines: list[str]) -> dict[str, int]:
    """
    【聚合 · §26.3】按分钟统计 5xx(500~599)错误数,返回 {分钟: 错误数}。
    非法行跳过,非 5xx(2xx/3xx/4xx)不计入。

    示例:
        count_5xx_per_minute([
            "2026-07-24T10:00:01 500 GET /",
            "2026-07-24T10:00:30 503 GET /x",
            "2026-07-24T10:00:45 200 GET /y",   # 2xx 不计
            "2026-07-24T10:01:05 500 GET /z",
        ]) -> {"2026-07-24T10:00": 2, "2026-07-24T10:01": 1}
        count_5xx_per_minute([]) -> {}

    思路(流式聚合,复用 extract_ts_status):
        counts: dict[str, int] = {}
        for line in lines:
            parsed = extract_ts_status(line)
            if parsed is None:
                continue
            minute, status = parsed
            if 500 <= status < 600:                  # 5xx 才算(链式比较)
                counts[minute] = counts.get(minute, 0) + 1
        return counts
        - counts.get(minute, 0) + 1:Java map.merge 思路,不存在当 0
    """
    # TODO: 循环 lines,extract_ts_status 过滤 None,5xx 用 counts.get(minute,0)+1 累加
    ...


# ========== §26.4 阈值:find_spike_minutes ==========


def find_spike_minutes(counts: dict[str, int], threshold: int) -> list[str]:
    """
    【阈值 · §26.4】从「分钟→错误数」里找出错误数 >= threshold 的分钟,返回排序后的列表。

    示例:
        counts = {"2026-07-24T10:00": 5, "2026-07-24T10:01": 1}
        find_spike_minutes(counts, threshold=3)  -> ["2026-07-24T10:00"]   # 只有 10:00 达标
        find_spike_minutes(counts, threshold=1)  -> ["2026-07-24T10:00", "2026-07-24T10:01"]
        find_spike_minutes(counts, threshold=99) -> []                      # 没超标

    思路(生成器推导 + 排序,让结果稳定):
        return sorted(m for m, c in counts.items() if c >= threshold)
        - 注意是 >=(达到阈值就告),不是 >
    """
    # TODO: 推导筛 c >= threshold 的 minute,sorted 返回
    ...


# ========== §26.5 告警:build_alert_message ==========


def build_alert_message(minute: str, count: int, threshold: int) -> dict:
    """
    【告警 · §26.5】构造一条报警消息(dict,方便后续序列化成 json 推送 webhook)。
    severity:count >= threshold*2 算 critical,否则 warning。

    示例:
        build_alert_message("2026-07-24T10:00", 5, 3)
            -> {"minute": "2026-07-24T10:00", "count": 5, "threshold": 3,
                "severity": "warning",                       # 5 < 3*2=6
                "message": "2026-07-24T10:00 5xx 错误数 5 超过阈值 3"}
        build_alert_message("2026-07-24T10:00", 6, 3)["severity"]
            -> "critical"                                    # 6 >= 3*2

    思路(数据 vs 表现分离:返回 dict 不 print 字符串):
        severity = "critical" if count >= threshold * 2 else "warning"
        return {
            "minute": minute,
            "count": count,
            "threshold": threshold,
            "severity": severity,
            "message": f"{minute} 5xx 错误数 {count} 超过阈值 {threshold}",
        }
    """
    # TODO: 算 severity(2 倍阈值分界),返回含 minute/count/threshold/severity/message 的 dict
    ...


# ========== §26.6 综合:alert_on_spikes ==========


def alert_on_spikes(lines: list[str], threshold: int = 3) -> list[dict]:
    """
    【综合 · §26.6】串起完整 pipeline:吃进日志行,吐出告警 dict 列表。
    复用前 4 个函数:聚合 → 筛超标分钟 → 逐分钟生成告警。

    示例(10:00 有 5 个 5xx、10:01 有 1 个):
        alert_on_spikes(lines, threshold=3)
            -> [{"minute": "2026-07-24T10:00", "count": 5, ..., "severity": "warning"}]
            # 只有 10:00 达标(5>=3),1 条告警
        alert_on_spikes(lines, threshold=1)
            -> [ {...10:00...}, {...10:01...} ]              # 都达标,2 条告警

    思路(小函数 + 组合;注意 counts[m] 回查错误数):
        counts = count_5xx_per_minute(lines)                 # §26.3
        return [
            build_alert_message(m, counts[m], threshold)     # §26.5
            for m in find_spike_minutes(counts, threshold)   # §26.4
        ]
    """
    # TODO: counts = count_5xx_per_minute(lines);列表推导对 find_spike_minutes 结果逐个 build_alert_message(m, counts[m], threshold)
    ...


# ========== §26.7 输出:format_report ==========


def format_report(alerts: list[dict]) -> str:
    """
    【输出 · §26.7】把告警 dict 列表格式化成多行文本报告(数据 → 表现)。
    空列表返回「系统正常」文案;否则标题行(含条数)+ 每条告警一行。

    示例:
        format_report([]) -> "✅ 系统正常:无 5xx 超阈值告警"
        format_report([{"minute": "2026-07-24T10:00", "count": 5,
                        "threshold": 3, "severity": "warning", "message": "..."}])
            -> "🚨 5xx 告警报告(共 1 条)\\n[warning] 2026-07-24T10:00 5xx=5 (阈值 3)"

    思路:
        if not alerts:
            return "✅ 系统正常:无 5xx 超阈值告警"
        lines = [f"🚨 5xx 告警报告(共 {len(alerts)} 条)"]
        for a in alerts:
            lines.append(f"[{a['severity']}] {a['minute']} 5xx={a['count']} (阈值 {a['threshold']})")
        return "\\n".join(lines)              # "\\n".join = Java String.join
    """
    # TODO: 空列表返回正常文案;否则标题行(含条数)+ 每条一行 [severity] minute 5xx=count (阈值 threshold),"\n".join 拼接
    ...


# ========== §26.8 定时:schedule_job ==========


def schedule_job(func, every_minutes: int):
    """
    【schedule · §26.8】注册一个每 every_minutes 分钟执行一次的任务,返回 schedule.Job。

    示例:
        job = schedule_job(cleanup, every_minutes=30)
        job.interval  -> 30
        job.unit      -> "minutes"

    思路(对比 Java ScheduledExecutorService.scheduleAtFixedRate):
        import schedule
        return schedule.every(every_minutes).minutes.do(func)
        - schedule.every(n).minutes.do(f):每 n 分钟跑 f(声明式)
        - 进程内定时;脚本要配 while True + schedule.run_pending() 才真正触发
        - 进程挂了就停(单点),生产用 cron/systemd/任务队列兜底
    """
    # TODO: import schedule; return schedule.every(every_minutes).minutes.do(func)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch26/ch26_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    lines = load_mock_json("server_logs.json")
    counts = count_5xx_per_minute(lines)
    print("5xx per minute:", counts)

    alerts = alert_on_spikes(lines, threshold=3)
    print(format_report(alerts))

    # 定时跑(每 5 分钟检查一次,真实部署改用 cron/systemd 兜底):
    # schedule_job(lambda: print(format_report(alert_on_spikes(lines))), every_minutes=5)
