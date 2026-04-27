# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React)
- `npm start` — Start React development server on http://localhost:3000
- `npm run build` — Build production bundle
- Do NOT use `npm test` for backend tests (that runs the React test runner)

### Backend (FastAPI)
- `uv run uvicorn backend.service:app --reload` — Start the FastAPI dev server on http://localhost:8000
- Python version: **3.9.6** (pinned via `.python-version`)
- All backend commands must be run with `uv run` — do not use `python` or `python3` directly
- Dependencies are managed via `pyproject.toml` and `uv`

### Running Tests
- `uv run pytest` — Run all backend tests
- `uv run pytest tests/test_recipe_list_api.py -v` — Run a specific test file
- Tests hit the **real PostgreSQL database** (`bread_makes`) — no mocking
- `pythonpath = ["."]` is set in `pyproject.toml` so `backend.*` imports resolve correctly

### Database
- PostgreSQL 15 required (`brew install postgresql@15`), database name: `bread_makes`
- Schema files are in `/database/` — apply manually with `psql`
- Active tables: `recipes`, `recipe_versions`, `bakers_percentages`, `bread_timings`
- `account_makes` and `dough_makes` are legacy tables, no longer the primary data model

## Architecture Overview

### Frontend (`src/`)
React + TypeScript single-page app. All UI lives in `src/BreadAppNew.tsx` (the main component) with supporting files:
- `src/components/` — `CreateTab`, `RecipeTab`, `StatusBadge`
- `src/hooks/` — `useBreadForm` (form state + validation + submit), `useSavedMakes`
- `src/services/api.ts` — `breadTimingApi` (all timing CRUD); recipe calls are inline fetch in `BreadAppNew.tsx`
- `src/types/bread.ts` — shared TypeScript types

UI libraries: Material-UI (DatePicker, TimePicker), Tailwind CSS, Wouter (routing), dayjs.

### Backend (`backend/`)
FastAPI service with these key files:
- `service.py` — all route definitions (the FastAPI app entry point)
- `recipe_service.py` — recipe business logic layer
- `db.py` — `DBConnector` class with all raw SQL via psycopg3; uses a connection pool (`DatabasePool`)
- `models.py` — all Pydantic request/response models
- `recipe_versioning.py` — diff logic, baker's percentage calculation, version bump rules

### Key Data Models
- **Recipe** — versioned; `recipes` table holds current pointer, `recipe_versions` holds all versions, `bakers_percentages` holds calculated percentages per version. Cascade delete removes versions and percentages when a recipe is deleted.
- **BreadTiming** — a single bread-making session. Fields: `recipe_name` (NOT NULL), `date`, process timestamps (`autolyse_ts`, `mix_ts`, `bulk_ts`, `preshape_ts`, `final_shape_ts`, `fridge_ts`), temperature readings, `stretch_folds` (JSONB), `status` (`in_progress` | `completed`), `notes`.

### API Conventions
- Recipes: `POST/GET/PATCH/DELETE /recipes/`, `GET /recipes/{id}`
- Timings: `POST /timings`, `GET /timings`, `GET /timings/{id}`, `PATCH /timings/{id}`, `DELETE /timings/{id}`
- `GET /recipes/` supports: `search`, `sort_by` (`created_at` | `name`), `sort_direction` (`asc` | `desc`), `ingredient` (ILIKE match against JSONB ingredients array), `category`, `limit`, `offset`
- `GET /timings` supports: `page`, `limit`, `recipe_name`, `status`, `date`, `search`, `order_by`, `order_direction`
- All DELETE endpoints require an explicit `conn.commit()` — psycopg3 does not autocommit

### Key Behaviors to Know
- `BreadTimingCreate.recipe_name` is required (NOT NULL in DB) — validate on the frontend before submit
- `recipe_versions` and `bakers_percentages` cascade-delete when a recipe is deleted
- `GET /recipes/` returns `RecipeListItem` (includes `description`, `flour_ingredient_names`, `version`) — no per-recipe follow-up fetch needed
- `GET /recipes/{id}` returns the full `Recipe` with `current_version` and `bakers_percentages` — only needed for View & Edit / Use Template
- The `recentTimings` state in `BreadAppNew.tsx` is used by the Saved Timings tab (paginated). The dropdown for bread name uses a **separate** `timingDropdownNames` state populated by `loadAllDistinctBreadNames()`
- psycopg3 connection pool logs `rolling back returned connection` for reads — this is harmless (no autocommit on reads, rollback is a no-op)

### Tests (`tests/`)
- `test_recipe_list_api.py` — sorting and ingredient filter tests for `GET /recipes/`
- `test_timing_api.py` — full CRUD coverage for timing endpoints
- `test_recipe_creation_api.py`, `test_recipe_creation_service.py`, `test_recipe_creation_transactions.py`
- `test_baker_percentages.py`, `test_recipe_versioning.py`, `test_ingredient_matching.py`
- Fixtures in `conftest.py` provide sample ingredients, instructions, and recipe shapes
- Each test class that writes data should clean up (delete) created records in a `yield` fixture
