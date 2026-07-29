"""
冒烟测试：验证测试基础设施正常工作。

跑通这个文件 = 你的环境 OK，「测试通过 = 掌握」机制 ready。
    pytest tests/test_smoke.py -v
"""
from conftest import load_mock_json, MOCK_DATA_DIR


def test_mock_data_dir_exists():
    """mock 数据目录存在。"""
    assert MOCK_DATA_DIR.exists(), f"目录不存在: {MOCK_DATA_DIR}"


def test_load_mock_json():
    """能正确加载 products.json，且是 10 个商品（用户案例里的数据）。"""
    products = load_mock_json("products.json")
    assert isinstance(products, list)
    assert len(products) == 10, f"期望 10 个商品，实际 {len(products)}"


def test_products_fixture(products):
    """conftest 的 products fixture 注入正常。"""
    assert len(products) == 10
    # 每个商品都有必需字段
    for p in products:
        assert {"id", "name", "price", "category"}.issubset(p.keys())


def test_python_version():
    """确认 Python >= 3.11（部分语法特性需要）。"""
    import sys
    assert sys.version_info >= (3, 11), f"需要 Python 3.11+，当前 {sys.version}"
