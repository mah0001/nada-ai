# nada-ai (`nada_ai`)

**nada-ai** is the search service for [NADA](https://github.com/ihsn/nada) catalogs. It runs next to NADA and gives it:

- **Catalog search on OpenSearch**: keyword, semantic and hybrid search over studies, variables and citations, with
  facets and paging. NADA sends its catalog searches to nada-ai and keeps nada-ai's indexes in sync with catalog
  changes.
- **An MCP server** at `/mcp`: catalog search, metadata and timeseries analytics as tools, interactive apps, resources
  and prompts for LLM clients such as Claude. See the [MCP guide](docs/mcp.md).

Metadata is read from NADA through [`ai4data.discovery`](https://github.com/mah0001/ai4data).

> **Repository.** NADA's documentation points to this repository, `https://github.com/mah0001/nada-ai`. It receives
> changes first. The original project is [avsolatorio/nada-ai](https://github.com/avsolatorio/nada-ai).

## Quick start with Docker

```bash
git clone https://github.com/mah0001/nada-ai.git
cd nada-ai
cp .env.example .env        # set NADA_AI_ADMIN_KEY, the NADA URL and NADA API key
docker compose -f docker-compose.opensearch.yml up --build -d
curl -s http://localhost:8020/health
```

This compose file is for development: OpenSearch runs without security and both ports listen on `127.0.0.1` only.
The [OpenSearch setup guide](docs/opensearch-setup-guide.md) walks through the whole install: `.env`, the embedding
model, creating the indexes, the first full index, keeping it in sync, connecting NADA, and production.

## Connecting NADA

In NADA, open **Site configurations > Search**:

| NADA setting | Value |
|---|---|
| NADA-AI API URL (`nada_ai_url`) | The URL NADA's server can reach nada-ai on, e.g. `http://127.0.0.1:8020` |
| NADA-AI API Key (`nada_ai_api_key`) | A nada-ai **admin** key. NADA uses it for searches and for indexing |
| Index kept in sync (`search_index_engine`) | `NADA-AI` |
| Search engine (`search_engine`) | `NADA-AI`, once the first full index is done |

nada-ai reads from NADA with a NADA API key (`AI4DATA_METADATA_CATALOG_X_API_KEY`) whose user has the **Search
index** permission (view and edit) and **Studies** view. Details:
[NADA search engine settings](docs/nada-search-engine-settings.md).

## Install without Docker

Requirements: Python **3.11+** and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra local          # local embedding model (default)
```

To run OpenSearch and the API as system services on Linux, follow the
[OpenSearch host setup](docs/opensearch-host-setup.md).

## Guides

| Guide | For |
|---|---|
| [OpenSearch setup guide](docs/opensearch-setup-guide.md) | Installing, indexing, connecting NADA, production, troubleshooting |
| [OpenSearch host setup](docs/opensearch-host-setup.md) | Linux install without Docker, systemd, reverse proxy |
| [NADA search engine settings](docs/nada-search-engine-settings.md) | NADA's search settings, fallbacks and change tracking |
| [MCP guide](docs/mcp.md) | Running, exposing and connecting the MCP server |
| [Developer guide](docs/GUIDE.md) | Architecture, ingestion, search internals, every configuration variable, testing |
| [Architecture](docs/architecture.md) | How ingest, embeddings, OpenSearch and NADA fit together |
| [Dynamic filters](docs/dynamic-filters.md) | Catalog filters and facets |

API contracts NADA relies on: [studies](docs/studies-search-contract.md), [variables](docs/variables-search-contract.md),
[citations](docs/citations-search-contract.md), [study facets](docs/studies-search-facets.md).

## Other search backends

OpenSearch is the engine NADA uses. nada-ai can also run on **Qdrant**, but only its own `/search` endpoint works
there: NADA's study, variable and citation searches need OpenSearch. Older Qdrant guides are kept in
[docs/legacy](docs/legacy/).

## Configuration

Settings use the **`NADA_`** prefix for nada-ai, **`NADA_MCP_`** for the MCP server and **`AI4DATA_`** for the NADA
connection. [`.env.example`](.env.example) lists every variable with comments; the
[configuration reference](docs/GUIDE.md#configuration-reference) explains them.

## Tests

```bash
uv run pytest -q
```

Integration tests against a live backend or catalog are gated behind env flags and skip without them. See
[Testing](docs/GUIDE.md#testing).
