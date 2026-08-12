"""
Ch13 作业:HTTP 客户端 httpx —— 订单服务对接「商品中心」中台 API。

主线场景:你是订单服务(order-service)的后端负责人,要用 httpx 写一个
商品中心客户端模块:拉列表 → 搜索 → 创建 → 查单个(404)→ 带认证 → 改库存
→ 带重试 → 聚合报表。

每个函数都接收一个 httpx.Client 参数(依赖注入:实战传 httpx.Client(),
测试传带 MockTransport 的 client,无需真服务 —— 见 tutorial §13.8/§13.9)。

    uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import httpx


# ========== §13.1 GET + raise_for_status ==========


def fetch_products(client: httpx.Client, url: str) -> list:
    """
    【GET 列表 · §13.1】GET 商品列表,返回解析后的 JSON 数组;非 2xx/3xx 抛异常。

    场景:订单服务启动时要拉商品中心的全量商品做本地缓存。

    示例:
        # 商品中心返回 [{"id":1,"name":"机械键盘",...}, ...](共 10 条)
        fetch_products(client, "http://product-center/api/products")
            -> [{"id": 1, "name": "机械键盘", ...}, ...]
        # 商品中心 500 → 抛 httpx.HTTPStatusError

    提示:三行——client.get(url) → resp.raise_for_status() → resp.json()。
         千万别忘 raise_for_status:httpx 默认把 404/500 也当「成功响应」。
    """
    # TODO: get + raise_for_status + json
    ...


# ========== §13.2 params 查询参数 ==========


def search_products(
    client: httpx.Client,
    url: str,
    keyword: str | None = None,
    max_price: float | None = None,
) -> list:
    """
    【查询参数 · §13.2】GET 搜索商品。keyword / max_price 均可选,【None 的参数不要发】。

    场景:订单服务的选品页,两个筛选条件用户可填可不填。

    示例:
        search_products(client, "/api/products/search", keyword="键盘", max_price=600)
            -> 实际请求 /api/products/search?keyword=键盘&max_price=600
        search_products(client, "/api/products/search")
            -> 实际请求 /api/products/search(不带任何 query)

    提示:先建空 dict,非 None 才放进去;client.get(url, params=params) 会自动
         URL 编码(中文变 %XX)。别用 f-string 拼 query(§13.2 的两个雷)。
    """
    # TODO: 组装 params dict(只放非 None 条件)+ get(url, params=...) + raise_for_status + json
    ...


# ========== §13.3 POST + json body ==========


def create_product(client: httpx.Client, url: str, product: dict) -> dict:
    """
    【POST 创建 · §13.3】POST 创建商品(json body),返回服务端响应(含生成的 id)。

    场景:供应商在订单服务后台录入新商品,转发给商品中心。

    示例:
        create_product(client, "/api/products", {"name": "机械键盘", "price": 599.0})
            -> 服务端 201 → {"id": 11, "name": "机械键盘", "price": 599.0}
        # 服务端 400(参数非法)→ 抛 httpx.HTTPStatusError

    提示:client.post(url, json=product) —— json= 自动序列化 dict +
         设 Content-Type: application/json。用 data= 发的是表单,JSON API 会拒。
    """
    # TODO: post(url, json=...) + raise_for_status + json
    ...


# ========== §13.4 404 精细处理 ==========


def get_product_or_none(client: httpx.Client, url: str) -> dict | None:
    """
    【状态码处理 · §13.4】GET 单个商品;【404 返回 None】,其他错误(500 等)抛异常。

    场景:订单里引用的商品可能已下架——「不存在」是正常业务结果,不该炸;
         但商品中心真挂了(500)必须抛出来。

    示例:
        get_product_or_none(client, "/api/products/1")    -> {"id": 1, "name": "机械键盘", ...}
        get_product_or_none(client, "/api/products/999")  -> None(已下架)
        # 服务端 500 → 抛 httpx.HTTPStatusError

    提示:顺序是全部诀窍——先 if resp.status_code == 404: return None,
         再 resp.raise_for_status() 兜底其余错误。顺序反了 404 也会被抛掉。
    """
    # TODO: get + 判 404 返回 None + raise_for_status + json
    ...


# ========== §13.5 headers Bearer 认证 ==========


def fetch_with_auth(client: httpx.Client, url: str, token: str) -> dict:
    """
    【请求头认证 · §13.5】带 Bearer Token 的 GET,返回解析后的 JSON。

    场景:商品中心的敏感接口要认证——请求头 Authorization: Bearer <token>,
         token 错/缺 → 401。

    示例:
        fetch_with_auth(client, "/api/products/1", token="abc123")
            -> 请求头带 Authorization: Bearer abc123 → {"id": 1, ...}
        fetch_with_auth(client, "/api/products/1", token="wrong")
            -> 401 → 抛 httpx.HTTPStatusError

    提示:client.get(url, headers={"Authorization": f"Bearer {token}"})。
         真实项目里 token 从 os.environ 读(Ch12),绝不硬编码。
    """
    # TODO: get(url, headers={"Authorization": f"Bearer {token}"}) + raise_for_status + json
    ...


# ========== §13.6 PUT + json body ==========


def update_stock(client: httpx.Client, url: str, delta: int) -> dict:
    """
    【PUT 修改 · §13.6】PUT 调整库存,body 为 {"delta": delta},返回更新后的商品。

    场景:订单成交 2 件,调商品中心扣库存:delta=-2(负=扣减,正=回补)。

    示例:
        update_stock(client, "/api/products/1/stock", -2)
            -> PUT /api/products/1/stock  body={"delta": -2}
            -> {"id": 1, "name": "机械键盘", "stock": 118, ...}
        # 商品不存在(404)→ 抛 httpx.HTTPStatusError

    提示:client.put(url, json={"delta": delta}),和 post 一个套路。
         注意:若服务端返回 204 No Content(如 DELETE),千万别 resp.json()。
    """
    # TODO: put(url, json={"delta": delta}) + raise_for_status + json
    ...


# ========== §13.7 超时/异常体系 + 重试 ==========


def fetch_with_retry(client: httpx.Client, url: str, retries: int = 3) -> list:
    """
    【重试 · §13.7】GET 列表,带重试:【5xx 和网络错误(超时/连接失败)重试,
    4xx 立即抛】;最多试 retries 次,全部失败则抛出最后一次的异常。

    场景:商品中心抖动(间歇 503 / 偶发超时),订单服务不能一次失败就跪;
         但 4xx 是请求本身有错,重发 100 次也没用。

    示例:
        # 商品中心 503 → 503 → 200:第 3 次成功返回列表(共发 3 次请求)
        fetch_with_retry(client, "/api/products", retries=3) -> [...]
        # 一直 503:试满 3 次后抛 HTTPStatusError
        # 400:第 1 次就抛,不多发请求

    提示:for attempt in range(retries) + try:
              成功就 return;
              except httpx.HTTPStatusError:4xx 直接 raise;5xx 且已是最后一次也 raise;
              except httpx.TransportError:最后一次 raise,否则进下一轮。
    """
    # TODO: for attempt in range(retries) 循环 + try/except 分类处置(见上)
    ...


# ========== §13.10 综合:聚合报表 ==========


def aggregate_by_category(client: httpx.Client, url: str) -> list[dict]:
    """
    【综合 · §13.10】拉全量商品,按 category 分组统计,返回报表(按总价降序)。

    场景:运营要「各类目货品汇总」——每个类目的商品数和库存总价,贵的类目排前面。

    示例:
        # 商品中心返回 products.json 的 10 条商品时:
        aggregate_by_category(client, "/api/products")
            -> [
                {"category": "电脑外设", "count": 4, "total_price": 3226.0},
                {"category": "生活用品", "count": 2, "total_price": 1798.0},
                {"category": "影音设备", "count": 2, "total_price": 1698.0},
                {"category": "图书",     "count": 2, "total_price": 164.5},
            ]
        # 商品中心返回 [] → 返回 []

    提示:① 直接调用你写好的 fetch_products(client, url) 拉数据;
         ② dict.setdefault(category, {...}) 分组累加 count 和 price;
         ③ 整形成 {"category":..., "count":..., "total_price": round(x, 2)};
         ④ sort(key=..., reverse=True) 按 total_price 降序。
    """
    # TODO: 调 fetch_products 拉数据 + setdefault 分组累加 + 整形 + 降序排序
    ...


# ---------------------------------------------------------------------
# 实战中这样用(真服务):
#     with httpx.Client(base_url="http://localhost:8000", timeout=5.0) as client:
#         products = fetch_products(client, "/api/products")
# 测试用 MockTransport 模拟响应(见 test_ch13_assignment.py / tutorial §13.9)
# ---------------------------------------------------------------------
