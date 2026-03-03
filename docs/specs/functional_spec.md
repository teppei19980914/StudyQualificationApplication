# 機能仕様書

更新日: 2026-03-03

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-03-03 | 初版作成（設計書に基づきMECEで全機能を網羅） |

---

## 1. 概要

本書はStudy Planner（Study Qualification Application）の全機能の詳細仕様を定義する。
設計書（docs/design/architecture.md）をもとに、各機能の入力・処理・出力・制約条件を漏れなく記載する。

---

## 2. 目標管理機能（3W1H目標）

### 2.1 目標登録

| 項目 | 内容 |
|------|------|
| 画面 | GoalDialog |
| トリガー | GoalPageの「+ 目標追加」ボタン |
| 入力 | Why（動機）、When（期限）、WhenType（日付/期間）、What（学習対象）、How（学習方法） |
| バリデーション | 全フィールド空不可（空の場合はValueError） |
| 処理 | GoalService.create_goal() → GoalRepository.add() |
| 色割り当て | GOAL_COLORS（8色）から未使用色を順に割当。全色使用済みは目標数 mod 8 で循環 |
| 出力 | GoalPageにカードが追加表示される |
| 連動 | goals_changedシグナル → DashboardPage/GanttPage/StatsPage をrefresh |

### 2.2 目標編集

| 項目 | 内容 |
|------|------|
| 画面 | GoalDialog（編集モード） |
| トリガー | GoalCardの「編集」ボタン |
| 入力 | 既存の目標データ + 変更フィールド |
| バリデーション | 全フィールド空不可 |
| 処理 | GoalService.update_goal() → GoalRepository.update() |
| 出力 | GoalCard内容が更新される |

### 2.3 目標削除

| 項目 | 内容 |
|------|------|
| 画面 | GoalPage |
| トリガー | GoalCardの「削除」ボタン |
| 確認 | 削除確認ダイアログ |
| 処理 | GoalService.delete_goal() |
| カスケード | 目標に紐づくTask全削除（TaskRepository.delete_by_goal_id） |
| 出力 | GoalPageからカード消去 |

### 2.4 目標一覧表示

| 項目 | 内容 |
|------|------|
| 画面 | GoalPage |
| 処理 | GoalService.get_all_goals() |
| 出力 | GoalCardの一覧表示（色分け表示） |

---

## 3. タスク管理機能（ガントチャート）

### 3.1 タスク登録

| 項目 | 内容 |
|------|------|
| 画面 | TaskDialog |
| トリガー | GanttPageの「+ タスク追加」ボタン |
| 入力 | タスク名、開始日、終了日、メモ、関連書籍（任意） |
| バリデーション | start_date ≦ end_date、タスク名必須 |
| 処理 | TaskService.create_task() → TaskRepository.add() |
| order自動割当 | 同一goal_idのタスク数で自動設定 |
| 出力 | ガントチャートにバー追加 |

#### 3.1.1 タスク追加時の目標/読書選択

GanttPageの「+ タスク追加」クリック時、以下の選択肢を提示：
- 目標タスク: goal_idに選択した目標IDを設定
- 書籍タスク: goal_id = `"__books__"`、book_idに選択した書籍IDを設定（book_task_mode=True）

### 3.2 タスク編集

| 項目 | 内容 |
|------|------|
| 画面 | TaskDialog（編集モード） |
| トリガー | ガントチャートのバークリック |
| 入力 | タスク名、開始日、終了日、進捗率、メモ、関連書籍 |
| 処理 | TaskService.update_task() |
| ステータス自動決定 | progress 0% → NOT_STARTED / 1-99% → IN_PROGRESS / 100% → COMPLETED |
| 出力 | バーの長さ・進捗表示が更新 |

### 3.3 タスク削除

| 項目 | 内容 |
|------|------|
| トリガー | TaskDialog内の削除操作 |
| 処理 | TaskService.delete_task() |
| 出力 | ガントチャートからバー消去 |

### 3.4 進捗更新

