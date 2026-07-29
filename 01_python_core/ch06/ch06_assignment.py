"""
Ch06 作业:异常、上下文管理器、文件 IO。

5 个任务:自定义异常、try/except/else、pathlib 文件 IO + 异常、
类版上下文管理器、@contextmanager 生成器版。在每处 TODO 写实现,然后:

    uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v

全绿 = 你掌握了 Ch06。

每题顶部的【对应小节】指向 tutorial.md 里的讲解。卡住 → 回查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import json
import time
from pathlib import Path


# ========== §6.1 自定义异常 ==========


# TODO: 让它成为一个【自定义异常】——继承哪个类?(= Java: class XxxException extends Exception)
class DataLoadError:
    """数据加载失败的自定义异常。"""
    ...


# ========== §6.2 try/except/else/finally ==========


def safe_divide(a: float, b: float) -> float | None:
    """
    【try/except/else · §6.2】安全除法:b 为 0 时返回 None,否则返回 a/b。

    示例:
        safe_divide(10, 2)  -> 5.0
        safe_divide(10, 0)  -> None

    思路:用 try/except/else 三段式:
      try:        result = a / b          # 可能抛 ZeroDivisionError
      except ZeroDivisionError:  return None
      else:       return result           # 没异常才走这里
    """
    # TODO: try/except/else
    ...


# ========== §6.3 pathlib 文件 IO + 自定义异常 ==========


def read_config(path: str | Path) -> dict:
    """
    【pathlib + 自定义异常 · §6.3】读取 JSON 配置文件返回解析后的对象。
    文件不存在时抛 DataLoadError(用 raise ... from e 保留原始异常链)。

    示例:
        read_config("products.json")   -> [{"name": ...}, ...]
        read_config("不存在.json")       -> 抛 DataLoadError

    思路:
      p = Path(path)
      try:
          text = p.read_text(encoding="utf-8")    # 文件不存在会抛 FileNotFoundError
      except FileNotFoundError as e:
          raise DataLoadError(f"配置文件不存在: {path}") from e   # from e 保留原因
      return json.loads(text)
    """
    # TODO: Path + read_text + except FileNotFoundError + raise DataLoadError from e + json.loads
    ...


# ========== §6.4 类版上下文管理器(__enter__/__exit__)==========


class Timer:
    """【with 协议 · §6.4】计时器:with Timer() as t: ... ; 退出后 t.elapsed 是耗时秒数。

    实现 __enter__ 和 __exit__ 两个方法,对象就支持 with 语句(= Java AutoCloseable)。
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


# ========== §6.5 @contextmanager 生成器版 ==========


# TODO: 给这个函数加上 @contextmanager 装饰器(从 contextlib 导入)
def managed_resource(state: dict, name: str):
    """【@contextmanager · §6.5】进入 with 块时设 state["active"]=name;
    【无论是否异常】退出后恢复为 None。

    生成器版上下文管理器的固定套路:
      1. yield 之前的代码 = __enter__(进入时执行)
      2. yield 的值 = as 后面拿到的对象
      3. yield 之后的代码(放 finally 里)= __exit__(退出时执行,保证清理)

    思路:
      state["active"] = name
      try:
          yield state
      finally:
          state["active"] = None
    """
    # TODO: 需要 from contextlib import contextmanager,然后加装饰器 + 上面骨架
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch06/ch06_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("safe_divide(10,2) =", safe_divide(10, 2))
    print("safe_divide(10,0) =", safe_divide(10, 0))
    with Timer() as t:
        sum(range(100000))
    print("elapsed =", t.elapsed)
