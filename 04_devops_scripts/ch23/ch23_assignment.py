"""
Ch23 作业:文件系统批量操作 —— pathlib / shutil。

主线场景:你是后端负责人,服务器上 /var/log/myapp 日志目录天天膨胀、磁盘报警。
你要写一个「日志归档机器人」:扫描日志 → 出大小报告 → 按类型归类 → 建归档目录
→ 搬走超大日志 → 给当天日志加日期前缀 → 一键归档并输出报告。

8 个函数,从单知识点到综合递进(最后一题复用前 6 个)。写完运行:

    uv run pytest 04_devops_scripts/ch23/test_ch23_assignment.py -v

全绿 = 你掌握了 Ch23。

每题 docstring 标注【对应小节】,卡住 → 回查 tutorial.md 对应 §。
约定:directory / path 参数都是 pathlib.Path(测试用 tmp_path 临时目录,真实建文件)。
"""
import shutil
from pathlib import Path


# ========== §23.2 遍历与匹配:list_files ==========


def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    """
    【对应 §23.2】扫描日志目录:列出 directory 下匹配 pattern 的【文件】(不含子目录),
    返回按文件名排序的 Path 列表。非递归(只看顶层)。

    示例(目录下有 app.log、error.log、metrics.json、readme、子目录 old/):
        list_files(d)            -> [Path("app.log"), Path("error.log"), Path("metrics.json"), Path("readme")]
        list_files(d, "*.log")   -> [Path("app.log"), Path("error.log")]   # old/ 被排除;old/ 里的 .log 不递归

    提示:用 glob 做顶层通配;遍历结果会把【子目录】也列出来,记得过滤;
    文件系统返回顺序不保证,要按 name 排序才稳定可测。
    """
    # TODO: glob(pattern) + is_file 过滤 + sorted(key=按文件名)
    ...


# ========== §23.2 遍历与匹配:file_size_report ==========


def file_size_report(directory: Path) -> dict[str, int]:
    """
    【对应 §23.2】磁盘报警了,先搞清楚「谁占的」:统计 directory 下【顶层文件】
    (不递归)的大小,返回 {文件名: 字节数}。

    示例(app.log 17 字节、error.log 11 字节、readme 3 字节、子目录 old/):
        file_size_report(d) -> {"app.log": 17, "error.log": 11, "readme": 3}
        # "old" 是目录不进报告;old/ 里的文件也不进(非递归)

    提示:遍历顶层条目用 iterdir();字节数在 p.stat() 返回对象的 st_size 字段上;
    字典推导(Ch02)一行就能建好。
    """
    # TODO: iterdir + is_file + p.stat().st_size,字典推导
    ...


# ========== §23.3 分组:group_by_extension ==========


def group_by_extension(directory: Path) -> dict[str, list[str]]:
    """
    【对应 §23.3】归档前盘点:按扩展名把【顶层文件】分组,
    返回 {扩展名: [文件名...]},无扩展名的文件归到 "" 键下,组内文件名按字母序。

    示例(app.log、error.log、metrics.json、readme):
        group_by_extension(d)
            -> {".log": ["app.log", "error.log"], ".json": ["metrics.json"], "": ["readme"]}

    提示:扩展名用 p.suffix(永远含点;无扩展名是 "" 不是 None);
    分组用 setdefault(= Java map.computeIfAbsent),key 不存在先放空 list 再 append;
    只统计 is_file() 的;想要组内有序,遍历时先排序。
    """
    # TODO: setdefault 按 suffix 分组,只取 is_file
    ...


# ========== §23.4 建目录:ensure_dir ==========


def ensure_dir(path: Path) -> Path:
    """
    【对应 §23.4】幂等地创建目录(含所有缺失的父目录),已存在不报错。返回该 Path。
    等于 shell 的 `mkdir -p`。归档脚本第一步永远是它。

    示例:
        ensure_dir(Path("/backup/logs/2026-08"))   # 中间目录不存在也一并建好
        ensure_dir(已存在的目录)                      # 不报错,原样返回 Path

    提示:mkdir 的两个参数各防一种错——parents=True 防「中间目录不存在」
    (FileNotFoundError),exist_ok=True 防「目录已存在」(FileExistsError)。
    注意:若同名【文件】已存在,exist_ok=True 也救不了,照样抛 FileExistsError。
    """
    # TODO: mkdir(parents=True, exist_ok=True) + return path
    ...


# ========== §23.4 递归:total_size ==========


def total_size(directory: Path) -> int:
    """
    【对应 §23.4】递归求 directory 下【所有文件】总字节数(含子目录里的)。
    归档完成后用它汇报「这次腾出了多少空间」。

    示例(root/app.log 17 字节 + root/old/app.1.log 8 字节):
        total_size(root) -> 25        # 子目录里的也算;目录本身不占数

    提示:递归遍历用 rglob("*")(glob 的递归版,返回惰性生成器);
    sum(生成器表达式) 一行搞定,对比 Java 的 Files.walk + filter + mapToLong + sum。
    """
    # TODO: rglob("*") + is_file + sum(.stat().st_size)
    ...