| 項目 | 内容 |
|------|------|
| 処理 | TaskService.update_progress() |
| ステータス自動決定 | progress値に応じてステータスが自動変更 |

### 3.5 ガントチャート表示

| 項目 | 内容 |
|------|------|
| 画面 | GanttPage |
| 描画方式 | QGraphicsView + QGraphicsScene |
| 座標計算 | GanttCalculator（30px/日、40px/行） |
| ヘッダー | 月ラベル + 日ラベルの2段構成 |
| バー | 計画バー（半透明）+ 進捗バー（進捗%分の幅） |
| 今日線 | 赤い破線 |
| ツールチップ | バーホバーでタスク詳細表示 |
| 色 | 目標の割当色を使用（書籍タスクは固定色 #F9E2AF） |

### 3.6 統合セレクタ

| 選択肢 | 表示内容 |
|--------|---------|
| すべてのタスク | 全目標 + 全書籍のタスク |
| 各目標名 | その目標のタスクのみ |
| すべての書籍 | 全書籍タスク |
| 各書籍名 | その書籍のタスクのみ |

---

## 4. 学習時間記録機能

### 4.1 手動入力

| 項目 | 内容 |
|------|------|
| 画面 | StudyLogDialog |
| トリガー | GanttPageの「記録」ボタン |
| 入力 | タスク選択、学習日、学習時間（分）、メモ |
| バリデーション | duration_minutes > 0 |
| 処理 | StudyLogService.add_study_log() → StudyLogRepository.add() |
| task_name | 入力時にタスク名をキャッシュ（タスク削除後の表示用） |
| 出力 | 学習ログに記録追加 |

### 4.2 タイマー計測

| 項目 | 内容 |
|------|------|
| 画面 | StudyTimerWidget（GanttPage内） |
| トリガー | 開始/停止ボタン |
| 処理 | リアルタイム計測、停止時に自動記録 |
| 切り上げ | 最小1分、秒単位は切り上げ |
| 出力 | 学習ログに自動記録 |

### 4.3 学習ログ削除

| 項目 | 内容 |
|------|------|
| 処理 | StudyLogService.delete_log() |
| 出力 | ログ一覧から削除 |

### 4.4 タスク名バックフィル

| 項目 | 内容 |
|------|------|
| 処理 | StudyLogService.backfill_task_names(task_name_map) |
| 用途 | タスク削除後にtask_nameが空のログにタスク名を補完 |
| 出力 | 更新されたログ数を返却 |

---

## 5. 統計・分析機能

### 5.1 統計ページ構成

| セクション | 表示内容 | 使用Calculator |
|-----------|---------|---------------|
| 今日の学習バナー | 学習済/未学習、時間・セッション数 | MotivationCalculator.calculate_today_study() |
| サマリーカード | 合計時間、学習日数、目標数、連続日数 | MotivationCalculator.calculate_streak() |
| 自己ベスト記録 | 日最長、週最長、最長連続、累計 | MotivationCalculator.calculate_personal_records() |
| 学習実施率 | 今週/今月/全体の実施率 | MotivationCalculator.calculate_consistency() |
| 実績ボタン(🏆) | 累計値、達成通知、次の目標 | MotivationCalculator.calculate_milestones() |
| 通知ボタン(🔔) | 未読通知一覧 | NotificationService |
| アクティビティチャート | 日別/週別/月別/年別の棒グラフ | StudyStatsCalculator.calculate_activity() |
| 目標別統計 | 目標/読書の統計切替 | StudyLogService.get_goal_stats() |
| ログ履歴テーブル | 個別ログの一覧 | StudyLogService.get_all_logs() |

### 5.2 ストリーク計算

| 項目 | 内容 |
|------|------|
| 計算ロジック | MotivationCalculator.calculate_streak() |
| 連続日数 | 今日から遡って連続する学習日をカウント |
| 今日未学習 | 昨日まで連続していればストリーク維持 |
| 最長記録 | 全期間で最長の連続学習日数も計算 |

