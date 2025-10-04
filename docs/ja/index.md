# Tracability について

Tracability は CSV を中心にしたトレーサビリティ探索ツールです。システム定義のスプレッドシートを読み込み、関係グラフを構築することで、「この機能に紐づく画面は？」「このプログラムはどのテーブルを触っている？」といった問いにターミナルから直接答えられるようになります。

## ハイライト

- **日本語／英語のヘッダエイリアスに対応した CSV 取り込み** ― 必要に応じてマスターデータを読み込み、ノード情報を自動で補完します。【F:src/tracability/infrastructure/csv/loader.py†L1-L170】
- **パラメータ化可能な探索** ― 関係種別や深さ・方向を制御しながら幅優先探索を実行できます。【F:src/tracability/domain/graph.py†L99-L207】
- **CLI と Python API を統一** ― スクリプトからの自動化と対話的な利用の両方で一貫した挙動を提供します。【F:src/tracability/interfaces/cli/commands.py†L71-L196】【F:src/tracability/application/service.py†L39-L118】

## はじめに

1. `uv sync` で依存関係をインストールします（Python 3.13 以上）。【F:pyproject.toml†L5-L44】
2. `relations.csv` と必要であれば画面／帳票／テーブルのマスター CSV を準備します。【F:src/tracability/infrastructure/csv/loader.py†L91-L170】
3. 最初のクエリを実行します。

    ```bash
    uv run trcli trace \
      --relations data/relations.csv \
      --from-level program \
      --to-level table \
      --target PRG110 \
      --format list
    ```

詳しい手順とサンプルデータは[クイックスタート](quickstart.md)を参照してください。
