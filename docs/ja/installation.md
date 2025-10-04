# インストール

Tracability は [uv](https://github.com/astral-sh/uv) で管理される Python プロジェクトとして提供されます。`pyproject.toml` に記載のとおり Python 3.13 以上が必要で、`trcli` というコンソールスクリプトを提供します。【F:pyproject.toml†L5-L44】

## 必要条件

- Python 3.13 以上
- uv 0.4 以降
- Git（ソースコードからインストールする場合）

## uv のインストール

=== "Linux / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## ソースコードからのインストール

```bash
git clone https://github.com/your-org/tracability.git
cd tracability
uv sync
```

- `uv sync` は隔離された `.venv` を作成し、依存関係と `trcli` エントリポイントをインストールします。
- `uv run trcli --help` を実行して CLI が利用できることを確認してください。

## オプションのエクストラ

```bash
uv sync --extra dev    # 開発用ツール
uv sync --extra docs   # ドキュメント生成ツール
```

これらのエクストラは `pyproject.toml` で定義されたオプション依存関係グループに対応します。

## インストール確認

```bash
uv run trcli trace --help
```

CLI リファレンスに記載されている `trace` コマンドと各オプションが表示されれば成功です。【F:src/tracability/interfaces/cli/commands.py†L71-L196】`--relations` を省略して実行するとバリデーションエラーが発生し、Typer が正しく動作していることを確認できます。

## トラブルシューティング

- **コマンドが見つからない** ― `uv run trcli ...` を使用したか、仮想環境を有効化したか確認してください。
- **文字化けする** ― CSV に合わせて `--encoding` や `--delimiter` を指定してください。【F:src/tracability/interfaces/cli/commands.py†L134-L196】【F:src/tracability/application/service.py†L25-L118】
- **結果が返らない** ― ターゲット識別子が存在するか確認してください。グラフは `--by` オプションに応じて ID／論理名／エイリアスでノードを検索します。【F:src/tracability/domain/graph.py†L132-L207】

## 次のステップ

- [クイックスタート](quickstart.md) でトレース処理の全体像を確認しましょう。
- 詳細な使い方は [CLI リファレンス](guides/cli.md) を参照してください。
