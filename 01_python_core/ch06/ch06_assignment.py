"""
Ch06 作业:异常、上下文管理器、文件 IO。

场景:你是电商平台的值班工程师,要写一个**日志批处理脚本**——
读 nginx 访问日志(assets/mock_data/nginx_logs.txt,13 行样本,含 2 行脏数据)
→ 逐行解析(坏行跳过)→ 聚合成统计报告 → 写出报告文件
→ 记录每阶段耗时 → 最后把结果批量「入库」(模拟事务:全部成功才 commit,否则 rollback)。

7 个任务,从自定义异常一路搭到事务上下文管理器。
在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v

全绿 = 你掌握了 Ch06。

约定:
- nginx_logs.txt 每行形如:
    192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234
- 第 4 行和第 10 行是脏数据(格式不合法),解析时要能跳过。
- 每题顶部的【对应小节】指向 tutorial.md 里的讲解。卡住 → 回查对应 §。
"""
import time
from contextlib import contextmanager
from pathlib import Path


# ========== §6.1 自定义异常 ==========


# TODO: 让 LogParseError 继承正确的基类(= Java: class XxxException extends Exception)
class LogParseError:
    """日志行解析失败的自定义异常。

    继承 Exception 即可,不需要写构造器——message 直接传给 Exception.__init__。
    """
    ...


# ========== §6.2 try/except + EAFP ==========


def parse_log_line(line: str) -> dict:
    """
    【EAFP + 自定义异常 · §6.2】解析一行 nginx 日志,提取请求路径和状态码。

    任务:返回 {"path": <请求路径>, "status": <状态码 int>}。
         任何一步解析失败(没引号段 / 拆不出路径 / 状态码不是数字),
         都抛 LogParseError(用 raise ... from e 保留原始异常)。

    示例:
        parse_log_line('192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234')
            -> {"path": "/api/products", "status": 200}
        parse_log_line("this line is malformed")
            -> 抛 LogParseError

    提示(EAFP 三段解析):
      try:
          request = line.split('"')[1]        # "GET /api/products HTTP/1.1"
          path = request.split()[1]           # "/api/products"
          status = int(line.rsplit('"', 1)[-1].split()[0])   # 200
      except (IndexError, ValueError) as e:
          raise LogParseError(f"无法解析: {line}") from e
      return {"path": path, "status": status}
    """
    # TODO: try 三段解析 + except (IndexError, ValueError) 转 LogParseError
    ...


# ========== §6.3 pathlib 读文件 + 单行容错 ==========


def parse_log_file(path: str | Path) -> tuple[list[dict], list[int]]:
    """
    【pathlib 读文件 + 单行容错 · §6.3】读取整个日志文件,逐行解析,坏行跳过。

    任务:返回 (entries, skipped) 二元组:
         - entries: 解析成功的 entry 列表(每个是 parse_log_line 返回的 dict)
         - skipped: 解析失败的【行号】列表(从 1 开始)
         不能因为某一行坏就中断整个批处理。

    示例(nginx_logs.txt 共 13 行,第 4/10 行是脏数据):
        entries, skipped = parse_log_file("assets/mock_data/nginx_logs.txt")
        len(entries)   -> 11
        skipped        -> [4, 10]

    提示:
      lines = Path(path).read_text(encoding="utf-8").splitlines()
      for i, line in enumerate(lines, 1):          # 行号从 1 开始
          try:
              entries.append(parse_log_line(line))
          except LogParseError:
              skipped.append(i)                    # try 放 for 里面,粒度是单行
    """
    # TODO: read_text().splitlines() → for enumerate(lines, 1) → 单行 try/except
    ...


# ========== §6.4 raise from + try/except/else ==========


def build_summary(entries: list[dict]) -> dict:
    """
    【raise from + try/except/else · §6.4】把 entry 列表聚合成统计摘要。

    任务:返回 {"total": <entry 总数>, "by_status": <按状态码段位聚合的计数>}。
         状态码段位 = status // 100 拼 "xx"(200→"2xx", 404→"4xx", 500→"5xx")。
         某条 entry 缺 "status" 字段时,抛 LogParseError(带 entry 内容,from e 保留 KeyError)。

    示例(nginx_logs.txt 解析出的 11 条 entry):
        build_summary(entries)
            -> {"total": 11,
                "by_status": {"2xx": 6, "5xx": 3, "4xx": 2}}

    提示:
      for e in entries:
          try:
              bucket = f"{e['status'] // 100}xx"
          except KeyError as ex:
              raise LogParseError(f"entry 缺 status 字段: {e}") from ex
          else:                                    # 只有 status 提取成功才累加
              total += 1
              by_status[bucket] = by_status.get(bucket, 0) + 1
    """
    # TODO: try 提取 status → except KeyError raise from → else 累加
    ...


