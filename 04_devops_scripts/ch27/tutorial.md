# Ch27 · 配置管理与系统监控:psutil 巡检 + webhook 告警

> **预计**:0.5 天 ｜ **前置**:Ch24(psutil)、Ch12(配置/环境变量)、Ch26(告警 pipeline)｜ **M4 收官**
> **目标**:把 M4 串成生产级**系统巡检脚本**——配置分层(默认 < 环境变量)→ 检查磁盘/内存/CPU 水位 + 关键端口探活 → 汇总健康报告 → 异常时推 webhook 告警(飞书/钉钉/Slack)。
> **本章主线**:你是电商后端的 on-call 工程师。上周一台订单服务器磁盘写满,直到支付失败才发现。你决定写一个「**巡检脚本**」:阈值走环境变量(生产/测试不同水位),每 5 分钟检查磁盘/内存/CPU + 依赖的 DB 端口,汇总成健康报告,任何一项超阈值就把报告 POST 到飞书群。8 个函数全为这条主线服务,最后 1 题把前 7 个组装成完整巡检。

> 📐 **本教程的契约**:§27.2–§27.7 每节**精确对应**作业里的函数,讲过的才考,考的必讲过。§27.1 是开胃、§27.8 生产化与 §27.9 坑清单讲透不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 用「默认 dict + 环境变量覆盖 + `float()` 转换」手写配置分层,并说清生产上为什么交给 pydantic-settings
- 用 `psutil.disk_usage` / `virtual_memory` / `cpu_percent` 采集水位,挂阈值判断,避开「字节当 GB」「cpu_percent 首次为 0」两个坑
- 用 `socket.create_connection` 给关键端口做探活,并说清为什么必须带 `timeout`
- 用 `all()` 把多项检查汇总成「整体健康」,说清 `all([])` 的语义
- 用 stdlib `urllib` POST JSON webhook,做到**绝不抛异常**(EAFP)
- 把 7 个小函数组装成 `run_inspection`,并说清「模块级小函数」为什么天生好测(可 monkeypatch)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `load_thresholds` | §27.2 | 配置分层:默认 < 环境变量 + float 转换 |
| `check_disk` | §27.3 | psutil.disk_usage + 字节转 GB + 阈值判断 |
| `check_memory` | §27.3 | psutil.virtual_memory + 阈值判断 |
| `check_cpu` | §27.3 | psutil.cpu_percent(interval) 采样 |
| `check_port` | §27.4 | socket.create_connection + timeout + EAFP |
| `build_health_report` | §27.5 | all() 聚合 + get("ok", False) 防御 |
| `send_webhook` | §27.6 | urllib POST JSON + 2xx 判定 + 绝不抛 |
| `run_inspection` | §27.7 | 综合:复用前 7 个函数组装巡检 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 6 个问题,先猜答案 | 本页 ① |
| ② 先动手 | 打开 `ch27_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「配置分层、EAFP 告警、数据 vs 表现」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(先想,别急着翻答案)

1. 开发环境磁盘阈值 80%、生产 90%。怎么让阈值「可配置」且带默认值?环境变量 `"90"` 读出来是什么类型?
2. `psutil.disk_usage("/")` 返回的 `free` 是 GB 还是字节?`cpu_percent()` 第一次调用为什么可能返回 0.0?
3. 检查「DB 的 5432 端口通不通」,不用 subprocess 调 `nc`,stdlib 怎么写?忘了 `timeout` 会怎样?
4. 「磁盘 + 内存 + CPU」三项检查,怎么一行汇总成「整体健康与否」?空检查列表算健康吗?
5. 推飞书 webhook(POST JSON)用 stdlib `urllib` 怎么写?为什么宁愿麻烦也不 `pip install requests`?
6. webhook 推送时网络抖动——这一步骤能允许抛异常吗?为什么?

> 猜完带着验证心态进入正文。第 5、6 题的「绝不抛异常」是 🔴,是巡检脚本敢放上生产的底线。

---

## §27.1 巡检脚本架构(开胃 · 不出题)🟡

生产巡检脚本的标准结构,每个环节都是一个**小函数**(可单独测、可 monkeypatch):

```
配置 load_thresholds          ← 阈值:默认 < 环境变量
   │
   ├─ check_disk / check_memory / check_cpu   ← psutil 采水位,挂阈值
   ├─ check_port                                ← socket 探活关键端口
   │
