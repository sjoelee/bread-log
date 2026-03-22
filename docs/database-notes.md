# Database Implementation Notes

## Parameter Placeholders in psycopg3

**IMPORTANT**: When writing SQL queries for psycopg3 in this codebase, use `%s` placeholders, NOT `$1`, `$2`, etc.

### Issue Encountered
During recipe editing implementation (March 2026), encountered this error:
```
ERROR: the query has 0 placeholders but 5 parameters were passed
```

### Root Cause
Mixed parameter placeholder styles in the same codebase:
- **Wrong**: `UPDATE recipes SET name = $1, description = $2 WHERE id = $3`
- **Correct**: `UPDATE recipes SET name = %s, description = %s WHERE id = %s`

### Solution
Always use `%s` style placeholders for consistency with the rest of the codebase.

### Code Example
```python
# Correct approach
update_fields.append(f"{field} = %s")
query = f"UPDATE recipes SET {', '.join(update_fields)} WHERE id = %s"
cur.execute(query, params)
```

### Files Using %s Placeholders
- All existing database methods in `db.py` use `%s` style
- Recipe CRUD operations
- Timing and bread make operations

### Note for Future Development
Check existing database methods for parameter style before implementing new queries to maintain consistency.