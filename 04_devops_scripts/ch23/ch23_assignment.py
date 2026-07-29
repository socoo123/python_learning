"""
Ch23 作业:文件系统批量操作 —— pathlib / shutil。

运维脚本最常见的事:扫文件、归类、归档、算大小。Python 的 pathlib 比传统
os.path 优雅得多(链式、面向对象),shutil 负责「复制/移动/删目录」这类重活。

6 个函数。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch23/test_ch23_assignment.py -v

全绿 = 你掌握了 Ch23。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:directory / path 参数都是 pathlib.Path(测试用 tmp_path 临时目录,真实建文件)。
"""
import shutil
from pathlib import Path


# ========== §23.2 pathlib 基础:list_files ==========


def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    """
    【pathlib · §23.2】列出 directory 下匹配 pattern 的【文件】(不含子目录),
    返回按文件名排序的 Path 列表。

    示例(目录下有 a.txt、b.json、子目录 sub/):
        list_files(d)             -> [Path("a.txt"), Path("b.json")]   # sub 被排除
        list_files(d, "*.json")   -> [Path("b.json")]

    思路(对比 Java NIO Files.list + filter):
        sorted(p for p in directory.glob(pattern) if p.is_file())
        - glob 非递归匹配(rglob 才递归,§23.4 讲)
        - is_file() 过滤掉子目录(glob "*" 会把目录也匹配进来)
        - sorted 让结果稳定(文件系统返回顺序不保证)
    """
    # TODO: directory.glob(pattern) + is_file 过滤 + sorted
    ...


# ========== §23.2 pathlib 基础:file_size_report ==========


def file_size_report(directory: Path) -> dict[str, int]:
    """
    【pathlib · §23.2】统计 directory 下【顶层文件】(不递归)的大小,
    返回 {文件名: 字节数}。

    示例(a.txt 10 字节,b.json 20 字节):
        file_size_report(d) -> {"a.txt": 10, "b.json": 20}

    思路:
        {p.name: p.stat().st_size for p in directory.iterdir() if p.is_file()}
        - iterdir() 遍历顶层条目(= Java File.listFiles)
        - p.stat() 取文件元数据(Linux inode 信息),.st_size 是字节数
    """
    # TODO: iterdir + is_file + p.stat().st_size,字典推导
    ...


# ========== §23.3 分组:group_by_extension ==========


def group_by_extension(directory: Path) -> dict[str, list[str]]:
    """
    【pathlib · §23.3】按扩展名把【顶层文件】分组,返回 {扩展名: [文件名...]}。
    无扩展名的文件归到 "" 键下。文件名按字母序排。

    示例(a.txt、b.txt、c.json、readme):
        group_by_extension(d)
            -> {".txt": ["a.txt", "b.txt"], ".json": ["c.json"], "": ["readme"]}

    思路(setdefault 分组,Ch02 学过):
        groups: dict[str, list[str]] = {}
        for p in sorted(directory.iterdir(), key=lambda x: x.name):
            if p.is_file():
                groups.setdefault(p.suffix, []).append(p.name)
        return groups
        - p.suffix 含点(".txt");无扩展名时 suffix == ""
    """
    # TODO: setdefault 按 suffix 分组,只取 is_file
    ...


# ========== §23.4 建目录:ensure_dir ==========


def ensure_dir(path: Path) -> Path:
    """
    【pathlib · §23.4】幂等地创建目录(含父目录),已存在不报错。返回该 Path。
    等于 shell 的 `mkdir -p`。

    示例:
        ensure_dir(Path("/tmp/a/b/c"))   # /tmp/a/b/c 不存在就创建,存在也不报错

    思路(对比 Java Files.createDirectories):
        path.mkdir(parents=True, exist_ok=True)
        return path
        - parents=True:连同父目录一起建(否则中间目录不存在会报错)
        - exist_ok=True:已存在不抛 FileExistsError(默认会抛)
    """
    # TODO: mkdir(parents=True, exist_ok=True) + return
    ...


# ========== §23.5 shutil:archive_files ==========


def archive_files(files: list[Path], archive_dir: Path) -> int:
    """
    【shutil · §23.5】把一批文件【移动】到 archive_dir(不存在则先建),
    返回成功移动的文件数。

    示例:
        archive_files([Path("a.txt"), Path("b.log")], Path("archive"))
            -> 2          # archive/a.txt、archive/b.log 就位,原位置消失

    思路(对比 Java Files.move):
        archive_dir.mkdir(parents=True, exist_ok=True)   # ⚠️ 必须先建
        count = 0
        for f in files:
            shutil.move(str(f), str(archive_dir))        # 目标是目录→移进去
            count += 1
        return count
        - shutil.move(src, dst):dst 是已存在目录就把 src 移进去;
          ⚠️ 若 dst 不存在,会把 src 重命名成 dst(变成文件!)——所以务必先建目录
    """
    # TODO: 先 ensure_dir(archive_dir) 或 mkdir,再循环 shutil.move 计数
    ...


# ========== §23.4 递归:total_size ==========


def total_size(directory: Path) -> int:
    """
    【pathlib · §23.4】递归求 directory 下【所有文件】总字节数(含子目录里的)。

    示例(目录树:root/a.txt(10) + root/sub/b.txt(20)):
        total_size(root) -> 30

    思路(rglob 递归 + 生成器求和,对比 Java Files.walk):
        return sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
        - rglob("*") 递归遍历所有条目(= glob 的递归版)
        - is_file() 排除目录(目录本身也占点空间,这里不计)
    """
    # TODO: rglob("*") + is_file + sum(.stat().st_size)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     python 04_devops_scripts/ch23/ch23_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a.txt").write_text("hello", encoding="utf-8")
        (root / "b.json").write_text('{"x":1}', encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub" / "c.txt").write_text("deep", encoding="utf-8")

        print("list_files:", [p.name for p in list_files(root)])
        print("json only:", [p.name for p in list_files(root, "*.json")])
        print("sizes:", file_size_report(root))
        print("grouped:", group_by_extension(root))
        print("total_size:", total_size(root))
        moved = archive_files(list_files(root), ensure_dir(root / "archive"))
        print("archived:", moved, "->", [p.name for p in list_files(root / "archive")])
