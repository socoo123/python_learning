"""
全局 pytest 配置 & 共享工具。

所有章节的测试都可以从这里 import 工具，比如：
    from conftest import load_mock_json, MOCK_DATA_DIR
"""
import json
from pathlib import Path

import pytest

# 项目根目录（conftest.py 所在目录）
ROOT_DIR = Path(__file__).parent
# 共享 mock 数据目录
MOCK_DATA_DIR = ROOT_DIR / "assets" / "mock_data"


def load_mock_json(name: str):
    """
    读取 assets/mock_data/<name>，返回解析后的 Python 对象。

    用法（在任意测试里）：
        data = load_mock_json("products.json")
        # 或带子目录：
        data = load_mock_json("web/orders.json")
    """
    path = MOCK_DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"mock 数据不存在: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------- 共享 fixtures ----------

@pytest.fixture
def mock_data_dir() -> Path:
    """返回共享 mock 数据目录路径。"""
    return MOCK_DATA_DIR


@pytest.fixture
def products():
    """10 个商品的 mock 数据（用户案例中反复用到）。"""
    return load_mock_json("products.json")
