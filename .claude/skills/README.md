# Claude Skills for MCP Servers

This folder contains **Claude skills** that teach Claude how and when to use each MCP server. Skills use progressive disclosure: Claude loads metadata first to decide relevance, then full instructions when needed.

## Using MCP with Claude Code

1. **MCP configuration**  
   Project MCP servers are defined in the project root **`.mcp.json`**. Claude Code loads them when you work in this project (project scope).

2. **Secrets (env vars)**  
   For servers that need API keys or tokens, set them in **one** of these places so `.mcp.json` can use `${VAR}` expansion:
   - **Claude Code (recommended):** `.claude/settings.local.json` — add an `"env"` object with your keys (see sample below). This file is gitignored.
   - **Shell:** Export the vars before starting Claude Code, or use `CLAUDE_ENV_FILE=/path/to/script.sh` so Claude sources them before each session.
   - **Project .env:** Copy `.env.example` to `.env` and set values; then source it before running Claude (e.g. `set -a && source .env && set +a && claude`).

   **Sample entry — where to put it**

   **Option A: Claude Code project settings (recommended)**  
   Copy `.claude/settings.local.json.example` to `.claude/settings.local.json` and replace placeholders with your real values:

   ```json
   {
     "env": {
       "CONTEXT7_API_KEY": "ctx7sk-your-real-key",
       "HUB_PAT_TOKEN": "dckr_pat_...",
       "DOCKERHUB_USERNAME": "your-username",
       "N8N_API_URL": "https://your-instance.app.n8n.cloud",
       "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIs..."
     }
   }
   ```

   **Option B: Shell / .env**  
   Add to `.env` (or export in your shell):

   ```
   CONTEXT7_API_KEY=ctx7sk-your-real-key
   HUB_PAT_TOKEN=dckr_pat_...
   DOCKERHUB_USERNAME=your-username
   N8N_API_URL=https://your-instance.app.n8n.cloud
   N8N_API_KEY=eyJhbGciOiJIUzI1NiIs...
   ```

   Vars used by `.mcp.json`: `CONTEXT7_API_KEY`, `HUB_PAT_TOKEN`, `DOCKERHUB_USERNAME`, `N8N_API_URL`, `N8N_API_KEY`.

3. **Skills**  
   Each subfolder (e.g. `mcp-postgres/`, `mcp-context7/`) is one skill with a `SKILL.md` that describes when to use that MCP server and (where relevant) tool naming (e.g. `pg_*`, `minio_*`, `pdf_*`). Claude discovers these skills automatically and loads them when the task matches.

## Skill list

| Skill folder      | MCP server    | Use for                        |
| ----------------- | ------------- | ------------------------------ |
| mcp-index         | (index)       | See all MCP skills             |
| mcp-postgres      | postgres      | SQL, tables; `pg_*` tools      |
| mcp-minio         | minio         | S3 storage; `minio_*` tools    |
| mcp-context7      | context7      | Library/framework docs         |
| mcp-calculator    | calculator    | Math expressions               |
| mcp-pdf-generator | pdf-generator | PDF generation; `pdf_*` tools  |
| mcp-ffmpeg        | ffmpeg        | Video/audio processing         |
| mcp-mail          | mail          | Send email                     |
| mcp-openproject   | openproject   | Work management, documents     |
| mcp-meilisearch   | meilisearch   | Search indexing/query          |
| mcp-genimage      | genimage      | AI image generation            |
| mcp-archon        | archon        | External knowledge search only |
| mcp-livekit-docs  | livekit-docs  | LiveKit SDK / real-time docs   |
| mcp-dockerhub     | dockerhub     | Docker image search            |
| mcp-gpu-ai        | gpu-ai        | GPU/AI (AskCollections)        |
| mcp-figma         | figma         | Figma design/file access       |
| mcp-n8n           | n8n-mcp       | n8n workflow automation        |

## Cursor vs Claude Code

- **Cursor** uses `~/.cursor/mcp.json` (or project `.cursor/mcp.json`) and the rules in `.cursor/rules/mcp-skills/` for MCP awareness.
- **Claude Code** uses project `.mcp.json` and the skills in `.claude/skills/` (this folder).  
  Both setups describe the same MCP servers; skills tell Claude _when_ and _how_ to use them.
