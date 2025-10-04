# Tracability

Tracability is a CSV-first traceability explorer. It turns system definition spreadsheets into a navigable graph that answers
questions such as "which screens are connected to this function?" or "what tables does this program touch?" directly from the
terminal.

👉 日本語版は [こちら](ja/index.md) から参照できます。

## Highlights

- **CSV ingestion with alias matching** for Japanese/English exports and optional master data enrichment.【F:src/tracability/infrastructure/csv/loader.py†L1-L170】
- **Configurable traversals** using breadth-first search with relation, depth, and direction controls.【F:src/tracability/domain/graph.py†L99-L207】
- **CLI & Python APIs** providing consistent behaviour across automation scripts and interactive usage.【F:src/tracability/interfaces/cli/commands.py†L71-L196】【F:src/tracability/application/service.py†L39-L118】

## Getting Started

1. Install dependencies with `uv sync` (Python 3.13+).【F:pyproject.toml†L5-L44】
2. Prepare a `relations.csv` file and optional master files (screens/reports/tables).【F:src/tracability/infrastructure/csv/loader.py†L91-L170】
3. Run your first query:

    ```bash
    uv run trcli trace \
      --relations data/relations.csv \
      --from-level program \
      --to-level table \
      --target PRG110 \
      --format list
    ```

Explore the [Quick Start](quickstart.md) for a guided walkthrough and sample datasets.
