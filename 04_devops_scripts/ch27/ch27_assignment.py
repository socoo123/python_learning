"""
Ch27 作业:配置管理与系统监控 —— psutil 巡检 + webhook 告警(M4 收官)。

主线场景:你是电商后端的 on-call 工程师,要写一个「系统巡检脚本」——
① 配置分层(默认 < 环境变量)→ ② 检查磁盘/内存/CPU 水位 + 关键端口探活
→ ③ 汇总健康报告 → ④ 异常时推 webhook 告警(飞书/钉钉/Slack)。

8 个函数,最后 1 题把前 7 个组装成完整巡检。在每处 TODO 写实现,然后:

    uv sync --extra devops   # 本章依赖 psutil(extras 互斥)
    uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v

全绿 = 你掌握了 Ch27 = M4 运维脚本毕业 🎓。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

设计说明:本章配置用纯 stdlib 手写「默认 < 环境变量」分层(Ch22 学的
pydantic-settings 是生产升级版,tutorial §27.2 末尾有对照)。webhook 用
stdlib urllib,不引 requests,零额外依赖——巡检脚本常跑在受限服务器上。
"""
import json
import socket
import urllib.request

import psutil


# ========== §27.2 配置分层:load_thresholds ==========


def load_thresholds(env: dict) -> dict:
    """
    【配置 · §27.2】从 env dict(模拟环境变量)读告警阈值,带默认值。
    规则:env 里有就用 env(转 float),没有用默认。模拟「默认 < 环境变量」分层。

    示例:
        load_thresholds({})                       -> {"disk": 80.0, "memory": 80.0, "cpu": 90.0}
        load_thresholds({"DISK_THRESHOLD": "95"}) -> {"disk": 95.0, "memory": 80.0, "cpu": 90.0}
        load_thresholds({"HOME": "/root"})        -> 全默认(无关变量忽略)

    思路(配置分层:默认兜底,env 覆盖):
        result = {"disk": 80.0, "memory": 80.0, "cpu": 90.0}   # 默认值
        if "DISK_THRESHOLD" in env:
            result["disk"] = float(env["DISK_THRESHOLD"])      # env 覆盖 + 转 float
        - 环境变量读出来永远是 str("95"),必须 float() 才能和数字阈值比较
        - 入参用 env dict 而不是直接读 os.environ:测试传 dict 即可,不污染真实环境
    """
    # TODO: 默认 dict + 三个 if 覆盖(float 转换)
    ...


# ========== §27.3 水位三检:check_disk / check_memory / check_cpu ==========


def check_disk(path: str = "/", threshold: float = 80.0) -> dict:
    """
    【psutil · §27.3】检查指定路径所在分区的磁盘水位。
    返回 {"percent", "free_gb", "total_gb", "ok"};ok = percent < threshold(严格小于)。

    示例(数值随机器而变,测试会 mock):
        check_disk("/", threshold=80.0)
            -> {"percent": 62.3, "free_gb": 78.57, "total_gb": 250.0, "ok": True}
        check_disk("/var/log", threshold=80.0)   # 日志分区 91% 超标
            -> {"percent": 91.0, "free_gb": 4.2, "total_gb": 50.0, "ok": False}

    思路(psutil.disk_usage,Ch24 学过):
        du = psutil.disk_usage(path)
        - du.percent 直接是百分比;du.free/du.total 单位是【字节】,要 / (1024**3) 转 GB
        - round(x, 2) 保留 2 位小数;ok = du.percent < threshold
    """
    # TODO: psutil.disk_usage(path) → 组装 dict,字节转 GB,ok = percent < threshold
    ...


def check_memory(threshold: float = 80.0) -> dict:
    """
    【psutil · §27.3】检查内存水位。返回 {"percent", "ok"};ok = percent < threshold。

    示例(数值随机器而变):
        check_memory(threshold=80.0) -> {"percent": 55.0, "ok": True}
        check_memory(threshold=40.0) -> {"percent": 55.0, "ok": False}   # 阈值更严就超标

    思路(psutil.virtual_memory,Ch24 学过):
        vm = psutil.virtual_memory()
        - vm.percent 直接是百分比;ok = vm.percent < threshold
    """
    # TODO: psutil.virtual_memory() → 返回 {"percent", "ok"}
    ...


def check_cpu(threshold: float = 90.0, interval: float = 0.1) -> dict:
    """
    【psutil · §27.3】检查 CPU 水位。返回 {"percent", "ok"};ok = percent < threshold。

    示例(数值随机器而变):
        check_cpu(threshold=90.0) -> {"percent": 42.0, "ok": True}
        check_cpu(threshold=30.0) -> {"percent": 42.0, "ok": False}

    思路(psutil.cpu_percent):
        percent = psutil.cpu_percent(interval=interval)   # 阻塞采样 interval 秒
        - 必须传 interval!不传时首次调用恒返回 0.0(它算「距上次调用」的平均,首次没有"上次")
        - ok = percent < threshold
    """
    # TODO: psutil.cpu_percent(interval=interval) → 返回 {"percent", "ok"}
    ...


# ========== §27.4 端口探活:check_port ==========


