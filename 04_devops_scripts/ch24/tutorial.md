# Ch24 · 进程与子进程管理:subprocess / psutil

> **预计**:0.5 天 ｜ **前置**:Ch07(EAFP/类型注解)、Ch23(pathlib)｜ **M4 第 2 章**
> **目标**:① 用 `subprocess` 在 Python 里调外部命令(= Java `ProcessBuilder`,但一个调用搞定);② 用 `psutil` 跨平台读内存/磁盘/CPU 指标。写完你能独立产出「健康检查脚本」「系统巡检脚本」。
> **本章主线**:你是今晚的 on-call。公司一批微服务散落在多台主机上,监控平台每晚跑一次「**巡检机器人**」:对目标机跑探测命令(绝不崩)→ 跨平台 ping 一组服务 → 采集本机内存/磁盘 → 按阈值判断要不要告警 → 汇总成一份结构化健康报告。8 个函数全为这条主线服务。

> 📐 **本教程的契约**:§24.2–§24.7 每节**精确对应**作业里的函数,讲过的才考,考的必讲过。§24.1 是开胃、§24.8 是进阶阅读、§24.9 是坑清单,讲透不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 一个 `subprocess.run(...)` 顶 Java 里 `ProcessBuilder.start() + 读流 + waitFor()` 一整套
- 说清 `capture_output` / `text` / `timeout` 三个参数各自防什么坑
- 用 EAFP 把子进程异常「拍扁」成 `(bool, str)` 返回值,让巡检脚本绝不崩
- 写出真正跨平台的 `ping`(Windows/macOS/Linux 参数各不同,macOS 还有个毫秒坑)
- 一行 `psutil` 读到内存使用率/磁盘剩余,并完成字节 → GB 的 1024 进制换算
- 把「阈值告警判断」拆成**纯函数**,说清为什么这样才可测
- 把 7 个零件组装成健康报告——「小函数 + 组合」的收尾综合题

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `run_command` | §24.2 | subprocess.run + capture_output / text / timeout |
| `run_command_safely` | §24.3 | EAFP:异常拍扁成 (bool, str) 返回值 |
| `ping_host` | §24.4 | 跨平台参数 + returncode 判断 + 超时双保险 |
| `bytes_to_gb` | §24.5 | 字节 → GB 换算(1024 进制,纯函数) |
| `memory_usage_percent` | §24.5 | psutil.virtual_memory().percent |
| `disk_free_gb` | §24.5 | psutil.disk_usage().free + 复用 bytes_to_gb |
| `check_thresholds` | §24.6 | 阈值告警拆成纯函数 + dict 遍历 + 后缀约定 |
| `health_report` | §24.7 | 综合:组装前 7 个函数出健康报告 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 6 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch24_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「三参数各防什么、EAFP 封装、纯函数可测」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(先想,别急着翻答案)

1. Java 调外部命令:`ProcessBuilder("git","--version").start()` → 拿 `getInputStream()` 开流读 → `waitFor()` → `exitValue()`。Python 的 `subprocess.run(...)` 一个调用返回什么?
2. `run` 默认把 stdout 当 `bytes` 返回。怎么让它直接给 `str`?(= Java 读流时指定 charset)
3. 命令不存在、或者子进程超时,`run` 会抛什么异常?巡检脚本要对一批机器跑命令,怎么做到「一台失败绝不拖垮整批」?
4. ping 在 Windows 是 `-n 1 -w 2000`,在 macOS/Linux 是 `-c 1 -W ?`——最后这个超时参数,macOS 和 Linux 的**单位还不一样**。怎么写一个函数通吃三平台?
5. Java 读「内存使用率」要碰 `OperatingSystemMXBean` 且各平台实现不一致。Python 的 `psutil` 一行怎么读?
6. 巡检报告里「内存 87% > 阈值 80% → 告警」这段判断,为什么要拆成一个**不碰 psutil 的纯函数**?(提示:想想单测怎么写)

> 猜完带着验证心态进入正文。第 4 题的 macOS 毫秒坑是 🔴,老运维都踩过。

