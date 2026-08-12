"""
Ch23 作业测试。运行: uv run pytest 04_devops_scripts/ch23/test_ch23_assignment.py -v
"""
from pathlib import Path

import pytest

from ch23_assignment import (
    add_date_prefix,
    archive_files,
    archive_large_logs,
    ensure_dir,
    file_size_report,
    group_by_extension,
    list_files,
    total_size,
)


# ---------- 辅助:在 tmp_path 下造一个「日志目录」 ----------
def _make_tree(root: Path) -> None:
    (root / "app.log").write_text("INFO app started\n", encoding="utf-8")      # 17 字节
    (root / "error.log").write_text("ERROR boom\n", encoding="utf-8")          # 11 字节
    (root / "metrics.json").write_text('{"cpu":0.5}', encoding="utf-8")        # 11 字节
    (root / "readme").write_text("doc", encoding="utf-8")                      # 3 字节,无扩展名
    (root / "old").mkdir()
    (root / "old" / "app.1.log").write_text("old log\n", encoding="utf-8")     # 8 字节,子目录里


# ---------- list_files ----------
class TestListFiles:
    def test_lists_top_level_files_only(self, tmp_path):
        _make_tree(tmp_path)
        names = [p.name for p in list_files(tmp_path)]
        assert names == ["app.log", "error.log", "metrics.json", "readme"]  # 子目录 old 被排除

    def test_pattern_filter(self, tmp_path):
        _make_tree(tmp_path)
        names = [p.name for p in list_files(tmp_path, "*.log")]
        assert names == ["app.log", "error.log"]  # old/app.1.log 不在(非递归)

    def test_pattern_no_match(self, tmp_path):
        _make_tree(tmp_path)
        assert list_files(tmp_path, "*.csv") == []

    def test_returns_path_objects(self, tmp_path):
        _make_tree(tmp_path)
        for p in list_files(tmp_path):
            assert isinstance(p, Path)

    def test_result_sorted_regardless_of_creation_order(self, tmp_path):
        # 故意倒着造,拦住「不排序直接返回」的实现
        (tmp_path / "z.log").write_text("1", encoding="utf-8")
        (tmp_path / "a.log").write_text("1", encoding="utf-8")
        (tmp_path / "m.log").write_text("1", encoding="utf-8")
        names = [p.name for p in list_files(tmp_path)]
        assert names == ["a.log", "m.log", "z.log"]

    def test_empty_dir(self, tmp_path):
        assert list_files(tmp_path) == []


# ---------- file_size_report ----------
class TestFileSizeReport:
    def test_sizes_are_exact_bytes(self, tmp_path):
        _make_tree(tmp_path)
        report = file_size_report(tmp_path)
        assert report["app.log"] == 17
        assert report["error.log"] == 11
        assert report["metrics.json"] == 11
        assert report["readme"] == 3

    def test_excludes_directories(self, tmp_path):
        _make_tree(tmp_path)
        assert "old" not in file_size_report(tmp_path)

    def test_excludes_nested_files(self, tmp_path):
        _make_tree(tmp_path)
        assert "app.1.log" not in file_size_report(tmp_path)  # 非递归

    def test_empty_dir(self, tmp_path):
        assert file_size_report(tmp_path) == {}


# ---------- group_by_extension ----------
class TestGroupByExtension:
    def test_groups_by_suffix(self, tmp_path):
        _make_tree(tmp_path)
        groups = group_by_extension(tmp_path)
        assert groups[".log"] == ["app.log", "error.log"]  # 组内有序
        assert groups[".json"] == ["metrics.json"]
        assert groups[""] == ["readme"]  # 无扩展名归 "" 键

    def test_excludes_directories_and_nested_files(self, tmp_path):
        _make_tree(tmp_path)
        groups = group_by_extension(tmp_path)
        all_names = [name for names in groups.values() for name in names]
        assert "old" not in all_names        # 目录不分组
        assert "app.1.log" not in all_names  # 子目录里的文件不分组(非递归)

    def test_multiple_same_ext_sorted(self, tmp_path):
        (tmp_path / "y.log").write_text("1", encoding="utf-8")
        (tmp_path / "x.log").write_text("1", encoding="utf-8")
        groups = group_by_extension(tmp_path)
        assert groups[".log"] == ["x.log", "y.log"]

    def test_empty_dir(self, tmp_path):
        assert group_by_extension(tmp_path) == {}


