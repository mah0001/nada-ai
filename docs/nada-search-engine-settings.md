# NADA search engine settings

How NADA decides which engine answers a search, and how nada-ai fits in. The settings live in NADA, under **Site
configurations > Search**. nada-ai's own environment (`NADA_SEARCH_BACKEND`, `NADA_EMBEDDING_BACKEND`, index names)
describes the deployment and is not a NADA setting.

nada-ai must run **OpenSearch** for NADA. On Qdrant it has no study, variable or citation search, and NADA treats that
as a configuration error.

## Settings

| Setting | Label in NADA | Values | Notes |
|---|---|---|---|
| `search_engine` | Search engine | `database`, `solr`, `nada_ai` | The engine that serves catalog search. |
| `search_index_engine` | Index kept in sync | `none`, `solr`, `nada_ai` | The engine whose index NADA records changes for. |
| `nada_ai_url` | NADA-AI API URL | URL, no trailing slash | Required before `nada_ai` can be chosen for either setting above. |
| `nada_ai_api_key` | NADA-AI API Key | secret | A nada-ai **admin** key, sent as `X-NADA-Admin-Key`. Used for searches and for indexing from the Search index page. A read-only key cannot run indexing. |
| `nada_ai_on_outage` | When NADA-AI is unavailable | `database` (default), `error` | What a search does while nada-ai is down. |
| `nada_ai_multilingual` | Multilingual search | yes, no | Turn on when the embedding model matches queries across languages (the default Harrier model does). The home page then shows example searches in several languages. |
| `nada_ai_debug` | NADA-AI debug | yes, no | Logs nada-ai request and response bodies, and may attach them to catalog API errors for signed-in administrators. Off in production. |

Two more values are in `application/config/nada_ai.php`, not in the settings page:

| Setting | Default | Notes |
|---|---|---|
| `nada_ai_timeout` | 8 seconds | HTTP timeout for a search request (maximum 15). Keep it short: every search waits this long before falling back. |
| `nada_ai_breaker_cooldown` | 30 seconds | How long nada-ai is not called after a failure that means it is down. |

Site settings win over the config files, which only supply defaults.

### Search engine and index engine

The two settings are separate so an index can be built while the database still serves searches:

1. Set **Index kept in sync** to NADA-AI. From then on, NADA records every study and citation change for nada-ai.
2. Build the index from the **Search index** page (or nada-ai's own admin API).
3. Set **Search engine** to NADA-AI.

The search engine must be either `database` or the index engine. NADA refuses to save a search engine whose index is
not kept in sync.

## What each engine serves

| `search_engine` | Studies | Variables | Citations |
|---|---|---|---|
| `database` | database | database | database |
| `solr` | Solr | database | Solr |
| `nada_ai` | nada-ai | nada-ai, when it reports variable search | nada-ai, when it reports citation search |

With `nada_ai`, nada-ai returns the order, counts and tab counts, and the database loads the rows of each page. NADA
reads which searches nada-ai offers from `GET /info`, cached for a minute and kept for a day while nada-ai is down. A
nada-ai that gains a search is used without a NADA change.

**nada-ai must run what NADA expects.** If `/info` reports any engine other than OpenSearch, catalog searches fail with
a message naming both, and the Search index page shows a banner. The settings page itself never contacts nada-ai.

## When nada-ai does not answer

| Situation | What happens |
|---|---|
| nada-ai does not offer the search | The database serves it, every time. This is not a fallback. |
| A request the index cannot answer: no keyword, unpublished citations, admin-only filters, an unsupported sort or page size | The database serves that request. |
| nada-ai is down: no connection, timeout, HTTP 5xx except 501, HTTP 429 | `nada_ai_on_outage`: the database, or an error with the reason. |
| nada-ai rejects the request: HTTP 4xx, or 501 | Always an error. A bad key or a search the engine does not have is a configuration problem, not an outage. |

**Outage breaker.** A failure that means nada-ai is down opens a breaker for `nada_ai_breaker_cooldown` seconds.
While it is open, calls fail at once instead of each waiting for its own timeout. After the cooldown, one request
probes nada-ai: a success closes the breaker, a failure opens it again. The state is kept in NADA's file cache
(`cache/`), shared by all PHP processes on the server.

`GET /api/admin/semantic/engine_status` returns the engine, the index engine, what serves what, nada-ai's
capabilities, the breaker state and this hour's fallbacks. The Search index page shows the same as a Search engine
card on its Overview page.

## Change tracking

While **Index kept in sync** is not `none`, NADA queues every study and citation change (create, update, delete) for
that engine, whichever engine serves the searches. nada-ai pulls the queue and acknowledges each change; it does not
receive pushes. See [Keep the index in sync with NADA](./opensearch-setup-guide.md#7-keep-the-index-in-sync-with-nada).

nada-ai reads the queue and the catalog with a NADA API key (`AI4DATA_METADATA_CATALOG_X_API_KEY`). The key's user
needs **Studies** view on every collection, to read each study's variables, and the **Search index** permission:
view to read the queue, edit to read the metadata extract in batches, acknowledge changes and
report what was indexed.

## Upgrading

`php index.php cli/migrate latest` runs `20261107120004_rename_search_engine_settings`. It:

- renames `search_provider` to `search_engine`: `db`, `mysql`, `mysqli`, `sqlsrv` become `database`; `solr` stays;
  `semantic` becomes `nada_ai`; the earlier values `nada_ai_opensearch` and `nada_ai_qdrant` become `nada_ai`;
- maps NADA's removed native OpenSearch engine (`opensearch`) to `database`;
- renames `semantic_search_url`, `semantic_search_api_key` and `semantic_search_debug` to `nada_ai_url`,
  `nada_ai_api_key` and `nada_ai_debug`;
- folds a stored admin key (`semantic_search_admin_api_key` or `nada_ai_admin_api_key`) into `nada_ai_api_key`;
- drops `semantic_search_engine` and `citation_search_provider`;
- adds `search_index_engine`, set from the old search engine (`database` becomes `none`).

The migration is idempotent and one-way, and works on MySQL and SQL Server. Back up the database first. Settings kept
in `application/config/config.php` under the old names must be renamed by hand.
