"""
Ch24 作业:进程与子进程管理 —— subprocess / psutil。

主线场景:你是今晚的 on-call。监控平台每晚跑一次「巡检机器人」:对目标机跑探测
命令(绝不崩)→ 跨平台 ping 一组服务 → 采集本机内存/磁盘指标 → 按阈值判断告警
→ 汇总成一份结构化健康报告。subprocess = Java ProcessBuilder;psutil = 跨平台
系统监控(Java 没有等价单一库,要靠 OperatingSystemMXBean 等拼凑)。

8 个函数,从单知识点到综合递进(最后一题复用前 7 个)。写完运行:

    uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v

全绿 = 你掌握了 Ch24。

每题 docstring 标注【对应小节】,卡住 → 回查 tutorial.md 对应 §。
"""
import platform
import subprocess

import psutil


# ========== §24.2 run 三件套:run_command ==========


def run_command(args: list[str], timeout: float = 10.0) -> subprocess.CompletedProcess:
    """
    【对应 §24.2】巡检第一步:执行外部命令,返回 CompletedProcess 对象。
    捕获 stdout/stderr 为【文本】,并设超时防卡死。

    示例:
        r = run_command([sys.executable, "-c", "print(42)"])
        r.returncode  -> 0
        r.stdout      -> "42\\n"          # text=True,所以是 str 不是 bytes
        r.stderr      -> ""

    提示(对比 Java ProcessBuilder 的 start+读流+waitFor 一条龙):
        subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        - capture_output=True:把 stdout/stderr 收进 result(不设则 stdout 是 None)
        - text=True:返回 str 而不是 bytes(= Java 读流时指定 charset)
        - timeout:超时抛 subprocess.TimeoutExpired(本题不 catch,§24.3 才包)
        ⚠️ 不要用 shell=True(命令注入风险),传 list 让 Python 自己 exec
    """
    # TODO: subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    ...


# ========== §24.3 EAFP 封装:run_command_safely ==========


def run_command_safely(args: list[str], timeout: float = 10.0) -> tuple[bool, str]:
    """
    【对应 §24.3】安全执行命令:对一批机器巡检时,一台失败绝不拖垮整批。
    捕获所有异常,绝不抛错。返回 (是否成功, 输出文本)。

    契约:
        成功(returncode == 0) -> (True, stdout.strip())
        非 0 退出              -> (False, (stdout + stderr).strip())  # stderr 才是原因
        命令不存在             -> (False, "命令不存在: <命令名>")     # FileNotFoundError
        超时                  -> (False, "命令超时: <命令名>")       # TimeoutExpired

    示例:
        run_command_safely([sys.executable, "-c", "print('ok')"])
            -> (True, "ok")
        run_command_safely(["不存在的命令xyz"])
            -> (False, "命令不存在: 不存在的命令xyz")

    提示(EAFP,Ch07:先跑,出错再处理,别事先检查命令存不存在):
        try 里 subprocess.run 三件套;except 要【具体】(FileNotFoundError /
        subprocess.TimeoutExpired),别裸 except——会把 KeyboardInterrupt 和
        代码 bug 一起吞掉。
    """
    # TODO: try/except FileNotFoundError/TimeoutExpired,看 returncode 决定 ok
    ...


# ========== §24.4 跨平台 ping:ping_host ==========


def ping_host(host: str, timeout: float = 2.0) -> bool:
    """
    【对应 §24.4】ping 一个主机,通返回 True,不通/超时/没装 ping 都返回 False。
    跨平台:三个平台参数不同,且 macOS 的 -W 单位是【毫秒】、Linux 是【秒】!

    示例:
        ping_host("127.0.0.1")              -> True     # 本机回环永远通
        ping_host("definitely-not-real.invalid") -> False  # DNS 立即失败,秒回 False

    提示:
        system = platform.system()   # "Windows" / "Darwin"(macOS)/ "Linux"
        Windows: ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
        Darwin : ["ping", "-c", "1", "-W", str(int(timeout * 1000)), host]  # 毫秒!
        Linux  : ["ping", "-c", "1", "-W", str(int(timeout)), host]         # 秒!
        通了 returncode == 0;不通非 0。
        超时双保险:subprocess.run(timeout=timeout + 2) 兜底(防参数单位搞错死等);
        except (subprocess.TimeoutExpired, FileNotFoundError) -> False。
        .invalid 是 RFC2606 保留域名,DNS 查询立即失败,适合测试「不通」分支。
    """
    # TODO: 按 platform.system() 三分支拼参数,run 后看 returncode,异常兜底 False
    ...


# ========== §24.5 字节换算:bytes_to_gb ==========


def bytes_to_gb(n: float) -> float:
    """
    【对应 §24.5】字节数 → GB,1024 进制(= `df -h` 看到的数)。
    独立成纯函数:好测(精确断言)、好复用(磁盘/内存/网络流量都用它)。

    示例:
        bytes_to_gb(1073741824)   -> 1.0     # 1 GiB = 1024³ 字节
        bytes_to_gb(5368709120)   -> 5.0
        bytes_to_gb(0)            -> 0.0

    提示:一行,n / (1024 ** 3)。别用 1000³——那是硬盘厂商标的 GB,
    比 1024 进制「看着多」,运维不认(500GB 硬盘装系统只剩 465G 就是这个差)。
    """
    # TODO: n / (1024 ** 3)
    ...


# ========== §24.5 psutil:memory_usage_percent ==========