# ---------- ensure_dir ----------
class TestEnsureDir:
    def test_creates_nested_dirs(self, tmp_path):
        target = tmp_path / "backup" / "logs" / "2026-08"
        result = ensure_dir(target)
        assert target.is_dir()
        assert result == target

    def test_idempotent(self, tmp_path):
        target = tmp_path / "archive"
        ensure_dir(target)
        ensure_dir(target)  # 再调一次不报错(exist_ok=True)
        assert target.is_dir()

    def test_partial_existing_parents(self, tmp_path):
        (tmp_path / "backup").mkdir()
        ensure_dir(tmp_path / "backup" / "logs")
        assert (tmp_path / "backup" / "logs").is_dir()

    def test_existing_file_still_raises(self, tmp_path):
        # exist_ok=True 只对「已存在的是目录」宽容;同名文件照样抛
        f = tmp_path / "not_a_dir"
        f.write_text("x", encoding="utf-8")
        with pytest.raises(FileExistsError):
            ensure_dir(f)


# ---------- total_size ----------
class TestTotalSize:
    def test_recursive_sum(self, tmp_path):
        _make_tree(tmp_path)
        # 17 + 11 + 11 + 3 + old/app.1.log(8) = 50
        assert total_size(tmp_path) == 50

    def test_counts_nested_files(self, tmp_path):
        (tmp_path / "top.log").write_text("12345", encoding="utf-8")   # 5
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "deep.log").write_text("1234567", encoding="utf-8")  # 7
        assert total_size(tmp_path) == 12  # 拦得住「只算顶层」的错误实现

    def test_empty_dir(self, tmp_path):
        assert total_size(tmp_path) == 0

    def test_ignores_empty_subdirs(self, tmp_path):
        (tmp_path / "app.log").write_text("12345", encoding="utf-8")  # 5
        (tmp_path / "empty").mkdir()
        assert total_size(tmp_path) == 5  # 目录本身不占数


# ---------- archive_files ----------
class TestArchiveFiles:
    def test_moves_files_and_counts(self, tmp_path):
        f1 = tmp_path / "app.log"
        f2 = tmp_path / "error.log"
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")
        archive = tmp_path / "archive"

        count = archive_files([f1, f2], archive)

        assert count == 2
        assert not f1.exists()  # 原位置消失
        assert not f2.exists()
        assert (archive / "app.log").is_file()
        assert (archive / "error.log").is_file()

    def test_content_preserved(self, tmp_path):
        f = tmp_path / "app.log"
        f.write_text("INFO app started\n", encoding="utf-8")
        archive_files([f], tmp_path / "archive")
        assert (tmp_path / "archive" / "app.log").read_text(encoding="utf-8") == "INFO app started\n"

    def test_creates_nested_archive_dir(self, tmp_path):
        f = tmp_path / "app.log"
        f.write_text("x", encoding="utf-8")
        archive = tmp_path / "deep" / "archive"  # 父目录也不存在
        count = archive_files([f], archive)
        assert count == 1
        assert archive.is_dir()
        assert (archive / "app.log").is_file()
        # 拦住「没先建目录」的实现:那种实现会把 f 重命名成叫 archive 的【文件】

    def test_empty_list_still_creates_dir(self, tmp_path):
        archive = tmp_path / "archive"
        assert archive_files([], archive) == 0
        assert archive.is_dir()


