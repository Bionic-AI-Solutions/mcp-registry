---
name: mcp-minio
description: Use when you need to upload, download, or list objects in S3-compatible storage. Requires tenant_id. Tool names use minio_* prefix (e.g. minio_upload_object, minio_list_buckets).
---

# MinIO MCP

Use the **minio** MCP server when the task involves:

- Uploading, downloading, or listing objects
- Managing buckets or object metadata per tenant
- Storing files, artifacts, or blobs with tenant isolation

## Tool naming (do not guess)

- **Prefix:** `minio_*`
- **Correct:** `minio_upload_object`, `minio_list_buckets`, `minio_get_object`
- **Wrong:** `upload_object`, `s3_upload`, `minio_upload`

Always pass the correct `tenant_id` and use exact tool names.