# ========== §23.5 shutil:archive_files ==========


def archive_files(files: list[Path], archive_dir: Path) -> int:
    """
    【对应 §23.5】把一批超阈值日志【移动】到 archive_dir(不存在则先建),
    返回成功移动的文件数。移动后原位置文件消失。

    示例:
        archive_files([Path("app.log"), Path("error.log")], Path("archive"))
            -> 2          # archive/app.log、archive/error.log 就位,原位置没了
        archive_files([], Path("archive"))
            -> 0          # 空列表返回 0,但 archive 目录照样建好

    提示:🔴 shutil.move(src, dst) 的行为随 dst 而变——dst 是【已存在目录】才把
    src 移进去;dst 不存在会把 src【重命名】成 dst(变成一个文件!)。
    所以第一行必须先建目录(可以复用你写的 ensure_dir),再循环 move 计数。
    """
    # TODO: 先 ensure_dir(archive_dir),再循环 shutil.move(str(f), str(archive_dir)) 计数
    ...


# ========== §23.6 批量重命名:add_date_prefix ==========


def add_date_prefix(directory: Path, date_tag: str) -> list[Path]:
    """
    【对应 §23.6】logrotate 风格:给 directory 顶层所有 .log 文件加日期前缀,
    返回重命名后的新 Path 列表(按文件名排序)。非递归;非 .log 文件不动。

    示例(date_tag="20260812",目录下有 app.log、error.log、metrics.json、子目录 old/):
        add_date_prefix(d, "20260812")
            -> [Path("20260812_app.log"), Path("20260812_error.log")]
        # app.log / error.log 原文件名消失;metrics.json 不动;old/ 里的 .log 不动

    提示:先用 §23.2 的 list_files 圈定顶层 .log;新名字用 p.with_name(f"...")
    算出来(它只返回新 Path、不动磁盘),再 p.rename(新路径) 落地。
    rename 是同文件系统的原子改名;搬到别的目录才用 shutil.move。
    """
    # TODO: list_files(directory, "*.log") → rename(with_name(f"{date_tag}_{p.name}")) → 收集新路径排序
    ...


# ========== §23.7 综合:archive_large_logs ==========


def archive_large_logs(log_dir: Path, archive_dir: Path, threshold: int) -> dict:
    """
    【对应 §23.7 · 综合题】日志归档机器人:扫描 log_dir,把【>= threshold 字节】的
    顶层文件搬进 archive_dir,返回一份报告 dict。

    报告契约(4 个 key):
        "scanned":          扫描到的顶层文件数
        "archived":         实际归档的文件数
        "remaining_by_ext": 归档【后】log_dir 剩余文件按扩展名分组
        "freed_bytes":      归档目录总字节数(= 这次腾出多少空间)

    示例(log_dir 下 app.log 17B、error.log 11B、metrics.json 11B、readme 3B,threshold=12):
        archive_large_logs(log_dir, arch, 12)
            -> {"scanned": 4, "archived": 1, "freed_bytes": 17,
                "remaining_by_ext": {".log": ["error.log"], ".json": ["metrics.json"], "": ["readme"]}}

    提示:本题不写新知识,纯组装——ensure_dir(§23.4)→ file_size_report(§23.2)
    → 筛 size >= threshold 的名字拼回完整 Path → archive_files(§23.5)
    → group_by_extension(§23.3,对【归档后】的 log_dir 调用)→ total_size(§23.4)。
    顺序有讲究:必须先盘点再搬走,最后盘点剩余。
    """
    # TODO: 按上面的调用关系组装前 6 个函数
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch23/ch23_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "myapp"
        ensure_dir(root / "old")
        (root / "app.log").write_text("INFO app started\n", encoding="utf-8")   # 17B
        (root / "error.log").write_text("ERROR boom\n", encoding="utf-8")       # 11B
        (root / "metrics.json").write_text('{"cpu":0.5}', encoding="utf-8")     # 11B
        (root / "readme").write_text("doc", encoding="utf-8")                   # 3B
        (root / "old" / "app.1.log").write_text("old log\n", encoding="utf-8")  # 8B

        print("list_files:", [p.name for p in list_files(root)])
        print("*.log only:", [p.name for p in list_files(root, "*.log")])
        print("sizes:", file_size_report(root))
        print("grouped:", group_by_extension(root))
        print("total_size:", total_size(root))

        renamed = add_date_prefix(root, "20260812")
        print("renamed:", [p.name for p in renamed])

        report = archive_large_logs(root, Path(td) / "backup", threshold=12)
        print("archive report:", report)
