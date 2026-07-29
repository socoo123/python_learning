# Ch24 · 进程与子进程管理:subprocess / psutil

> **预计**:0.5 天 ｜ **前置**:Ch23、Ch07(EAFP)｜ **M4 第 2 章**
> **目标**:① 用 `subprocess` 在 Python 里调用外部命令(ping/git/系统工具),= Java `ProcessBuilder`;② 用 `psutil` 跨平台读系统指标(内存/磁盘/CPU)。写完这章你能写「健康检查脚本」「系统巡检脚本」。

> 📐 **本教程的契约**:§24.2–§24.5 全部对应作业(5 个函数)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `run_command` | §24.2 | subprocess.run + capture_output + text + timeout |
| `run_command_safely` | §24.3 | try/except 包住 subprocess(EAFP) |
| `ping_host` | §24.4 | 跨平台参数 + returncode 判断 + 超时兜底 |
| `memory_usage_percent` | §24.5 | psutil.virtual_memory |
| `disk_free_gb` | §24.5 | psutil.disk_usage + 字节换算 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

① 预览猜 → ② 写 assignment(5 个函数)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 调外部命令要 `ProcessBuilder("ping", "127.0.0.1").start()` 再手动读流、等退出码。Python 的 `subprocess.run(...)` 一步到位返回什么对象?
2. `subprocess.run` 默认把 stdout 当 `bytes` 返回。怎么让它返回 `str`?(= Java 读流指定 charset)
3. 命令不存在、或超时,subprocess 会抛什么异常?运维脚本里该怎么处理才「绝不崩」?
4. ping 在 macOS/Linux 用 `-c`,Windows 用 `-n`。怎么写一个跨平台 ping?
5. Java 想读「内存用了百分之几」很费劲(OperatingSystemMXBean)。Python 一行怎么读?

---

## §24.1 subprocess 是什么 🟡

`subprocess` = 在 Python 里**启动子进程**、跟它交互(给输入、读输出、等退出)的标准库。

```
你的 Python 脚本 → subprocess.run(["git", "status"]) → 起一个 git 子进程
                     ↑ 等它跑完,拿 stdout/stderr/returncode
```

> 🟡 **Java 对比**:= `ProcessBuilder` + `Process`。Python 的 `subprocess.run` 把 Java 那套「builder.start() → getInputStream → 读流 → waitFor → exitValue」压成一个调用 + 一个返回对象,体验好太多。

| subprocess API | 作用 | Java 对应 |
|----------------|------|-----------|
| `run(args, ...)` | 跑命令,等它结束,返回 CompletedProcess | `pb.start()` + `waitFor()` |
| `Popen(...)` | 起进程但不等(异步读/管道) | `pb.start()` 不 waitFor |
| `CompletedProcess` | 结果对象(.returncode/.stdout/.stderr) | `Process` + 手动收集 |

**90% 场景用 `run` 就够**(同步等结果)。管道流式才用 `Popen`。

---

## §24.2 run + capture_output + text + timeout(对应:`run_command`)🟢

```python
import subprocess

r = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
r.returncode   # 0(成功)/ 非 0(失败)
r.stdout       # "git version 2.43.0\n"   ← str(text=True)
r.stderr       # ""                        ← str
```

四个关键参数:

| 参数 | 作用 | 不设的后果 |
|------|------|-----------|
| `capture_output=True` | 把 stdout/stderr 收进结果对象 | 输出直接打到你的控制台,拿不到 |
| `text=True` | 返回 `str` 而非 `bytes` | 拿到 `b"git version...\n`,每次要 `.decode()` |
| `timeout=10` | 超时抛 `TimeoutExpired` | 子进程卡住,你的脚本永远 hang |
| (传 list 不传 shell=True) | 安全 exec | `shell=True` 有**命令注入**风险 |

> 🔴 **安全红线**:永远传 `list`(`["git", "status"]`),**别用 `shell=True`**。`shell=True` 会把命令交给 shell 解析,如果参数里有用户输入,就是命令注入漏洞(= Java 里 `Runtime.exec` 拼字符串的坑)。

### CompletedProcess 对象

```python
r = subprocess.run([sys.executable, "-c", "print(42)"], capture_output=True, text=True)
r.args        # 你传的命令 list
r.returncode  # 0
r.stdout      # "42\n"
r.stderr      # ""
```