build_health_report            ← all() 汇总成「整体健康」
   │
   └─ 不健康 → send_webhook     ← urllib POST 到飞书/钉钉
        ▲
run_inspection                 ← 把以上全部串起来(综合题)
```

贯穿全局的两条原则:
- **配置外置**:阈值、webhook URL 绝不写死,走环境变量——改配置不用改代码、不用重新部署。
- **绝不崩**:任何一步失败都返回明确的 bool/dict,不让脚本挂掉——巡检脚本崩了,等于监控瞎了。

> 🟡 **Java 对比**:Spring Boot 用 `@ConfigurationProperties` + `application-{env}.yml` 管配置,Actuator `/health` 做健康检查,再外挂 Prometheus + Alertmanager 告警。这套很重;Python 手写几十行就能得到同等能力的轻量版——这正是「胶水语言」的舒适区。生产升级版 pydantic-settings 见 §27.2 末尾。

---

## §27.2 配置分层:默认 < 环境变量(对应:`load_thresholds`)🟡

**铁律**:阈值/告警 URL/敏感配置**绝不写死在代码里**。最简单的分层就两层:**默认值兜底,环境变量覆盖**。

### Java 对照最小例

```java
// Java(Spring):@Value 注进来,冒号后是默认值,自动类型转换
@Value("${disk.threshold:80}")
private double diskThreshold;
```

```python
# Python(stdlib 手写版):默认 dict + env 覆盖 + float 转换
def load_thresholds(env: dict) -> dict:
    result = {"disk": 80.0, "memory": 80.0, "cpu": 90.0}   # ① 默认值兜底
    if "DISK_THRESHOLD" in env:
        result["disk"] = float(env["DISK_THRESHOLD"])      # ② env 覆盖 + 转 float
    if "MEMORY_THRESHOLD" in env:
        result["memory"] = float(env["MEMORY_THRESHOLD"])
    if "CPU_THRESHOLD" in env:
        result["cpu"] = float(env["CPU_THRESHOLD"])
    return result
```

三个要点:
- **入参是 `env: dict` 而不是直接读 `os.environ`**:测试时传 `{"DISK_THRESHOLD": "95"}` 就行,不用 `monkeypatch.setenv`,也不用污染真实环境。真实运行时传 `dict(os.environ)`(见 §27.8)。这是「依赖注入」的迷你版——**依赖当参数传,不在函数里抓全局**。
- **`float()` 转换**:环境变量读出来**永远是字符串** `"95"`,不转没法和数字阈值比较。这是配置层最经典的坑,见下面的错误对照。
- **没配就用默认**:脚本开箱即用,新机器零配置跑起来。

### ❌ → ✅ 错误对照:环境变量的类型坑

❌ **错误写法 1**(str 和 int 直接比,Python 3 直接崩):

```python
if float(os.environ["DISK_THRESHOLD"]) ... # 先记住:os.environ["DISK_THRESHOLD"] 是 str
os.environ["DISK_THRESHOLD"] < 80          # TypeError: '<' not supported between 'str' and 'int'
```

❌ **错误写法 2**(两边都是 str,不崩但**结果错得离谱**——字典序比较):

```python
"95" < "80"     # False!"9" 的字典序大于 "8",磁盘都 95% 了还认为没超 80%
"100" < "80"    # True!"1" < "8",100% 反而"小于"80%
```

✅ **正确写法**(先 `float()` 再比较):

```python
float("95") < 80.0    # False,95 不小于 80,正确告急
float("100") < 80.0   # False,正确
```

### 真实场景例:同一套代码,两种环境

```python
load_thresholds({})
#   -> {"disk": 80.0, "memory": 80.0, "cpu": 90.0}          # 开发机:全默认

load_thresholds({"DISK_THRESHOLD": "95", "CPU_THRESHOLD": "98"})
#   -> {"disk": 95.0, "memory": 80.0, "cpu": 98.0}          # 生产机:磁盘/CPU 放宽

