# Ch27 · 配置管理与系统监控:psutil 巡检 + webhook 告警

> **预计**:0.5 天 ｜ **前置**:Ch24(psutil)、Ch12(配置/环境变量)、Ch26(告警)｜ **M4 收官**
> **目标**:把 M4 串成生产级**系统巡检脚本**——配置分层(默认 < 环境变量)→ 检查磁盘/内存水位 → 汇总健康报告 → 异常时推 webhook 告警(飞书/钉钉/Slack)。这是 M4 的毕业项目。

> 📐 **本教程的契约**:§27.2–§27.5 全部对应作业(5 个函数)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `load_thresholds` | §27.2 | 配置分层:默认 < 环境变量 + 类型转换 |
| `check_disk` | §27.3 | psutil.disk_usage + 阈值判断 |
| `check_memory` | §27.3 | psutil.virtual_memory + 阈值判断 |
| `build_health_report` | §27.4 | all() 聚合多项检查 |
| `send_webhook` | §27.5 | urllib POST JSON + EAFP 绝不抛 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

① 预览猜 → ② 写 assignment(5 个函数)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. 不同环境(开发/生产)磁盘告警阈值不同。怎么让阈值「可配置」且带默认值?(Ch12、Ch22 学过)
2. 环境变量读出来都是字符串 `"95"`,怎么变成 `95.0`?
3. 「磁盘水位 + 内存水位」两项检查,怎么汇总成一个「整体健康与否」?
4. Python 推 webhook(POST JSON)用 stdlib 怎么写?要不要引 requests?
5. 告警推送网络可能失败——怎么让它「绝不抛异常,只返回成功/失败」?

---

## §27.1 系统巡检的整体架构 🟡

生产巡检脚本的标准结构:

```
配置(load_thresholds)         ← 阈值从环境变量读,带默认
   │
   ├─ check_disk               ← psutil 读磁盘
   ├─ check_memory             ← psutil 读内存
   │
build_health_report            ← all() 汇总成「整体健康」
   │
   └─ 不健康 → send_webhook    ← urllib POST 到飞书/钉钉
```

每一步都是小函数(可测),串起来就是生产脚本。注意贯穿全局的两个原则:
- **配置外置**:阈值不写死,走环境变量。
- **绝不崩**:任何一步失败都返回明确的 bool/dict,不让脚本挂掉(挂了就漏告警)。

> 🟡 **Java 对比**:Spring Boot 用 `@ConfigurationProperties` + `application-{env}.yml` + Actuator `/health`。本章手写实现同等能力,让你理解底层;Ch22 的 pydantic-settings 是 Spring Boot 那套的 Python 版。

---

## §27.2 配置分层(对应:`load_thresholds`)🟡

**铁律**:阈值/告警 URL/敏感配置**绝不写死在代码**,走配置。最简单的分层是「默认值 < 环境变量覆盖」:

```python
def load_thresholds(env: dict) -> dict:
    result = {"disk": 80.0, "memory": 80.0, "cpu": 90.0}   # 默认值
    if "DISK_THRESHOLD" in env:
        result["disk"] = float(env["DISK_THRESHOLD"])      # env 覆盖 + 转 float
    if "MEMORY_THRESHOLD" in env:
        result["memory"] = float(env["MEMORY_THRESHOLD"])
    if "CPU_THRESHOLD" in env:
        result["cpu"] = float(env["CPU_THRESHOLD"])
    return result
```

要点:
- **默认兜底**:没配就用默认(80%),脚本开箱即用。
- **env 覆盖**:生产环境设 `DISK_THRESHOLD=90` 就调整,不用改代码、重新部署。
- **`float()` 类型转换**:环境变量读出来**永远是字符串**(`"95"`),必须转成 float 才能比较(Ch12 §12.4 踩过)。这是配置层最经典的坑。

> 🟡 **Java 对比**:= Spring 的 `@Value("${disk.threshold:80}")`(默认值语法)+ 自动类型转换。Python 手写更显式。
>
> 🔴 **生产升级版**:Ch22 学的 `pydantic-settings` 的 `BaseSettings` 自动做这套(读环境变量 + 类型校验 + 默认值 + 缺必填 fail-fast)。这里手写加固理解;真实项目用 pydantic-settings。

