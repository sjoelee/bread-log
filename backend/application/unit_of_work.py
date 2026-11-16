"""The Unit of Work interface the application layer depends on.

One use case runs inside ``with uow_factory() as uow:``; everything reached
through ``uow.recipes`` shares one transaction. The PostgreSQL implementation
lives in ``infrastructure.unit_of_work``; tests use an in-memory fake.
"""

from __future__ import annotations

from typing import Optional, Protocol

from ..domain.repositories import RecipeRepository


class UnitOfWork(Protocol):
  @property
  def recipes(self) -> RecipeRepository: ...

  def __enter__(self) -> UnitOfWork: ...

  def __exit__(self, exc_type, exc, tb) -> Optional[bool]: ...