load_thresholds({"HOME": "/root", "PATH": "/usr/bin"})
#   -> {"disk": 80.0, "memory": 80.0, "cpu": 90.0}          # 无关变量自动忽略
```

### 🔴 生产升级版:pydantic-settings(Ch22 已深讲)

手写的 `if KEY in env` 三个键还行,三十个键就是灾难。生产用 `pydantic-settings`(Ch22 §22.3 学过),**声明字段即完成「读环境变量 + 类型转换 + 默认值 + 校验」**:

```python
from pydantic_settings import BaseSettings

class MonitorSettings(BaseSettings):
    disk_threshold: float = 80.0      # 环境变量 DISK_THRESHOLD 自动覆盖、自动转 float
    memory_threshold: float = 80.0
    cpu_threshold: float = 90.0
    webhook_url: str                  # 无默认 = 必填,缺了启动就 fail-fast 报错

settings = MonitorSettings()          # = Spring 的 @ConfigurationProperties
```

本章**作业仍手写**简化版分层——理解原理后,你才用得动 pydantic-settings 的自动魔法,也才能在它报错时看懂为什么。

> ✅ 做 `load_thresholds`:默认 dict + 三个 `if KEY in env: result[...] = float(env[KEY])`。

---

## §27.3 水位三检:disk / memory / cpu(对应:`check_disk`、`check_memory`、`check_cpu`)🟢

Ch24 已经见过 `psutil`,这一节给它挂上**阈值判断**——巡检的核心不是「读出数字」,是「判断超没超」。

### Java 对照最小例

```java
// Java:读系统指标要么用 com.sun.management(非标准 API),要么引 Sigar/Oshi 三方库
OperatingSystemMXBean osBean = ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);
double cpuLoad = osBean.getCpuLoad() * 100;      // 0~100,首次调用可能返回负值(无效)
```

```python
# Python:psutil 一个库统一三大指标,跨平台
import psutil
psutil.disk_usage("/").percent        # 磁盘水位,直接给百分比
psutil.virtual_memory().percent       # 内存水位
psutil.cpu_percent(interval=0.1)      # CPU:采样 0.1 秒内的使用率
```

### 三个检查函数

```python
def check_disk(path: str = "/", threshold: float = 80.0) -> dict:
    du = psutil.disk_usage(path)
    return {
        "percent": du.percent,
        "free_gb": round(du.free / (1024 ** 3), 2),    # 字节 → GB,留 2 位小数
        "total_gb": round(du.total / (1024 ** 3), 2),
        "ok": du.percent < threshold,                   # 低于阈值 = 健康
    }

def check_memory(threshold: float = 80.0) -> dict:
    vm = psutil.virtual_memory()
    return {"percent": vm.percent, "ok": vm.percent < threshold}

def check_cpu(threshold: float = 90.0, interval: float = 0.1) -> dict:
    percent = psutil.cpu_percent(interval=interval)     # 阻塞采样 interval 秒
    return {"percent": percent, "ok": percent < threshold}
```

设计要点(三个函数同构,记一套就行):
- **返回带 `ok` 键的 dict**:不只返回数字,直接给出「健不健康」的判断,上游(§27.5)拿来就汇总。
- **`du.free` 是字节不是 GB**:`disk_usage` 返回的 `total/used/free` 单位全是**字节**,给人看的报告要除以 `1024**3` 转 GB。`round(x, 2)` 保留 2 位小数,报告干净。
- **`ok = percent < threshold` 是严格小于**:水位恰好等于阈值就算超标(宁多告不漏告),和 Ch26 的 `>=` 告警同一个哲学。

### ❌ → ✅ 错误对照

❌ **错误写法 1**(把字节当 GB,报告说「还剩 84000000000 GB」):

```python
"free_gb": du.free     # 84,359,196,935 字节 ≈ 78.57 GB,直接放进去报告没法看
```

✅ **正确写法**:

```python
"free_gb": round(du.free / (1024 ** 3), 2)   # 78.57
```

❌ **错误写法 2**(`cpu_percent()` 不传 interval,首次调用恒返回 0.0——假健康):

```python
psutil.cpu_percent()          # 第一次调用:0.0!它算的是「距上次调用」的平均,首次没有"上次"
```

✅ **正确写法**(传 `interval` 阻塞采样,结果才有意义):

```python
psutil.cpu_percent(interval=0.1)   # 采样 0.1 秒,返回真实使用率
```

### 真实场景例:巡检订单服务器

```python
check_disk("/", threshold=80.0)
#   -> {"percent": 62.3, "free_gb": 78.57, "total_gb": 250.0, "ok": True}