> ✅ 做 `load_thresholds`:默认 dict + 三个 `if KEY in env: result[...] = float(env[KEY])`。

---

## §27.3 水位检查(对应:`check_disk`、`check_memory`)🟢

复用 Ch24 的 psutil,加阈值判断:

```python
def check_disk(path: str = "/", threshold: float = 80.0) -> dict:
    import psutil
    du = psutil.disk_usage(path)
    return {
        "percent": du.percent,
        "free_gb": round(du.free / (1024 ** 3), 2),
        "total_gb": round(du.total / (1024 ** 3), 2),
        "ok": du.percent < threshold,        # 低于阈值=健康
    }

def check_memory(threshold: float = 80.0) -> dict:
    import psutil
    vm = psutil.virtual_memory()
    return {"percent": vm.percent, "ok": vm.percent < threshold}
```

设计要点:
- **返回 dict 带 `ok` 键**:不只返回数字,直接给出「健不健康」的判断(`ok`),上游用起来简单。
- `round(x, 2)`:GB 保留 2 位小数,报告干净。
- `du.percent < threshold`:< 阈值=健康。阈值从配置来(§27.2)。

> ✅ 做 `check_disk`:`psutil.disk_usage(path)` → 组装含 percent/free_gb/total_gb/ok 的 dict。
> 做 `check_memory`:`psutil.virtual_memory()` → 返回 {percent, ok}。

---

## §27.4 汇总健康报告(对应:`build_health_report`)🟢

多项检查汇总成「整体健康与否」:

```python
def build_health_report(checks: dict) -> dict:
    return {
        "overall_ok": all(c.get("ok", False) for c in checks.values()),
        "checks": checks,
    }
```

- `all(...)`:所有检查的 `ok` 都为 True 才整体健康。= Java `stream.allMatch(...)`。
- `c.get("ok", False)`:某个检查 dict 没有 `ok` 键时默认 False(健壮性,防止脏数据漏判)。
- **空 checks → `all([])` 返回 True**(vacuous truth,数学约定):没检查就视为没毛病。记住这个语义。

> ✅ 做 `build_health_report`:`all(c.get("ok", False) for c in checks.values())`,返回 {overall_ok, checks}。

---

## §27.5 webhook 告警(对应:`send_webhook`)🔴

不健康时推 webhook(飞书/钉钉/Slack 都是 HTTP POST JSON)。用 **stdlib urllib**,不引 requests(零依赖):

```python
def send_webhook(url: str, payload: dict, timeout: float = 5.0) -> bool:
    import json as _json
    import urllib.request
    data = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300       # 2xx 算成功
    except Exception:
        return False                              # 任何异常都返回 False,绝不抛
```

关键设计:
- **`json.dumps(...).encode("utf-8")`**:payload dict → JSON 字符串 → bytes(网络传字节)。
- **`Request(url, data=..., method="POST")`**:有 `data` 才是 POST(否则 GET);显式 `method="POST"` 更清晰。
- **`Content-Type: application/json`**:告诉服务器 body 是 JSON,不加的话对方不认。
- **`except Exception: return False`**(EAFP,Ch07):网络抖动、超时、DNS 失败……webhook 推送**绝不**让巡检脚本崩——崩了下次就不巡检了。失败返回 False,记日志即可。
- **`2xx` 判断**:webhook 服务器返回 200 才算送达(飞书成功返回 200 + errno=0,严谨还要看 body,这里简化)。

> 🟡 **Java 对比**:= `HttpClient` + `BodyPublishers.ofString(json)` + try/catch IOException。Python urllib 是 stdlib 自带,不引三方。
>
> 🔴 **为什么不引 requests**:requests 更好用但要装;urllib 零依赖,巡检脚本越少依赖越好部署(尤其跑在受限服务器)。简单 POST 用 urllib 足够。

> ✅ 做 `send_webhook`:`dumps→encode→Request(POST, json 头)→urlopen`,2xx 返 True,`except Exception: return False`。

---

## §27.6 实战:完整巡检脚本(讲透不出题)