def check_port(host: str, port: int, timeout: float = 2.0) -> dict:
    """
    【socket · §27.4】TCP 探活关键端口(DB 5432 / Redis 6379...),返回 {"host", "port", "ok"}。
    连得上 ok=True;拒连/超时/DNS 失败 ok=False——绝不抛异常(EAFP)。

    示例:
        check_port("127.0.0.1", 5432, timeout=1.0) -> {"host": "127.0.0.1", "port": 5432, "ok": True}
        check_port("db.internal", 6379, timeout=1.0)   # Redis 挂了/网络不通
            -> {"host": "db.internal", "port": 6379, "ok": False}

    思路(socket.create_connection = Java new Socket().connect(addr, timeout)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return {"host": host, "port": port, "ok": True}
        except OSError:
            return {"host": host, "port": port, "ok": False}
        - 拒连(ConnectionRefusedError)/超时(socket.timeout)/DNS(socket.gaierror)
          全是 OSError 子类,一个 except 全兜住
        - timeout 必传!忘了可能挂起几分钟,巡检卡死
        - with 包住:探活 socket 用完即关,不泄漏文件描述符
    """
    # TODO: with create_connection(...) 成功返 ok=True,except OSError 返 ok=False
    ...


# ========== §27.5 汇总:build_health_report ==========


def build_health_report(checks: dict) -> dict:
    """
    【汇总 · §27.5】把多项检查结果汇总成健康报告。
    输入 checks = {名字: 检查dict(含 ok 键)},返回 {"overall_ok", "checks"}。
    overall_ok = 所有的 ok 都为 True;某项缺 ok 键按 False 算;空 checks 视为健康(True)。

    示例:
        build_health_report({"disk": {"ok": True}, "memory": {"ok": False}})
            -> {"overall_ok": False, "checks": {...}}
        build_health_report({}) -> {"overall_ok": True, "checks": {}}   # all([]) == True

    思路(all() = Java stream.allMatch):
        return {
            "overall_ok": all(c.get("ok", False) for c in checks.values()),
            "checks": checks,
        }
        - c.get("ok", False):脏数据缺 ok 键按 False,宁误告不漏判;c["ok"] 会 KeyError 崩巡检
    """
    # TODO: all(各 c.get("ok", False)),返回 {"overall_ok", "checks"}
    ...


# ========== §27.6 告警:send_webhook ==========


def send_webhook(url: str, payload: dict, timeout: float = 5.0) -> bool:
    """
    【webhook · §27.6】向 url POST 一个 JSON payload,成功(2xx)返回 True,失败返回 False。
    用 stdlib urllib(不引 requests),网络错误/超时绝不抛,只返回 False。

    示例:
        send_webhook("https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
                     {"overall_ok": False, "checks": {...}})   -> True   # 飞书返回 200
        send_webhook("https://example.invalid/hook", {"a": 1}) -> False  # DNS 失败,不抛

    思路(EAFP + urllib,= Java HttpClient + BodyPublishers.ofString):
        data = json.dumps(payload).encode("utf-8")       # dict → JSON str → bytes
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 300          # 2xx 算送达
        except Exception:
            return False                                 # 任何异常返 False,绝不抛
        - 忘 Content-Type,服务器把 JSON 当普通文本;忘 timeout 可能挂起
    """
    # TODO: dumps→encode→Request(POST + json 头)→urlopen,2xx 返 True,异常返 False
    ...


# ========== §27.7 综合:run_inspection ==========


def run_inspection(env: dict, webhook_url: str | None = None, disk_path: str = "/") -> dict:
    """
    【综合 · §27.7】完整巡检:读配置 → 三检(磁盘/内存/CPU)→ 汇总 → 异常推 webhook。
    返回 {"report": 健康报告, "webhook_sent": None|True|False}。

    webhook_sent 三态:None = 没推(健康或没配 url);True = 推了且成功;False = 推了但失败。

    示例(测试会 monkeypatch 各检查函数,不连真机):
        run_inspection({}, webhook_url="https://hook.example/x")
            # 各项正常 -> {"report": {"overall_ok": True, ...}, "webhook_sent": None}
            # 磁盘超标 -> {"report": {"overall_ok": False, ...}, "webhook_sent": True}

    思路(纯组装,复用前 7 个函数):
        thresholds = load_thresholds(env)                       # §27.2
        checks = {
            "disk": check_disk(disk_path, thresholds["disk"]),
            "memory": check_memory(thresholds["memory"]),
            "cpu": check_cpu(thresholds["cpu"]),
        }
        report = build_health_report(checks)                    # §27.5
        webhook_sent = None
        if not report["overall_ok"] and webhook_url:            # 异常 且 配了 url 才推
            webhook_sent = send_webhook(webhook_url, report)    # §27.6
        return {"report": report, "webhook_sent": webhook_sent}
    """
    # TODO: 按思路串 5 步;webhook_sent 初始 None,仅「不健康且有 url」时赋为 send_webhook 返回值
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch27/ch27_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import os

    webhook = os.environ.get("WEBHOOK_URL")          # webhook URL 也走环境变量(含 token,敏感)
    result = run_inspection(dict(os.environ), webhook_url=webhook)
    print(json.dumps(result["report"], indent=2, ensure_ascii=False))
    if result["webhook_sent"] is True:
        print("已推送 webhook 告警")
    elif result["webhook_sent"] is False:
        print("webhook 推送失败(脚本不崩,等下一轮巡检)")
    else:
        print("系统健康或未配置 webhook,无需推送")
