# CLI Reference

The `trcli` command exposes the traceability graph through a Typer-powered interface. This guide explains command structure,
options, and practical workflows for day-to-day analysis.

👉 日本語の CLI リファレンスは [こちら](../ja/guides/cli.md)。

## Entry Point

Install the project (or run `uv sync`) and execute:

```bash
uv run trcli --help
```

This prints the available commands. Currently only `trace` is provided, which loads CSV files and performs a graph traversal.
The Typer configuration lives in `tracability.interfaces.cli.commands.add_trace_command`. Refer to the source when you need the
exact option definitions or defaults.【F:src/tracability/interfaces/cli/commands.py†L71-L196】

## Required Arguments

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --from-level program \
  --to-level table \
  --target PRG110
```

- `--relations/-r` must point to an existing CSV file containing hierarchy rows.
- `--from-level` and `--to-level` correspond to the `Level` enum used by the graph (`subsystem`, `business`, `function`,
  `program`, `screen`, `report`, `table`).【F:src/tracability/domain/models.py†L1-L120】
- `--target` identifies the starting node. By default the CLI auto-detects whether this is an ID or logical name using
  the `NodeIndex` heuristics.【F:src/tracability/domain/index.py†L1-L169】

## Optional Enhancements

### Master Data

Provide master CSVs to enrich nodes with names and aliases:

```bash
--screens data/screens.csv \
--reports data/reports.csv \
--tables data/tables.csv
```

Each file is parsed with the same alias-aware loader used for relations and linked to the graph accordingly.【F:src/tracability/infrastructure/csv/loader.py†L91-L170】

### Relation Filtering

Use `--relations-filter` to restrict traversal to specific edge types. Examples:

- `--relations-filter hierarchy` – only follow subsystem→program links.
- `--relations-filter screen,crud` – jump from programs to screens and tables.

Internally this string is normalised into a `set[str]` before being passed to the traversal engine.【F:src/tracability/interfaces/cli/commands.py†L36-L134】

### Including Paths

Set `--include-path` to add the traversed edges to the output. Path entries display the relation name and connecting nodes,
mirroring the structure generated inside `TraceGraph.trace`.【F:src/tracability/interfaces/formatter.py†L34-L63】【F:src/tracability/domain/graph.py†L99-L207】

### Output Formats

| Format   | Description |
| -------- | ----------- |
| `string` | Human-readable lines with optional paths and CRUD summary.【F:src/tracability/interfaces/formatter.py†L34-L63】 |
| `list`   | Python dictionaries for direct JSON serialisation.【F:src/tracability/interfaces/formatter.py†L19-L50】 |
| `json`   | Pretty-printed JSON string (indent=2).【F:src/tracability/interfaces/formatter.py†L51-L63】 |

Switch formats using `--format/-m`. Combine with `--include-path` for audit trails.

### Encoding and Delimiter

When working with Shift-JIS exports or tab separated files, override the defaults:

```bash
--encoding cp932 --delimiter "\t"
```

These values are passed into `TraceabilityService.from_files`, which forwards them to the CSV loader.【F:src/tracability/application/service.py†L25-L118】

## Error Handling

Most validation happens before the traversal runs. Invalid paths raise Typer errors, while runtime issues bubble up as Python
exceptions and are reported by the CLI before exiting with status code `1`.【F:src/tracability/interfaces/cli/commands.py†L134-L196】 Use `-v` or environment
logging to debug underlying stack traces when running inside other tooling.

## Automation Tips

- Pipe JSON output into `jq` for further filtering: `uv run trcli trace ... --format json | jq '.[].id'`.
- Combine with `--max-depth` to guard against runaway traversals on large graphs.【F:src/tracability/interfaces/cli/commands.py†L134-L196】【F:src/tracability/domain/graph.py†L139-L207】
- Call `TraceabilityService` directly inside Python workflows to reuse the same parsing logic without shell commands.【F:src/tracability/application/service.py†L39-L118】