本章的 `__main__` 段已经是完整脚本,读它对照:

```python
thresholds = load_thresholds({"DISK_THRESHOLD": "70"})       # §27.2 配置
disk = check_disk("/", threshold=thresholds["disk"])          # §27.3
mem = check_memory(threshold=thresholds["memory"])            # §27.3
report = build_health_report({"disk": disk, "memory": mem})   # §27.4
if not report["overall_ok"]:
    send_webhook(WEBHOOK_URL, report)                         # §27.5 异常才推
```

加上 Ch26 的 `schedule_job` 定时,就是一个能跑的巡检服务:

```python
def run_inspection():
    # ... 上面的逻辑 ...
    pass

if __name__ == "__main__":
    schedule_job(run_inspection, every_minutes=5)   # 每 5 分钟巡检一次(Ch26)
    while True:
        schedule.run_pending()
        time.sleep(1)
```

> 🔴 生产化:① 用 systemd/supervisor 守护进程;② webhook URL 也走环境变量;③ 多次失败要「告警升级」(电话叫人);④ 加日志(Ch12)。

---

## §27.7 Java 老手常踩的坑 ⚠️

1. **环境变量是字符串**:`os.environ["X"]` / `env["X"]` 读出来永远是 str。要比较数字必须 `int()`/`float()`。否则 `"95" < 80` 是字符串比较,结果错得离谱。
2. **阈值写死在代码**:改阈值要改代码重发版。走环境变量/配置文件。
3. **webhook 抛异常拖垮巡检**:网络调用必须 try/except,失败返回 False + 记日志,**绝不**让脚本挂(挂了就漏告警)。
4. **忘 `Content-Type: application/json`**:服务器把 JSON body 当普通文本,解析失败。
5. **忘 `timeout`**:`urllib.request.urlopen` 默认可能长时间挂起。网络调用必设 timeout。
6. **裸 `except:` 吞一切**:虽然 webhook 这里 `except Exception` 是刻意的,但别滥用裸 except(会吞 KeyboardInterrupt 等)。用 `except Exception` 限定。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `load_thresholds` | 配置分层 + float 转换 | 🟡 |
| `check_disk` | psutil.disk_usage + 阈值 | 🟢 |
| `check_memory` | psutil.virtual_memory + 阈值 | 🟢 |
| `build_health_report` | all() 聚合 | 🟢 |
| `send_webhook` | urllib POST JSON + EAFP | 🔴 |

```bash
uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v
```

全绿 = 掌握 Ch27 = **M4 运维脚本毕业** 🎓。

---

## ✅ 自测

- [ ] 能说清配置分层(默认 < 环境变量)和为什么环境变量要类型转换
- [ ] 会用 psutil 检查磁盘/内存水位并判断是否超阈
- [ ] 能用 `all()` 汇总多项检查,知道空 checks 的 `all` 语义
- [ ] 会用 stdlib urllib POST JSON webhook,且绝不抛异常(EAFP)
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「环境变量读出来是什么类型?为什么配置层要做类型转换?不转会怎样?」— 重读 §27.2/§27.7
2. 「webhook 推送为什么必须 try/except 返回 bool,而不是让它抛异常?」— 重读 §27.5
3. 「`all([])` 返回什么?为什么 build_health_report 空检查视为健康?」— 重读 §27.4

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ M4 毕业 → M5 AI 框架

恭喜!**Ch23–27 全部学完,M4 运维脚本模块毕业** 🎓。你现在能:
- 文件批处理(pathlib/shutil)→ 调外部命令 + 系统监控(subprocess/psutil)→ 写漂亮 CLI(Typer/Rich)→ 日志聚合告警(schedule + 正则)→ 系统巡检 + webhook 告警。

这是 Python 相对 Java 的**舒适区**——胶水语言、运维利器,几十行干 Java 几百行的活。

下一站 **M5 AI 框架**(Ch28–33)⭐:LLM 调用 → Prompt 工程 → LangChain → RAG 向量检索 → Agent 工具调用 → FastAPI 封装 AI 服务。这是你点名的核心方向,也是当下最热的 Python 应用领域。