def memory_usage_percent() -> float:
    """
    【对应 §24.5】返回系统【内存】使用率(百分比,0~100)。

    示例:
        memory_usage_percent() -> 62.3    # 具体值随机器而变

    提示:
        psutil.virtual_memory() 返回 namedtuple:.total/.available/.used/.percent
        .percent 就是「已用/总量×100」,一行拿走。
        对比 Java:OperatingSystemMXBean 各平台实现不一致,macOS 上常不支持。
    """
    # TODO: psutil.virtual_memory().percent
    ...


# ========== §24.5 psutil:disk_free_gb ==========


def disk_free_gb(path: str = "/") -> float:
    """
    【对应 §24.5】返回指定路径所在分区的【可用空间】(GB,1024 进制)。

    示例:
        disk_free_gb("/")       -> 465.8    # 根分区剩 465.8 GB(值随机器而变)
        disk_free_gb("/Users")  -> 465.8    # macOS 同一分区

    提示:
        psutil.disk_usage(path) 返回 namedtuple:.total/.used/.free(单位:字节)
        复用你刚写的 bytes_to_gb 换算——别重算一遍 1024**3。
    """
    # TODO: bytes_to_gb(psutil.disk_usage(path).free)
    ...


# ========== §24.6 阈值告警:check_thresholds ==========


def check_thresholds(metrics: dict[str, float], limits: dict[str, float]) -> list[str]:
    """
    【对应 §24.6】阈值判断【纯函数】:不碰 psutil,只吃两个 dict,输出告警消息列表。
    拆开才可用确定性输入做单测(你没法让测试机内存「刚好 81%」)。

    约定:limits 的 key 以 _max/_min 结尾,基础名 = key[:-4]:
        "memory_percent_max" → 查 metrics["memory_percent"],值 > 上限 才告警
        "disk_free_gb_min"   → 查 metrics["disk_free_gb"],  值 < 下限 才告警
    消息格式:f"{name}={value} 超过上限 {limit}" / f"{name}={value} 低于下限 {limit}"

    示例:
        check_thresholds({"memory_percent": 87.5, "disk_free_gb": 12.0},
                         {"memory_percent_max": 80.0, "disk_free_gb_min": 20.0})
            -> ["memory_percent=87.5 超过上限 80.0", "disk_free_gb=12.0 低于下限 20.0"]
        check_thresholds({"memory_percent": 50.0}, {"memory_percent_max": 80.0})
            -> []                                  # 没超,不告警
        check_thresholds({}, {"memory_percent_max": 80.0})
            -> []                                  # metrics 缺 key:跳过,不报错

    提示:
        遍历 limits.items()(dict 保插入序,告警按此顺序产出);
        key.endswith("_max")/"_min" 判方向,[:-4] 切基础名;
        metrics.get(name) 拿到值,None 就 continue;
        严格 > / <(等于阈值不告警)。
    """
    # TODO: 按后缀约定遍历 limits,严格比较,拼消息 append
    ...


# ========== §24.7 综合:health_report ==========


def health_report(hosts: list[str], limits: dict[str, float] | None = None) -> dict:
    """
    【对应 §24.7 · 综合题】巡检机器人主流程:
    批量 ping 一组主机 + 采集本机内存/磁盘 + 阈值判断 → 一份结构化健康报告。
    监控平台拿到这份 dict 直接 json.dumps 就能发 webhook(Ch27 会干这事)。

    报告契约(6 个 key):
        "hosts":          {主机: 是否通},如 {"127.0.0.1": True, "x.invalid": False}
        "up_count":       通的主机数
        "total":          主机总数
        "memory_percent": 本机内存使用率(float)
        "disk_free_gb":   本机根分区剩余 GB(float)
        "alerts":         阈值告警消息列表;limits=None 时为 []

    示例:
        report = health_report(["127.0.0.1", "definitely-not-real.invalid"],
                               {"memory_percent_max": 80.0})
        report["hosts"]    -> {"127.0.0.1": True, "definitely-not-real.invalid": False}
        report["up_count"] -> 1
        report["total"]    -> 2
        health_report([], None)["alerts"] -> []        # 空主机、无阈值也照出报告

    提示:本题不写新知识,纯组装——
        {h: ping_host(h) for h in hosts}              # §24.4 字典推导
        metrics = {"memory_percent": memory_usage_percent(),
                   "disk_free_gb": disk_free_gb("/")}  # §24.5(key 名对齐 limits 基础名)
        check_thresholds(metrics, limits) if limits else []   # §24.6
        up_count 用 sum(1 for ok in hosts_dict.values() if ok)  # 生成器求和
    """
    # TODO: 按上面的调用关系组装前 7 个函数
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch24/ch24_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    r = run_command([sys.executable, "--version"])
    print("python version:", r.stdout.strip(), "| returncode:", r.returncode)

    ok, out = run_command_safely([sys.executable, "-c", "print('hi')"])
    print("safe run:", ok, repr(out))
    ok2, out2 = run_command_safely(["不存在的命令xyz"])
    print("safe run(不存在):", ok2, repr(out2))

    print("bytes_to_gb(5 GiB):", bytes_to_gb(5368709120))
    print("memory %:", memory_usage_percent())
    print("disk free GB:", round(disk_free_gb("/"), 1))

    metrics = {"memory_percent": memory_usage_percent(), "disk_free_gb": disk_free_gb("/")}
    print("alerts:", check_thresholds(metrics, {"memory_percent_max": 99.9, "disk_free_gb_min": 1.0}))

    report = health_report(["127.0.0.1", "definitely-not-real.invalid"],
                           {"memory_percent_max": 99.9})
    print("health report:", report)