> ✅ 做 `run_command`:`return subprocess.run(args, capture_output=True, text=True, timeout=timeout)`。

---

## §24.3 异常处理:绝不崩的 run_command_safely(对应)🔴

`subprocess.run` 会抛三种异常:
- `FileNotFoundError`:命令本身不存在(打错字/没装)。
- `subprocess.TimeoutExpired`:超过 timeout。
- `PermissionError`:没权限执行。

运维脚本要**绝不让一个命令的失败拖垮整个脚本**(= Java 里 catch 住 `IOException`)。这是 Ch07 讲的 **EAFP**(Easier to Ask Forgiveness than Permission)风格——先跑,出错再处理:

```python
def run_command_safely(args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        return False, f"命令不存在: {args[0]}"
    except subprocess.TimeoutExpired:
        return False, f"命令超时: {args[0]}"

    ok = result.returncode == 0
    output = result.stdout if ok else (result.stdout + result.stderr)
    return ok, output.strip()
```

设计要点:
- 返回 `tuple[bool, str]`——调用方不用 try/except,看布尔就行。这是运维脚本的常见封装模式(把异常拍扁成返回值)。
- 成功只回 stdout;失败把 stdout + stderr 都带回去(方便排查)。
- `.strip()` 去掉末尾换行,输出干净。

> 🟡 **Java 对比**:Java 你大概会写 `try { ... } catch (IOException e) { return Result.fail(e.getMessage()); }`。一样的思路,Python 的 `try/except` 更轻。

> ✅ 做 `run_command_safely`:try 里 run;except FileNotFoundError / TimeoutExpired 返回 (False, 提示);看 returncode 决定 ok,output 成功取 stdout 失败取 stdout+stderr。

---

## §24.4 跨平台 ping(对应:`ping_host`)🟡

ping 是健康检查的核心。坑在于 **macOS/Linux 和 Windows 的 ping 参数不同**:
- Unix:`ping -c 1 -W 2 host`(`-c`=次数,`-W`=等几秒)
- Windows:`ping -n 1 -w 2000 host`(`-n`=次数,`-w`=等几毫秒)

用 `platform.system()` 判断系统,选对应参数:

```python
import platform, subprocess

def ping_host(host: str, timeout: float = 2.0) -> bool:
    is_win = platform.system() == "Windows"
    if is_win:
        args = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
    else:
        args = ["ping", "-c", "1", "-W", str(int(timeout)), host]
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout + 2)
        return r.returncode == 0      # 0 = 通,非 0 = 不通
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

要点:
- **returncode 判断**:`ping` 通了退出码 0,不通(超时/不可达)退出码非 0。
- **超时兜底**:`subprocess.run` 的 timeout 设比 ping 自身 `-W` 稍大(这里 `timeout+2`),双保险防卡死。
- **`.invalid` 域名测试**:RFC 2606 保留的假域名,DNS 查询**立即失败**,适合单元测试(不用真等超时)。

> 🟡 **Java 对比**:Java 里 `InetAddress.isReachable(timeout)` 能判可达,但它在 Unix 上常因没 root 权限发 ICMP 而失效。用 `subprocess`/`ProcessBuilder` 调系统 ping 反而更可靠——Python 这边同理。

> ✅ 做 `ping_host`:`platform.system()` 选参数,`subprocess.run` 后看 `returncode == 0`,异常兜底返回 False。

---

## §24.5 psutil:跨平台系统监控(对应:`memory_usage_percent`、`disk_free_gb`)🟢

`psutil`(python system and process utilities)= 跨平台系统监控库。读 CPU/内存/磁盘/网络/进程列表,一行一个指标。**Java 没有等价的单库**(要组合 `OperatingSystemMXBean`、`File.getUsableSpace()` 等,且跨平台一致性差)。

```python
import psutil

psutil.virtual_memory()        # 内存 namedtuple
# svmem(total=17179869184, available=8589934592, used=8589934592, percent=50.0, ...)

psutil.disk_usage("/")         # 磁盘 namedtuple
# sdiskusage(total=500107862016, used=300000000000, free=200000000000, percent=60.0)

psutil.cpu_percent(interval=0.1)   # CPU 使用率
psutil.net_io_counters()           # 网络收发字节数
psutil.process_iter()              # 所有进程(可拿 pid/name/memory)
```

### 作业实现

```python
def memory_usage_percent() -> float:
    return psutil.virtual_memory().percent      # 已用 / 总量 * 100

