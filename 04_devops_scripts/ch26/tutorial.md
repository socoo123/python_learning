# Ch26 · 定时任务与日志分析:schedule + 聚合告警

> **预计**:0.5 天 ｜ **前置**:Ch10(正则)、Ch02(dict.get)｜ **M4 第 4 章**
> **目标**:监控告警的核心 pipeline——**解析日志 → 按分钟聚合 5xx → 超阈值告警 → 定时跑**。用 `schedule` 库做进程内定时(= Java `ScheduledExecutorService`),用正则 + dict 做流式聚合。

> 📐 **本教程的契约**:§26.2–§26.6 全部对应作业(5 个函数)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `extract_ts_status` | §26.2 | re.compile + search + 命名捕获 + 截断到分钟 |
| `count_5xx_per_minute` | §26.3 | 流式聚合 + dict.get(k, 0) 计数 |
| `find_spike_minutes` | §26.4 | 列表推导 + sorted 筛超阈值 |
| `build_alert_message` | §26.5 | 构造告警 dict(可序列化) |
| `schedule_job` | §26.6 | schedule.every(n).minutes.do(f) |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

① 预览猜 → ② 写 assignment(5 个函数)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. 监控告警的 pipeline 是什么?为什么不能「看到一条 5xx 就报警」?
2. 一行日志 `"2026-07-24T10:00:01 500 GET /x"`,怎么用正则把「分钟」和「状态码」抠出来?
3. 「按分钟计数」用 dict 怎么写?(`counts.get(minute, 0) + 1` 这招对应 Java 什么?)
4. `schedule` 库怎么表达「每 5 分钟跑一次」?它和系统 cron、Java `ScheduledExecutorService` 什么关系?
5. 告警消息为什么用 dict(不直接 print 字符串)?

---

## §26.1 监控告警 pipeline 🟡

监控脚本的核心是**聚合 + 阈值**,不是「单条告警」——单条错误可能是偶发,聚合后超阈值才真有问题:

```
日志流 ──► 逐行解析 ──► 按分钟聚合 5xx ──► 找超阈值分钟 ──► 生成告警 ──► 定时跑
         extract_ts_status  count_5xx_per_minute  find_spike_minutes  build_alert  schedule
```

每个环节都是一个**小函数**(可单独测),串起来就是完整 pipeline。这是运维脚本的典型架构。

> 🟡 **Java 对比**:Java 你可能用 Logstash/Fluentd 做这套,或自己写。Python 用几十行 + 标准库就能跑,这就是「胶水语言」的舒适区。

---

## §26.2 正则提取(对应:`extract_ts_status`)🟡

模块顶部已预编译正则(Ch10 学过 `re.compile` 复用):
```python
import re
_TS_STATUS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\d{3})")
```
- `(\d{4}-...:\d{2})` 第 1 组捕获时间戳。
- `\s+` 中间空白。
- `(\d{3})` 第 2 组捕获状态码。

提取逻辑:
```python
def extract_ts_status(line: str) -> tuple[str, int] | None:
    m = _TS_STATUS_RE.search(line)
    if not m:
        return None
    ts, status = m.group(1), int(m.group(2))
    return ts[:16], status       # ts[:16] 截到分钟
```

要点:
- `search`:在任意位置找(不要求从头匹配);`match` 才要求从头。日志解析用 `search` 更宽松。
- `m.group(1)` / `m.group(2)`:取捕获组内容(字符串)。
- **非法行返回 None**:解析失败不抛异常,返回 None 让上游 `continue` 跳过(EAFP 风格,运维脚本绝不为一条脏数据崩)。
- `ts[:16]`:`"2026-07-24T10:00:01"`[:16] = `"2026-07-24T10:00"`(分钟级)。切片同 Java substring。

> ✅ 做 `extract_ts_status`:`search` → 没匹配返 None → `m.group(1)`、`int(m.group(2))` → `ts[:16]`。

---

## §26.3 流式聚合(对应:`count_5xx_per_minute`)🟢

逐行解析,按分钟累加 5xx 次数:

```python
def count_5xx_per_minute(lines: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        parsed = extract_ts_status(line)
        if parsed is None:
            continue
        minute, status = parsed
        if 500 <= status < 600:                       # 5xx 才算
            counts[minute] = counts.get(minute, 0) + 1
    return counts
```

核心是 `counts.get(minute, 0) + 1`:
- key 不存在 → `get` 返回默认 0,加 1 后赋值。
- key 存在 → 取出当前值加 1。
- = Java `map.merge(minute, 1, Integer::sum)` 或 `map.getOrDefault(k,0)+1`。

> 🟢 **Java 对比**:`counts[minute] = counts.get(minute, 0) + 1` 一行顶 Java 三行(containsKey 判断 + put)。`get(k, default)` 是 Pythonic 套路。

> ✅ 做 `count_5xx_per_minute`:循环 → `extract_ts_status` 过滤 None → `500 <= status < 600` → `counts[minute] = counts.get(minute,0) + 1`。

---

## §26.4 阈值筛选(对应:`find_spike_minutes`)🟢

从聚合结果里找超阈值的分钟:

```python
def find_spike_minutes(counts: dict[str, int], threshold: int) -> list[str]:
    return sorted(m for m, c in counts.items() if c >= threshold)
```

- `counts.items()` → `(minute, count)` 对。
- 推导式筛 `c >= threshold`,取 `m`(分钟)。
- `sorted`:让结果稳定(分钟按时间排序,便于报告)。

> ✅ 做 `find_spike_minutes`:`sorted(m for m, c in counts.items() if c >= threshold)`。

---

## §26.5 告警消息(对应:`build_alert_message`)🟢

构造一个 dict(不直接 print 字符串),因为它要被序列化成 JSON 推送 webhook(Ch27):

