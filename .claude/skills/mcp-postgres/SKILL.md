---
name: mcp-postgres
description: Use when you need to run SQL, list or describe tables, or query PostgreSQL. Requires tenant_id for multi-tenant. Tool names use pg_* prefix (e.g. pg_execute_query, pg_list_tables).
---

# Postgres MCP

Use the **postgres** MCP server when the task involves:

- Running SQL (SELECT, INSERT, UPDATE, DELETE, DDL)
- Listing or describing tables
- Inspecting schema or debugging data

## Tool naming (do not guess)

- **Prefix:** `pg_*`
- **Correct:** `pg_execute_query`, `pg_list_tables`, `pg_describe_table`
- **Wrong:** `execute_query`, `postgres_execute_query`, `postgres_query`

## Usage

- Always pass the correct `tenant_id` for the target database.
- Use exact tool names from the MCP server; wrong names cause silent failures.
- Verify that data is actually written or read after operations.
