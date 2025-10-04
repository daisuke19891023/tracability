# Tracability

A command line tool and Python library for exploring traceability relationships across business subsystems, functions, programs,
and downstream artefacts such as screens, reports, and database tables.

👉 日本語版の README は [README.ja.md](README.ja.md) を参照してください。

The project is optimised for Japanese/English mixed CSV exports that are common in enterprise requirement management. Flexible
parsing, breadth-first graph traversal, and multiple output formats make it easy to answer "where is this requirement used?" or
"which programs touch this table?" directly from your modelling spreadsheets.

## Key Features

- **CSV-first workflow** – Build a traceability graph from relations and optional master CSV files while automatically resolving
  header aliases in Japanese and English.【F:src/tracability/infrastructure/csv/loader.py†L1-L189】
- **Configurable traversals** – Perform bounded breadth-first searches between any supported levels with direction, relation, and
  depth controls.【F:src/tracability/domain/graph.py†L39-L207】
- **Rich CLI experience** – `typer` based CLI with validated options, optional pretty printers, and JSON/list/string output
  formats.【F:src/tracability/interfaces/cli/commands.py†L36-L196】【F:src/tracability/interfaces/formatter.py†L1-L63】
- **Reusable service layer** – Import `TraceabilityService` inside Python applications or tests to execute the same queries used by
  the CLI.【F:src/tracability/application/service.py†L11-L118】

## Installation

Tracability targets Python 3.13+ and is managed with [uv](https://github.com/astral-sh/uv).

```bash
# Clone the repository
git clone https://github.com/your-org/tracability.git
cd tracability

# Install dependencies (creates .venv automatically)
uv sync

# Optional: install development extras
uv sync --extra dev
```

A console entry point named `trcli` is installed as part of the package metadata.【F:pyproject.toml†L5-L44】 You can run it directly
from the virtual environment via `uv run trcli`.

## Preparing Your Data

The CLI requires at minimum a `relations.csv` file describing hierarchical relationships between subsystems, businesses, functions,
and programs. Optional master files can enrich the graph with screen, report, and table metadata. Column headers are matched using a
large alias table, so both Japanese and English exports are accepted without manual renaming.【F:src/tracability/infrastructure/csv/loader.py†L1-L189】

### Required Relations Columns

The loader attempts to resolve the following fields (case-insensitive, alias aware):

| Field            | Purpose                                 |
| ---------------- | --------------------------------------- |
| `subsystem_id`   | Subsystem identifier                    |
| `subsystem_name` | Subsystem logical name                  |
| `business_id`    | Business identifier                     |
| `business_name`  | Business logical name                   |
| `function_id`    | Function identifier                     |
| `function_name`  | Function logical name                   |
| `program_id`     | Program identifier                      |
| `program_name`   | Program logical name                    |
| `screen_id`      | Linked screen identifier (optional)     |
| `report_id`      | Linked report identifier (optional)     |
| `table_id`       | CRUD target table identifier (optional) |
| `crud`           | CRUD operations such as `CUD`           |

If optional screen/report/table master CSVs are provided, Tracability enriches the nodes with logical/physical names and links them
to their parent function automatically.【F:src/tracability/infrastructure/csv/loader.py†L91-L170】

## CLI Quick Start

Create a minimal set of CSV files (see `tests/unit/tracability/test_cli_command.py` for a concise example fixture) and run:

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --from-level program \
  --to-level screen \
  --target PRG110 \
  --screens data/screens.csv \
  --format json
```

The command loads the CSV files, constructs the traceability graph, and prints the result in the requested format. Errors are
reported with helpful messages and non-zero exit codes.【F:src/tracability/interfaces/cli/commands.py†L71-L196】

### Command Options

| Option                | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `--relations, -r`     | Path to the mandatory relations CSV (validated for existence).              |
| `--from-level, -f`    | Start level for traversal (e.g. `program`, `business`).                      |
| `--to-level, -t`      | Destination level (e.g. `table`, `screen`).                                  |
| `--target`            | ID or name of the start node.                                                |
| `--by`                | Interpret target as `auto`, `id`, or `name`.                                 |
| `--screens`           | Optional screens master CSV.                                                 |
| `--reports`           | Optional reports master CSV.                                                 |
| `--tables`            | Optional tables master CSV.                                                  |
| `--relations-filter`  | Comma separated list of relations to follow (`hierarchy`, `screen`, `crud`). |
| `--include-path`      | Include the traversed edges in the response.                                 |
| `--format, -m`        | Output format: `string`, `list`, or `json`.                                   |
| `--encoding`          | CSV encoding (defaults to `utf-8-sig`).                                      |
| `--delimiter`         | CSV delimiter (defaults to comma).                                           |
| `--max-depth`         | Maximum breadth-first depth (defaults to 16).                                |

See `trcli trace --help` for the authoritative list with help text pulled directly from the Typer definitions.【F:src/tracability/interfaces/cli/commands.py†L71-L196】

### Output Formats

- `string` – Human-readable list with optional path expansion and CRUD summary, using Japanese fallback when no matches are
  found.【F:src/tracability/interfaces/formatter.py†L34-L63】
- `list` – JSON-serialisable list of dictionaries suitable for downstream processing.【F:src/tracability/interfaces/formatter.py†L19-L50】
- `json` – Preformatted JSON string (indent=2) that mirrors the list structure.【F:src/tracability/interfaces/formatter.py†L51-L63】

## Python API

If you need to embed the functionality in another system, use the service layer:

```python
from tracability.application import TraceabilityService

service = TraceabilityService.from_files(
    "data/relations.csv",
    screens_csv="data/screens.csv",
    encoding="utf-8-sig",
)
results = service.query(
    "program",
    "table",
    "PRG110",
    relations={"crud"},
    fmt="list",
    include_path=True,
)
```

The same configuration options exposed by the CLI are available when calling `TraceabilityService.query`. Traversal uses a bounded
breadth-first search with relation filtering and optional reverse CRUD edges, ensuring predictable performance on large datasets.【F:src/tracability/application/service.py†L39-L118】【F:src/tracability/domain/graph.py†L99-L207】

## Development and Testing

Run the nox sessions to execute quality gates:

```bash
uv run nox -s lint
uv run nox -s typing
uv run nox -s test
```

Unit tests include CLI fixtures that demonstrate minimal CSV inputs and expected outputs.【F:tests/unit/tracability/test_cli_command.py†L1-L44】 Inspect these when crafting your own datasets.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
