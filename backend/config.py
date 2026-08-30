"""Application configuration.

Environment variables are read exactly once, here, via ``get_settings()``.
Nothing else in the codebase should touch ``os.environ`` for configuration.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple

DEFAULT_DATABASE_URL = "postgresql://sammylee@localhost/bread_makes"
DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000"


@dataclass(frozen=True)
class Settings:
  """Immutable snapshot of runtime configuration."""

  database_url: str = DEFAULT_DATABASE_URL
  pool_min_size: int = 2
  pool_max_size: int = 10
  allowed_origins: Tuple[str, ...] = (DEFAULT_ALLOWED_ORIGINS,)


@lru_cache
def get_settings() -> Settings:
  """Build the Settings once and cache it for the process lifetime."""
  return Settings(
    database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    pool_min_size=int(os.environ.get("DB_POOL_MIN_SIZE", "2")),
    pool_max_size=int(os.environ.get("DB_POOL_MAX_SIZE", "10")),
    allowed_origins=tuple(
      origin.strip()
      for origin in os.environ.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(
        ","
      )
      if origin.strip()
    ),
  )
