# CLAUDE.md

## What this repo is

**Upstream project** — owner: osomai/echelon-ai-labs. MCP server for ServiceNow.

Used for VUL (vulnerability) ticket workflows against the Red Hat ServiceNow instances.

## Critical: Two instances — Hub vs Legacy

| Instance | Use for | Config |
|----------|---------|--------|
| **Legacy** (`redhat.service-now.com`) | VUL tickets | `snowlegacy` MCP in `.mcp.json` |
| **Hub** (`redhat.servicenow.com`) | SNOW Hub (newer) | `servicenow` MCP in `.mcp.json` |

**VUL tickets live on Legacy.** Hub returns 0 results for VUL queries — this is the #1 confusion point. Always use `snowlegacy` for vulnerability work.

## Write access gap

The `spre-servicenow-sa` service account can **read** Legacy but cannot **write**. Write access request stalled at GRC (as of 2026-08-17). Do not attempt Jira-style automated updates through this MCP — reads only.

## Auth

Basic auth: `SERVICENOW_INSTANCE_URL`, `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD` env vars. Credentials in `~/.config/mcp-tools/servicenow-legacy.env` (Legacy) and `~/.config/mcp-tools/servicenow.env` (Hub).

## Structure

`src/servicenow_mcp/` — main module
`prompts/` — pre-built prompts for common workflows
`examples/` — usage examples
`config/` — config templates

## Setup (if running locally)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
SERVICENOW_INSTANCE_URL=https://redhat.service-now.com SERVICENOW_USERNAME=... SERVICENOW_PASSWORD=... python -m servicenow_mcp
```
<!-- verified: 2026-10-06 -->
