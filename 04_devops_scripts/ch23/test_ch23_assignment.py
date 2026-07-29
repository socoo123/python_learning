"""
Ch23 作业测试。运行: uv run pytest 04_devops_scripts/ch23/test_ch23_assignment.py -v
"""
from pathlib import Path

import pytest

from ch23_assignment import (
    archive_files,
    ensure_dir,
    file_size_report,
    group_by_extension,
    list_files,
    total_size,
)


# ---------- 辅助:在 tmp_path 下造一批测试文件 ----------
def _make_tree(root: Path) -> None:
    (root / "a.txt").write_text("hello", encoding="utf-8")          # 5 字节
    (root / "b.json").write_text('{"x":1}', encoding="utf-8")       # 7 字节
    (root / "readme").write_text("doc", encoding="utf-8")           # 3 字节,无扩展名
    (root / "sub").mkdir()
    (root / "sub" / "c.txt").write_text("deep file", encoding="utf-8")  # 子目录里


# ---------- list_files ----------
class TestListFiles:
    def test_lists_files_only(self, tmp_path):
        _make_tree(tmp_path)
        names = sorted(p.name for p in list_files(tmp_path))
        assert names == ["a.txt", "b.json", "readme"]  # 子目录 sub 被排除

    def test_pattern_filter(self, tmp_path):
        _make_tree(tmp_path)
        names = [p.name for p in list_files(tmp_path, "*.json")]
        assert names == ["b.json"]

    def test_pattern_txt(self, tmp_path):
        _make_tree(tmp_path)
        names = sorted(p.name for p in list_files(tmp_path, "*.txt"))
        assert names == ["a.txt"]  # sub/c.txt 不在(非递归)

    def test_returns_path_objects(self, tmp_path):
        _make_tree(tmp_path)
        for p in list_files(tmp_path):
            assert isinstance(p, Path)

    def test_empty_dir(self, tmp_path):
        assert list_files(tmp_path) == []

    def test_result_sorted(self, tmp_path):
        # 故意倒着造,验证返回是排好序的
        (tmp_path / "z.txt").write_text("1", encoding="utf-8")
        (tmp_path / "a.txt").write_text("1", encoding="utf-8")
        (tmp_path / "m.txt").write_text("1", encoding="utf-8")
        names = [p.name for p in list_files(tmp_path)]
        assert names == ["a.txt", "m.txt", "z.txt"]


# ---------- file_size_report ----------
class TestFileSizeReport:
    def test_sizes(self, tmp_path):
        _make_tree(tmp_path)
        report = file_size_report(tmp_path)
        assert report["a.txt"] == 5
        assert report["b.json"] == 7
        assert report["readme"] == 3

    def test_excludes_directories(self, tmp_path):
        _make_tree(tmp_path)
        report = file_size_report(tmp_path)
        assert "sub" not in report  # 目录不算

    def test_excludes_nested_files(self, tmp_path):
        _make_tree(tmp_path)
        report = file_size_report(tmp_path)
        assert "c.txt" not in report  # 子目录里的文件不算(非递归)

    def test_empty_dir(self, tmp_path):
        assert file_size_report(tmp_path) == {}


# ---------- group_by_extension ----------
class TestGroupByExtension:
    def test_groups_by_suffix(self, tmp_path):
        _make_tree(tmp_path)
        groups = group_by_extension(tmp_path)
        assert sorted(groups[".txt"]) == ["a.txt"]
        assert groups[".json"] == ["b.json"]
        assert groups[""] == ["readme"]  # 无扩展名

    def test_multiple_same_ext(self, tmp_path):
        (tmp_path / "x.txt").write_text("1", encoding="utf-8")
        (tmp_path / "y.txt").write_text("1", encoding="utf-8")
        (tmp_path / "z.log").write_text("1", encoding="utf-8")
        groups = group_by_extension(tmp_path)
        assert sorted(groups[".txt"]) == ["x.txt", "y.txt"]
        assert groups[".log"] == ["z.log"]

    def test_excludes_directories(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "a.txt").write_text("1", encoding="utf-8")
        groups = group_by_extension(tmp_path)
        assert "sub" not in groups.get("", [])
        assert all("sub" not in v for v in groups.values())


# ---------- ensure_dir ----------
class TestEnsureDir:
    def test_creates_nested_dirs(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        result = ensure_dir(target)
        assert target.is_dir()
        assert result == target

    def test_idempotent(self, tmp_path):
        target = tmp_path / "dir"
        ensure_dir(target)
        ensure_dir(target)  # 再调一次不报错
        assert target.is_dir()

    def test_returns_path(self, tmp_path):
        target = tmp_path / "x"
        assert ensure_dir(target) == target

    def test_existing_with_parents(self, tmp_path):
        # 中间目录已存在也能继续往下建
        (tmp_path / "a").mkdir()
        ensure_dir(tmp_path / "a" / "b")
        assert (tmp_path / "a" / "b").is_dir()


# ---------- archive_files ----------
class TestArchiveFiles:
    def test_moves_files(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.log"
        f1.write_text("1", encoding="utf-8")
        f2.write_text("2", encoding="utf-8")
        archive = tmp_path / "archive"

        count = archive_files([f1, f2], archive)

        assert count == 2
        assert not f1.exists()  # 原位置没了
        assert not f2.exists()
        assert (archive / "a.txt").is_file()
        assert (archive / "b.log").is_file()

    def test_creates_archive_dir(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("1", encoding="utf-8")
        archive = tmp_path / "deep" / "archive"  # 不存在,且父也不存在
        count = archive_files([f], archive)
        assert count == 1
        assert archive.is_dir()
        assert (archive / "a.txt").is_file()

    def test_empty_list(self, tmp_path):
        archive = tmp_path / "archive"
        assert archive_files([], archive) == 0
        assert archive.is_dir()  # 目录还是建了

    def test_count_matches(self, tmp_path):
        files = []
        for i in range(5):
            f = tmp_path / f"f{i}.txt"
            f.write_text(str(i), encoding="utf-8")
            files.append(f)
        count = archive_files(files, tmp_path / "archive")
        assert count == 5


# ---------- total_size ----------
class TestTotalSize:
    def test_recursive_sum(self, tmp_path):
        _make_tree(tmp_path)
        # a.txt(5) + b.json(7) + readme(3) + sub/c.txt(9) = 24
        assert total_size(tmp_path) == 5 + 7 + 3 + len("deep file")

    def test_empty_dir(self, tmp_path):
        assert total_size(tmp_path) == 0

    def test_ignores_empty_subdirs(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello", encoding="utf-8")  # 5
        (tmp_path / "empty").mkdir()
        assert total_size(tmp_path) == 5  # 空目录不计