check_disk("/var/log", threshold=80.0)     # 日志分区 91%,超标!
#   -> {"percent": 91.0, "free_gb": 4.2, "total_gb": 50.0, "ok": False}

check_memory(threshold=80.0)
#   -> {"percent": 55.0, "ok": True}

check_cpu(threshold=90.0)
#   -> {"percent": 42.0, "ok": True}       # 采样 0.1 秒后的真实值
```

(数字随机器而变——测试里会 monkeypatch 掉 psutil,所以作业断言是确定性的。)

> ✅ 做 `check_disk` / `check_memory` / `check_cpu`:psutil 采集 → 组 dict → `ok = percent < threshold`。磁盘记得字节转 GB,CPU 记得传 `interval`。

---

## §27.4 端口探活:socket.create_connection(对应:`check_port`)🟡

磁盘/内存/CPU 是「本机水位」,巡检还要盯**关键依赖的端口**:DB 的 5432、Redis 的 6379 不通,本机再健康也是瘫的。不用 subprocess 调 `nc`/`telnet`,stdlib `socket` 一行探活。

### Java 对照最小例

```java
// Java:Socket + connect 带超时
try (Socket s = new Socket()) {
    s.connect(new InetSocketAddress("db.internal", 5432), 2000);   // 2 秒超时
    // 走到这 = 端口通
} catch (IOException e) {
    // 拒连/超时/DNS 失败 = 端口不通
}
```

```python
# Python:socket.create_connection,成功即通,OSError 即不通
import socket
with socket.create_connection(("db.internal", 5432), timeout=2.0):
    pass    # 走到这 = 端口通
```

### 实现:EAFP,绝不抛

```python
def check_port(host: str, port: int, timeout: float = 2.0) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"host": host, "port": port, "ok": True}
    except OSError:
        return {"host": host, "port": port, "ok": False}
```

- **`create_connection((host, port), timeout=...)`**:TCP 三次握手成功就返回一个已连接的 socket;拒连(`ConnectionRefusedError`)、超时(`socket.timeout`)、DNS 解析失败(`socket.gaierror`)**全是 `OSError` 的子类**,一个 `except OSError` 全兜住。
- **`with` 包住**:探活 socket 用完即关,不泄漏文件描述符。
- **返回带 host/port 的 dict**:告警报告里能直接看出「是哪台机的哪个端口挂了」,不只是一个 False。

### ❌ → ✅ 错误对照

❌ **错误写法 1**(忘 `timeout`,对端防火墙丢包时**挂死到地老天荒**):

```python
socket.create_connection(("10.0.0.99", 5432))    # 默认超时可能长达几分钟,巡检卡死在这
```

✅ **正确写法**(网络调用必设超时):

```python
socket.create_connection(("10.0.0.99", 5432), timeout=2.0)   # 最多等 2 秒
```

❌ **错误写法 2**(异常往上抛,一个端口不通拖垮整个巡检):

```python
def check_port(host, port):
    sock = socket.create_connection((host, port), timeout=2.0)   # DB 一挂,巡检脚本直接崩
    ...
```

✅ **正确写法**(EAFP,失败也是一份**结果**,不是一次事故):

```python
except OSError:
    return {"host": host, "port": port, "ok": False}   # 端口不通 = 一次不健康的检查结果
```

### 真实场景例

```python
check_port("127.0.0.1", 5432, timeout=1.0)
#   -> {"host": "127.0.0.1", "port": 5432, "ok": True}     # 本机 Postgres 活着

