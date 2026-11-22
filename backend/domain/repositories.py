"""Storage interfaces the domain declares and infrastructure implements.

``RecipeRepository`` lists what the application layer needs from storage. The
PostgreSQL class in ``infrastructure`` and the in-memory fake in ``tests`` both
satisfy it structurally (no inheritance); pyright checks the match.
"""

from __future__ import annotations

from typing import List, Optional, Protocol
from uuid import UUID

from . import models as domain


class RecipeRepository(Protocol):
  def get(self, recipe_id: UUID) -> Optional[domain.Recipe]: ...

  def get_version(self, version_id: UUID) -> Optional[domain.RecipeVersion]: ...

  def get_versions(self, recipe_id: UUID) -> List[domain.RecipeVersion]: ...

  def list(
    self,
    *,
    category: Optional[str] = None,
    search: Optional[str] = None,
    ingredient: Optional[str] = None,
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    limit: int = 50,
    offset: int = 0,
  ) -> List[domain.RecipeSummary]: ...

  def add(self, recipe: domain.Recipe) -> None: ...

  def save(self, recipe: domain.Recipe) -> None: ...

  def delete(self, recipe_id: UUID) -> bool: ...
