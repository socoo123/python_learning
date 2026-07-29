"""
Ch24 作业:进程与子进程管理 —— subprocess / psutil。

运维脚本第二大场景:① 调用外部命令(ping/系统工具/git...);② 读取系统指标
(内存/磁盘/CPU)。subprocess = Java ProcessBuilder;psutil = 跨平台系统监控
(Java 没有等价的单一库,要靠 OperatingSystemMXBean 等拼凑)。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch24/test_ch24_assignment.py -v

全绿 = 你掌握了 Ch24。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import platform
import subprocess


# ========== §24.2 subprocess:run_command ==========


def run_command(args: list[str], timeout: float = 10.0) -> subprocess.CompletedProcess:
    """
    【subprocess · §24.2】执行外部命令,返回 CompletedProcess 对象。
    捕获 stdout/stderr 为【文本】,设超时。

    示例:
        r = run_command([sys.executable, "-c", "print(42)"])
        r.returncode  -> 0
        r.stdout      -> "42\\n"          # text=True,所以是 str 不是 bytes
        r.stderr      -> ""

    思路(对比 Java ProcessBuilder):
        subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        - capture_output=True:把 stdout/stderr 收进 result.stdout/.stderr
        - text=True:返回 str 而不是 bytes(= Java 读流时指定 charset)
        - timeout:超时抛 subprocess.TimeoutExpired(务必设,防脚本卡死)
        ⚠️ 不要用 shell=True(命令注入风险),传 list 让 Python 自己 exec
    """
    # TODO: subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    ...


# ========== §24.3 异常处理:run_command_safely ==========


def run_command_safely(args: list[str]) -> tuple[bool, str]:
    """
    【subprocess · §24.3】安全执行命令:捕获所有异常,绝不抛错。
    返回 (是否成功, 输出文本)。成功=returncode==0,输出取 stdout;
    失败取「stdout + stderr」或错误信息。

    示例:
        run_command_safely([sys.executable, "-c", "print('ok')"])
            -> (True, "ok\\n")
        run_command_safely(["不存在的命令xyz"])
            -> (False, "命令不存在: ...")        # FileNotFoundError 被捕获

    思路(EAFP,Ch07 学过:先干,出错再处理):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            return False, f"命令不存在: {args[0]}"
        except subprocess.TimeoutExpired:
            return False, f"命令超时: {args[0]}"

        ok = result.returncode == 0
        output = result.stdout if ok else (result.stdout + result.stderr)
        return ok, output.strip()
    """
    # TODO: try/except FileNotFoundError/TimeoutExpired,看 returncode 决定 ok
    ...


# ========== §24.4 跨平台 ping:ping_host ==========


def ping_host(host: str, timeout: float = 2.0) -> bool:
    """
    【subprocess · §24.4】ping 一个主机,通返回 True,不通/超时返回 False。
    跨平台:Windows 用 -n/-w,Unix(macOS/Linux)用 -c/-W。

    示例:
        ping_host("127.0.0.1")      -> True     # 本机永远通
        ping_host("xxx.invalid")     -> False    # DNS 解析失败,快速返回 False

    思路:
        is_win = platform.system() == "Windows"
        args = (["ping", "-n", "1", "-w", str(int(timeout*1000)), host] if is_win
                else ["ping", "-c", "1", "-W", str(int(timeout)), host])
        try:
            r = subprocess.run(args, capture_output=True, timeout=timeout + 2)
            return r.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
        - returncode==0 表示通;ping 不通用非 0 退出码表示
        - .invalid 是 RFC2606 保留域名,DNS 查询立即失败,适合测试
    """
    # TODO: 按 platform.system() 选 ping 参数,run 后看 returncode
    ...


# ========== §24.5 psutil:memory_usage_percent ==========


def memory_usage_percent() -> float:
    """
    【psutil · §24.5】返回系统【内存】使用率(百分比,0~100)。

    示例:
        memory_usage_percent() -> 62.3

    思路:
        import psutil
        return psutil.virtual_memory().percent
        - virtual_memory() 返回 namedtuple:.total/.available/.used/.percent
        - .percent 是已用占总量的百分比(= 已用 / 总量 * 100)
    """
    # TODO: psutil.virtual_memory().percent
    ...


# ========== §24.5 psutil:disk_free_gb ==========


def disk_free_gb(path: str = "/") -> float:
    """
    【psutil · §24.5】返回指定路径所在分区的【可用空间】(GB)。

    示例:
        disk_free_gb("/")           -> 78.5      # 根分区剩 78.5 GB
        disk_free_gb("/Users")      -> 78.5      # macOS 同分区

    思路:
        import psutil
        return psutil.disk_usage(path).free / (1024 ** 3)
        - disk_usage(path) 返回 namedtuple:.total/.used/.free(字节)
        - / (1024**3) 把字节换算成 GB(1024 进制,不是 1000)
    """
    # TODO: psutil.disk_usage(path).free / (1024**3)
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

    print("ping 127.0.0.1:", ping_host("127.0.0.1"))

    print("memory %:", memory_usage_percent())
    print("disk free GB:", disk_free_gb("/"))
