"""
Ch14 作业:FastAPI 入门 + Pydantic 模型。

一个商品管理 mini app:GET 列表 / POST 创建 / GET 单个。
体会 FastAPI 的核心理念——「类型注解驱动一切」:参数自动解析、自动校验、自动序列化。

    uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="商品管理 API")


# ---------- Pydantic 模型(= Java DTO + 自动校验)----------


class Product(BaseModel):
    """响应模型:商品完整信息。"""
    id: int
    name: str
    price: float
    stock: int = 0


# TODO: 定义创建商品的【请求模型】ProductCreate。要求:
#   - name: str(必填)
#   - price: float = Field(gt=0, description="价格必须大于 0")   ← gt=0 校验必须 > 0
#   - stock: int = 0(默认 0)
class ProductCreate(BaseModel):
    """创建商品时客户端传入的字段(没有 id,服务端生成)。"""
    ...


# ---------- 内存存储(Ch19 才接真数据库)----------

PRODUCTS: dict[int, Product] = {
    1: Product(id=1, name="机械键盘", price=599.0, stock=120),
    2: Product(id=2, name="无线鼠标", price=159.0, stock=300),
}
_next_id = 3


# ---------- 端点(路由)----------


@app.get("/products")
def list_products():
    """
    【路由 + 序列化 · §14.1】返回所有商品。
    FastAPI 自动把 [Product, ...] 序列化成 JSON 数组。

    思路:return list(PRODUCTS.values())。
    """
    # TODO: 返回所有商品
    ...


@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    """
    【请求体模型 · §14.2/§14.3】创建商品。
    p 的类型注解 ProductCreate 让 FastAPI【自动】:① 解析 JSON body ② 按 Pydantic 校验
    ③ 校验失败返回 422。你只管用 p 当普通对象。

    思路:
        global _next_id                                    # 函数内改全局变量要声明
        product = Product(id=_next_id, **p.model_dump())   # model_dump() 把 ProductCreate 转 dict
        PRODUCTS[_next_id] = product
        _next_id += 1
        return product
    """
    # TODO: 造 Product(分配 id)、存入、自增 _next_id、返回
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    【路径参数 + HTTPException · §14.5】查单个商品。
    product_id 的 int 注解让 FastAPI 自动把 URL 里的 "1" 转成 int(并校验类型)。
    不存在时 raise HTTPException(404)。

    思路:
        if product_id not in PRODUCTS:
            raise HTTPException(status_code=404, detail="商品不存在")
        return PRODUCTS[product_id]
    """
    # TODO: 不存在 raise HTTPException(404);否则返回
    ...
