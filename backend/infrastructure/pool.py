"""Connection pool. One ``DatabasePool`` per process (built in the app lifespan)."""

from contextlib import contextmanager
from typing import Optional
from urllib.parse import urlparse

import logging

from psycopg_pool import ConnectionPool

from ..config import Settings, get_settings

logger = logging.getLogger("psycopg")


def _build_conninfo(settings: Settings) -> str:
  url = urlparse(settings.database_url)
  parts = [
    f"host={url.hostname or 'localhost'}",
    f"port={url.port or 5432}",
    f"dbname={url.path.lstrip('/')}",
    f"user={url.username or ''}",
  ]
  if url.password:
    parts.append(f"password={url.password}")
  return " ".join(parts)


class DatabasePool:
  """Owns a psycopg connection pool. Construct one per process, in the app
  lifespan (or per test session); call ``close()`` on shutdown."""

  def __init__(self, settings: Optional[Settings] = None):
    settings = settings or get_settings()
    self.pool = ConnectionPool(
      _build_conninfo(settings),
      min_size=settings.pool_min_size,
      max_size=settings.pool_max_size,
      open=False,
    )
    self.pool.open()

  @contextmanager
  def get_connection(self):
    conn = self.pool.getconn()
    logger.debug(f"Got connection from pool: {conn}")
    try:
      yield conn
    except Exception as e:
      logger.error(f"Error during database operation: {str(e)}")
      raise
    finally:
      logger.debug(f"Returning connection to pool: {conn}")
      self.pool.putconn(conn)

  def getconn(self):
    """Check out a raw connection. The caller owns commit/rollback and must
    return it with ``putconn``. Used by ``UnitOfWork``."""
    conn = self.pool.getconn()
    logger.debug(f"Checked out connection: {conn}")
    return conn

  def putconn(self, conn):
    logger.debug(f"Returning connection: {conn}")
    self.pool.putconn(conn)

  def close(self):
    self.pool.close()