---

## §24.1 subprocess 是什么(开胃 · 不出题)🟡

`subprocess` = 在 Python 里**启动子进程**、跟它交互(给输入、读输出、等退出)的标准库。

```
你的 Python 脚本 → subprocess.run(["git", "status"]) → 起一个 git 子进程
                     ↑ 等它跑完,拿到 returncode / stdout / stderr
```

> 🟡 **Java 对比**:= `ProcessBuilder` + `Process`。Java 那套「builder.start() → getInputStream() 开 BufferedReader → 逐行读 → waitFor() → exitValue()」五步,Python 压成**一个调用 + 一个结果对象**。

| subprocess API | 作用 | Java 对应 |
|----------------|------|-----------|
| `run(args, ...)` | 跑命令,**等它结束**,返回 CompletedProcess | `pb.start()` + `waitFor()` |
| `Popen(...)` | 起进程但**不等**(异步读流/管道/长驻进程) | `pb.start()` 不 waitFor |
| `CompletedProcess` | 结果对象:`.args/.returncode/.stdout/.stderr` | `Process` + 手动收集的输出 |

**90% 的运维场景用 `run` 就够**(同步等结果);只有「边跑边读输出」「管道串联」「起守护进程」才上 `Popen`(§24.8 延伸阅读)。

---

## §24.2 run 三件套:capture_output / text / timeout(对应:`run_command`)🟢

### Java 对照最小例

```java
// Java:跑 git --version 并拿到输出
ProcessBuilder pb = new ProcessBuilder("git", "--version");
Process p = pb.start();
String out = new String(p.getInputStream().readAllBytes());  // 还得自己读流
int code = p.waitFor();                                        // 还得自己等
```

```python
import subprocess

r = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
r.returncode   # 0(成功)/ 非 0(失败)
r.stdout       # "git version 2.43.0\n"   ← str(因为 text=True)
r.stderr       # ""
```

一个调用,流也读了、退出码也等了。

### 三个关键参数:各防一种坑

| 参数 | 作用 | 不设的后果 |
|------|------|-----------|
| `capture_output=True` | 把 stdout/stderr 收进结果对象 | 输出直接打到你的控制台,`r.stdout` 是 `None` |
| `text=True` | 返回 `str` 而非 `bytes` | 拿到 `b"git version..."`,每次要 `.decode()` |
| `timeout=10` | 超时抛 `TimeoutExpired` | 子进程卡住,你的脚本**永远 hang** |

❌ **错误写法**(Java 老手第一次写,三个坑踩俩):

```python
r = subprocess.run(["some_tool", "--check"])   # 没 capture_output:输出飞了,stdout 是 None
print(r.stdout.strip())                         # AttributeError: NoneType 没有 strip
```

✅ **正确写法**(巡检脚本固定三件套):

```python
r = subprocess.run(["some_tool", "--check"],
                   capture_output=True, text=True, timeout=10)
print(r.stdout.strip())
```

### 🔴 安全红线:传 list,别用 shell=True

❌ **错误写法**(命令注入,= Java 里 `Runtime.exec` 拼字符串的坑):

```python
host = "8.8.8.8; rm -rf /"                 # 假设这来自用户输入/配置文件
subprocess.run(f"ping -c 1 {host}", shell=True)   # 💥 分号后的命令也会被执行
```

✅ **正确写法**(list 形式不走 shell 解析,参数就是参数):

```python
subprocess.run(["ping", "-c", "1", host], capture_output=True, timeout=5)
# host 里的 "; rm -rf /" 只会被当成一个奇怪的主机名,ping 报错,但不会执行
```

### 真实场景例:巡检第一步,确认目标机上的工具可用

```python
r = subprocess.run(["systemctl", "is-active", "myapp"],
                   capture_output=True, text=True, timeout=5)
if r.returncode == 0 and r.stdout.strip() == "active":
    print("服务活着")
else:
    print(f"服务异常: rc={r.returncode} stderr={r.stderr.strip()}")
```

