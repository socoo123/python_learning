"""
Ch26 作业:定时任务与日志分析 —— schedule + 聚合告警。

监控告警的核心:① 解析日志流 → ② 按分钟聚合 5xx → ③ 超阈值生成告警 → ④ 定时跑。
schedule 库做进程内定时(= Java ScheduledExecutorService);聚合用纯正则 + dict。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch26/test_ch26_assignment.py -v

全绿 = 你掌握了 Ch26。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

日志行格式约定:
    "2026-07-24T10:00:01 500 GET /api/orders"
     └── 时间戳 ──┘ └状态┘ └方法┘ └─路径─┘
    分钟 = 时间戳前 16 个字符("2026-07-24T10:00")。
"""
import re

# 预编译正则(Ch10 学过:compile 复用,性能好)。匹配「时间戳 状态码」。
# 时间戳:YYYY-MM-DDTHH:MM:SS;状态码:3 位数字。用 group 捕获。
_TS_STATUS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\d{3})")


# ========== §26.2 正则提取:extract_ts_status ==========


def extract_ts_status(line: str) -> tuple[str, int] | None:
    """
    【正则 · §26.2】从一行日志提取 (分钟级时间戳, 状态码),非法行返回 None。

    示例:
        extract_ts_status("2026-07-24T10:00:01 500 GET /api")
            -> ("2026-07-24T10:00", 500)        # 分钟=时间戳前16字符
        extract_ts_status("乱七八糟") -> None

    思路(用模块顶部的 _TS_STATUS_RE):
        m = _TS_STATUS_RE.search(line)
        if not m:
            return None
        ts, status = m.group(1), int(m.group(2))   # group(1)=时间戳 group(2)=状态码
        return ts[:16], status                       # 截到分钟
    """
    # TODO: _TS_STATUS_RE.search → 取两个 group → ts[:16] + int(status)
    ...


# ========== §26.3 聚合:count_5xx_per_minute ==========


def count_5xx_per_minute(lines: list[str]) -> dict[str, int]:
    """
    【聚合 · §26.3】按分钟统计 5xx(500~599)错误数,返回 {分钟: 错误数}。
    非法行跳过,非 5xx 不计入。

    示例(10:00 有 5 个 5xx,10:01 有 1 个):
        count_5xx_per_minute(lines) -> {"2026-07-24T10:00": 5, "2026-07-24T10:01": 1}

    思路(流式聚合,复用 extract_ts_status):
        counts: dict[str, int] = {}
        for line in lines:
            parsed = extract_ts_status(line)
            if parsed is None:
                continue
            minute, status = parsed
            if 500 <= status < 600:                  # 5xx 才算
                counts[minute] = counts.get(minute, 0) + 1
        return counts
        - counts.get(minute, 0) + 1:Java map.merge 思路,不存在当 0
    """
    # TODO: 循环 lines,extract_ts_status 过滤,5xx 用 get(minute,0)+1 累加
    ...


# ========== §26.4 阈值:find_spike_minutes ==========


def find_spike_minutes(counts: dict[str, int], threshold: int) -> list[str]:
    """
    【阈值 · §26.4】从「分钟→错误数」里找出错误数 >= threshold 的分钟,返回排序后的列表。

    示例:
        counts = {"10:00": 5, "10:01": 1}
        find_spike_minutes(counts, threshold=3)  -> ["10:00"]      # 只有 10:00 超标
        find_spike_minutes(counts, threshold=1)  -> ["10:00", "10:01"]

    思路(列表推导 + 排序,让结果稳定):
        return sorted(m for m, c in counts.items() if c >= threshold)
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
            -> {"minute": "...", "count": 5, "threshold": 3,
                "severity": "warning", "message": "...10:00 5xx 错误数 5 超过阈值 3"}

    思路:
        severity = "critical" if count >= threshold * 2 else "warning"
        return {
            "minute": minute,
            "count": count,
            "threshold": threshold,
            "severity": severity,
            "message": f"{minute} 5xx 错误数 {count} 超过阈值 {threshold}",
        }
    """
    # TODO: 算 severity,返回含 minute/count/threshold/severity/message 的 dict
    ...


# ========== §26.6 定时:schedule_job ==========


def schedule_job(func, every_minutes: int):
    """
    【schedule · §26.6】注册一个每 every_minutes 分钟执行一次的任务,返回 schedule.Job。

    示例:
        job = schedule_job(cleanup, every_minutes=30)
        job.interval  -> 30
        job.unit      -> "minutes"

    思路(对比 Java ScheduledExecutorService.scheduleAtFixedRate):
        import schedule
        return schedule.every(every_minutes).minutes.do(func)
        - schedule.every(n).minutes.do(f):每 n 分钟跑 f
        - 进程内定时;脚本要配 while True + schedule.run_pending() 才真正触发
    """
    # TODO: import schedule; schedule.every(every_minutes).minutes.do(func)
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
    for minute in find_spike_minutes(counts, threshold=3):
        print("ALERT:", build_alert_message(minute, counts[minute], 3))
