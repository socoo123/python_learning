"""
Ch22 测试:部署(uvicorn/gunicorn/Docker + 配置管理)。

测点(每个函数一个 TestXxx 类):
- TestWorkerCountForCores        §22.2 容量公式 2×CPU+1,下限兜底
- TestBuildGunicornCommand       §22.2 gunicorn 命令是 list[str] 数据
- TestGetSettings                §22.3 lru_cache 单例 + cache_clear 重读
- TestMaskSecret                 §22.3 脱敏:正常/太短/None/空串
- TestSafeConfigDict             §22.3 model_dump + 敏感字段被脱敏、其余原样
- TestBuildDockerRunCommand      §22.4 docker run -e 注入,env 排序确定性
- TestHealth                     §22.5 端点 200 + 字段 + 反映环境变量
- TestCheckProductionReadiness   §22.6 检查清单:dev/prod/边界,顺序断言
"""
import pytest
from fastapi.testclient import TestClient

from ch22_assignment import (
    APP_VERSION,
    DEFAULT_SECRET_KEY,
    Settings,
    app,
    build_docker_run_command,
    build_gunicorn_command,
    check_production_readiness,
    get_settings,
    health,  # noqa: F401  (经 TestClient 间接测)
    mask_secret,
    safe_config_dict,
    worker_count_for_cores,
)