### 5.3 自己ベスト記録

| 記録 | 計算方法 |
|------|---------|
| 1日最長 | 日別合計の最大値（日付付き） |
| 週間最長 | 週別（月曜起点）合計の最大値（週開始日付き） |
| 最長連続 | 全期間の最長連続学習日数 |
| 累計時間 | 全ログのduration_minutes合計 |
| 累計日数 | ユニーク学習日数 |

### 5.4 学習実施率

| 期間 | 計算方法 | 色分け |
|------|---------|--------|
| 今週 | 今週の学習日数 / 今週の総日数 | 80%+: success / 50-80%: warning / 50%-: error |
| 今月 | 今月の学習日数 / 今月の総日数 | 同上 |
| 全体 | 総学習日数 / 初回学習日からの総日数 | 同上 |

### 5.5 アクティビティチャート

| 項目 | 内容 |
|------|------|
| 描画方式 | QPainter棒グラフ |
| バー色 | テーマのaccentカラー |
| Y軸 | 分数ラベル（0、中間値、最大値） |
| X軸 | バケットラベル（15本以下は全表示、それ以上は7間隔） |
| 0分バケット | border色の1px線で表示 |
| 切替 | QComboBoxで日別/週別/月別/年別を即時切替 |

### 5.6 目標別統計

| 項目 | 内容 |
|------|------|
| 画面 | GoalStatsSection |
| 切替 | プルダウンで「目標」「読書」を選択 |
| 表示 | GoalStatsCardを動的生成（目標名、色、合計時間、タスク内訳） |

---

## 6. 書籍管理機能

### 6.1 書籍登録

| 項目 | 内容 |
|------|------|
| 画面 | BookManagementDialog / BookPage |
| 入力 | 書籍名 |
| バリデーション | タイトル空不可 |
| 処理 | BookService.create_book() |
| 初期ステータス | UNREAD |

### 6.2 ステータス変更

| 項目 | 内容 |
|------|------|
| 処理 | BookService.update_status() |
| 遷移 | UNREAD → READING → COMPLETED |

### 6.3 読了記録

| 項目 | 内容 |
|------|------|
| 画面 | BookReviewDialog |
| 入力 | 要約、感想、読了日 |
| 処理 | BookService.complete_book() |
| 結果 | ステータスCOMPLETED + summary/impressions/completed_date設定 |

### 6.4 書籍削除

| 項目 | 内容 |
|------|------|
| 処理 | BookService.delete_book() |
| カスケード | 書籍タスク（goal_id=="__books__"かつbook_id一致）完全削除 |
| 参照クリア | 関連タスクのbook_idをクリア |

### 6.5 読書スケジュール

| 項目 | 内容 |
|------|------|
| 画面 | BookScheduleDialog |
| 処理 | BookGanttService.set_book_schedule() / clear_book_schedule() |
| 設定 | start_date、end_date |

### 6.6 書籍ガントチャート表示

| 項目 | 内容 |
|------|------|
| 処理 | BookGanttService |
| 表示 | 書籍タスクをガントチャートに表示（📖プレフィックス、固定色 #F9E2AF） |
| 進捗同期 | sync_book_progress() でタスク進捗平均→書籍progressに同期 |

### 6.7 本棚ウィジェット

| 項目 | 内容 |
|------|------|
| 画面 | BookshelfWidget（ダッシュボード内） |
| 表示内容 | 登録書籍数、読了数、読書中数、最近の読了5冊 |
| データ | BookService.get_bookshelf_data() → BookshelfData |

---

## 7. 通知・実績機能

### 7.1 実績通知の自動生成

| 項目 | 内容 |
|------|------|
| トリガー | DashboardPage/StatsPageのrefresh() |
| 処理 | NotificationService.check_and_create_achievement_notifications() |
| 前提条件 | notifications_enabled == True |
| 重複防止 | dedup_keyで既存チェック |
| 閾値 | 累計時間: 1,5,10,25,50,100,250,500,1000h / 学習日数: 3,7,14,30,60,100,200,365日 / 連続: 3,7,14,30,60,100日 |

