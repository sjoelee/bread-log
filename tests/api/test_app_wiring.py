"""Stage 1 — verifies the config / lifespan / dependency-injection seam.

These don't touch business logic; they check that the app wires itself together
the way the DDD refactor needs: an explicit pool lifecycle, services injected
(and therefore overridable), settings read once.
"""

from unittest.mock import MagicMock

from backend.config import Settings, get_settings
from backend.db import DatabasePool, _build_conninfo
from backend.service import app, get_recipe_service, lifespan


class TestDatabasePool:
  def test_open_on_construct_and_close_on_close(self):
    pool = DatabasePool(get_settings())
    try:
      assert not pool.pool.closed
    finally:
      pool.close()
    assert pool.pool.closed


class TestLifespanWiring:
  def test_app_registers_our_lifespan(self):
    # FastAPI stores the lifespan callable it was constructed with.
    assert app.router.lifespan_context is lifespan

  def test_session_fixture_left_a_live_pool(self):
    # _app_lifespan (conftest, session-scoped autouse) ran startup.
    assert isinstance(app.state.pool, DatabasePool)
    assert not app.state.pool.pool.closed


class TestDependencyInjection:
  def test_recipe_service_is_injected_and_overridable(self, client):
    fake = MagicMock()
    fake.list_recipes.return_value = []

    app.dependency_overrides[get_recipe_service] = lambda: fake
    try:
      resp = client.get("/recipes/?limit=1")
    finally:
      app.dependency_overrides.pop(get_recipe_service, None)

    assert resp.status_code == 200
    assert resp.json() == []
    fake.list_recipes.assert_called_once()

  def test_no_module_global_service_or_connector(self):
    import backend.service as svc

    assert not hasattr(svc, "db_conn")
    assert not hasattr(svc, "recipe_service")


class TestSettings:
  def test_settings_is_cached(self):
    assert get_settings() is get_settings()

  def test_build_conninfo_reads_settings_not_env(self):
    s = Settings(database_url="postgresql://alice:secret@db.example:6543/mydb")
    info = _build_conninfo(s)
    assert "host=db.example" in info
    assert "port=6543" in info
    assert "dbname=mydb" in info
    assert "user=alice" in info
    assert "password=secret" in info