> 🟡 **注意**:`run` 默认**非 0 退出码不抛异常**(`check=False`)——退出码 3 也只是 `r.returncode == 3`。要它抛得加 `check=True`(抛 `CalledProcessError`)。巡检脚本通常自己看 returncode,不加 check。

### 作业实现要点

- `run_command`:就是把上面三件套封装成一行 `subprocess.run(args, capture_output=True, text=True, timeout=timeout)`,原样返回 CompletedProcess。超时触发的 `TimeoutExpired` **不在本题处理**(§24.3 才包 try)。

---

## §24.3 绝不崩:EAFP 封装(对应:`run_command_safely`)🔴

巡检要对**一批**机器跑命令。任何一台命令不存在/超时,都不能拖垮整批——一个失败,记下来,继续下一台。

### run 会抛的三种异常

| 异常 | 触发场景 |
|------|---------|
| `FileNotFoundError` | 命令本身不存在(打错字/没装) |
| `subprocess.TimeoutExpired` | 超过 `timeout` |
| `PermissionError` | 文件存在但没执行权限 |

### ❌ → ✅ 错误对照

❌ **错误写法**(第一台机器上命令不存在,整批巡检直接死):

```python
for host in hosts:
    r = subprocess.run(["probe_tool", host], capture_output=True, text=True, timeout=5)
    print(host, r.returncode)      # 某台没装 probe_tool → FileNotFoundError → 循环中断!
```

✅ **正确写法**(把异常拍扁成返回值,调用方看布尔就行):

```python
ok, output = run_command_safely(["probe_tool", host])
if not ok:
    report.append(f"{host}: 探测失败 - {output}")   # 记下来,继续下一台
```

> 🟡 **Java 对比**:这就是你熟悉的 `try { ... } catch (IOException e) { return Result.fail(...); }`,只是 Python 的 `try/except` 更轻。这是 Ch07 的 **EAFP** 风格:先跑,出错再处理,而不是事先检查命令存不存在(LBYL)。
>
> 🔴 **注意**:catch 要**具体**(`FileNotFoundError` / `TimeoutExpired`),别裸 `except:`——裸 except 会把 `KeyboardInterrupt`、代码 bug 也一起吞掉,排查时哭都哭不出来。

### 封装的设计细节(作业契约)

- 返回 `tuple[bool, str]`:`(是否成功, 输出文本)`。
- **成功** = `returncode == 0`,输出取 `stdout`;**失败** = 非 0 退出,把 `stdout + stderr` 都带回去(排查时 stderr 往往才是原因)。
- 命令不存在 → `(False, "命令不存在: xxx")`;超时 → `(False, "命令超时: xxx")`。
- 输出 `.strip()` 去掉末尾换行,报告里干净。

### 真实场景例:批量探测,失败只记不断

```python
for host in ["web-01", "web-02", "db-01"]:
    ok, out = run_command_safely(["systemctl", "is-active", "myapp"])
    print(f"{host:10s} {'UP' if ok else 'DOWN: ' + out}")
# web-02 上没 systemctl?那也只影响它这一行,循环继续
```

### 作业实现要点

- `run_command_safely`:`try` 里调 `subprocess.run`(三件套照带,timeout 用参数传入);两个 `except` 分别返回 `(False, 提示)`;`try` 之后看 `returncode` 决定 ok,按上面的契约取输出。本题是「拍扁异常」模式,本身不抛任何异常。

---

## §24.4 跨平台 ping(对应:`ping_host`)🟡

ping 是健康检查的标配。坑在于:**三个平台的 ping 参数不一样,而且 macOS 还藏了个单位坑**。

| 平台 | 次数参数 | 超时参数 | 超时单位 |
|------|---------|---------|---------|
| Windows | `-n 1` | `-w 2000` | **毫秒** |
| macOS(BSD) | `-c 1` | `-W 2000` | **毫秒** ⚠️ |
| Linux(iputils) | `-c 1` | `-W 2` | **秒** ⚠️ |