check_port("db.internal", 6379, timeout=1.0)
#   -> {"host": "db.internal", "port": 6379, "ok": False}  # Redis 挂了/网络不通 → False,不抛
```

> ✅ 做 `check_port`:`with socket.create_connection((host, port), timeout=timeout)` 成功返 `ok: True`,`except OSError` 返 `ok: False`。

---

## §27.5 汇总健康报告:all() 聚合(对应:`build_health_report`)🟢

单项检查都返回了带 `ok` 的 dict,现在汇总成「整体健康与否」。

### Java 对照最小例

```java
// Java:Stream.allMatch,有一个 false 整体就 false
boolean overallOk = checks.values().stream()
    .allMatch(c -> c.getOrDefault("ok", false));
```

```python
# Python:内置 all(),生成器喂给它
overall_ok = all(c.get("ok", False) for c in checks.values())
```

### 实现

```python
def build_health_report(checks: dict) -> dict:
    return {
        "overall_ok": all(c.get("ok", False) for c in checks.values()),
        "checks": checks,
    }
```

三个细节:
- **`all(...)`**:所有 `ok` 都为 True 才整体健康 = Java `allMatch`。短路:遇到第一个 False 就停。
- **`c.get("ok", False)`**:某个检查 dict **缺了 `ok` 键**(脏数据)时按 False 处理——宁可误告,不可漏判。写 `c["ok"]` 遇到脏数据会 `KeyError` 崩掉巡检。
- **报告把原始 checks 原样带上**:`{"overall_ok": ..., "checks": {...}}`——overall 给「要不要告警」用,checks 给「告警里写什么」用(哪项挂了、水位多少)。

### ❌ → ✅ 错误对照

❌ **错误写法**(手写循环,啰嗦还容易写错):

```python
overall = True
for c in checks.values():
    if not c["ok"]:            # 脏数据没 ok 键 → KeyError 崩掉
        overall = False
```

✅ **正确写法**(`all` + `get` 防御,一行):

```python
all(c.get("ok", False) for c in checks.values())
```

### 🔴 空检查的语义:all([]) 是 True

```python
all([])                          # True!vacuous truth(空真):没有反例 = 成立
build_health_report({})          # -> {"overall_ok": True, "checks": {}}
```

「没做任何检查」视为「健康」。这是数学约定(和 Java `Stream.empty().allMatch(...)` 返回 true 一致)。记住它,面试爱问。

### 真实场景例

```python
checks = {
    "disk":   {"percent": 62.3, "ok": True},
    "memory": {"percent": 91.0, "ok": False},     # 内存爆了
    "cpu":    {"percent": 42.0, "ok": True},
}
build_health_report(checks)
#   -> {"overall_ok": False, "checks": {...}}    # 一项挂 = 整体挂
```

> ✅ 做 `build_health_report`:`all(c.get("ok", False) for c in checks.values())`,返回 `{"overall_ok", "checks"}`。

---

## §27.6 webhook 告警:urllib POST JSON(对应:`send_webhook`)🔴

整体不健康时,把报告推到飞书/钉钉/Slack 群——它们都是同一个套路:**HTTP POST + JSON body**。用 stdlib `urllib` 写,**不引 requests**(零依赖,巡检脚本跑在受限服务器上,越少依赖越好部署)。

### Java 对照最小例

```java
// Java 11+:HttpClient POST JSON
HttpRequest req = HttpRequest.newBuilder(URI.create(url))
    .header("Content-Type", "application/json")
    .POST(BodyPublishers.ofString(json))
    .timeout(Duration.ofSeconds(5))
    .build();
int status = HttpClient.newHttpClient().send(req, BodyHandlers.discarding()).statusCode();
boolean ok = status >= 200 && status < 300;      // 得 try/catch IOException
```

```python
# Python stdlib:等价,更短
import json, urllib.request

