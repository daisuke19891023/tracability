# CLI リファレンス

`trcli` コマンドは Typer ベースのインターフェースを通じてトレーサビリティグラフを操作します。本ガイドではコマンド構造、主要オプション、日常的な分析ワークフローを解説します。

## エントリポイント

プロジェクトをインストール（または `uv sync` を実行）したら、次のコマンドを実行します。

```bash
uv run trcli --help
```

利用可能なコマンドが表示されます。現在は `trace` のみが提供されており、CSV を読み込んでグラフ探索を実行します。Typer の設定は `tracability.interfaces.cli.commands.add_trace_command` に実装されているため、詳細なデフォルト値が必要な場合はソースを参照してください。【F:src/tracability/interfaces/cli/commands.py†L71-L196】

## 必須引数

```bash
uv run trcli trace \
  --relations data/relations.csv \
  --from-level program \
  --to-level table \
  --target PRG110
```

- `--relations/-r` は階層情報を含む既存の CSV ファイルを指す必要があります。
- `--from-level` と `--to-level` はグラフで使用する `Level` 列挙体（`subsystem`、`business`、`function`、`program`、`screen`、`report`、`table`）に対応します。【F:src/tracability/domain/models.py†L1-L120】
- `--target` は探索の起点ノードを指定します。既定では `NodeIndex` のヒューリスティクスにより ID か論理名かが自動判別されます。【F:src/tracability/domain/index.py†L1-L169】

## オプション機能

### マスターデータの取り込み

ノード情報を充実させるためにマスター CSV を指定できます。

```bash
--screens data/screens.csv \
--reports data/reports.csv \
--tables data/tables.csv
```

各ファイルは関係 CSV と同じエイリアス対応ローダで解析され、グラフに関連付けられます。【F:src/tracability/infrastructure/csv/loader.py†L91-L170】

### 関係のフィルタリング

`--relations-filter` を使って特定のエッジ種別だけを辿ることができます。例：

- `--relations-filter hierarchy` ― サブシステムからプログラムへのリンクのみ。
- `--relations-filter screen,crud` ― プログラムから画面とテーブルへジャンプ。

内部的には文字列を正規化した `set[str]` に変換してから探索エンジンへ渡します。【F:src/tracability/interfaces/cli/commands.py†L36-L134】

### 経路情報の出力

`--include-path` を指定すると、辿ったエッジ情報を結果に含められます。経路要素には関係名と接続ノードが表示され、`TraceGraph.trace` が生成する構造と一致します。【F:src/tracability/interfaces/formatter.py†L34-L63】【F:src/tracability/domain/graph.py†L99-L207】

### 出力形式

| 形式      | 説明 |
| --------- | ---- |
| `string`  | 経路や CRUD 要約を含む読みやすいテキスト一覧。【F:src/tracability/interfaces/formatter.py†L34-L63】 |
| `list`    | JSON シリアライズしやすい辞書リスト。【F:src/tracability/interfaces/formatter.py†L19-L50】 |
| `json`    | インデント付きの JSON 文字列。【F:src/tracability/interfaces/formatter.py†L51-L63】 |

`--format/-m` で切り替えられ、`--include-path` と組み合わせると監査証跡として利用しやすくなります。

### 文字コードと区切り文字

Shift-JIS のエクスポートや TSV を扱う場合はデフォルト値を上書きしてください。

```bash
--encoding cp932 --delimiter "\t"
```

これらの値は `TraceabilityService.from_files` に渡され、CSV ローダへ連鎖します。【F:src/tracability/application/service.py†L25-L118】

## エラーハンドリング

探索を実行する前に多くのバリデーションが行われます。無効なパスは Typer のエラーとして処理され、実行時エラーは Python 例外として CLI に報告され、終了コード `1` で終了します。【F:src/tracability/interfaces/cli/commands.py†L134-L196】ツールから呼び出す際は `-v` や環境変数によるロギング設定でスタックトレースを確認してください。

## 自動化のヒント

- JSON 出力を `jq` で絞り込む: `uv run trcli trace ... --format json | jq '.[].id'`
- 大規模グラフでは `--max-depth` を指定して探索の広がりを制限しましょう。【F:src/tracability/interfaces/cli/commands.py†L134-L196】【F:src/tracability/domain/graph.py†L139-L207】
- シェルコマンドを介さずに同じパース処理を使いたい場合は Python から `TraceabilityService` を直接呼び出してください。【F:src/tracability/application/service.py†L39-L118】