> 🔴 **macOS 毫秒坑**:macOS 的 `-W` 单位是**毫秒**,Linux 的 `-W` 是**秒**——同名参数,单位差 1000 倍。想当然写 `-W 2`,在 macOS 上只等 2 毫秒(基本等于不等),在 Linux 上等 2 秒。所以分支里 `Darwin`(macOS 的系统名)要乘 1000,Linux 直接用秒。

### Java 对照最小例

```java
// Java:InetAddress.isReachable 看着美,实际坑多
boolean up = InetAddress.getByName(host).isReachable(2000);
// Unix 上它需要发 ICMP 包,没 root 权限时会退化(甚至直接 false),不可靠
```

```python
# Python:直接调系统 ping,反而更可靠
is_win = platform.system() == "Windows"
```

### 三个判断点

1. **returncode 判断**:ping 通了退出码 0;不通(超时/不可达/DNS 失败)退出码非 0。`ping_host` 的返回值就是 `r.returncode == 0`。
2. **超时双保险**:ping 自己的 `-W`/`-w` 是第一道;`subprocess.run(timeout=...)` 设得比它**稍大**(比如 `timeout + 2`)做兜底——就算参数单位搞错了、ping 死等,subprocess 也会超时杀掉它。
3. **异常兜底**:`TimeoutExpired` / `FileNotFoundError`(精简 Docker 镜像里可能没装 ping)→ 一律返回 `False`,绝不抛给调用方。

### ❌ → ✅ 错误对照

❌ **错误写法**(一套参数走天下,换平台就废):

```python
r = subprocess.run(["ping", "-c", "1", host], capture_output=True)
# Windows 上没有 -c 参数,直接报错;而且没 timeout,目标死机你就死等
```

✅ **正确写法**(按 `platform.system()` 分支选参数):

```python
system = platform.system()        # "Windows" / "Darwin"(macOS)/ "Linux"
# Windows:-n 1 -w <毫秒>;macOS:-c 1 -W <毫秒>;Linux:-c 1 -W <秒>
```

> 💡 **测试怎么写**:`.invalid` 是 RFC 2606 保留的假域名,DNS 查询**立即失败**,ping 秒回非 0——测「不通」分支不用真等超时。测「通」用 `127.0.0.1`,本机回环永远通。

### 作业实现要点

- `ping_host`:`platform.system()` 三分支拼参数 list(注意上表的单位);`subprocess.run(args, capture_output=True, timeout=timeout + 2)`;返回 `returncode == 0`;`except (TimeoutExpired, FileNotFoundError)` 兜底 `False`。

---

## §24.5 psutil 系统监控 + 字节换算(对应:`bytes_to_gb`、`memory_usage_percent`、`disk_free_gb`)🟢

`psutil`(python system and process utilities)= 跨平台系统监控库:CPU/内存/磁盘/网络/进程列表,一行一个指标。

> 🟡 **Java 对比**:Java 没有等价的单一库——要组合 `OperatingSystemMXBean`、`File.getUsableSpace()`,且各平台实现不一致(macOS 上 MXBean 很多方法直接不支持)。psutil 把这堆事统一了。

### 两个核心 namedtuple

```python
import psutil

psutil.virtual_memory()
# svmem(total=17179869184, available=8589934592, used=8589934592, percent=50.0, ...)
#        ↑ 总字节           ↑ 可用字节              ↑ 已用          ↑ 已用百分比(直接可用!)

psutil.disk_usage("/")
# sdiskusage(total=500107862016, used=300000000000, free=200000000000, percent=60.0)
#                                            ↑ 剩余字节(注意:是字节,不是 GB)
```

- 内存使用率:**`.percent` 字段直接给**(已用/总量×100),一行拿走。
- 磁盘剩余:只有 `.free`(字节),报告里要人读单位 → 自己换算。

### 字节换算:1024 进制,别用 1000

❌ **错误写法**(硬盘厂商的 GB,运维不认):

```python
free_gb = usage.free / (1000 ** 3)     # 500107862016 → 500.1,比实际「看着多」
```

✅ **正确写法**(1024 进制,= `df -h` 看到的数):