# ========== §6.5 with open() 写文件 ==========


def write_report(summary: dict, path: str | Path) -> None:
    """
    【with open() 写文件 · §6.5】把统计摘要写成人类可读的报告文件。

    任务:按下面格式写入 path(UTF-8 编码,覆盖模式):
        第一行: total: N
        后续行: 每个状态码段位一行 "bucket: count"(按 dict 遍历顺序)
        末尾补一个换行符。

    示例:
        write_report({"total": 11, "by_status": {"2xx": 6, "5xx": 3, "4xx": 2}}, "report.txt")
        # report.txt 内容:
        # total: 11
        # 2xx: 6
        # 5xx: 3
        # 4xx: 2

    提示:
      lines = [f"total: {summary['total']}"]
      for bucket, count in summary["by_status"].items():
          lines.append(f"{bucket}: {count}")
      report = "\\n".join(lines) + "\\n"
      with Path(path).open("w", encoding="utf-8") as f:   # "w"=覆盖; encoding 必须显式写
          f.write(report)
    """
    # TODO: 拼报告字符串 → with Path(path).open("w", encoding="utf-8") as f → f.write
    ...


# ========== §6.6 类版上下文管理器(__enter__/__exit__)==========


class Timer:
    """【with 协议 · §6.6】计时器:with Timer() as t: ... ; 退出后 t.elapsed 是耗时秒数。

    实现 __enter__ 和 __exit__ 两个方法,对象就支持 with 语句(= Java AutoCloseable)。
    用于打点「读文件 / 解析 / 写报告」各阶段耗时,上报监控系统。
    """

    def __enter__(self):
        """进入 with 块时调用。记录开始时间到 self.start,并 return self。"""
        # TODO: self.start = time.time(); return self
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出 with 块时调用(无论是否异常)。计算耗时到 self.elapsed。
        三个参数是异常信息(没异常时都是 None)。返回 False 表示不吞异常。"""
        # TODO: self.elapsed = time.time() - self.start; return False
        ...


# ========== §6.7 @contextmanager 生成器版(事务)==========


# TODO: 给这个函数加上 @contextmanager 装饰器(已从 contextlib 导入)
def db_transaction(db: dict):
    """【@contextmanager 事务 · §6.7】模拟数据库事务的上下文管理器。

    db 是一个 dict,形如 {"committed": [], "pending": [], "rolled_back": False}。
    事务语义:全部成功才 commit,任何异常整个 rollback,不能留半截数据。

    行为约定:
      进入 with:db["pending"] 重置为 []
      with 块正常结束:把 pending 里的记录 append 到 db["committed"],pending 清空
      with 块抛异常:db["rolled_back"] = True,pending 清空,committed 不变,异常继续抛
      无论如何:finally 里保证 pending 被清空

    示例:
        db = {"committed": [], "pending": [], "rolled_back": False}
        with db_transaction(db) as tx:
            tx["pending"].append({"total": 11})
        # db["committed"] == [{"total": 11}], db["pending"] == []

        with db_transaction(db) as tx:
            tx["pending"].append({"total": 12})
            raise RuntimeError("DB 挂了")
        # db["rolled_back"] == True, db["committed"] 不变, 异常向外抛

    提示(yield 切三段):
      db["pending"] = []
      try:
          yield db
          db["committed"].extend(db["pending"])    # 正常结束:commit
      except Exception:
          db["rolled_back"] = True                  # 异常:rollback
          raise                                     # 重新抛,让调用方知道
      finally:
          db["pending"] = []                        # 无论如何:清理
    """
    # TODO: yield 三段套路(yield 前准备 / yield 后 commit / except rollback / finally 清理)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch06/ch06_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    log_path = Path(__file__).parent / ".." / ".." / "assets" / "mock_data" / "nginx_logs.txt"

    with Timer() as t_parse:
        entries, skipped = parse_log_file(log_path)
    print(f"解析 {len(entries)} 条,跳过 {len(skipped)} 行,耗时 {t_parse.elapsed:.4f}s")

    summary = build_summary(entries)
    print("summary =", summary)

    report_path = Path(__file__).parent / "report.txt"
    with Timer() as t_write:
        write_report(summary, report_path)
    print(f"报告已写入 {report_path},耗时 {t_write.elapsed:.4f}s")

    db = {"committed": [], "pending": [], "rolled_back": False}
    with db_transaction(db) as tx:
        tx["pending"].append(summary)
    print(f"入库完成,committed = {len(db['committed'])} 条")
