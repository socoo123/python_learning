"""
Ch13 作业:HTTP 客户端 httpx —— 调用 API。

3 个函数演示「调」REST API 的常见模式:GET 列表 / POST 创建 / GET 单个(处理 404)。
每个函数接收一个 httpx.Client 参数(依赖注入:实战传 httpx.Client(),测试传带
MockTransport 的 client,无需真服务)。

    uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import httpx


# ========== §13.1 GET + raise_for_status ==========


def fetch_products(client: httpx.Client, url: str):
    """
    【GET · §13.1】GET 商品列表,返回解析后的 JSON。【非 2xx 抛异常】。

    示例:
        fetch_products(client, "http://localhost:8000/api/products")
            -> [{"name":"键盘"}, ...]

    思路:
        resp = client.get(url)
        resp.raise_for_status()    # 4xx/5xx 抛 HTTPStatusError(不自己判 status_code)
        return resp.json()
    """
    # TODO: get + raise_for_status + json
    ...


# ========== §13.2 POST + json body ==========


def create_product(client: httpx.Client, url: str, product: dict) -> dict:
    """
    【POST · §13.2】POST 创建商品(json body),返回服务端响应(通常含生成的 id)。

    示例:
        create_product(client, "/api/products", {"name":"键盘","price":599})
            -> {"id":1, "name":"键盘", "price":599}

    思路:client.post(url, json=product) —— json= 参数自动序列化 + 设 Content-Type。
         再 raise_for_status + resp.json()。
    """
    # TODO: post(url, json=...) + raise_for_status + json
    ...


# ========== §13.3 处理 404 ==========


def get_product_or_none(client: httpx.Client, url: str):
    """
    【状态码处理 · §13.3】GET 单个商品;【404 返回 None】,其他错误(500 等)抛异常。

    示例:
        get_product_or_none(client, "/api/products/999")  -> None(不存在)
        get_product_or_none(client, "/api/products/1")    -> {"id":1,...}

    思路:
        resp = client.get(url)
        if resp.status_code == 404:     # 单独放行 404
            return None
        resp.raise_for_status()          # 其他错误抛
        return resp.json()
    """
    # TODO: get + 判 404 返回 None + raise_for_status + json
    ...


# ---------------------------------------------------------------------
# 实战中这样用(真服务):
#     with httpx.Client(base_url="http://localhost:8000", timeout=5.0) as client:
#         products = fetch_products(client, "/api/products")
# 测试用 MockTransport 模拟响应(见 test_ch13_assignment.py / tutorial §13.5)
# ---------------------------------------------------------------------
