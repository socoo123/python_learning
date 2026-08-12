"""
Ch14 作业:FastAPI 入门 + Pydantic 模型。

场景:你是「极客商城」后端,上线第一版商品管理 API。
数据暂存内存字典(Ch19 再接数据库),种子数据与 Ch13 的 products.json 同源。
需要:
  ProductCreate 校验入库单 → 组装 Product → CRUD 端点 → 库存运营报表。

体会 FastAPI 核心理念——「类型注解驱动一切」:解析、校验、序列化、文档。

    uv sync --extra web
    uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="极客商城 · 商品 API")


# ---------- 响应模型(脚手架:完整商品,直接用)----------


class Product(BaseModel):
    """响应模型:商品完整信息(含服务端分配的 id)。"""

    id: int
    name: str
    category: str
    price: float
    stock: int = 0
    sku: str


# ---------- 请求模型(你来补字段约束)----------


class ProductCreate(BaseModel):
    """
    【Pydantic Field · §14.2】创建/更新时客户端传入的字段(无 id)。

    任务:声明五个字段及约束——
      - name: str, Field(min_length=1, max_length=50)
      - category: str, Field(min_length=1)            # 如 电脑外设
      - price: float, Field(gt=0)
      - stock: int, Field(default=0, ge=0)
      - sku: str, Field(pattern=r"^[A-Z]{2}-\\d{3}$")  # 如 KB-001

    示例:
        ProductCreate(name="机械键盘", category="电脑外设", price=599, stock=120, sku="KB-001")  # OK
        ProductCreate(name="机械键盘", category="电脑外设", price=599, sku="KB-001")             # OK,stock 默认 0
        ProductCreate(name="", category="电脑外设", price=10, sku="KB-001")                      # 校验失败
        ProductCreate(name="X", category="图书", price=0, sku="KB-001")                          # 校验失败(gt=0)
        ProductCreate(name="X", category="图书", price=10, sku="kb-001")                         # 校验失败(pattern)

    提示:约束写在 Field(...) 里,不要手写 if;price: float = 0 只是默认值不是校验。
    """

    # TODO: name / category / price / stock / sku 五个字段 + Field 约束
    ...


# ---------- 内存存储(Ch19 才接真数据库)----------

PRODUCTS: dict[int, Product] = {
    1: Product(id=1, name="机械键盘", category="电脑外设", price=599.0, stock=120, sku="KB-001"),
    2: Product(id=2, name="无线鼠标", category="电脑外设", price=159.0, stock=300, sku="MS-002"),
    3: Product(id=3, name="设计模式", category="图书", price=75.5, stock=200, sku="BK-005"),
    4: Product(id=4, name="智能水杯", category="生活用品", price=199.0, stock=0, sku="CP-009"),
}
_next_id = 5


# ---------- 纯函数 + 端点 ----------


def build_product_from_create(product_id: int, data: ProductCreate) -> Product:
    """
    【model_dump · §14.2】把「入库单」变成带 id 的完整商品。

    任务:用 data.model_dump() 得到字段 dict,再 Product(id=product_id, **...) 返回。
         create / update 端点都会调用它——id 策略由调用方决定。

    示例:
        p = ProductCreate(name="键盘", category="电脑外设", price=599, stock=10, sku="KB-001")
        build_product_from_create(1, p)
            -> Product(id=1, name="键盘", category="电脑外设", price=599.0, stock=10, sku="KB-001")

    提示:Pydantic v2 用 model_dump();不要用已废弃的 dict()。
    """
    # TODO: Product(id=product_id, **data.model_dump())
    ...


@app.get("/products")
def list_products():
    """
    【GET 列表 · §14.3】返回当前全部商品。

    任务:把 PRODUCTS 的 values 收成 list 返回。FastAPI 会自动序列化成 JSON 数组。

    示例:
        GET /products -> 200, 含「机械键盘」「无线鼠标」「设计模式」「智能水杯」

    提示:list(PRODUCTS.values());千万别自己 json.dumps(客户端会收到字符串不是数组)。
    """
    # TODO: 返回所有商品
    ...


@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    """
    【POST 创建 · §14.4】校验通过后分配 id、入库、返回新商品。

    任务:global _next_id → build_product_from_create → 写入 PRODUCTS → id 自增 → return。
         校验失败(price≤0 / 空名 / 坏 SKU)由框架直接 422,你不用写 if。

    示例:
        POST {"name":"降噪耳机","category":"影音设备","price":1299,"stock":80,"sku":"HP-006"}
            -> 201, body 含新 id 与全部字段
        POST {"name":"X","category":"图书","price":-1,"sku":"HP-006"} -> 422

    提示:函数内给 _next_id 赋值前必须 global(否则 UnboundLocalError)。
    """
    # TODO: global + build + 存入 + 自增 + return
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    【路径参数 + 404 · §14.5】按 id 查单个商品。

    任务:不在 PRODUCTS 里 → raise HTTPException(status_code=404, detail="商品不存在");
         否则返回该 Product。

    示例:
        GET /products/1 -> 200, name == "机械键盘"
        GET /products/99999 -> 404
        GET /products/abc -> 422(框架转 int 失败,函数体不执行)

    提示:if product_id not in PRODUCTS。别用 .get 返回 None(会变成 200 + null)。
    """
    # TODO: 404 守卫 + return
    ...


@app.put("/products/{product_id}")
def update_product(product_id: int, p: ProductCreate):
    """
    【PUT 全量更新 · §14.6】用请求体整单替换已有商品(保留路径里的 id)。

    任务:不存在 → 404;存在 → build_product_from_create(product_id, p) 写回并返回。

    示例:
        PUT /products/2 {"name":"无线鼠标","category":"电脑外设","price":169,"stock":350,"sku":"MS-002"}
            -> 200, id 仍为 2, price == 169.0
        PUT /products/99999 {...合法 body...} -> 404

    提示:复用 build_product_from_create,不要逐字段手拷。
    """
    # TODO: 404 守卫 + build + 写回 + return
    ...


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int) -> None:
    """
    【DELETE 204 · §14.7】删除商品;成功无响应体。

    任务:不存在 → 404;存在 → del PRODUCTS[product_id]。装饰器已设 status_code=204。

    示例:
        DELETE /products/4 -> 204
        再 GET /products/4 -> 404
        DELETE /products/99999 -> 404

    提示:不要 PRODUCTS.pop(id, None) 静默吞掉缺失 id。
    """
    # TODO: 404 守卫 + del
    ...


@app.get("/inventory/report")
def inventory_report():
    """
    【综合报表 · §14.8】运营库存汇总,复用 PRODUCTS。

    任务:返回 dict,四键——
      - total_skus: 商品种数
      - total_units: 所有 stock 之和
      - total_value: 库存总货值 Σ price*stock,round(..., 2)
      - out_of_stock: stock == 0 的商品名,sorted 排序

    示例(种子 4 件:599×120 + 159×300 + 75.5×200 + 199×0):
        GET /inventory/report
            -> {"total_skus": 4, "total_units": 620,
                "total_value": 134680.0, "out_of_stock": ["智能水杯"]}

    提示:items = list(PRODUCTS.values()); 生成式喂给 sum;out_of_stock 用 sorted(...)。
    """
    # TODO: 四字段汇总
    ...