```python
free_gb = usage.free / (1024 ** 3)     # 500107862016 → 465.8 GiB
```

> 🟡 **背景**:硬盘厂商用 1000³ 标容量(数字大好看),操作系统和 `df` 用 1024³——这就是为什么「500GB 硬盘」装上系统只剩 465GB。运维脚本一律 1024 进制。把这个换算独立成 `bytes_to_gb` **纯函数**:好测(精确断言)、好复用(磁盘、内存、网络流量都用它)。

### 真实场景例:巡检报告里的人读单位

```python
vm = psutil.virtual_memory()
du = psutil.disk_usage("/")
print(f"内存: {vm.percent}% 已用;磁盘剩余: {du.free / (1024**3):.1f} GB")
```

顺带一提:`psutil.cpu_percent(interval=0.1)` 采样 0.1 秒内的 CPU 使用率;`psutil.process_iter()` 能遍历所有进程拿 pid/名字/内存——本章作业用不到,Ch27 巡检章会再见面。

### 作业实现要点

- `bytes_to_gb`:一行,`n / (1024 ** 3)`,注意返回 float。
- `memory_usage_percent`:`psutil.virtual_memory().percent` 一行拿走。
- `disk_free_gb`:`psutil.disk_usage(path).free` 过一遍你自己的 `bytes_to_gb`——**复用,别重算**(综合题里还会再用)。

---

## §24.6 阈值告警:把判断拆成纯函数(对应:`check_thresholds`)🟡

巡检脚本三段式:**采集 → 判断 → 报告**。§24.5 管采集,本节管判断。

### 为什么判断要拆纯函数?

```python
# ❌ 判断和采集揉在一起:
def check():
    pct = psutil.virtual_memory().percent   # 采集
    if pct > 80:                             # 判断
        return ["内存超阈值"]
# 单测怎么写?你没法让测试机的内存「刚好 81%」——不可测!
```

✅ **拆开后**:判断函数只吃两个 dict(指标 + 阈值),不碰 psutil:

```python
check_thresholds({"memory_percent": 87.5}, {"memory_percent_max": 80.0})
# → ["memory_percent=87.5 超过上限 80.0"]    ← 输入确定,输出确定,随便测
```

> 🟡 **Java 对比**:这就是你熟悉的「把业务规则从 `System.getenv`/静态调用里剥离出来,做成可注入的纯逻辑」。单元测试只能稳定测**确定性逻辑**;采集那层(碰真实系统)测试只断言「返回 float、在 0~100」这种弱不变量。

### 阈值配置约定:`_max` / `_min` 后缀

阈值用一个 dict 表达,key 的后缀决定比较方向(类似配置文件的命名约定):

| limits 的 key | 对应 metrics 的 key | 告警条件 | 消息格式 |
|---------------|--------------------|---------|---------|
| `memory_percent_max` | `memory_percent` | 值 **>** 上限 | `memory_percent=87.5 超过上限 80.0` |
| `disk_free_gb_min` | `disk_free_gb` | 值 **<** 下限 | `disk_free_gb=12.0 低于下限 20.0` |

规则细节(测试按这个断言):
- 基础名 = key 去掉 `_max`/`_min` 后缀(`"memory_percent_max"[:-4]` → `"memory_percent"`)。
- metrics 里**没有**该基础名 → 跳过(不告警、不报错)。
- 值**等于**阈值不告警(严格 `>` / `<`)。
- 多条告警按 `limits` 的 key 顺序产出(dict 3.7+ 保插入序,Ch02)。
- `limits` 为空 dict → 返回 `[]`。

### 示例

```python
metrics = {"memory_percent": 87.5, "disk_free_gb": 12.0}
limits  = {"memory_percent_max": 80.0, "disk_free_gb_min": 20.0}
check_thresholds(metrics, limits)
# ["memory_percent=87.5 超过上限 80.0", "disk_free_gb=12.0 低于下限 20.0"]
```

> 💡 消息里**不带单位**,保持 `f"{name}={value} 低于下限 {limit}"` 统一格式,简单可测——阅读者看 key 名(`disk_free_gb`)就知道单位。