# ---------- add_date_prefix ----------
class TestAddDatePrefix:
    def test_renames_logs_with_prefix(self, tmp_path):
        _make_tree(tmp_path)
        new_paths = add_date_prefix(tmp_path, "20260812")
        assert [p.name for p in new_paths] == ["20260812_app.log", "20260812_error.log"]
        assert not (tmp_path / "app.log").exists()      # 原名消失
        assert (tmp_path / "20260812_app.log").is_file()
        assert (tmp_path / "20260812_error.log").is_file()

    def test_only_logs_touched(self, tmp_path):
        _make_tree(tmp_path)
        new_paths = add_date_prefix(tmp_path, "20260812")
        assert [p.name for p in new_paths] == ["20260812_app.log", "20260812_error.log"]
        assert (tmp_path / "metrics.json").is_file()  # 非 .log 不动
        assert (tmp_path / "readme").is_file()

    def test_non_recursive(self, tmp_path):
        _make_tree(tmp_path)
        new_paths = add_date_prefix(tmp_path, "20260812")
        assert [p.name for p in new_paths] == ["20260812_app.log", "20260812_error.log"]
        assert (tmp_path / "old" / "app.1.log").is_file()  # 子目录里的不动

    def test_content_preserved_after_rename(self, tmp_path):
        _make_tree(tmp_path)
        add_date_prefix(tmp_path, "20260812")
        assert (tmp_path / "20260812_app.log").read_text(encoding="utf-8") == "INFO app started\n"

    def test_no_logs_returns_empty(self, tmp_path):
        (tmp_path / "a.txt").write_text("1", encoding="utf-8")
        assert add_date_prefix(tmp_path, "20260812") == []
        assert (tmp_path / "a.txt").is_file()  # 原文件未动


# ---------- archive_large_logs(综合) ----------
class TestArchiveLargeLogs:
    def test_threshold_archives_only_big_files(self, tmp_path):
        _make_tree(tmp_path)
        archive = tmp_path / "backup"
        report = archive_large_logs(tmp_path, archive, threshold=12)

        assert report["scanned"] == 4          # 顶层 4 个文件
        assert report["archived"] == 1         # 只有 app.log(17B)>= 12
        assert report["freed_bytes"] == 17
        assert report["remaining_by_ext"] == {
            ".log": ["error.log"],
            ".json": ["metrics.json"],
            "": ["readme"],
        }

    def test_files_actually_moved(self, tmp_path):
        _make_tree(tmp_path)
        archive = tmp_path / "backup"
        archive_large_logs(tmp_path, archive, threshold=12)
        assert not (tmp_path / "app.log").exists()      # 原位置消失
        assert (archive / "app.log").is_file()          # 归档目录就位
        assert (tmp_path / "error.log").is_file()       # 未达标的留下

    def test_threshold_is_inclusive(self, tmp_path):
        # threshold=11:error.log(11B) 和 metrics.json(11B) 也要归档(>= 语义)
        _make_tree(tmp_path)
        report = archive_large_logs(tmp_path, tmp_path / "backup", threshold=11)
        assert report["archived"] == 3
        assert report["freed_bytes"] == 17 + 11 + 11

    def test_zero_threshold_archives_everything(self, tmp_path):
        _make_tree(tmp_path)
        report = archive_large_logs(tmp_path, tmp_path / "backup", threshold=0)
        assert report["archived"] == 4
        assert report["freed_bytes"] == 17 + 11 + 11 + 3
        assert report["remaining_by_ext"] == {}  # 顶层只剩 old/ 子目录

    def test_nothing_qualifies(self, tmp_path):
        _make_tree(tmp_path)
        report = archive_large_logs(tmp_path, tmp_path / "backup", threshold=10_000)
        assert report["archived"] == 0
        assert report["freed_bytes"] == 0
        assert (tmp_path / "backup").is_dir()  # 归档目录照样建好
        assert (tmp_path / "app.log").is_file()  # 原文件都在

    def test_creates_archive_dir(self, tmp_path):
        _make_tree(tmp_path)
        archive = tmp_path / "deep" / "backup"
        archive_large_logs(tmp_path, archive, threshold=12)
        assert archive.is_dir()