### 7.2 システム通知

| 項目 | 内容 |
|------|------|
| ソース | data/system_notifications.json |
| 処理 | NotificationService.load_system_notifications() |
| タイミング | アプリ起動時 |
| 重複防止 | dedup_keyで既存チェック |
| フォーマット | `[{"dedup_key": "system:v1.0", "title": "...", "message": "..."}]` |

### 7.3 通知一覧表示

| 項目 | 内容 |
|------|------|
| 画面 | NotificationPopup |
| トリガー | NotificationButton（🔔）クリック |
| 表示 | スクロール可能な通知リスト |
| アイコン | SYSTEM=📢、ACHIEVEMENT=✨ |
| 未読 | accent色ボーダーでハイライト |

### 7.4 通知既読化

| 操作 | 処理 |
|------|------|
| 個別クリック | NotificationService.mark_as_read(id) |
| 全て既読ボタン | NotificationService.mark_all_as_read() |

### 7.5 通知詳細表示

| 項目 | 内容 |
|------|------|
| 画面 | NotificationDetailDialog |
| トリガー | 通知一覧の個別通知クリック |
| 表示 | タイトル、メッセージ全文、日時 |

### 7.6 未読バッジ

| 項目 | 内容 |
|------|------|
| 画面 | NotificationButton |
| 表示 | 赤丸バッジに未読数（99+ 上限） |
| 更新タイミング | ページrefresh時、ポップアップ閉じ後 |

### 7.7 実績ポップアップ

| 項目 | 内容 |
|------|------|
| 画面 | MilestonePopup |
| トリガー | MilestoneButton（🏆）クリック |
| 上部 | 累計学習時間、累計学習日数、連続学習日数 |
| 下部 | 達成済み閾値リスト、次の目標 |

### 7.8 通知有効/無効設定

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageの通知セクション |
| 操作 | 「有効にする」/「無効にする」ボタン |
| 処理 | NotificationService.set_notifications_enabled() |
| 永続化 | settings.jsonの`notifications_enabled`キー |
| 影響 | 無効時: check_and_create_achievement_notifications()が空リスト返却 |

---

## 8. ダッシュボード機能

### 8.1 ウィジェットグリッド

| 項目 | 内容 |
|------|------|
| レイアウト | 2カラムQGridLayout |
| ウィジェット数 | 9種類から選択配置 |
| サイズ | 半幅（span=1）/ 全幅（span=2） |
| 永続化 | settings.jsonの`dashboard_layout`キー |

### 8.2 ウィジェット一覧

| タイプID | 表示名 | デフォルト幅 | データ更新 |
|---------|--------|-------------|-----------|
| today_banner | 今日の学習状況 | 全幅 | TodayStudyData |
| total_time_card | 合計学習時間 | 半幅 | 全ログのduration_minutes合計 |
| study_days_card | 学習日数 | 半幅 | ユニーク学習日数 |
| goal_count_card | 目標数 | 半幅 | 目標の件数 |
| streak_card | 連続学習 | 半幅 | StreakData.current_streak |
| personal_record | 自己ベスト | 半幅 | PersonalRecordData |
| consistency | 学習の実施率 | 半幅 | ConsistencyData |
| bookshelf | 本棚 | 全幅 | BookshelfData |
| daily_chart | 学習アクティビティ | 全幅 | ActivityChartData（全4期間） |

### 8.3 編集モード

| 操作 | 説明 |
|------|------|
| ✏️ 編集ボタン | 編集モード開始 |
| ドラッグ&ドロップ | ウィジェットの順序変更 |
| ↔ リサイズ | allowed_spans内で幅切替（半幅↔全幅） |
| ✕ 削除 | ウィジェットをグリッドから除去 |
| パレットドロップ | 未配置ウィジェットをグリッドに追加 |
| ✓ 完了ボタン | 編集モード終了、レイアウト保存 |

### 8.4 ウィジェットパレット

