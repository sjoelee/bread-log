"""Unit of Work: one connection and one transaction per use case.

A ``RecipeService`` use case runs inside ``with self._uow_factory() as uow:``.
Everything reached through ``uow.recipes`` shares that connection, so the whole
block is a single transaction — committed when it exits cleanly, rolled back if
it raises. The connection is always returned to the pool.
"""

from __future__ import annotations

import logging

from ..db import DatabasePool
from .recipe_repository import RecipeRepository

logger = logging.getLogger("unit_of_work")


class UnitOfWork:
  def __init__(self, pool: DatabasePool):
    self._pool = pool
    self._conn = None
    self.recipes: RecipeRepository | None = None

  def __enter__(self) -> UnitOfWork:
    self._conn = self._pool.getconn()
    self.recipes = RecipeRepository(self._conn)
    return self

  def __exit__(self, exc_type, exc, tb) -> None:
    try:
      if exc_type is None:
        self._conn.commit()
      else:
        logger.debug(f"rolling back unit of work: {exc!r}")
        self._conn.rollback()
    finally:
      self._pool.putconn(self._conn)
      self._conn = None
      self.recipes = None
