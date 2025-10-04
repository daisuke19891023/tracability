# Installation

Tracability ships as a Python project managed with [uv](https://github.com/astral-sh/uv). The tool requires Python 3.13 or
newer as defined in `pyproject.toml` and exposes a console script named `trcli`.【F:pyproject.toml†L5-L44】

👉 日本語のインストールガイドは [こちら](ja/installation.md)。

## Requirements

- Python ≥ 3.13
- uv 0.4+
- Git (if installing from source)

## Install uv

=== "Linux / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## Install from Source

```bash
git clone https://github.com/your-org/tracability.git
cd tracability
uv sync
```

- `uv sync` creates an isolated `.venv` and installs dependencies plus the `trcli` entry point.
- Use `uv run trcli --help` to verify the CLI is available.

## Optional Extras

```bash
uv sync --extra dev    # development tooling
uv sync --extra docs   # documentation builders
```

These extras correspond to optional dependency groups declared in `pyproject.toml`.

## Verifying the Installation

```bash
uv run trcli trace --help
```

You should see the `trace` command with all options described in the CLI reference.【F:src/tracability/interfaces/cli/commands.py†L71-L196】 Running the command without the
`--relations` flag triggers validation errors, confirming Typer is wired correctly.

## Troubleshooting

- **Command not found** – Ensure you ran `uv run trcli ...` or activated the virtual environment.
- **Encoding issues** – Pass `--encoding` and `--delimiter` to match your CSV exports.【F:src/tracability/interfaces/cli/commands.py†L134-L196】【F:src/tracability/application/service.py†L25-L118】
- **No results** – Confirm the target identifier exists. The underlying graph looks up nodes using ID, logical name, or alias based
  on the `--by` option.【F:src/tracability/domain/graph.py†L132-L207】

## Next Steps

- Follow the [Quick Start](quickstart.md) to run a full traversal.
- Read the [CLI Reference](guides/cli.md) for advanced usage patterns.
