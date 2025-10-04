# Quick Start

Follow this guide to ingest your first CSV files and issue a trace query from the command line.

## 1. Install and Configure

```bash
git clone https://github.com/your-org/tracability.git
cd tracability
uv sync
```

The `uv sync` command creates a local virtual environment and installs the `trcli` console script defined in `pyproject.toml`.
Use `uv run trcli --help` to confirm the CLI is available.【F:pyproject.toml†L5-L44】

## 2. Prepare Sample Data

Create a `data` folder with the following minimal CSV files (UTF-8 with BOM is supported by default):

=== "relations.csv"

    ```csv
    サブシステムID,サブシステム名,業務ID,業務名,機能ID,機能名,プログラムID,プログラム名,画面ID,帳票ID,テーブルID,CRUD
    SS01,受注,BU01,受注管理,FN11,受注照会,PRG110,受注検索,SC110,,T_ORDERS,R
    ```

=== "screens.csv" *(optional)*

    ```csv
    screen_id,機能ID,画面名,物理名
    SC110,FN11,受注検索,ORDERS_SEARCH
    ```

The loader automatically recognises the Japanese headers thanks to the alias table and links screens to their parent function
while building the graph.【F:src/tracability/infrastructure/csv/loader.py†L1-L170】

## 3. Run Your First Query

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --screens data/screens.csv \
  --from-level program \
  --to-level screen \
  --target PRG110 \
  --format json
```

Expected output:

```json
[
  {
    "level": "screen",
    "id": "SC110",
    "logical_name": "受注検索",
    "physical_name": "ORDERS_SEARCH",
    "crud": null
  }
]
```

The CLI validates file paths, handles CSV encoding, and prints structured errors if the traversal fails.【F:src/tracability/interfaces/cli/commands.py†L71-L196】

## 4. Explore Other Formats

- `--format list` returns Python-friendly dictionaries.
- `--format string --include-path` prints a readable list with the traversed edges.【F:src/tracability/interfaces/formatter.py†L34-L63】

## 5. Use the Python API

Embed the same workflow in scripts or notebooks:

```python
from tracability.application import TraceabilityService

svc = TraceabilityService.from_files(
    "data/relations.csv",
    screens_csv="data/screens.csv",
)
print(svc.query("program", "screen", "PRG110", fmt="string"))
```

This constructs a `TraceGraph`, runs a bounded breadth-first search, and formats the results identically to the CLI.【F:src/tracability/application/service.py†L39-L118】【F:src/tracability/domain/graph.py†L99-L207】

## Next Steps

- Review [CLI usage](guides/cli.md) for a detailed option reference.
- Inspect the unit tests under `tests/unit/tracability` for more sample datasets.【F:tests/unit/tracability/test_cli_command.py†L1-L44】
