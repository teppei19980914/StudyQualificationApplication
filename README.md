# Study Qualification Application

社会人の自己学習者向けの学習管理GUIアプリケーション。複数の学習目標を3W1H（Why・When・What・How）で登録し、ガントチャートで進捗を視覚的に管理する。

## 主要機能

### 3W1H 目標管理

学習目標を以下の4つの視点で登録・管理する:

- **Why（なぜ）**: 学習の動機・目的（モチベーション維持に活用）
- **When（いつまでに）**: 目標日（日付指定）または期間（「3ヶ月以内」等）
- **What（何を）**: 学習対象（資格名、スキル名等）
- **How（どうやって）**: 学習方法・計画

複数の目標を同時に管理でき、カラーパレットで自動色分けされる。

### ガントチャート

各目標に紐づくタスクを視覚的に管理:

- タスクの期間をバーで表示
- 進捗率（0-100%）を色付きオーバーレイで表示
- ステータス管理: 未着手 / 進行中 / 完了
- 今日線（赤い縦線）で現在位置を表示
- バークリックでタスク編集ダイアログを表示

### テーマ切替

- ダークテーマ（Catppuccin Mocha ベース）
- ライトテーマ（Catppuccin Latte ベース）
- サイドバーのボタンでワンクリック切替
- テーマ設定は永続化（次回起動時も維持）

## スクリーンショット

（アプリ起動後にスクリーンショットを追加予定）

## 必要条件

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/StudyQualificationApplication.git
cd StudyQualificationApplication
```

### 2. 依存関係のインストール

**uv を使用する場合（推奨）:**

```bash
# uv のインストール（未インストールの場合）
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync --dev
```

**pip を使用する場合:**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. pre-commit フックのインストール

```bash
uv run pre-commit install
```

## 使い方

### アプリケーションの起動

```bash
uv run python -m study_python.main
```

### 基本的な操作フロー

1. **目標を登録する**: サイドバーの「3W1H目標」ページで「+ 新しい目標を追加」ボタンをクリック
2. **3W1Hを入力する**: ダイアログでWhy・When・What・Howを入力して保存
3. **タスクを追加する**: サイドバーの「ガントチャート」ページで目標を選択し、タスクを追加
4. **進捗を更新する**: ガントチャート上のバーをクリックしてタスクの進捗率を更新
5. **テーマを切り替える**: サイドバー下部のテーマ切替ボタンをクリック

## アーキテクチャ

```
GUI Layer (View/Widget)  →  Service Layer (Logic)  →  Repository Layer (Data)
     PySide6 Widgets           Pure Python              JSON File I/O
```

### ディレクトリ構造

```
src/study_python/
├── main.py                        # アプリエントリポイント
├── models/
│   ├── goal.py                    # 3W1Hデータモデル（Goal）
│   └── task.py                    # タスクモデル（Task）
├── repositories/
│   ├── json_storage.py            # 汎用JSON永続化
│   ├── goal_repository.py         # Goal CRUD
│   └── task_repository.py         # Task CRUD
├── services/
│   ├── goal_service.py            # 目標ビジネスロジック
│   ├── task_service.py            # タスクビジネスロジック
│   └── gantt_calculator.py        # ガントチャート座標計算
├── gui/
│   ├── app.py                     # QApplication初期化
│   ├── main_window.py             # メインウィンドウ
│   ├── theme/
│   │   └── theme_manager.py       # テーマ管理
│   ├── pages/
│   │   ├── goal_page.py           # 3W1H一覧ページ
│   │   └── gantt_page.py          # ガントチャートページ
│   ├── dialogs/
│   │   ├── goal_dialog.py         # 目標登録/編集ダイアログ
│   │   └── task_dialog.py         # タスク登録/編集ダイアログ
│   └── widgets/
│       ├── sidebar.py             # サイドバーナビゲーション
│       └── gantt_chart.py         # ガントチャートウィジェット
```

### データ保存先

- `data/goals.json` - 目標データ
- `data/tasks.json` - タスクデータ
- `data/settings.json` - テーマ設定

## 開発コマンド

```bash
# リンターの実行
uv run ruff check .

# フォーマッターの実行
uv run ruff format .

# 型チェック
uv run mypy src/

# テストの実行
uv run pytest

# テスト（カバレッジ付き）
uv run pytest --cov=src/study_python --cov-report=html

# pre-commit の手動実行
uv run pre-commit run --all-files
```

## バッチスクリプト

`scripts/` フォルダにWindows(.bat)とUnix(.sh)両対応のスクリプトを用意しています。

**すべてのスクリプトは実行時に依存関係を自動インストールします。**
手動で `uv sync` を実行する必要はありません。

### テスト実行（用途別）

| スクリプト | 用途 | 速度 |
|-----------|------|------|
| `test.bat` / `test.sh` | 開発中の頻繁なテスト | 高速 |
| `test-full.bat` / `test-full.sh` | カバレッジ確認・レビュー前 | 通常 |

```bash
# 高速テスト（開発中に使用）
scripts\test.bat              # Windows
./scripts/test.sh             # Unix/macOS

# カバレッジ付きテスト（コミット前・レビュー時）
scripts\test-full.bat         # Windows
./scripts/test-full.sh        # Unix/macOS

# オプション（すべてのスクリプトで共通）
--verbose       # 詳細出力
--fast          # 最初の失敗で停止
--skip-install  # 依存関係のインストールをスキップ（高速化）
```

### リント・フォーマット

```bash
# Windows
scripts\lint.bat

# Unix/macOS
./scripts/lint.sh

# オプション
--fix           # 自動修正を適用
--check         # チェックのみ（デフォルト）
--skip-install  # 依存関係のインストールをスキップ
```

### 全チェック（リント + 型チェック + テスト）

```bash
# Windows
scripts\check-all.bat

# Unix/macOS
./scripts/check-all.sh

# オプション
--fix           # リント・フォーマットを自動修正
--cov           # カバレッジを取得
--skip-install  # 依存関係のインストールをスキップ
```

## テスト

232件のテストで91%以上のカバレッジを達成:

```
tests/
├── models/           # データモデルテスト（Goal, Task）
├── repositories/     # リポジトリテスト（CRUD操作）
├── services/         # サービス層テスト（ビジネスロジック）
├── gui/              # GUIテスト（pytest-qt使用）
├── test_calculator.py
└── test_logging_config.py
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| GUI | PySide6 (Qt 6) |
| データ永続化 | JSON ファイル |
| テスト | pytest, pytest-qt, pytest-cov |
| リント/フォーマット | ruff |
| 型チェック | mypy (strict mode) |
| パッケージ管理 | uv |

## コーディング規約

詳細は [CLAUDE.md](CLAUDE.md) を参照してください。

### 主なルール

- **PEP 8 準拠**: ruff による自動フォーマット
- **型ヒント必須**: すべての関数に型アノテーション
- **docstring**: Google スタイル
- **GUI/ロジック分離**: GUI層はロジック呼び出しと表示更新のみ
- **テスト**: pytest を使用、カバレッジ80%以上必須

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式に従います:

```
feat: 新機能
fix: バグ修正
docs: ドキュメント変更
style: フォーマット変更
refactor: リファクタリング
test: テスト追加・修正
chore: ビルド・ツール変更
```

## ライセンス

MIT License
