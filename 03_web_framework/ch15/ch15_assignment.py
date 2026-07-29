"""
Ch15 作业:路由参数 —— 路径参数 / 查询参数 / 分页 / Query 校验。

给商品 API 加【筛选】和【分页】:
    GET /products?category=图书&min_price=50&page=1&size=10
    GET /products/{id}

    uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="商品查询 API")


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    stock: int = 0


PRODUCTS: list[Product] = [
    Product(id=1, name="机械键盘", category="电脑外设", price=599.0, stock=120),
    Product(id=2, name="无线鼠标", category="电脑外设", price=159.0, stock=300),
    Product(id=3, name="设计模式", category="图书", price=75.5, stock=200),
    Product(id=4, name="Python编程", category="图书", price=89.0, stock=500),
    Product(id=5, name="降噪耳机", category="影音设备", price=1299.0, stock=80),
]


@app.get("/products")
def list_products(
    category: str | None = None,
    min_price: float | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """
    【查询参数 + 分页 · §15.2/§15.3/§15.4】支持按 category/min_price 筛选 + page/size 分页。
    参数签名已给(category/min_price 可选,page/size 用 Query 校验)。你实现筛选+分页逻辑。

    思路:
        result = PRODUCTS
        if category is not None:     # None 表示没传,不过滤
            result = [p for p in result if p.category == category]
        if min_price is not None:
            result = [p for p in result if p.price >= min_price]
        start = (page - 1) * size     # 分页切片起点(第几页 → 跳过多少个)
        return result[start:start + size]
    """
    # TODO: 筛选(category/min_price,只过滤「非 None 的」)+ 分页切片
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    【路径参数 · §15.1】按 id 查单个商品;不存在 404。
    product_id 是 int 注解 → URL 里的 "1" 自动转 int,非数字(如 /products/abc)返 422。

    思路:遍历 PRODUCTS 找 id 匹配的返回;找不到 raise HTTPException(404)。
    """
    # TODO: 查找;不存在 HTTPException(404)
    ...
