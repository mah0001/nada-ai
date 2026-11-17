# Legacy guides (Qdrant)

These guides describe running nada-ai on **Qdrant**. They are kept for reference and are not maintained.

NADA's catalog search needs **OpenSearch**: on Qdrant, nada-ai serves only its own `/search` endpoint. For a NADA
deployment, follow the [OpenSearch setup guide](../opensearch-setup-guide.md).

| Guide | What it was |
|---|---|
| [qdrant-pipeline-guide.md](qdrant-pipeline-guide.md) | Catalog ingest and search with Qdrant, host and Docker |
| [architecture-qdrant.md](architecture-qdrant.md) | Ingest, embeddings and search on Qdrant |
| [local-docker.md](local-docker.md) | Day-to-day commands for the Qdrant Docker stack |
| [qdrant-db-search-evaluation.md](qdrant-db-search-evaluation.md) | Evaluation of NADA's former `qdrant_db` search driver, which has been removed |
