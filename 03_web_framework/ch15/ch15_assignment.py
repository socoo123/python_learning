"""
Ch15 作业:路由参数 —— 路径/查询参数、Query/Path 校验、分页排序、嵌套请求体、APIRouter。

场景:你是「极客商城」后端。Ch14 的 CRUD 上线后,运营后台提了 2.0 需求:
  商品:按类目/价格带筛选、关键词搜索、价格/库存榜单、详情(id 校验)
  订单:列表分页(12 条种子)、收「一单多商品」的嵌套 JSON 下单
  工程:路由按资源分组(APIRouter);系统路由(健康检查)已定义,待你注册

    uv sync --extra web
    uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v

⚠️ 题目按「路由注册顺序」排列:具体路径(/search、/ranking)必须先于参数路径
(/products/{product_id})注册,否则会被抢走(§15.3)。做题顺序按 tutorial 对应表跳。
每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field


# ---------- 模型(脚手架,直接用)----------


class Product(BaseModel):
    """商品(数据与 assets/mock_data/products.json 一致)。"""

    id: int
    name: str
    category: str
    price: float
    stock: int = 0
    sku: str


class OrderItem(BaseModel):
    """订单里的商品行快照:下单那一刻的名称/单价/小计。"""

    product_id: int
    name: str
    quantity: int
    unit_price: float
    subtotal: float


class Order(BaseModel):
    id: int
    customer: str
    items: list[OrderItem]
    total: float
    status: str = "pending"


class OrderItemCreate(BaseModel):
    """下单请求里的商品行(§15.6)。约束:product_id >= 1;quantity 1~99。"""

    product_id: int = Field(ge=1)
    quantity: int = Field(gt=0, le=99)


class OrderCreate(BaseModel):
    """下单请求(§15.6 嵌套请求体):客户名非空,商品行至少 1 条。"""

    customer: str = Field(min_length=1)
    items: list[OrderItemCreate] = Field(min_length=1)


# ---------- 内存数据(Ch19 才接数据库)----------

PRODUCTS: list[Product] = [
    Product(id=1, name="机械键盘", category="电脑外设", price=599.0, stock=120, sku="KB-001"),
    Product(id=2, name="无线鼠标", category="电脑外设", price=159.0, stock=300, sku="MS-002"),
    Product(id=3, name="27寸4K显示器", category="电脑外设", price=2199.0, stock=45, sku="MN-003"),
    Product(id=4, name="Python编程:从入门到实践", category="图书", price=89.0, stock=500, sku="BK-004"),
    Product(id=5, name="设计模式", category="图书", price=75.5, stock=200, sku="BK-005"),
    Product(id=6, name="降噪耳机", category="影音设备", price=1299.0, stock=80, sku="HP-006"),
    Product(id=7, name="蓝牙音箱", category="影音设备", price=399.0, stock=150, sku="SP-007"),
    Product(id=8, name="USB-C扩展坞", category="电脑外设", price=269.0, stock=220, sku="DK-008"),
    Product(id=9, name="智能水杯", category="生活用品", price=199.0, stock=0, sku="CP-009"),
    Product(id=10, name="人体工学椅", category="生活用品", price=1599.0, stock=30, sku="CH-010"),
]

ORDERS: list[Order] = [
    Order(id=1, customer="张三", status="shipped", total=599.0, items=[
        OrderItem(product_id=1, name="机械键盘", quantity=1, unit_price=599.0, subtotal=599.0),
    ]),
    Order(id=2, customer="李四", status="shipped", total=318.0, items=[
        OrderItem(product_id=2, name="无线鼠标", quantity=2, unit_price=159.0, subtotal=318.0),
    ]),
    Order(id=3, customer="王五", status="paid", total=2468.0, items=[
        OrderItem(product_id=3, name="27寸4K显示器", quantity=1, unit_price=2199.0, subtotal=2199.0),
        OrderItem(product_id=8, name="USB-C扩展坞", quantity=1, unit_price=269.0, subtotal=269.0),
    ]),
    Order(id=4, customer="赵六", status="paid", total=267.0, items=[
        OrderItem(product_id=4, name="Python编程:从入门到实践", quantity=3, unit_price=89.0, subtotal=267.0),
    ]),
    Order(id=5, customer="张三", status="paid", total=1299.0, items=[
        OrderItem(product_id=6, name="降噪耳机", quantity=1, unit_price=1299.0, subtotal=1299.0),
    ]),
    Order(id=6, customer="钱七", status="pending", total=240.0, items=[
        OrderItem(product_id=5, name="设计模式", quantity=2, unit_price=75.5, subtotal=151.0),
        OrderItem(product_id=4, name="Python编程:从入门到实践", quantity=1, unit_price=89.0, subtotal=89.0),
    ]),
    Order(id=7, customer="孙八", status="pending", total=1599.0, items=[
        OrderItem(product_id=10, name="人体工学椅", quantity=1, unit_price=1599.0, subtotal=1599.0),
    ]),
    Order(id=8, customer="李四", status="pending", total=558.0, items=[
        OrderItem(product_id=7, name="蓝牙音箱", quantity=1, unit_price=399.0, subtotal=399.0),
        OrderItem(product_id=2, name="无线鼠标", quantity=1, unit_price=159.0, subtotal=159.0),
    ]),
    Order(id=9, customer="周九", status="shipped", total=398.0, items=[
        OrderItem(product_id=9, name="智能水杯", quantity=2, unit_price=199.0, subtotal=398.0),
    ]),
    Order(id=10, customer="王五", status="paid", total=758.0, items=[
        OrderItem(product_id=1, name="机械键盘", quantity=1, unit_price=599.0, subtotal=599.0),
        OrderItem(product_id=2, name="无线鼠标", quantity=1, unit_price=159.0, subtotal=159.0),
    ]),
    Order(id=11, customer="赵六", status="pending", total=2199.0, items=[
        OrderItem(product_id=3, name="27寸4K显示器", quantity=1, unit_price=2199.0, subtotal=2199.0),
    ]),
    Order(id=12, customer="张三", status="shipped", total=538.0, items=[
        OrderItem(product_id=8, name="USB-C扩展坞", quantity=2, unit_price=269.0, subtotal=538.0),
    ]),
]
_next_order_id = 13

# ---------- 路由分组(§15.7:一个资源一个 router)----------

products_router = APIRouter(tags=["商品"])
orders_router = APIRouter(tags=["订单"])


# ---------- 商品查询端点(注意注册顺序:具体路径在前,参数路径在后)----------


@products_router.get("/products")
def list_products(
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
):
    """
    【可选查询参数 · §15.2】按类目/价格带筛选商品,三个条件可任意组合。

    任务:三个参数都是「不传 = None = 不过滤」。用 `if xxx is not None` 守卫,
         逐级用列表推导过滤:category 精确相等;price >= min_price;price <= max_price。

    示例(种子 10 件):
        GET /products                          -> 全部 10 件
        GET /products?category=电脑外设        -> 4 件(键盘/鼠标/显示器/扩展坞)
        GET /products?max_price=200            -> 4 件(鼠标159/Python89/设计模式75.5/水杯199)
        GET /products?category=电脑外设&min_price=500&max_price=1500 -> [机械键盘 599]
        GET /products?category=不存在          -> []

    提示:判断「传没传」用 `is not None`,不要 `if min_price:`(会把 0 当没传)。
    """
    # TODO: is not None 守卫 + 逐级列表推导过滤
    ...


@products_router.get("/products/search")
def search_products(
    q: str = Query(min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    """
    【Query 校验 · §15.3】按「名称或类目」关键词搜索。q 必填且至少 2 字符;limit 默认 10,范围 1~50。

    任务:返回「name 或 category 包含 q」的商品,最多 limit 条(切片截断)。
         校验(缺 q / q 太短 / limit 越界)由签名里的 Query 自动 422,你不用写 if。

    示例:
        GET /products/search?q=键盘             -> [机械键盘](名称匹配)
        GET /products/search?q=影音             -> [降噪耳机, 蓝牙音箱](类目匹配)
        GET /products/search?q=电脑外设&limit=2 -> 4 条匹配截断到 2 条
        GET /products/search?q=机               -> 422(不足 2 字符)
        GET /products/search                    -> 422(缺必填 q)
        GET /products/search?q=键盘&limit=0     -> 422(limit < 1)

    提示:`q in p.name or q in p.category` 做包含匹配;`matched[:limit]` 截断。
         本函数必须定义在 get_product 之前,否则 /products/search 被 {product_id} 抢走。
    """
    # TODO: 名称/类目包含匹配 + 切片截断
    ...


@products_router.get("/products/ranking")
def list_product_ranking(
    sort_by: Literal["price", "stock"] = "price",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(5, ge=1, le=20),
):
    """
    【Literal 白名单 · §15.5】商品榜单:按 price/stock 排序,取前 limit 名。

    任务:sort_by/order 是 Literal 枚举,非法值框架自动 422(不用你判断)。
         用 sorted 排序:升序 order == "asc",降序 reverse=True;再 [:limit] 截断。

    示例:
        GET /products/ranking
            -> 价格升序前 5:设计模式75.5 / Python编程89 / 无线鼠标159 / 智能水杯199 / 扩展坞269
        GET /products/ranking?sort_by=price&order=desc&limit=3
            -> [27寸4K显示器 2199, 人体工学椅 1599, 降噪耳机 1299]
        GET /products/ranking?sort_by=stock&order=desc&limit=1
            -> [Python编程 stock=500]
        GET /products/ranking?sort_by=name   -> 422(不在白名单)

    提示:`sorted(PRODUCTS, key=lambda p: getattr(p, sort_by), reverse=order == "desc")`。
         Literal 白名单保证 sort_by 一定是合法字段名,getattr 才安全。
    """
    # TODO: sorted + getattr(p, sort_by) + reverse + 截断
    ...


@products_router.get("/products/{product_id}")
def get_product(product_id: int = Path(ge=1)):
    """
    【路径参数 + Path 校验 · §15.1】按 id 查单个商品;不存在 404。

    任务:遍历 PRODUCTS 找 id 匹配的返回;找不到 raise HTTPException(404)。
         product_id 的 int 转换(abc → 422)和 ge=1 约束(0 → 422)框架已包办。

    示例:
        GET /products/1    -> 200, name == "机械键盘"
        GET /products/999  -> 404, {"detail": "商品不存在"}
        GET /products/abc  -> 422(int 转换失败,函数体不执行)
        GET /products/0    -> 422(Path(ge=1) 约束失败)

    提示:找不到要 `raise HTTPException(status_code=404, detail="商品不存在")`,
         别返回 None(会变成 200 + null)。我定义在最后:路由顺序,具体路径先注册。
    """
    # TODO: 遍历查找;不存在 HTTPException(404)
    ...


# ---------- 订单端点 ----------


@orders_router.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """
    【分页 · §15.4】订单列表分页,返回「当前页数据 + 分页元信息」。

    任务:切片取当前页,返回 dict 五键——
      - items: 当前页订单,start = (page - 1) * size,切 [start : start + size]
      - total: 订单总数(12)
      - page / size: 回显请求参数
      - pages: 总页数,向上取整 (total + size - 1) // size

    示例(种子 12 条):
        GET /orders                -> items 10 条, total=12, pages=2
        GET /orders?page=2         -> items 2 条(id 11、12)
        GET /orders?page=99        -> items == [](越界返空,不是 404)
        GET /orders?size=5&page=3  -> items 2 条(id 11、12), pages=3
        GET /orders?page=0         -> 422;GET /orders?size=200 -> 422

    提示:切片越界自动得 [],不要手动 raise 404;pages 用整数向上取整公式。
    """
    # TODO: 公式切片 + 五元组元信息
    ...


@orders_router.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    """
    【嵌套请求体 · §15.6】下单:一单多商品,框架管形状、你管业务。

    任务:遍历 order.items,逐行——
      1. 按 product_id 查商品,查不到 raise HTTPException(404, f"商品不存在: {id}")
      2. 库存 < quantity  raise HTTPException(400, f"库存不足: {商品名}")
      3. 组装 OrderItem(快照 name/unit_price,subtotal = unit_price * quantity)
         然后:total = 各行 subtotal 之和;用 _next_order_id 分配 id(记得 global);
         append 到 ORDERS;id 自增;返回新 Order。
         形状校验(quantity=0 / items=[] / 空 customer)框架已 422,不用你写。

    示例:
        POST {"customer":"张三","items":[{"product_id":1,"quantity":2},
                                        {"product_id":4,"quantity":1}]}
            -> 201, id=13, total=1287.0(599*2 + 89), status="pending"
        POST {"customer":"李四","items":[{"product_id":999,"quantity":1}]} -> 404
        POST {"customer":"李四","items":[{"product_id":9,"quantity":1}]}   -> 400(水杯 stock=0)
        POST {"customer":"李四","items":[{"product_id":1,"quantity":0}]}   -> 422(框架)

    提示:查商品 `next((p for p in PRODUCTS if p.id == item.product_id), None)`;
         函数内给 _next_order_id 赋值前必须 global(Ch14 的坑)。
    """
    # TODO: 查商品(404)/ 验库存(400)/ 组装 OrderItem / total / global id / append / return
    ...


# ---------- 系统路由(脚手架:已定义,未注册)----------

system_router = APIRouter()


@system_router.get("/health")
def health():
    """健康检查(脚手架,已实现)。注册后:GET /system/health。"""
    return {"status": "ok"}


@system_router.get("/info")
def info():
    """服务信息(脚手架,已实现)。注册后:GET /system/info。"""
    return {"service": "极客商城", "version": "2.0"}


# ---------- app 组装(脚手架:商品/订单 router 已挂上)----------

app = FastAPI(title="极客商城 · 商品与订单 API")
app.include_router(products_router)
app.include_router(orders_router)


def register_system_router() -> None:
    """
    【APIRouter 分组 · §15.7】把 system_router 挂进 app,统一加前缀和文档标签。

    任务:一行代码——app.include_router(system_router, prefix="/system", tags=["系统"])。
         效果:/health 变成 /system/health,/info 变成 /system/info。

    示例:
        注册前:GET /system/health -> 404
        注册后:GET /system/health -> 200, {"status": "ok"}
               GET /system/info   -> 200, {"service": "极客商城", "version": "2.0"}

    提示:include_router 的 prefix 相当于 Spring 类级 @RequestMapping("/system");
         tags 是 /docs 里的分组名。生产代码只注册一次(测试里重复调用不影响正确性)。
    """
    # TODO: app.include_router(system_router, prefix=..., tags=...)
    ...
