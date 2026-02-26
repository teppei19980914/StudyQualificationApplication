"""学習タイマーウィジェット."""

from __future__ import annotations

import math

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class StudyTimerWidget(QWidget):
    """学習タイマーウィジェット.

    タスクの学習時間をリアルタイムで計測する。

    Signals:
        timer_stopped: タイマー停止時に経過分数を発行（task_id, minutes）.
    """

    timer_stopped = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """StudyTimerWidgetを初期化する.

        Args:
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._task_id: str = ""
        self._task_title: str = ""
        self._elapsed_seconds: int = 0
        self._is_running: bool = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

        self._setup_ui()
        self._update_display()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self._status_label = QLabel()
        self._status_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self._status_label)

        self._time_label = QLabel()
        self._time_label.setStyleSheet("font-size: 14px; font-family: monospace;")
        layout.addWidget(self._time_label)

        layout.addStretch()

        self._start_btn = QPushButton("▶ 開始")
        self._start_btn.clicked.connect(self._on_start)
        layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("■ 停止")
        self._stop_btn.clicked.connect(self._on_stop)
        layout.addWidget(self._stop_btn)

    @property
    def is_running(self) -> bool:
        """タイマーが実行中かどうか.

        Returns:
            実行中の場合True.
        """
        return self._is_running

    @property
    def elapsed_seconds(self) -> int:
        """経過秒数を返す.

        Returns:
            経過秒数.
        """
        return self._elapsed_seconds

    @property
    def current_task_id(self) -> str:
        """現在計測中のタスクIDを返す.

        Returns:
            タスクID.
        """
        return self._task_id

    def set_task(self, task_id: str, task_title: str) -> None:
        """計測対象タスクを設定する.

        実行中のタイマーがある場合は停止する。

        Args:
            task_id: タスクID.
            task_title: タスク名.
        """
        if self._is_running:
            self._on_stop()
        self._task_id = task_id
        self._task_title = task_title
        self._elapsed_seconds = 0
        self._update_display()

    def _on_start(self) -> None:
        """開始ボタンのハンドラ."""
        if not self._task_id or self._is_running:
            return
        self._is_running = True
        self._timer.start()
        self._update_display()

    def _on_stop(self) -> None:
        """停止ボタンのハンドラ."""
        if not self._is_running:
            return
        self._is_running = False
        self._timer.stop()
        # 最小1分に切り上げ
        minutes = max(1, math.ceil(self._elapsed_seconds / 60))
        self.timer_stopped.emit(self._task_id, minutes)
        self._elapsed_seconds = 0
        self._update_display()

    def _on_tick(self) -> None:
        """1秒ごとのタイマーコールバック."""
        self._elapsed_seconds += 1
        self._update_display()

    def _update_display(self) -> None:
        """表示を更新する."""
        if self._task_id:
            if self._is_running:
                self._status_label.setText(f"計測中: {self._task_title}")
            else:
                self._status_label.setText(f"対象: {self._task_title}")
        else:
            self._status_label.setText("タスクを選択してください")

        hours = self._elapsed_seconds // 3600
        minutes = (self._elapsed_seconds % 3600) // 60
        seconds = self._elapsed_seconds % 60
        self._time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self._start_btn.setEnabled(bool(self._task_id) and not self._is_running)
        self._stop_btn.setEnabled(self._is_running)