# 所有可能干扰 Settings 默认值的环境变量
_ENV_KEYS = (
    "APP_NAME", "ENVIRONMENT", "DEBUG", "DATABASE_URL",
    "SECRET_KEY", "ACCESS_TOKEN_EXPIRE_MINUTES", "REDIS_URL",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """每个测试前清掉相关环境变量 + 清 lru_cache,保证互不影响。"""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------- §22.2 容量规划 ----------


class TestWorkerCountForCores:
    def test_four_cores(self):
        """【正常】4 核 → 2×4+1 = 9。"""
        assert worker_count_for_cores(4) == 9

    def test_single_core(self):
        """【正常】1 核 → 3。"""
        assert worker_count_for_cores(1) == 3

    def test_eight_cores(self):
        """【正常】8 核 → 17(拦住只写 2*n 忘了 +1 的实现)。"""
        assert worker_count_for_cores(8) == 17

    def test_zero_and_negative_fallback_to_one(self):
        """【边界】0 核 / 负数 → 下限 1(总不能起 0 个进程)。"""
        assert worker_count_for_cores(0) == 1
        assert worker_count_for_cores(-2) == 1


# ---------- §22.2 生成 gunicorn 命令 ----------


class TestBuildGunicornCommand:
    def test_typical_command(self):
        """【正常】9 worker / 8000 端口的完整命令。"""
        cmd = build_gunicorn_command("order_service.main:app", 9, 8000)
        assert cmd == [
            "gunicorn", "order_service.main:app",
            "-w", "9",
            "-k", "uvicorn.workers.UvicornWorker",
            "-b", "0.0.0.0:8000",
        ]

    def test_another_port_and_workers(self):
        """【正常】参数变化 → 命令对应位置变化(拦住硬编码)。"""
        cmd = build_gunicorn_command("ch22_assignment:app", 3, 9000)
        assert cmd[1] == "ch22_assignment:app"
        assert cmd[cmd.index("-w") + 1] == "3"
        assert cmd[cmd.index("-b") + 1] == "0.0.0.0:9000"

    def test_all_elements_are_str(self):
        """【边界】list 里必须全是 str(workers/port 要 str() 转换,不能直接放 int)。"""
        cmd = build_gunicorn_command("a:app", 1, 1)
        assert all(isinstance(x, str) for x in cmd)


# ---------- §22.3 get_settings(lru_cache 单例)----------


class TestGetSettings:
    def test_returns_settings_instance(self):
        """【正常】返回 Settings 实例,默认值正确。"""
        s = get_settings()
        assert isinstance(s, Settings)
        assert s.app_name == "order-service"
        assert s.environment == "dev"

    def test_is_cached_same_instance(self):
        """【缓存】同进程内两次调用返回同一对象(lru_cache 生效)。"""
        assert get_settings() is get_settings()

    def test_cache_clear_rereads_env(self, monkeypatch):
        """【缓存】cache_clear() 后重读环境变量;不清则拿到旧值。"""
        monkeypatch.setenv("ENVIRONMENT", "dev")
        get_settings.cache_clear()
        before = get_settings()
        assert before.environment == "dev"

        monkeypatch.setenv("ENVIRONMENT", "prod")
        assert get_settings().environment == "dev"   # 缓存命中,不重读

        get_settings.cache_clear()
        after = get_settings()
        assert after.environment == "prod"
        assert before is not after


# ---------- §22.3 配置脱敏 ----------


class TestMaskSecret:
    def test_normal_secret_shows_prefix_and_length(self):
        """【正常】露前 4 位 + 总长。"""
        assert mask_secret("super-secret-xyz") == "supe...(16 chars)"

    def test_custom_visible(self):
        """【正常】visible 可配(拦住写死 4 的实现)。"""
        assert mask_secret("abcdefgh", visible=2) == "ab...(8 chars)"

    def test_too_short_fully_masked(self):
        """【边界】长度 <= visible 时全遮(露前 4 位就等于全露)。"""
        assert mask_secret("abc") == "***"          # 3 < 4
        assert mask_secret("abcd") == "***"         # 4 == 4,也全遮

    def test_none_and_empty(self):
        """【边界】None / 空串 → "(unset)"(区分「没配」和「配错」)。"""
        assert mask_secret(None) == "(unset)"
        assert mask_secret("") == "(unset)"


# ---------- §22.3 脱敏后的启动配置 ----------


class TestSafeConfigDict:
    def test_secret_is_masked_others_plain(self):
        """【正常】secret_key 被脱敏;非敏感字段原样保留。"""
        d = safe_config_dict(Settings())
        assert d["app_name"] == "order-service"
        assert d["environment"] == "dev"
        assert d["debug"] is True
        assert d["secret_key"] == mask_secret(DEFAULT_SECRET_KEY) == "dev-...(20 chars)"
        assert d["redis_url"] is None

    def test_contains_all_fields(self):
        """【正常】字段齐全(model_dump 全量导出)。"""
        d = safe_config_dict(Settings())
        assert set(d) == {
            "app_name", "environment", "debug", "database_url",
            "secret_key", "access_token_expire_minutes", "redis_url",
        }

    def test_real_secret_never_appears(self):
        """【边界】真实密钥绝不出现在结果里(短密钥也不列外)。"""
        d = safe_config_dict(Settings(secret_key="abc"))
        assert d["secret_key"] == "***"
        assert "abc" not in d.values()


# ---------- §22.4 生成 docker run 命令 ----------


class TestBuildDockerRunCommand:
    def test_with_env_sorted(self):
        """【正常】环境变量按 key 排序注入,镜像名在最后。"""
        cmd = build_docker_run_command(
            "order-service:1.0.0", 8000,
            {"SECRET_KEY": "abc", "DATABASE_URL": "postgresql://db/orders"},
        )
        assert cmd == [
            "docker", "run", "-d", "-p", "8000:8000",
            "-e", "DATABASE_URL=postgresql://db/orders",
            "-e", "SECRET_KEY=abc",
            "order-service:1.0.0",
        ]

    def test_env_order_is_deterministic(self):
        """【正常】不同插入顺序 → 同一命令(排序保证可 diff/可测)。"""
        env1 = {"B": "2", "A": "1"}
        env2 = {"A": "1", "B": "2"}
        assert build_docker_run_command("img", 8000, env1) == \
               build_docker_run_command("img", 8000, env2)

    def test_without_env(self):
        """【边界】env 为 None → 不带 -e,命令仍然完整。"""
        cmd = build_docker_run_command("order-service:1.0.0", 8000)
        assert cmd == ["docker", "run", "-d", "-p", "8000:8000", "order-service:1.0.0"]

    def test_port_mapping_uses_given_port(self):
        """【边界】宿主端口可变,容器端口固定 8000(拦住写死 8000:8000)。"""
        cmd = build_docker_run_command("img", 9000)
        assert cmd[cmd.index("-p") + 1] == "9000:8000"


# ---------- §22.5 健康检查端点 ----------


class TestHealth:
    def test_returns_200_with_config(self):
        """【正常】200 + status/app/environment/version/debug 五字段。"""
        resp = TestClient(app).get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["app"] == "order-service"
        assert body["environment"] == "dev"
        assert body["version"] == APP_VERSION
        assert body["debug"] is True

    def test_reflects_env_after_cache_clear(self, monkeypatch):
        """【正常】改环境变量 + 清缓存,/health 返回新配置。"""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("APP_NAME", "Staging API")
        get_settings.cache_clear()

        body = TestClient(app).get("/health").json()
        assert body["environment"] == "staging"
        assert body["app"] == "Staging API"

    def test_version_is_constant(self):
        """【边界】version 永远来自 APP_VERSION,不受环境变量影响。"""
        body = TestClient(app).get("/health").json()
        assert body["version"] == "1.0.0" == APP_VERSION


# ---------- §22.6 上线前安全检查清单 ----------


class TestCheckProductionReadiness:
    def test_dev_defaults_only_warn_default_secret(self):
        """【正常】全默认 dev 配置:只有「默认密钥」一条(dev 开 DEBUG/用 sqlite 不算问题)。"""
        assert check_production_readiness(Settings()) == [
            "SECRET_KEY 仍是开发默认值,必须更换",
        ]

    def test_prod_with_defaults_flags_three(self):
        """【正常】默认配置直接上 prod:DEBUG + 默认密钥 + SQLite 三条,顺序固定。"""
        assert check_production_readiness(Settings(environment="prod")) == [
            "生产环境必须关闭 DEBUG",
            "SECRET_KEY 仍是开发默认值,必须更换",
            "生产环境不应使用 SQLite",
        ]

    def test_prod_ready_returns_empty(self):
        """【正常】合格生产配置 → 空列表(可以上线)。"""
        ok = Settings(
            environment="prod", debug=False,
            secret_key="x" * 32, database_url="postgresql://db/orders",
        )
        assert check_production_readiness(ok) == []

    def test_short_secret_flagged_in_any_env(self):
        """【边界】短密钥任何环境都拦;默认密钥(20 字符)不触发「太短」。"""
        assert check_production_readiness(Settings(secret_key="abc")) == [
            "SECRET_KEY 太短(至少 16 字符)",
        ]
        problems = check_production_readiness(Settings())
        assert not any("太短" in p for p in problems)

    def test_prod_sqlite_only_when_prod(self):
        """【边界】staging 用 SQLite 不拦(只有 prod 拦)。"""
        s = Settings(environment="staging", debug=False, secret_key="y" * 32)
        assert check_production_readiness(s) == []