| 項目 | 内容 |
|------|------|
| 表示位置 | スクロールエリア右側 |
| 表示条件 | 編集モード時のみ |
| 内容 | 未配置ウィジェットのカード一覧 |
| 操作 | ドラッグでグリッドにドロップ |
| 更新 | ウィジェット削除時にパレット自動更新 |

---

## 9. 設定機能

### 9.1 テーマ設定

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのテーマセクション |
| 表示 | 現在のテーマ（ダーク/ライトモード） |
| 操作 | 切替ボタン |
| 処理 | ThemeManager.toggle_theme() |
| 永続化 | settings.jsonの`theme`キー |
| 連動 | theme_changedシグナル → MainWindow._apply_theme() → 全ページon_theme_changed() |

### 9.2 通知設定

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageの通知セクション |
| 表示 | 「実績通知: 有効/無効」 |
| 操作 | 「無効にする」/「有効にする」ボタン |
| 処理 | NotificationService.set_notifications_enabled() |
| 永続化 | settings.jsonの`notifications_enabled`キー |
| 未設定時 | 通知サービスなしの場合「通知サービス未設定」表示、ボタン無効化 |

### 9.3 データエクスポート

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのデータ管理セクション |
| トリガー | 「エクスポート」ボタン |
| 処理 | QFileDialogでZIP保存先選択 → DataExportService.export_data() |
| 対象 | 6ファイル（goals, tasks, study_logs, books, notifications, settings） |
| 形式 | ZIP（ZIP_DEFLATED圧縮） |
| 出力ディレクトリ | 自動作成（parents=True） |
| 結果 | エクスポートファイル数をQMessageBoxで表示 |
| エラー | OSError → QMessageBox.warning |

### 9.4 データインポート

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのデータ管理セクション |
| トリガー | 「インポート」ボタン |
| 処理フロー | QFileDialogでZIP選択 → 確認ダイアログ → DataExportService.import_data() |
| 確認ダイアログ | 「現在のデータが上書きされます。続行しますか？」 |
| JSONバリデーション | ZIP内の各JSONファイルをパース検証 |
| 対象 | 有効なデータファイル名のみインポート（不明ファイル無視） |
| 結果 | インポートファイル数 + 再起動案内をQMessageBoxで表示 |
| エラー | FileNotFoundError / BadZipFile / ValueError → QMessageBox.warning |

### 9.5 全データ削除

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのデータ管理セクション |
| トリガー | 「全データ削除」ボタン（danger_buttonスタイル） |
| 確認ダイアログ | 「すべてのデータが削除されます。この操作は元に戻せません。続行しますか？」 |
| 処理 | DataExportService.clear_all_data() |
| 対象 | goals.json, tasks.json, study_logs.json, books.json, notifications.json |
| 保持 | settings.json（テーマ/レイアウト/通知設定） |
| 結果 | 削除ファイル数 + 再起動案内をQMessageBoxで表示 |
| エラー | OSError → QMessageBox.warning |

### 9.6 アプリ情報

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのアプリ情報セクション |
| 表示 | 「Study Planner v{バージョン}」 |
| バージョンソース | study_python.__version__ |

### 9.7 データ保存先表示

| 項目 | 内容 |
|------|------|
| 画面 | SettingsPageのデータ管理セクション |
| 表示 | 「データ保存先: {data_dir}」 |

---

## 10. テーマ機能

### 10.1 テーマ種別

| テーマ | パレット名 | 背景色 | テキスト色 | アクセント色 |
|--------|-----------|--------|-----------|-------------|
| ダーク | Catppuccin Mocha | #1E1E2E | #CDD6F4 | #89B4FA |
| ライト | Catppuccin Latte | #EFF1F5 | #4C4F69 | #1E66F5 |

### 10.2 QSS適用範囲

