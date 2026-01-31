---
name: mcp-index
description: Index of available MCP server skills. Use when you need to know which MCP servers are available or which server to use for a task (Postgres, MinIO, Context7, OpenProject, etc.).
---

# MCP Servers Index

When the user or task needs to use an external tool, database, or service, use the MCP server that provides it. Load the matching skill only when that server is needed.

## Available MCP skills (load on demand)

| Server        | Skill name        | Use for                                                                                       |
| ------------- | ----------------- | --------------------------------------------------------------------------------------------- |
| postgres      | mcp-postgres      | SQL queries, list/describe tables; tools use `pg_*` prefix; multi-tenant (tenant_id required) |
| minio         | mcp-minio         | S3-compatible object storage; tools use `minio_*` prefix; multi-tenant                        |
| context7      | mcp-context7      | Library/framework documentation search; prefer over web for technical docs                    |
| calculator    | mcp-calculator    | Math expressions                                                                              |
| pdf-generator | mcp-pdf-generator | PDF generation; tools use `pdf_*` prefix                                                      |
| ffmpeg        | mcp-ffmpeg        | Video/audio processing                                                                        |
| mail          | mcp-mail          | Send email; multi-tenant                                                                      |
| openproject   | mcp-openproject   | Work management, documents; multi-tenant                                                      |
| meilisearch   | mcp-meilisearch   | Search indexing/query; multi-tenant                                                           |
| genimage      | mcp-genimage      | AI image generation (Runware)                                                                 |
| archon        | mcp-archon        | External knowledge search only (do not store project docs here)                               |
| livekit-docs  | mcp-livekit-docs  | LiveKit SDK and real-time docs                                                                |
| dockerhub     | mcp-dockerhub     | Docker image search                                                                           |
| gpu-ai        | mcp-gpu-ai        | GPU/AI (AskCollections)                                                                       |
| figma         | mcp-figma         | Figma design/file access                                                                      |
| n8n-mcp       | mcp-n8n           | n8n workflow automation                                                                       |

## Tool naming (do not guess)

- Postgres: `pg_execute_query`, `pg_list_tables`, `pg_describe_table` (not `execute_query`)
- MinIO: `minio_upload_object`, `minio_list_buckets` (not `upload_object`)
- PDF: `pdf_generate_pdf`, `pdf_get_pdf_file` (not `generate_pdf`)

Use the MCP server only when the task clearly needs it; do not preload all skills.
