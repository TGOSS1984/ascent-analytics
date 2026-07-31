# Stored Procedures

**Honest limitation:** SQLite has no `CREATE PROCEDURE` support — it's a single-user, embedded, file-based engine by design, not a client/server database with a procedural extension. Claiming stored procedures exist in this warehouse would be misleading, so this folder documents the situation instead of faking it.

Two things live here instead:

1. **`postgres_examples.sql`** — the same two procedures, written in real PL/pgSQL, as a reference for what these would look like on Postgres or SQL Server (both explicitly listed in the project's tech stack). These are **not executable against the SQLite warehouse** — they're a portability reference.
2. **`src/warehouse/procedures.py`** — the practical equivalent that actually runs against this warehouse: parameterised Python functions wrapping the same SQL logic, callable from a notebook, a script, or an API layer. This is the standard pattern for "stored procedure"-style reusable, parameterised logic on an engine that doesn't support them natively.

If this warehouse were migrated to Postgres for production (a reasonable next step for a growing business), `postgres_examples.sql` would run as-is with `CREATE OR REPLACE PROCEDURE`.