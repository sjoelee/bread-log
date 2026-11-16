#!/usr/bin/env bash
# Recreate the test database from database/schema.sql.
# Run once to set up, and again whenever schema.sql changes.
# Refuses any database whose name does not end in _test.
set -euo pipefail

DB_NAME="${TEST_DB_NAME:-bread_makes_test}"

case "$DB_NAME" in
  *_test) ;;
  *) echo "Refusing to reset '$DB_NAME': the name must end in _test" >&2; exit 1 ;;
esac

cd "$(dirname "$0")/.."

dropdb --if-exists "$DB_NAME"
createdb "$DB_NAME"
psql -q -1 -v ON_ERROR_STOP=1 "$DB_NAME" -f database/schema.sql
echo "Test database '$DB_NAME' is ready."
