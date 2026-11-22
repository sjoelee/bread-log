"""Mappers between API DTOs (``api.schemas``) and domain objects (``domain.models``).

``schemas.Ingredient.type`` is required (regex-validated) while
``domain.Ingredient.type`` is optional, so ``ingredient_to_dto`` on a domain
ingredient with ``type is None`` raises at DTO validation.
"""

from __future__ import annotations

from typing import List, Optional

from . import schemas
from ..domain import models as domain


# --- DTO -> domain ---------------------------------------------------------


def ingredient_to_domain(dto: schemas.Ingredient) -> domain.Ingredient:
  return domain.Ingredient(
    name=dto.name,
    amount=dto.amount,
    unit=dto.unit,
    type=dto.type,
    notes=dto.notes,
  )


def step_to_domain(dto: schemas.RecipeStep) -> domain.RecipeStep:
  return domain.RecipeStep(order=dto.order, instruction=dto.instruction, id=dto.id)


def ingredients_to_domain(dtos: List[schemas.Ingredient]) -> List[domain.Ingredient]:
  return [ingredient_to_domain(d) for d in dtos]


def steps_to_domain(dtos: List[schemas.RecipeStep]) -> List[domain.RecipeStep]:
  return [step_to_domain(d) for d in dtos]


# --- domain -> DTO --------------------------------------------------------


def ingredient_to_dto(ing: domain.Ingredient) -> schemas.Ingredient:
  return schemas.Ingredient(
    name=ing.name,
    amount=ing.amount,
    unit=ing.unit,
    type=ing.type,  # pyright: ignore[reportArgumentType] -- see module docstring
    notes=ing.notes,
  )


def step_to_dto(step: domain.RecipeStep) -> schemas.RecipeStep:
  return schemas.RecipeStep(id=step.id, order=step.order, instruction=step.instruction)


def version_to_dto(version: domain.RecipeVersion) -> schemas.RecipeVersion:
  return schemas.RecipeVersion(
    id=version.id,
    recipe_id=version.recipe_id,
    state=version.state,
    version_number=version.version_number,
    release_note=version.release_note,
    ingredients=[ingredient_to_dto(i) for i in version.ingredients],
    instructions=[step_to_dto(s) for s in version.instructions],
    created_at=version.created_at,
    change_summary=version.change_summary,
  )


def recipe_to_dto(recipe: domain.Recipe) -> schemas.Recipe:
  return schemas.Recipe(
    id=recipe.id,
    name=recipe.name,
    description=recipe.description,
    category=recipe.category,
    created_at=recipe.created_at,
    updated_at=recipe.updated_at,
    latest_ready=version_to_dto(recipe.latest_ready) if recipe.latest_ready else None,
    draft=version_to_dto(recipe.draft) if recipe.draft else None,
  )


def _version_summary_to_dto(
  summary: Optional[domain.VersionSummary],
) -> Optional[schemas.VersionSummary]:
  if summary is None:
    return None
  return schemas.VersionSummary(
    version_id=summary.version_id,
    version_number=summary.version_number,
    ingredient_count=summary.ingredient_count,
    step_count=summary.step_count,
  )


def summary_to_dto(summary: domain.RecipeSummary) -> schemas.RecipeListItem:
  return schemas.RecipeListItem(
    id=summary.id,
    name=summary.name,
    description=summary.description,
    category=summary.category,
    created_at=summary.created_at,
    updated_at=summary.updated_at,
    latest_ready=_version_summary_to_dto(summary.latest_ready),
    draft=_version_summary_to_dto(summary.draft),
  )
