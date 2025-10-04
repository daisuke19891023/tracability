# クイックスタート

このガイドでは、最初の CSV を取り込み、コマンドラインからトレースクエリを実行する手順を紹介します。

## 1. インストールと初期設定

```bash
git clone https://github.com/your-org/tracability.git
cd tracability
uv sync
```

`uv sync` はローカル仮想環境を作成し、`pyproject.toml` で定義されたコンソールスクリプト `trcli` をインストールします。`uv run trcli --help` を実行して CLI が利用可能か確認してください。【F:pyproject.toml†L5-L44】

## 2. サンプルデータの準備

UTF-8（BOM 付き可）の最小 CSV を `data` ディレクトリに用意します。

=== "relations.csv"

    ```csv
    サブシステムID,サブシステム名,業務ID,業務名,機能ID,機能名,プログラムID,プログラム名,画面ID,帳票ID,テーブルID,CRUD
    SS01,受注,BU01,受注管理,FN11,受注照会,PRG110,受注検索,SC110,,T_ORDERS,R
    ```

=== "screens.csv" *(任意)*

    ```csv
    screen_id,機能ID,画面名,物理名
    SC110,FN11,受注検索,ORDERS_SEARCH
    ```

ローダはエイリアステーブルを利用して日本語ヘッダを自動認識し、画面を親機能にひも付けながらグラフを構築します。【F:src/tracability/infrastructure/csv/loader.py†L1-L170】

## 3. 最初のクエリを実行

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --screens data/screens.csv \
  --from-level program \
  --to-level screen \
  --target PRG110 \
  --format json
```

想定される出力例：

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

CLI はファイルパスや CSV エンコーディングを検証し、探索に失敗した場合は構造化されたエラーメッセージを表示します。【F:src/tracability/interfaces/cli/commands.py†L71-L196】

## 4. 他の出力形式を試す

- `--format list` で Python から扱いやすい辞書リストを取得できます。
- `--format string --include-path` は辿った経路情報を含む読みやすい一覧を表示します。【F:src/tracability/interfaces/formatter.py†L34-L63】

## 5. Python API を利用

同じ処理をスクリプトやノートブックに組み込みましょう。

```python
from tracability.application import TraceabilityService

svc = TraceabilityService.from_files(
    "data/relations.csv",
    screens_csv="data/screens.csv",
)
print(svc.query("program", "screen", "PRG110", fmt="string"))
```

内部では `TraceGraph` が構築され、幅優先探索によって結果が導かれ、CLI と同じ形式でフォーマットされます。【F:src/tracability/application/service.py†L39-L118】【F:src/tracability/domain/graph.py†L99-L207】

## 次のステップ

- 詳細なオプションは [CLI の使い方](guides/cli.md) を参照してください。
- 追加のサンプルデータは `tests/unit/tracability` 配下のユニットテストで確認できます。【F:tests/unit/tracability/test_cli_command.py†L1-L44】
