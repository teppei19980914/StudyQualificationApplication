"""設定ページ."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager, ThemeType
from study_python.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """設定ページ.

    テーマ切替、通知設定、データ管理などのアプリケーション設定を提供する。

    Attributes:
        _theme_manager: テーママネージャ.
        _notification_service: 通知サービス.
        _data_dir: データディレクトリ.

    Signals:
        theme_changed: テーマ変更時に発火.
    """

    theme_changed = Signal()

    def __init__(
        self,
        theme_manager: ThemeManager,
        notification_service: NotificationService | None = None,
        data_dir: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """SettingsPageを初期化する.

        Args:
            theme_manager: テーママネージャ.
            notification_service: 通知サービス.
            data_dir: データディレクトリ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._notification_service = notification_service
        self._data_dir = data_dir or Path("data")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # セクションタイトル
        title = QLabel("設定")
        title.setObjectName("section_title")
        layout.addWidget(title)

        self._build_theme_section(layout)
        self._build_notification_section(layout)
        self._build_data_management_section(layout)
        self._build_about_section(layout)

        layout.addStretch()
        self._update_theme_display()
        self._update_notification_display()
        logger.debug("SettingsPage created")

    def _build_theme_section(self, layout: QVBoxLayout) -> None:
        """テーマセクションを構築する.

        Args:
            layout: 親レイアウト.
        """
        theme_header = QLabel("テーマ")
        theme_header.setObjectName("card_title")
        layout.addWidget(theme_header)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self._theme_label = QLabel()
        self._theme_label.setObjectName("settings_theme_label")
        theme_row.addWidget(self._theme_label)
        theme_row.addStretch()

        self._theme_toggle_button = QPushButton()
        self._theme_toggle_button.setObjectName("secondary_button")
        self._theme_toggle_button.setFixedHeight(36)
        self._theme_toggle_button.clicked.connect(self._on_toggle_theme)
        theme_row.addWidget(self._theme_toggle_button)
        layout.addLayout(theme_row)

    def _build_notification_section(self, layout: QVBoxLayout) -> None:
        """通知セクションを構築する.

        Args:
            layout: 親レイアウト.
        """
        notification_header = QLabel("通知")
        notification_header.setObjectName("card_title")
        layout.addWidget(notification_header)

        notification_row = QHBoxLayout()
        notification_row.setSpacing(12)
        self._notification_label = QLabel()
        self._notification_label.setObjectName("settings_notification_label")
        notification_row.addWidget(self._notification_label)
        notification_row.addStretch()

        self._notification_toggle_button = QPushButton()
        self._notification_toggle_button.setObjectName("secondary_button")
        self._notification_toggle_button.setFixedHeight(36)
        self._notification_toggle_button.clicked.connect(self._on_toggle_notifications)
        notification_row.addWidget(self._notification_toggle_button)
        layout.addLayout(notification_row)

    def _build_data_management_section(self, layout: QVBoxLayout) -> None:
        """データ管理セクションを構築する.

        Args:
            layout: 親レイアウト.
        """
        data_header = QLabel("データ管理")
        data_header.setObjectName("card_title")
        layout.addWidget(data_header)

        data_path_label = QLabel(f"データ保存先: {self._data_dir}")
        data_path_label.setObjectName("muted_text")
        layout.addWidget(data_path_label)

        data_row = QHBoxLayout()
        data_row.setSpacing(12)

        self._export_button = QPushButton("エクスポート")
        self._export_button.setObjectName("secondary_button")
        self._export_button.setFixedHeight(36)
        self._export_button.clicked.connect(self._on_export_data)
        data_row.addWidget(self._export_button)

        self._import_button = QPushButton("インポート")
        self._import_button.setObjectName("secondary_button")
        self._import_button.setFixedHeight(36)
        self._import_button.clicked.connect(self._on_import_data)
        data_row.addWidget(self._import_button)

        data_row.addStretch()

        self._clear_data_button = QPushButton("全データ削除")
        self._clear_data_button.setObjectName("danger_button")
        self._clear_data_button.setFixedHeight(36)
        self._clear_data_button.clicked.connect(self._on_clear_all_data)
        data_row.addWidget(self._clear_data_button)

        layout.addLayout(data_row)

    def _build_about_section(self, layout: QVBoxLayout) -> None:
        """アプリ情報セクションを構築する.

        Args:
            layout: 親レイアウト.
        """
        from study_python import __version__  # noqa: PLC0415

        about_header = QLabel("アプリ情報")
        about_header.setObjectName("card_title")
        layout.addWidget(about_header)

        version_label = QLabel(f"Study Planner v{__version__}")
        version_label.setObjectName("muted_text")
        layout.addWidget(version_label)

    # ---- テーマ ----

    def _on_toggle_theme(self) -> None:
        """テーマ切替ボタンのハンドラ."""
        self._theme_manager.toggle_theme()
        self._update_theme_display()
        self.theme_changed.emit()
        logger.info(f"Theme toggled to: {self._theme_manager.current_theme.value}")

    def _update_theme_display(self) -> None:
        """テーマ表示を現在の状態に更新する."""
        is_dark = self._theme_manager.current_theme == ThemeType.DARK
        if is_dark:
            self._theme_label.setText("現在: ダークモード")
            self._theme_toggle_button.setText("☀️  ライトモードに切替")
        else:
            self._theme_label.setText("現在: ライトモード")
            self._theme_toggle_button.setText("\U0001f319  ダークモードに切替")

    # ---- 通知 ----

    def _on_toggle_notifications(self) -> None:
        """通知切替ボタンのハンドラ."""
        if self._notification_service is None:
            return
        current = self._notification_service.notifications_enabled
        self._notification_service.set_notifications_enabled(not current)
        self._update_notification_display()
        logger.info(f"Notifications toggled to: {not current}")

    def _update_notification_display(self) -> None:
        """通知表示を現在の状態に更新する."""
        if self._notification_service is None:
            self._notification_label.setText("通知サービス未設定")
            self._notification_toggle_button.setEnabled(False)
            return
        enabled = self._notification_service.notifications_enabled
        if enabled:
            self._notification_label.setText("実績通知: 有効")
            self._notification_toggle_button.setText("無効にする")
        else:
            self._notification_label.setText("実績通知: 無効")
            self._notification_toggle_button.setText("有効にする")

    # ---- データ管理 ----

    def _on_export_data(self) -> None:
        """エクスポートボタンのハンドラ."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox  # noqa: PLC0415

        from study_python.services.data_export_service import (  # noqa: PLC0415
            DataExportService,
        )

        export_service = DataExportService(self._data_dir)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "データをエクスポート",
            "study_planner_backup.zip",
            "ZIP Files (*.zip)",
        )
        if not file_path:
            return
        try:
            count = export_service.export_data(Path(file_path))
            QMessageBox.information(
                self,
                "エクスポート完了",
                f"{count}個のデータファイルをエクスポートしました。",
            )
        except OSError as e:
            QMessageBox.warning(self, "エラー", f"エクスポートに失敗しました: {e}")

    def _on_import_data(self) -> None:
        """インポートボタンのハンドラ."""
        import zipfile as _zipfile  # noqa: PLC0415

        from PySide6.QtWidgets import QFileDialog, QMessageBox  # noqa: PLC0415

        from study_python.services.data_export_service import (  # noqa: PLC0415
            DataExportService,
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "データをインポート",
            "",
            "ZIP Files (*.zip)",
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "インポート確認",
            "現在のデータが上書きされます。続行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        export_service = DataExportService(self._data_dir)
        try:
            count = export_service.import_data(Path(file_path))
            QMessageBox.information(
                self,
                "インポート完了",
                f"{count}個のデータファイルをインポートしました。\n"
                "変更を反映するにはアプリを再起動してください。",
            )
        except (FileNotFoundError, _zipfile.BadZipFile, ValueError) as e:
            QMessageBox.warning(self, "エラー", f"インポートに失敗しました: {e}")

    def _on_clear_all_data(self) -> None:
        """全データ削除ボタンのハンドラ."""
        from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

        from study_python.services.data_export_service import (  # noqa: PLC0415
            DataExportService,
        )

        reply = QMessageBox.warning(
            self,
            "全データ削除",
            "目標・タスク・学習ログ・書籍・通知など\n"
            "すべてのデータが削除されます。\n\n"
            "この操作は元に戻せません。続行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        export_service = DataExportService(self._data_dir)
        try:
            count = export_service.clear_all_data()
            QMessageBox.information(
                self,
                "削除完了",
                f"{count}個のデータファイルを削除しました。\n"
                "変更を反映するにはアプリを再起動してください。",
            )
        except OSError as e:
            QMessageBox.warning(self, "エラー", f"データ削除に失敗しました: {e}")

    # ---- 外部通知 ----

    def on_theme_changed(self) -> None:
        """外部からのテーマ変更通知ハンドラ."""
        self._update_theme_display()
