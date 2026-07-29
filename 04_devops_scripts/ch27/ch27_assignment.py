"""
Ch27 作业:配置管理与系统监控 —— psutil 巡检 + webhook 告警(M4 收官)。

把 M4 串成生产级「系统巡检脚本」:① 配置分层(默认 < 环境变量)→ ② 检查磁盘/内存水位
→ ③ 汇总健康报告 → ④ 异常时推 webhook 告警(飞书/钉钉/Slack)。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch27/test_ch27_assignment.py -v

全绿 = 你掌握了 Ch27 = M4 运维脚本毕业 🎓。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

设计说明:本章配置用纯 stdlib(os/dict)实现「env > 默认」分层(Ch22 学的
pydantic-settings 是生产升级版,这里手写以加固理解)。webhook 用 stdlib urllib,
不引 requests,零额外依赖。
"""


# ========== §27.2 配置分层:load_thresholds ==========


def load_thresholds(env: dict) -> dict:
    """
    【配置 · §27.2】从 env dict(模拟环境变量)读告警阈值,带默认值。
    规则:env 里有就用 env(转 float),没有用默认。模拟「环境变量 > 默认」分层。

    示例:
        load_thresholds({})                              -> {"disk": 80.0, "memory": 80.0, "cpu": 90.0}
        load_thresholds({"DISK_THRESHOLD": "95"})        -> {"disk": 95.0, "memory": 80.0, "cpu": 90.0}

    思路(配置分层:默认兜底,env 覆盖):
        result = {"disk": 80.0, "memory": 80.0, "cpu": 90.0}   # 默认
        if "DISK_THRESHOLD" in env:
            result["disk"] = float(env["DISK_THRESHOLD"])      # env 覆盖 + 转浮点
        if "MEMORY_THRESHOLD" in env:
            result["memory"] = float(env["MEMORY_THRESHOLD"])
        if "CPU_THRESHOLD" in env:
            result["cpu"] = float(env["CPU_THRESHOLD"])
        return result
    """
    # TODO: 默认 dict + 三个 if 覆盖(float 转换)
    ...


# ========== §27.3 巡检:check_disk ==========


def check_disk(path: str = "/", threshold: float = 80.0) -> dict:
    """
    【psutil · §27.3】检查指定路径所在分区的磁盘水位。
    返回 {percent, free_gb, total_gb, ok};ok = percent < threshold。

    示例:
        check_disk("/", threshold=80)
            -> {"percent": 62.3, "free_gb": 78.5, "total_gb": 250.0, "ok": True}

    思路(Ch24 学过 psutil.disk_usage):
        import psutil
        du = psutil.disk_usage(path)
        return {
            "percent": du.percent,
            "free_gb": round(du.free / (1024 ** 3), 2),
            "total_gb": round(du.total / (1024 ** 3), 2),
            "ok": du.percent < threshold,
        }
    """
    # TODO: psutil.disk_usage(path),组装 dict,ok = percent < threshold
    ...


# ========== §27.3 巡检:check_memory ==========


def check_memory(threshold: float = 80.0) -> dict:
    """
    【psutil · §27.3】检查内存水位。返回 {percent, ok};ok = percent < threshold。

    示例:
        check_memory(threshold=80) -> {"percent": 55.0, "ok": True}

    思路(Ch24 学过 psutil.virtual_memory):
        import psutil
        vm = psutil.virtual_memory()
        return {"percent": vm.percent, "ok": vm.percent < threshold}
    """
    # TODO: psutil.virtual_memory(),返回 {percent, ok}
    ...


# ========== §27.4 汇总:build_health_report ==========


def build_health_report(checks: dict) -> dict:
    """
    【汇总 · §27.4】把多项检查结果汇总成健康报告。
    输入 checks = {名字: 检查dict(含 ok 键)},返回 {overall_ok, checks}。
    overall_ok = 所有的 ok 都为 True;空 checks 视为健康(True)。

    示例:
        checks = {"disk": {"percent": 50, "ok": True},
                  "memory": {"percent": 90, "ok": False}}
        build_health_report(checks)
            -> {"overall_ok": False, "checks": {...}}

    思路(all() = Java stream.allMatch):
        return {
            "overall_ok": all(c.get("ok", False) for c in checks.values()),
            "checks": checks,
        }
    """
    # TODO: all(各 c["ok"]),返回 {overall_ok, checks}
    ...


# ========== §27.5 告警:send_webhook ==========


def send_webhook(url: str, payload: dict, timeout: float = 5.0) -> bool:
    """
    【webhook · §27.5】向 url POST 一个 JSON payload,成功(2xx)返回 True,失败返回 False。
    用 stdlib urllib(不引 requests),网络错误/超时绝不抛,只返回 False。

    示例:
        send_webhook("https://oapi.dingtalk.com/robot/send?token=xxx",
                     {"text": "磁盘水位告警"})
            -> True/False

    思路(EAFP + urllib):
        import json as _json
        import urllib.request
        data = _json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False
    """
    # TODO: dumps→bytes→Request(POST)→urlopen,2xx 返回 True,异常返回 False
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch27/ch27_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    thresholds = load_thresholds({"DISK_THRESHOLD": "70"})
    print("阈值:", thresholds)

    disk = check_disk("/", threshold=thresholds["disk"])
    mem = check_memory(threshold=thresholds["memory"])
    report = build_health_report({"disk": disk, "memory": mem})
    print("健康报告:", report)

    if not report["overall_ok"]:
        # 真实场景:url 换成你的飞书/钉钉 webhook
        ok = send_webhook("https://example.invalid/hook", report)
        print("webhook 推送:", ok)
