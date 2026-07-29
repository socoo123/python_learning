"""
Ch22 测试:配置管理(pydantic-settings)。

测点:
① 默认值 —— 不设任何环境变量,Settings() 字段取默认。
② 环境变量覆盖 —— monkeypatch 设 DATABASE_URL/SECRET_KEY/DEBUG/REDIS_URL 等 → 实例化 → 断言。
③ 类型转换 —— DEBUG=false(字符串)→ bool False。
④ 可选字段 —— redis_url 默认 None,设了就有值。
⑤ get_settings 缓存 —— 同一进程返回同一实例;cache_clear 后重读环境变量。
⑥ /health 端点 —— TestClient 打,返回含 app/environment/version/debug。
"""
import pytest
from fastapi.testclient import TestClient

from ch22_assignment import APP_VERSION, Settings, app, get_settings


# ---------- §22.3 默认值 ----------


def test_settings_defaults(monkeypatch):
    """【默认值】不设任何环境变量,Settings 走默认值。"""
    # 清掉可能影响的环境变量,保证干净
    for key in (
        "APP_NAME", "ENVIRONMENT", "DEBUG", "DATABASE_URL",
        "SECRET_KEY", "ACCESS_TOKEN_EXPIRE_MINUTES", "REDIS_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    s = Settings()

    assert s.app_name == "Product API"
    assert s.environment == "dev"
    assert s.debug is True
    assert s.database_url == "sqlite:///./app.db"
    assert s.secret_key == "dev-secret-change-me"
    assert s.access_token_expire_minutes == 30
    assert s.redis_url is None


# ---------- §22.3 环境变量覆盖 + 类型转换 ----------


def test_settings_env_overrides(monkeypatch):
    """【环境变量覆盖 + 类型转换】设环境变量 → 字段被覆盖且类型正确。

    pydantic-settings 把字符串环境变量按字段注解自动转 bool/int/str。
    """
    monkeypatch.setenv("APP_NAME", "订单服务")
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/orders")
    monkeypatch.setenv("SECRET_KEY", "super-secret-xyz")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")

    s = Settings()

    assert s.app_name == "订单服务"
    assert s.environment == "prod"
    assert s.debug is False                      # "false" → bool False
    assert s.database_url == "postgresql://user:pass@db:5432/orders"
    assert s.secret_key == "super-secret-xyz"
    assert s.access_token_expire_minutes == 120  # "120" → int 120
    assert s.redis_url == "redis://redis:6379/0"


def test_settings_bool_variants(monkeypatch):
    """【类型转换·细节】pydantic 对 bool 的多种字符串写法都识别。"""
    for truthy in ("true", "True", "1", "yes", "on"):
        monkeypatch.setenv("DEBUG", truthy)
        assert Settings().debug is True, f"{truthy!r} 应判为 True"
    for falsy in ("false", "False", "0", "no", "off"):
        monkeypatch.setenv("DEBUG", falsy)
        assert Settings().debug is False, f"{falsy!r} 应判为 False"


def test_settings_env_not_case_sensitive(monkeypatch):
    """【大小写不敏感】case_sensitive=False,DATABASE_URL / database_url 都能匹配。"""
    monkeypatch.setenv("database_url", "mysql://localhost/test")  # 全小写
    assert Settings().database_url == "mysql://localhost/test"


def test_settings_invalid_int_raises(monkeypatch):
    """【fail-fast】类型转换失败 → ValidationError(启动即报错,= Spring 启动校验)。"""
    from pydantic import ValidationError

    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "不是数字")
    with pytest.raises(ValidationError):
        Settings()


# ---------- §22.3 get_settings 依赖(lru_cache 单例)----------


def test_get_settings_is_cached(monkeypatch):
    """【缓存】get_settings() 用 lru_cache,同进程内只构造一次 → 返回同一对象。"""
    monkeypatch.setenv("APP_NAME", "缓存验证")
    get_settings.cache_clear()          # 清缓存,保证本次读环境

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2                      # 同一实例(缓存生效)
    assert s1.app_name == "缓存验证"


def test_get_settings_cache_clear_rereads_env(monkeypatch):
    """【清缓存重读】cache_clear() 后再调,会重新读环境变量。"""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    get_settings.cache_clear()
    before = get_settings()
    assert before.environment == "dev"

    # 改环境变量,但没清缓存 → 仍是旧值
    monkeypatch.setenv("ENVIRONMENT", "prod")
    assert get_settings().environment == "dev"   # 缓存命中,不重读

    # 清缓存 → 重读,拿到新值
    get_settings.cache_clear()
    after = get_settings()
    assert after.environment == "prod"
    assert before is not after                    # 新实例


def test_settings_dependency_is_injectable():
    """【依赖注入】Settings 可作为 FastAPI 依赖被注入(get_settings)。"""
    # get_settings 返回的是 Settings 实例(类型正确,可被 Depends 使用)
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, Settings)


# ---------- §22.1 /health 端点 ----------


def test_health_endpoint_returns_config():
    """【端点】/health 用 Depends(get_settings) 注入配置,返回关键字段。

    = Spring Boot Actuator 的 /actuator/health,K8s 探针打这个端点。
    """
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "ok"
    assert "app" in body
    assert "environment" in body
    assert body["version"] == APP_VERSION
    assert "debug" in body
    # app_name 是 Settings.app_name 的值
    assert body["app"] == Settings().app_name


def test_health_reflects_env(monkeypatch):
    """【端点反映环境】改环境变量 + 清缓存,/health 返回的 environment 随之变化。"""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("APP_NAME", "Staging API")
    get_settings.cache_clear()

    client = TestClient(app)
    body = client.get("/health").json()
    assert body["environment"] == "staging"
    assert body["app"] == "Staging API"

    get_settings.cache_clear()   # 收尾,避免污染后续测试