def disk_free_gb(path: str = "/") -> float:
    return psutil.disk_usage(path).free / (1024 ** 3)   # 字节 → GB
```

**字节换算**:磁盘 `free` 是字节,换 GB 用 `/ (1024 ** 3)`(1024 进制,运维习惯;若要「硬盘厂家的 GB」用 1000³)。

> ✅ 做 `memory_usage_percent`:`psutil.virtual_memory().percent`。
> 做 `disk_free_gb`:`psutil.disk_usage(path).free / (1024 ** 3)`。

---

## §24.6 实战:批量服务健康检查(讲透不出题)

把本章零件串成真实脚本:「ping 一组服务,报告谁挂了」:

```python
def health_check(hosts: list[str]) -> dict[str, bool]:
    """批量 ping,返回 {host: 是否通}。任何一个失败都不会让脚本崩。"""
    return {h: ping_host(h) for h in hosts}     # §24.4

if __name__ == "__main__":
    services = ["127.0.0.1", "8.8.8.8", "definitely-not-real.invalid"]
    result = health_check(services)
    for host, ok in result.items():
        status = "✅ UP" if ok else "❌ DOWN"
        print(f"{host:30s} {status}")
    print(f"本机内存使用: {memory_usage_percent():.1f}%")   # §24.5
```

看,运维监控脚本的核心就是「**调命令/读指标 + 绝不崩 + 汇报**」。

---

## §24.7 Java 老手常踩的坑 ⚠️

1. **`shell=True` 命令注入**:永远传 `list`,别 `shell=True`。除非你真的需要 shell 特性(管道/通配符),那也要 `shlex.quote` 转义用户输入。
2. **忘设 `timeout`**:`subprocess.run` 默认无超时,子进程 hang 你的脚本就 hang。运维脚本必设 timeout。
3. **忘 `capture_output`**:不设的话子进程输出直接打到你的控制台,你拿不到 stdout。
4. **拿 `bytes` 当 `str` 用**:默认返回 bytes(`b"..."`)。要 str 加 `text=True`(老代码用 `universal_newlines=True`,已废弃别名)。
5. **以为 returncode 非 0 会抛异常**:`run` 默认**不抛**(`check=False`),非 0 退出码只是 `returncode != 0`。要它抛得加 `check=True`(抛 `CalledProcessError`)。
6. **Java 思维:catch IOException 写一大坨**:Python EAFP 风格,`try/except` 更轻,但记得 catch **具体的**异常(FileNotFoundError/TimeoutExpired),别裸 `except:`。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `run_command` | subprocess.run + capture_output/text/timeout | 🟢 |
| `run_command_safely` | try/except 包 subprocess(EAFP) | 🟡 |
| `ping_host` | 跨平台参数 + returncode + 超时兜底 | 🟡 |
| `memory_usage_percent` | psutil.virtual_memory | 🟢 |
| `disk_free_gb` | psutil.disk_usage + 字节换算 | 🟢 |

```bash
uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v
```

全绿 = 掌握 Ch24。

---

## ✅ 自测

- [ ] 能说清 `subprocess.run` 的 `capture_output`/`text`/`timeout` 三个参数各防什么坑
- [ ] 知道为什么不能 `shell=True`(命令注入)
- [ ] 知道 `run` 默认非 0 退出码**不抛**异常,要抛得加 `check=True`
- [ ] 能写出「绝不崩」的命令封装(EAFP + 具体异常)
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「`subprocess.run` 不设 timeout 会怎样?设了 timeout 触发什么异常?」— 重读 §24.2
2. 「为什么运维脚本要把 `subprocess.run` 包进 try/except 返回 `(bool, str)`?这对应 Java 什么习惯?」— 重读 §24.3
3. 「为什么不能 `shell=True`?给它一个命令注入的具体例子。」— 重读 §24.2(安全红线)

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch25 CLI 工具 Typer + Rich

会调命令了,接下来学「**把脚本变成漂亮的命令行工具**」——`Typer`(类型注解驱动 CLI,= Java Picocli)+ `Rich`(终端表格/颜色/进度条)。这是你能在同事面前炫耀的那种脚本。