### 作业实现要点

- `check_thresholds`:遍历 `limits.items()`;`key.endswith("_max")` / `"_min"` 判方向;`[:-4]` 切出基础名;`metrics.get(name)` 拿到值(拿不到就跳过);按方向严格比较,拼 `f"{name}={value} 超过上限 {limit}"` / `低于下限` 消息 append;最后返回 list。

---

## §24.7 综合:健康报告(对应:`health_report`)🔴

最后一题**不写新知识**,把前 7 个函数像积木一样拼成巡检机器人的主流程:「ping 一组主机 + 采集本机指标 + 阈值判断 → 一份结构化报告」。

### 组装思路(调用关系)

```
health_report(hosts, limits)
  ├─ {h: ping_host(h) for h in hosts}     # §24.4 批量 ping,字典推导一行
  ├─ memory_usage_percent()               # §24.5 本机内存
  ├─ disk_free_gb("/")                    # §24.5 本机磁盘(内部已复用 bytes_to_gb)
  ├─ check_thresholds(metrics, limits)    # §24.6 判断;limits=None 时 alerts=[]
  └─ 拼报告 dict
```

### 报告契约(测试按这个断言)

返回 dict,6 个 key:

| key | 含义 | 来自 |
|-----|------|------|
| `"hosts"` | `{主机: 是否通}` | `ping_host` 逐个调 |
| `"up_count"` | 通的主机数 | `sum(1 for ok in ... if ok)` |
| `"total"` | 主机总数 | `len(hosts)` |
| `"memory_percent"` | 本机内存使用率 | `memory_usage_percent()` |
| `"disk_free_gb"` | 本机根分区剩余 GB | `disk_free_gb("/")` |
| `"alerts"` | 阈值告警消息列表 | `check_thresholds`;`limits=None` → `[]` |

> 🔴 **两个边界**:`hosts=[]` → `"hosts": {}`、`up_count=0`,照出不误;`limits=None`(调用方不关心阈值)→ `alerts=[]`,别拿 None 去调 `check_thresholds`。

> 💡 注意 `metrics`  dict 的 key 要和 `limits` 的基础名对齐:`"memory_percent"` / `"disk_free_gb"`——这正是 §24.6 约定能转起来的原因。

这道题考察的不是新语法,而是**组合能力**——每个零件你都写过了,现在要按正确顺序调用、把前一个的输出当后一个的输入。监控平台拿到这份 dict 直接 `json.dumps` 就能发 webhook(Ch27 会干这事)。

---

## §24.8 进阶阅读:Popen / 管道 / 守护与信号(讲透不出题)

`run` 是「同步等结果」;下面三件事得用 `Popen`(= Java `pb.start()` 后不 waitFor)。**知道存在即可,作业不考。**

### 边跑边读:长任务的流式输出

```python
proc = subprocess.Popen(["rsync", "-av", "/data/", "/backup/"],
                        stdout=subprocess.PIPE, text=True)
for line in proc.stdout:          # 逐行实时读,不用等整个 rsync 跑完
    print("同步中:", line.strip())
proc.wait()                        # 最后还是要等它结束拿退出码
```

### 管道:`ps aux | grep python` 的 Python 写法

```python
p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
p2 = subprocess.Popen(["grep", "python"], stdin=p1.stdout,
                      stdout=subprocess.PIPE, text=True)
p1.stdout.close()                  # 让 p1 能收到 SIGPIPE
out, _ = p2.communicate()          # communicate = 读完输出 + 等结束
```

### 守护进程与信号

- **起守护进程**:`Popen(..., start_new_session=True)` 让子进程脱离终端会话(≈ `nohup cmd &`),你的脚本退出后它还活着——起临时 agent、本地隧道用得上。
- **信号**:`proc.terminate()`(发 `SIGTERM`,≈ `kill`,礼貌请它退)、`proc.kill()`(发 `SIGKILL`,≈ `kill -9`,强杀)。Python 的 `signal` 模块还能给自己的脚本注册信号处理器(如收到 `SIGTERM` 先清理再退)。
- Java 对应:`Process.destroy()` / `destroyForcibly()`。

