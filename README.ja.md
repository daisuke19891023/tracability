# Tracability（トレーサビリティ）

Tracability は、業務サブシステム・業務機能・プログラムなどの要素と、画面・帳票・データベーステーブルといった成果物のトレーサビリティ関係を探索するためのコマンドラインツール兼 Python ライブラリです。

日本語／英語が混在した CSV エクスポートに最適化されており、柔軟なパース処理・幅優先探索・複数の出力形式によって、「この要件はどこで使われているのか？」「どのプログラムがこのテーブルにアクセスしているのか？」といった問いに、モデリング用スプレッドシートから直接答えを得ることができます。

## 主な特徴

- **CSV を中心としたワークフロー** ― 関係 CSV とオプションのマスター CSV からトレーサビリティグラフを構築し、日本語・英語のヘッダエイリアスを自動で解決します。【F:src/tracability/infrastructure/csv/loader.py†L1-L189】
- **柔軟なトラバーサル設定** ― 任意のレベル間で方向・関係種別・深さを制御しながら、幅優先探索を実行できます。【F:src/tracability/domain/graph.py†L39-L207】
- **充実した CLI 体験** ― `typer` ベースの CLI で、バリデーション付きオプションや整形された出力（JSON／リスト／文字列表現）を利用できます。【F:src/tracability/interfaces/cli/commands.py†L36-L196】【F:src/tracability/interfaces/formatter.py†L1-L63】
- **再利用可能なサービス層** ― Python アプリケーションやテストコードから `TraceabilityService` を呼び出し、CLI と同じクエリを実行できます。【F:src/tracability/application/service.py†L11-L118】

## インストール方法

Tracability は Python 3.13 以降を対象とし、[uv](https://github.com/astral-sh/uv) で管理されています。

```bash
# リポジトリをクローン
git clone https://github.com/your-org/tracability.git
cd tracability

# 依存関係をインストール（.venv を自動作成）
uv sync

# 開発用依存関係を追加でインストール（任意）
uv sync --extra dev
```

パッケージのメタデータには `trcli` というコンソールエントリポイントが含まれているため、`uv run trcli` のように仮想環境から直接実行できます。【F:pyproject.toml†L5-L44】

## データ準備

CLI を使う際は、サブシステム・業務・機能・プログラム間の階層関係を表す `relations.csv` が必須です。必要に応じて画面・帳票・テーブルのマスター CSV を指定することで、グラフにメタデータを付加できます。大規模なエイリアステーブルを用いてヘッダ名を照合するため、日本語・英語のどちらの書式でもファイル名を変更する必要はありません。【F:src/tracability/infrastructure/csv/loader.py†L1-L189】

### 必須カラム

ローダは以下の項目（大文字小文字は区別せず、エイリアスに対応）を解決します。

| 項目             | 説明                                   |
| ---------------- | -------------------------------------- |
| `subsystem_id`   | サブシステム ID                        |
| `subsystem_name` | サブシステム論理名                     |
| `business_id`    | 業務 ID                                |
| `business_name`  | 業務論理名                             |
| `function_id`    | 機能 ID                                |
| `function_name`  | 機能論理名                             |
| `program_id`     | プログラム ID                          |
| `program_name`   | プログラム論理名                       |
| `screen_id`      | ひも付く画面 ID（任意）                |
| `report_id`      | ひも付く帳票 ID（任意）                |
| `table_id`       | CRUD 対象テーブル ID（任意）           |
| `crud`           | `CUD` などの CRUD 操作                 |

画面／帳票／テーブルのマスター CSV を併用すると、ローダがノードに論理名・物理名を付加し、親機能との関連も自動的に構築します。【F:src/tracability/infrastructure/csv/loader.py†L91-L170】

## CLI クイックスタート

最小限の CSV セット（例として `tests/unit/tracability/test_cli_command.py` のフィクスチャを参照）を用意し、以下を実行します。

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --from-level program \
  --to-level screen \
  --target PRG110 \
  --screens data/screens.csv \
  --format json
```

このコマンドは CSV を読み込み、トレーサビリティグラフを構築して、指定された形式で結果を出力します。エラー時には分かりやすいメッセージと非ゼロの終了コードで通知されます。【F:src/tracability/interfaces/cli/commands.py†L71-L196】

### 主なオプション

| オプション             | 説明                                                                            |
| ---------------------- | ------------------------------------------------------------------------------- |
| `--relations, -r`      | 必須の関係 CSV へのパス（存在チェックあり）。                                   |
| `--from-level, -f`     | 探索の起点レベル（例：`program`、`business`）。                                 |
| `--to-level, -t`       | 探索の終点レベル（例：`table`、`screen`）。                                     |
| `--target`             | 起点ノードの ID または名称。                                                     |
| `--by`                 | `auto`／`id`／`name` からターゲットの解釈方法を指定。                           |
| `--screens`            | 画面マスター CSV（任意）。                                                       |
| `--reports`            | 帳票マスター CSV（任意）。                                                       |
| `--tables`             | テーブルマスター CSV（任意）。                                                   |
| `--relations-filter`   | `hierarchy`、`screen`、`crud` など、辿る関係種別をカンマ区切りで指定。            |
| `--include-path`       | 辿ったエッジ情報を出力に含めるかどうか。                                         |
| `--format, -m`         | 出力形式：`string`／`list`／`json`。                                             |
| `--encoding`           | CSV 文字コード（既定は `utf-8-sig`）。                                           |
| `--delimiter`          | CSV 区切り文字（既定はカンマ）。                                                 |
| `--max-depth`          | 幅優先探索の最大深さ（既定は 16）。                                              |

詳細は `trcli trace --help` を実行して確認してください。Typer で定義したヘルプテキストがそのまま表示されます。【F:src/tracability/interfaces/cli/commands.py†L71-L196】

### 出力形式

- `string` ― パス展開や CRUD 集計を含む、人が読みやすい一覧形式。該当がない場合は日本語のフォールバックメッセージを表示します。【F:src/tracability/interfaces/formatter.py†L34-L63】
- `list` ― 下流処理に利用しやすい辞書型の JSON シリアライズ可能なリスト。【F:src/tracability/interfaces/formatter.py†L19-L50】
- `json` ― `list` と同じ構造をインデント付きで文字列化したもの。【F:src/tracability/interfaces/formatter.py†L51-L63】

## Python API

アプリケーション内で機能を再利用する場合はサービス層を使用します。

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

CLI が提供する設定項目は、`TraceabilityService.query` を呼び出す際にも同様に利用できます。探索処理は、関係フィルタと CRUD の逆方向エッジをオプションに持つ幅優先探索で実装されており、大規模データでも予測可能な性能を維持します。【F:src/tracability/application/service.py†L39-L118】【F:src/tracability/domain/graph.py†L99-L207】

## 開発とテスト

品質ゲートを実行するには nox セッションを利用してください。

```bash
uv run nox -s lint
uv run nox -s typing
uv run nox -s test
```

ユニットテストには、最小限の CSV 入力と期待される出力を示す CLI フィクスチャが含まれています。独自データを作成する際の参考にしてください。【F:tests/unit/tracability/test_cli_command.py†L1-L44】

## ライセンス

本プロジェクトは MIT License の下で公開されています。詳細は [LICENSE](LICENSE) を参照してください。

