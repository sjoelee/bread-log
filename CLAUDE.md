# CLAUDE.md

## Start of every session

Read first, in order:

1. `docs/adr/` — `README.md` (writing rules, index), then every ADR. Binding: check
   proposals against them, follow them in code, and stop and say so if work would
   contradict one. Changing a decision means a new ADR, reviewed before any code changes.
2. `docs/glossary.md` — shared vocabulary; use its terms exactly. Its *Layer* table maps
   layers to directories.
3. `docs/plan.md` — status and scope by *phase.slice*. Keep its tables current as slices
   merge.

## Changing or critiquing existing code

- **Verify before you flag.** Trace the real path (caller → callee, frontend included) and
  state a concrete failure with concrete inputs. Otherwise label it "unverified".
- **Tests are not the source of truth.** A weak test means the test is weak, not that the
  feature is broken. Judge from production code.
- **When it's fine, say so and stop.** Don't manufacture concerns or refactors.
- **Answer what was asked first.** Unrequested findings go in a short labeled section at
  the end, as an offer.
- **Evaluate each item on its own merits.** Check consumers before calling something unused.

## Commands

- Backend: `uv run uvicorn backend.service:app --reload` (http://localhost:8000). Always
  `uv run`; never `python` directly. Python **3.9.6** is pinned: no `match`, and
  `X | Y` needs `from __future__ import annotations`.
- Frontend: `npm start` (http://localhost:3000), `npm run build`. Never `npm test` for the
  backend.
- Tests: `uv run pytest`. They run against `bread_makes_test`, never the dev database
  `bread_makes`; `tests/conftest.py` reads `TEST_DATABASE_URL` and refuses any database not
  ending in `_test`. Run `scripts/reset_test_db.sh` on first setup and whenever
  `database/schema.sql` changes.
- Checks: `uv run ruff check`, `uv run ruff format`, `uv run pyright backend tests/fakes.py`
  (also run by pre-commit).

## Database

PostgreSQL 15. Apply schema changes manually with `psql`, then regenerate
`database/schema.sql` with `pg_dump --schema-only --no-owner --no-privileges bread_makes`
and rebuild the test database.

## Legacy, frozen until Phase 4

Bread timing (`/timings` routes in `service.py`, `backend/db.py` `DBConnector`,
`backend/models.py`, the Saved Timings UI) is not part of the layered design. Don't
refactor it or build on it; Phase 4 replaces it from scratch. It commits inside
`DBConnector`, not through the unit of work.

## Known noise

- The psycopg pool logs `rolling back returned connection` after reads. Harmless.
