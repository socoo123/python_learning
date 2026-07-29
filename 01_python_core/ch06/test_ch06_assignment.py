"""
Ch06 作业测试。运行: uv run pytest 01_python_core/ch06/test_ch06_assignment.py -v
"""
import pytest

from ch06_assignment import (
    DataLoadError,
    safe_divide,
    read_config,
    Timer,
    managed_resource,
)
from conftest import MOCK_DATA_DIR


# ---------- DataLoadError:自定义异常 ----------
class TestDataLoadError:
    def test_is_exception_subclass(self):
        assert issubclass(DataLoadError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(DataLoadError):
            raise DataLoadError("boom")

    def test_carries_message(self):
        try:
            raise DataLoadError("oops")
        except DataLoadError as e:
            assert "oops" in str(e)


# ---------- safe_divide:try/except/else ----------
class TestSafeDivide:
    def test_normal(self):
        assert safe_divide(10, 2) == 5.0

    def test_by_zero_returns_none(self):
        assert safe_divide(10, 0) is None

    def test_floats(self):
        assert safe_divide(7.5, 2.5) == 3.0

    def test_negative(self):
        assert safe_divide(-10, 2) == -5.0


# ---------- read_config:pathlib + 自定义异常 ----------
class TestReadConfig:
    def test_reads_existing_json(self):
        # 复用现成的 products.json
        data = read_config(MOCK_DATA_DIR / "products.json")
        assert isinstance(data, list)
        assert len(data) == 10

    def test_missing_raises_dataloaderror(self, tmp_path):
        bad = tmp_path / "nope.json"
        with pytest.raises(DataLoadError):
            read_config(bad)

    def test_missing_preserves_cause(self, tmp_path):
        # raise ... from e 保留了原始 FileNotFoundError 异常链
        bad = tmp_path / "nope.json"
        try:
            read_config(bad)
        except DataLoadError as e:
            assert e.__cause__ is not None

    def test_reads_dict_json(self, tmp_path):
        f = tmp_path / "cfg.json"
        f.write_text('{"host": "localhost", "port": 8080}', encoding="utf-8")
        cfg = read_config(f)
        assert cfg == {"host": "localhost", "port": 8080}


# ---------- Timer:类版上下文管理器 ----------
class TestTimer:
    def test_enter_returns_self(self):
        t = Timer()
        with t as ctx:
            assert ctx is t

    def test_elapsed_set_after_block(self):
        t = Timer()
        with t:
            pass
        assert hasattr(t, "elapsed")
        assert t.elapsed >= 0

    def test_elapsed_not_set_before_enter(self):
        t = Timer()
        assert not hasattr(t, "elapsed")


# ---------- managed_resource:@contextmanager 生成器版 ----------
class TestManagedResource:
    def test_active_during_block(self):
        state = {}
        with managed_resource(state, "db"):
            assert state["active"] == "db"

    def test_cleared_after_block(self):
        state = {}
        with managed_resource(state, "db"):
            pass
        assert state["active"] is None

    def test_cleared_even_on_exception(self):
        state = {}
        with pytest.raises(RuntimeError):
            with managed_resource(state, "db"):
                raise RuntimeError("boom")
        assert state["active"] is None   # finally 保证清理

    def test_yields_the_state(self):
        state = {}
        with managed_resource(state, "x") as s:
            assert s is state