```python
def build_alert_message(minute: str, count: int, threshold: int) -> dict:
    severity = "critical" if count >= threshold * 2 else "warning"
    return {
        "minute": minute,
        "count": count,
        "threshold": threshold,
        "severity": severity,
        "message": f"{minute} 5xx 错误数 {count} 超过阈值 {threshold}",
    }
```

设计要点:
- **返回 dict 而非字符串**:dict 能 `json.dumps` 推 webhook、能进数据库、能改格式;字符串锁死了格式。这是「数据 vs 表现」的分离(同 Ch25)。
- `severity` 分级:超阈值 2 倍算 critical,否则 warning。分级让告警系统决定要不要半夜打电话叫人。

> ✅ 做 `build_alert_message`:算 severity,返回含 5 个字段的 dict。

---

## §26.6 定时执行:schedule(对应:`schedule_job`)🟡

`schedule` 库做**进程内定时**:

```python
import schedule
def schedule_job(func, every_minutes: int):
    return schedule.every(every_minutes).minutes.do(func)
```

API 直白得像英语:`schedule.every(10).minutes.do(cleanup)` = 每 10 分钟跑 cleanup。

但要让它**真正触发**,得配一个事件循环:
```python
import time, schedule
schedule_job(cleanup, every_minutes=10)

while True:
    schedule.run_pending()    # 检查有没有到点的任务,有就跑
    time.sleep(1)
```

### schedule vs cron vs Java 定时器

| 方式 | 场景 | 特点 |
|------|------|------|
| **schedule 库** | 脚本进程内 | 简单,但**进程挂了就停**(单点) |
| **系统 cron / systemd timer** | 生产部署 | 系统级可靠,不依赖你的进程 |
| **Java ScheduledExecutorService** | Java 应用内 | = schedule 库,应用内定时 |

> 🟡 **Java 对比**:`schedule.every(n).minutes.do(f)` ≈ `ScheduledExecutorService.scheduleAtFixedRate(f, 0, n, MINUTES)`。Python 更声明式。
>
> ⚠️ 生产监控**别只靠 schedule**(进程挂就停)。要么用 systemd timer/cron 兜底,要么用 Celery/ARQ 等任务队列。schedule 适合轻量单机。

> ✅ 做 `schedule_job`:`import schedule; return schedule.every(every_minutes).minutes.do(func)`。

---

## §26.7 实战:日志报警器(讲透不出题)

串成完整脚本:

```python
def alert_on_spikes(log_file: Path, threshold: int = 3) -> list[dict]:
    """读日志 → 聚合 5xx → 超阈值的分钟生成告警。"""
    lines = log_file.read_text(encoding="utf-8").splitlines()
    counts = count_5xx_per_minute(lines)              # §26.3
    return [
        build_alert_message(m, counts[m], threshold)  # §26.5
        for m in find_spike_minutes(counts, threshold)  # §26.4
    ]

if __name__ == "__main__":
    alerts = alert_on_spikes(Path("server.log"), threshold=3)
    for a in alerts:
        print(a)
    # 定时跑(每 5 分钟检查一次):
    # schedule_job(lambda: alert_on_spikes(Path("server.log")), every_minutes=5)
```

> 🔴 真实生产:告警生成后调 `send_webhook`(Ch27 §27.5)推到飞书/钉钉,而不是 print。

---

## §26.8 Java 老手常踩的坑 ⚠️

1. **单条错误就报警**:偶发错误会刷屏。要**聚合 + 阈值**(按分钟/按窗口计数)。
2. **`match` vs `search`**:`match` 只匹配**开头**,日志中间才有目标时要用 `search`。
3. **非法行抛异常拖垮脚本**:解析失败要返回 None/跳过,别让一条脏数据让整个脚本崩。
4. **忘 `sorted` 让结果不稳定**:dict 遍历顺序虽 3.7+ 保持插入序,但跨运行可能不同;排序后报告才一致。
5. **schedule 进程挂就停**:生产用 schedule 要配合 systemd/supervisor 守护,或用 cron/任务队列。
6. **告警直接 print 字符串**:锁死格式。返回 dict,序列化后能推 webhook、入库、改格式。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `extract_ts_status` | re.search + 捕获组 + 截断 | 🟡 |
| `count_5xx_per_minute` | dict.get(k,0)+1 流式聚合 | 🟢 |
| `find_spike_minutes` | 推导 + sorted 筛阈值 | 🟢 |
| `build_alert_message` | 构造告警 dict | 🟢 |
| `schedule_job` | schedule.every().minutes.do() | 🟢 |

```bash
uv run pytest 04_devops_scripts/ch26/test_ch26_assignment.py -v
```

全绿 = 掌握 Ch26。

---

## ✅ 自测

- [ ] 能说清监控告警 pipeline 的 5 个环节
- [ ] 会用 `re.search` + 捕获组抠字段,非法行返回 None
- [ ] 能用 `dict.get(k, 0) + 1` 一行做流式聚合(对应 Java merge)
- [ ] 知道 schedule 库的局限(进程挂就停),生产怎么兜底
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「为什么监控不能单条告警,要按分钟聚合 + 阈值?」— 重读 §26.1
2. 「`re.match` 和 `re.search` 区别?日志解析为什么用 search?」— 重读 §26.2/§26.8
3. 「`schedule` 库和系统 cron 各适合什么场景?为什么生产不能只靠 schedule?」— 重读 §26.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch27 配置管理与系统监控

聚合告警会做了,最后把 M4 收尾——**系统巡检**:检查磁盘/内存水位,异常时推 webhook 告警(钉钉/飞书)。把 Ch24 的 psutil + 本章的告警 + 配置管理串成生产级巡检脚本。