---

## §24.9 Java 老手常踩的坑 ⚠️

1. **`shell=True` 命令注入**:永远传 `list`,别 `shell=True`。真要 shell 特性(管道/通配符),用户输入必须 `shlex.quote` 转义。
2. **忘设 `timeout`**:`run` 默认无超时,子进程 hang 你的脚本就 hang。运维脚本必设 timeout。
3. **忘 `capture_output`**:不设则 `r.stdout` 是 `None`,`None.strip()` 直接 `AttributeError`。
4. **拿 `bytes` 当 `str` 用**:默认返回 bytes(`b"..."`)。要 str 加 `text=True`(老代码的 `universal_newlines=True` 是废弃别名)。
5. **以为非 0 退出码会抛异常**:`run` 默认**不抛**(`check=False`),非 0 只是 `returncode != 0`。要抛加 `check=True`(抛 `CalledProcessError`)。
6. **裸 `except:`**:把 `KeyboardInterrupt` 和代码 bug 一起吞了。catch 具体异常:`FileNotFoundError` / `TimeoutExpired`。
7. **macOS 的 `ping -W` 是毫秒**:Linux 是秒。同名参数单位差 1000 倍,跨平台脚本必踩一次才长记性。
8. **`psutil.cpu_percent()` 首次调用返回 0.0**:它算的是「距上次调用」的平均,第一次没有「上次」所以无意义。要么传 `interval=0.1` 阻塞采样,要么丢弃首次值。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `run_command` | subprocess.run 三件套 | 🟢 |
| `run_command_safely` | EAFP 拍扁异常成 (bool, str) | 🟡 |
| `ping_host` | 跨平台参数 + returncode + 超时双保险 | 🟡 |
| `bytes_to_gb` | 字节换算(1024 进制,纯函数) | 🟢 |
| `memory_usage_percent` | psutil.virtual_memory | 🟢 |
| `disk_free_gb` | psutil.disk_usage + 复用 bytes_to_gb | 🟢 |
| `check_thresholds` | 纯函数阈值判断 + dict 遍历 | 🟡 |
| `health_report` | 综合:组装前 7 个函数 | 🔴 |

```bash
uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v
```

全绿 = 掌握 Ch24。

---

## ✅ 自测

- [ ] 能说清 `capture_output` / `text` / `timeout` 三参数各防什么坑(不设分别会怎样)
- [ ] 知道为什么不能 `shell=True`,能给一个注入例子
- [ ] 知道 `run` 默认非 0 退出码**不抛**异常,要抛得加 `check=True`
- [ ] 能写出「绝不崩」的命令封装:catch 哪两个具体异常?成功/失败各返回什么?
- [ ] 能默写三平台 ping 参数,说清 macOS `-W` 的单位坑和超时双保险
- [ ] 说清为什么阈值判断要拆纯函数(可测性),字节换算为什么是 1024³
- [ ] 8 个作业全绿

## 🎓 费曼挑战

1. 「`subprocess.run` 不设 timeout 会怎样?`capture_output` 不设又会怎样?」— 重读 §24.2
2. 「为什么巡检脚本要把 `run` 包成返回 `(bool, str)` 的函数?对应 Java 什么写法?为什么不能裸 `except:`?」— 重读 §24.3
3. 「macOS 和 Linux 的 `ping -W` 有什么区别?既然 ping 自己有 `-W`,为什么 subprocess 还要再设 timeout?」— 重读 §24.4
4. 「`check_thresholds` 为什么不直接在里面调 `psutil`?拆开前后单测分别怎么写?」— 重读 §24.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch25 CLI 工具开发:Typer + Rich

巡检逻辑会写了,但它现在还是个「裸脚本」。下一章把它变成**漂亮的命令行工具**——`Typer`(类型注解驱动 CLI,= Java Picocli)+ `Rich`(终端表格/颜色/进度条),`python巡检.py check --hosts web-01,web-02` 直接出彩色报告。