QMainWindow、全ウィジェット、全ボタン種類（primary/secondary/danger）、ラベル種類（section_title/card_title/muted_text等）、入力コンポーネント（QLineEdit/QTextEdit/QSpinBox/QDateEdit/QComboBox）、テーブル、ダイアログ、カレンダー、ヘッダーバー、ドロワー、サイドバー、ダッシュボードカード、通知ポップアップ。

### 10.3 テーマ変更時の連動

```
SettingsPage._on_toggle_theme()
  → ThemeManager.toggle_theme()
  → theme_changedシグナル発火
  → MainWindow._apply_theme()
      → ThemeManager.get_stylesheet()
      → MainWindow.setStyleSheet()
      → 全6ページの on_theme_changed() 呼出
```

---

## 11. ナビゲーション機能

### 11.1 ハンバーガーメニュー

| 項目 | 内容 |
|------|------|
| 位置 | HeaderBar左端 |
| サイズ | 36x36px |
| アイコン | ☰ |
| 動作 | ドロワーの開閉切替 |

### 11.2 ナビゲーションドロワー

| 項目 | 内容 |
|------|------|
| 幅 | 260px |
| 表示位置 | 画面左端（ヘッダー下） |
| 項目 | 5ページ + 設定（6項目） |
| 排他選択 | QButtonGroupで排他制御 |
| アニメーション | 開: 200ms OutCubic / 閉: 150ms InCubic |
| オーバーレイ | 半透明背景（rgba(0,0,0,100)）、クリックでドロワー閉じ |

### 11.3 ページ切替

| 項目 | 内容 |
|------|------|
| 処理 | QStackedWidget.setCurrentIndex() |
| タイトル更新 | HeaderBar.set_title()でページタイトル更新 |
| ボタン状態 | NavigationDrawer.set_checked_button()で選択状態同期 |
| ページrefresh | ダッシュボード(0)・ガント(2)・書籍(3)・統計(4)は切替時にrefresh実行 |

---

## 12. 日本祝日カレンダー

### 12.1 色分けルール

| 日付種別 | 色 | 優先度 |
|---------|-----|--------|
| 祝日 | 赤 (#DC2626) | 最高（土曜より優先） |
| 日曜日 | 赤 (#DC2626) | 高 |
| 土曜日 | 青 (#2563EB) | 中 |
| 平日 | 黒 (#1F2937) | 低 |

### 12.2 実装

| コンポーネント | 役割 |
|-------------|------|
| HolidayService | jpholidayで祝日判定（年単位キャッシュ） |
| JapaneseCalendarWidget | QCalendarWidget.paintCellオーバーライド |

### 12.3 使用箇所

- GoalDialog: When（いつまでに）の日付選択
- TaskDialog: 開始日/終了日の日付選択
- StudyLogDialog: 学習日の日付選択

---

## 13. ログ設計

### 13.1 ログ出力仕様

| 項目 | 値 |
|------|-----|
| 出力先 | logs/ディレクトリ |
| ファイル名 | app_YYYY-MM-DD.log |
| フォーマット | `YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line | message` |
| ローテーション | サイズ: 10MB / 保持: 30日 |
| デフォルトレベル | INFO |
| コンソール出力 | 併用可能 |

### 13.2 ログレベル使い分け

| レベル | 用途 |
|--------|------|
| DEBUG | 処理フロー、変数値 |
| INFO | 正常処理の記録（開始/完了/重要ステップ） |
| WARNING | 注意が必要だが処理継続可能 |
| ERROR | エラー発生（処理失敗） |
| CRITICAL | システム停止レベルの重大エラー |

---

## 14. データ永続化仕様

### 14.1 JsonStorage

| メソッド | 動作 |
|---------|------|
| load() | JSONファイル読込。未存在時は空リスト返却 |
| save(data) | JSONファイル書込（UTF-8、indent=2） |

### 14.2 ファイル操作

| 操作 | 挙動 |
|------|------|
| ディレクトリ不在 | 自動作成（parents=True） |
| JSONパースエラー | 空リスト返却（警告ログ） |
| ファイル不在 | 空リスト返却 |
| 書込エラー | OSError伝播 |