data = json.dumps(payload).encode("utf-8")                        # dict → JSON str → bytes
req = urllib.request.Request(
    url, data=data, headers={"Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(req, timeout=5.0) as resp:
    ok = 200 <= resp.status < 300
```

### 完整实现:EAFP,绝不抛

```python
def send_webhook(url: str, payload: dict, timeout: float = 5.0) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300      # 2xx 算送达
    except Exception:
        return False                             # 任何异常都返回 False,绝不抛
```

逐步拆解:
- **`json.dumps(payload).encode("utf-8")`**:dict → JSON 字符串 → **bytes**(网络传的是字节)。这三步缺一不可。
- **`Request(url, data=..., method="POST")`**:`Request` 带了 `data` 才是 POST(没带是 GET);显式写 `method="POST"` 更清晰。
- **`Content-Type: application/json`**:告诉服务器 body 是 JSON。不加,飞书/钉钉把你的 JSON 当普通文本,解析失败。
- **`2xx` 判定**:webhook 服务器返回 200~299 才算送达(飞书成功返回 200;严谨还要看 body 里的 errno,这里简化)。
- **`except Exception: return False`**:网络抖动、超时、DNS 失败、对端 500……**任何**失败都归一成 `False`。webhook 是巡检的最后一环,它崩了,前面查得再准也白搭——下次定时巡检也起不来。

### ❌ → ✅ 错误对照

❌ **错误写法 1**(不 try/except,一次网络抖动拖垮整个巡检):

```python
with urllib.request.urlopen(req, timeout=timeout) as resp:   # DNS 失败 → URLError → 脚本崩
    return 200 <= resp.status < 300
```

✅ **正确写法**(失败返回 False,记日志,脚本活着等下一轮):

```python
try:
    ...
except Exception:
    return False    # 调用方拿到 False 可以记日志/计数,升级告警(连推 3 次失败就打电话)
```

❌ **错误写法 2**(忘 `Content-Type`,服务器不认 JSON):

```python
req = urllib.request.Request(url, data=data, method="POST")   # 缺 header,飞书返回 400/解析失败
```

✅ **正确写法**:

```python
headers={"Content-Type": "application/json"}
```

### 真实场景例

```python
report = {"overall_ok": False, "checks": {"memory": {"percent": 91.0, "ok": False}}}
send_webhook("https://open.feishu.cn/open-apis/bot/v2/hook/xxx", report)
#   -> True    # 飞书返回 200,群里出现告警

send_webhook("https://example.invalid/hook", report)
#   -> False   # 域名不存在(DNS 失败)→ 不抛异常,返回 False
```

> 🟡 **为什么不用 requests**:requests 更好用(`requests.post(url, json=payload)` 一行),但要 `pip install`。巡检脚本常跑在不好装包的生产服务器上,stdlib urllib 零依赖够用。**复杂 HTTP(鉴权/重试/session)才上 requests/httpx**(Ch13)。

> ✅ 做 `send_webhook`:`dumps → encode → Request(POST + json 头) → urlopen(timeout)`,2xx 返 True,`except Exception: return False`。

---

## §27.7 综合:run_inspection 组装巡检(对应:`run_inspection`)🔴

最后一题**不写新知识**,把前 7 个函数像积木一样拼成完整巡检:「读配置 → 三检 → 汇总 → 异常推 webhook」。

### 调用关系

```
run_inspection(env, webhook_url, disk_path)
  ├─ load_thresholds(env)                         # §27.2 阈值:默认 < env
  ├─ check_disk(disk_path, thresholds["disk"])     # §27.3
  ├─ check_memory(thresholds["memory"])            # §27.3
  ├─ check_cpu(thresholds["cpu"])                  # §27.3
  ├─ build_health_report({"disk":…, "memory":…, "cpu":…})   # §27.5
  └─ 不健康 且 有 webhook_url → send_webhook(url, report)   # §27.6
```

### 实现

```python
def run_inspection(env: dict, webhook_url: str | None = None, disk_path: str = "/") -> dict:
    thresholds = load_thresholds(env)               # §27.2
    checks = {
        "disk": check_disk(disk_path, thresholds["disk"]),
        "memory": check_memory(thresholds["memory"]),
        "cpu": check_cpu(thresholds["cpu"]),
    }
    report = build_health_report(checks)            # §27.5
    webhook_sent = None
    if not report["overall_ok"] and webhook_url:    # 异常 且 配了 url 才推
        webhook_sent = send_webhook(webhook_url, report)
    return {"report": report, "webhook_sent": webhook_sent}
```

`webhook_sent` 三态语义:
- `None`:没推(系统健康,或没配 webhook_url)——「不需要推」和「推了」区分开。
- `True`:推了且成功。
- `False`:推了但失败(send_webhook 绝不抛,失败也是返回值)。

### 🔴 可测性设计:模块级小函数天生好测

注意每个函数都是**模块级 `def`**,`run_inspection` 通过**模块全局名**调用它们。这意味着测试可以 `monkeypatch.setattr(ch27_assignment, "check_disk", fake)` 把真实采集换成假数据——**不测真磁盘,只测编排逻辑**:

```python
# 测试片段预览(你作业里的测试就是这么验的)
monkeypatch.setattr(ch27_assignment, "check_disk", lambda path, threshold: {"percent": 99.0, "ok": False})
result = run_inspection({}, webhook_url="https://hook.example/x")
assert result["webhook_sent"] is True        # 磁盘假超标 → 真的去推了 webhook
```

这就是为什么运维脚本要拆成「小函数 + 组合」:**每个零件可单测,组装逻辑可 mock**。一个 100 行的巨型函数只能连真机祈祷。

### 真实场景例

```python
# 生产机:磁盘阈值放宽到 95,webhook 走环境变量
result = run_inspection(
    {"DISK_THRESHOLD": "95", "CPU_THRESHOLD": "98"},
    webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
)
# 磁盘 91% < 95,内存 91% > 80(默认)→ 整体不健康 → 推送
#   -> {"report": {"overall_ok": False, "checks": {...}}, "webhook_sent": True}

result = run_inspection({})        # 全默认阈值,各项正常
#   -> {"report": {"overall_ok": True, ...}, "webhook_sent": None}   # 健康,不推
```

> ✅ 做 `run_inspection`:按调用关系图串 5 步;`webhook_sent` 初始 None,仅「不健康且有 url」时赋为 `send_webhook(...)` 的返回值。

---

## §27.8 实战:加上定时就是巡检服务(讲透不出题)

`__main__` 段把 `run_inspection` 接上真实环境,再配上 Ch26 的 `schedule` 定时,就是一个能跑的巡检服务:

```python
if __name__ == "__main__":
    import os
    webhook = os.environ.get("WEBHOOK_URL")          # webhook URL 也走环境变量
    result = run_inspection(dict(os.environ), webhook_url=webhook)
    ...

# 定时版(Ch26 schedule):
def job():
    run_inspection(dict(os.environ), webhook_url=os.environ.get("WEBHOOK_URL"))

schedule.every(5).minutes.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)
```

生产化清单(从「能跑」到「敢上生产」):
1. **进程守护**:`schedule` 进程挂了就停(Ch26 §26.8),用 systemd/supervisor 守护,或干脆 cron 每分钟跑一次脚本。
2. **webhook URL 走环境变量**:URL 里带 token,是敏感配置,不进代码(Ch22 的 Settings 也行)。
3. **告警升级**:`send_webhook` 连续 N 次 False 要升级渠道(短信/电话),否则 webhook 服务挂了 = 监控全瞎。
4. **加日志**(Ch12):每轮巡检结果写日志,出事后能回溯水位曲线。
5. **端口检查接入**:`check_port` 没进 `run_inspection`(端口列表因机而异),真实场景用配置驱动:`WATCH_PORTS=db:5432,redis:6379`,解析后逐个 `check_port` 再并入 checks。留给你当课外练习。

---

## §27.9 Java 老手常踩的坑 ⚠️

1. **环境变量是字符串**:`env["X"]` 读出来永远是 str。`"95" < 80` 直接 TypeError;`"95" < "80"` 不崩但按字典序给**错误答案**。配置层第一件事 `float()`/`int()`。
2. **阈值写死在代码**:改阈值要改代码重发版。走环境变量/配置文件,`@Value("${x:80}")` 的道理在 Python 一样成立。
3. **`disk_usage().free` 是字节**:忘除 `1024**3`,报告里「剩余 840 亿 GB」。
4. **`cpu_percent()` 首次返回 0.0**:它算「距上次调用」的平均。传 `interval=0.1` 阻塞采样,或丢弃首次值。
5. **网络调用忘 `timeout`**:`urlopen`/`create_connection` 默认可能挂起几分钟,巡检卡死。网络调用必设超时。
6. **webhook 抛异常拖垮巡检**:网络调用必须 try/except,失败返回 False + 记日志,**绝不**让脚本挂(挂了就漏告警)。
7. **忘 `Content-Type: application/json`**:服务器把 JSON body 当普通文本,推送失败。
8. **裸 `except:` 吞一切**:webhook 里 `except Exception` 是刻意的(还要兜 TimeoutError 等),但别写裸 `except:`——它连 `KeyboardInterrupt`/`SystemExit` 都吞。
9. **用 `c["ok"]` 汇总遇脏数据崩掉**:用 `c.get("ok", False)` 防御,宁可误告不漏判。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `load_thresholds` | 配置分层 + float 转换 | 🟡 |
| `check_disk` | psutil.disk_usage + 字节转 GB + 阈值 | 🟢 |
| `check_memory` | psutil.virtual_memory + 阈值 | 🟢 |
| `check_cpu` | psutil.cpu_percent(interval) | 🟢 |
| `check_port` | socket 探活 + timeout + EAFP | 🟡 |
| `build_health_report` | all() 聚合 + get 防御 | 🟢 |
| `send_webhook` | urllib POST JSON + 绝不抛 | 🔴 |
| `run_inspection` | 综合:组装前 7 个函数 | 🔴 |

```bash
uv sync --extra devops   # 本章依赖 psutil(extras 互斥)
uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v
```

全绿 = 掌握 Ch27 = **M4 运维脚本毕业** 🎓。

---

## ✅ 自测

- [ ] 能说清配置分层(默认 < 环境变量)、环境变量为什么必须类型转换
- [ ] 知道 pydantic-settings 与手写分层的关系(Ch22)
- [ ] 会用 psutil 检查磁盘/内存/CPU,避开「字节当 GB」「cpu_percent 首次 0」两坑
- [ ] 会用 socket 给端口探活,说清 timeout 与 OSError 兜底
- [ ] 能用 `all()` 汇总多项检查,知道 `all([])` 的语义和 `get("ok", False)` 的防御意义
- [ ] 会用 stdlib urllib POST JSON webhook,且绝不抛异常(EAFP)
- [ ] 能说清小函数 + monkeypatch 的可测性设计
- [ ] 8 个作业全绿

## 🎓 费曼挑战

1. 「环境变量读出来是什么类型?`"95" < "80"` 结果是什么、为什么?配置层怎么防?」— 重读 §27.2/§27.9
2. 「`cpu_percent()` 不传 interval 为什么首次是 0.0?`disk_usage().free` 直接放进报告有什么问题?」— 重读 §27.3
3. 「`check_port` 为什么 `except OSError` 就够?忘了 timeout 会发生什么?」— 重读 §27.4
4. 「`all([])` 返回什么?`build_health_report` 为什么用 `c.get("ok", False)` 而不是 `c["ok"]`?」— 重读 §27.5
5. 「webhook 推送为什么必须 try/except 返回 bool?`run_inspection` 的 `webhook_sent` 三态各代表什么?」— 重读 §27.6/§27.7
6. 「为什么 `run_inspection` 的编排逻辑可以不连真机测?」— 重读 §27.7

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ M4 毕业 → M5 AI 框架

恭喜!**Ch23–27 全部学完,M4 运维脚本模块毕业** 🎓。你现在能:
- 文件批处理(pathlib/shutil)→ 调外部命令 + 系统监控(subprocess/psutil)→ 写漂亮 CLI(Typer/Rich)→ 日志聚合告警(schedule + 正则)→ 系统巡检 + webhook 告警。

这是 Python 相对 Java 的**舒适区**——胶水语言、运维利器,几十行干 Java 几百行的活。

下一站 **M5 AI 框架**(Ch28–33)⭐:LLM 调用 → Prompt 工程 → LangChain → RAG 向量检索 → Agent 工具调用 → FastAPI 封装 AI 服务。这是你点名的核心方向,也是当下最热的 Python 应用领域。
