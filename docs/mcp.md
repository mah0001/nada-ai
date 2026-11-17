# MCP server

nada-ai includes a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server. It lets an LLM client,
such as Claude, search a NADA catalog, read study metadata and analyse indicator data.

This guide is for people who run nada-ai. The internals (tool design, the prompt-injection validator, how apps render
charts) are in the [developer guide](./GUIDE.md#the-mcp-server).

## What it offers

| Kind | What | Count |
|---|---|---|
| Tools | Catalog search, study metadata, and timeseries data and analytics | 17 |
| Interactive apps | Forms and charts a compatible client renders inline, one per analytic plus search and schema | 15 |
| Resources | `nada://search-usage`, `nada://analytics-workflow`: usage notes a client can read | 2 |
| Prompts | `{prefix}_explore_indicator`, `{prefix}_compare_countries`, `{prefix}_find_anomalies`: slash commands a user starts | 3 |

The tools, all prefixed with `NADA_MCP_TOOL_PREFIX` (default `nada`):

| Tool | Works on | Purpose |
|---|---|---|
| `nada_search_catalog` | All data types | Search the catalog by keyword and filters. `type` defaults to `timeseries` |
| `nada_get_metadata` | All data types | Full metadata for one `idno` |
| `nada_get_schema`, `nada_get_codelist` | Timeseries | Columns, codelists and time format of an indicator. Call first |
| `nada_get_data` | Timeseries | Paged observations |
| `nada_rank`, `nada_extremes`, `nada_compare`, `nada_summarize`, `nada_growth`, `nada_trend`, `nada_coverage` | Timeseries | Analytics on one indicator |
| `nada_correlate`, `nada_join` | Timeseries | Two indicators together |
| `nada_outliers`, `nada_benchmark`, `nada_aggregate` | Timeseries | Outliers, peer comparison, group statistics |

Every tool is read-only. Microdata, documents, geospatial data and other types can be searched and their metadata
read, but analytics work on timeseries indicators only. Variables and citations have no MCP tools.

## Where the data comes from

The MCP tools call NADA's public API (`/api/catalog/search`, `/api/catalog/{idno}`, `/api/timeseries/data/...`). They do
not query nada-ai's OpenSearch index.

- Search results are semantic only when NADA's own search engine is set to NADA-AI, because NADA then passes its
  catalog search to nada-ai.
- The MCP server works the same whichever search backend nada-ai runs.
- NADA must be reachable from nada-ai at `AI4DATA_METADATA_CATALOG_URL`.

### What the tools can see

The tools call NADA's public API anonymously: catalog search, study metadata, and indicator data and schema. They
send no API key, bearer token or cookie, so they see only published studies, the same as a visitor to the catalog. An
unpublished study answers as not found.

nada-ai's NADA credential (`AI4DATA_METADATA_CATALOG_X_API_KEY`) is used for indexing only. Its user can read
unpublished studies, and `/mcp` has no authentication, so the tools never send it.

## Running it

The MCP server is part of the API. When the API runs, the endpoint is at:

```text
http://<nada-ai host>:8020/mcp
```

The transport is streamable HTTP. No extra setting is needed to turn it on. The Docker image and
`docker-compose.opensearch.yml` serve it.

A standalone server is also available, separate from the API:

```bash
uv run python -m nada_ai.mcp_server --port 8025
```

### Settings

Set these in `.env`. They apply to `/mcp` and to the standalone server.

| Variable | Default | Purpose |
|---|---|---|
| `NADA_MCP_TOOL_PREFIX` | `nada` | Prefix for every tool and prompt name. Lowercase letters, digits, underscores |
| `NADA_MCP_CATALOG_NAME` | `NADA catalog` | Catalog name used in the tool descriptions the model reads |
| `NADA_MCP_SERVER_NAME` | `NADA MCP Server` | Name shown in MCP clients |
| `NADA_MCP_SEARCH_CATALOG_DESCRIPTION`, `NADA_MCP_GET_METADATA_DESCRIPTION` | unset | Replace those two tool descriptions entirely |
| `NADA_MCP_LOG_LEVEL`, `NADA_MCP_LOG_FILE`, `NADA_MCP_ENV` | `INFO`, unset, unset | Logging |
| `NADA_MCP_PORT`, `NADA_MCP_TRANSPORT` | `8025`, `http` | Standalone server only |
| `FASTMCP_STATELESS_HTTP` | `false` | Set `true` behind a reverse proxy or with more than one process. See below |

`NADA_MCP_READINESS_ENABLED` and `NADA_MCP_HEALTH_CHECK_TIMEOUT` are defined but not used yet.

## Exposing it

### Stateless mode

By default `/mcp` keeps each client's session in the memory of the process that opened it. Set
`FASTMCP_STATELESS_HTTP=true` in `.env` when a reverse proxy, a load balancer or more than one process sits in front of
nada-ai. Each request is then handled on its own. The standalone server always runs stateless.

### Security

`/mcp` has **no authentication** and **no rate limit**: `NADA_RATE_LIMIT_SEARCH_PER_MINUTE` covers the REST search
only. The tools only read, but each call costs NADA requests. Choose one:

- keep `/mcp` on a private network or VPN;
- allow only known addresses at the proxy;
- put authentication in front of it at the proxy.

### Apache

In the nada-ai virtual host from the [host setup guide](./opensearch-host-setup.md#7-reverse-proxy), put the `/mcp`
lines **before** the catch-all `ProxyPass /`, since Apache uses the first match:

```apache
ProxyPass        /mcp http://127.0.0.1:8020/mcp flushpackets=on
ProxyPassReverse /mcp http://127.0.0.1:8020/mcp

<Location "/mcp">
    # Restrict who can reach it, e.g. an office network
    Require ip 10.0.0.0/8
</Location>
```

`flushpackets=on` sends streamed responses to the client as they are written.

### nginx

```nginx
location /mcp {
    allow 10.0.0.0/8;
    deny  all;

    proxy_pass http://127.0.0.1:8020/mcp;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 300s;
}
```

## Connecting clients

Replace the URL with your own, e.g. `https://nada-ai.example.org/mcp`.

**Claude Code**

```bash
claude mcp add --transport http nada https://nada-ai.example.org/mcp
```

**Claude Desktop or claude.ai:** add a custom connector with the `/mcp` URL under Settings > Connectors. The server must
be reachable from the internet for claude.ai.

**VS Code** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "nada": { "type": "http", "url": "https://nada-ai.example.org/mcp" }
  }
}
```

**MCP Inspector**, for testing:

```bash
npx @modelcontextprotocol/inspector
```

Choose the Streamable HTTP transport and enter the `/mcp` URL.

## Checking it works

1. Open the client and ask it to list the NADA tools. All 17 should appear with your prefix.
2. Ask for a search, e.g. "find poverty indicators". The client calls `nada_search_catalog`.
3. If a call fails, check the nada-ai logs and that NADA answers at `AI4DATA_METADATA_CATALOG_URL` from the nada-ai
   host or container.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Client cannot connect, or loses its session between calls | A proxy or several processes without stateless mode. Set `FASTMCP_STATELESS_HTTP=true` and restart |
| Responses arrive only at the end, or time out | The proxy buffers. Use `flushpackets=on` (Apache) or `proxy_buffering off` (nginx) |
| Search returns nothing for a non-timeseries study | `nada_search_catalog` defaults to `type=timeseries`. Ask for the type, e.g. survey or document |
| Tool calls fail with connection errors | nada-ai cannot reach NADA. From Docker, a NADA on the same machine is `http://host.docker.internal/...` |
| A tool call is rejected before it runs | The input validator blocked it: an argument over 5,000 characters, a search under 3 characters, or text that looks like a prompt injection |
