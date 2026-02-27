"""実績アイコンボタンウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QPushButton, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.milestone_popup import MilestonePopup
from study_python.services.motivation_calculator import MilestoneData


logger = logging.getLogger(__name__)


class MilestoneButton(QPushButton):
    """実績アイコンボタン.

    クリックでMilestonePopupを表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _data: 実績データ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """MilestoneButtonを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__("\U0001f3c6 実績", parent)
        self._theme_manager = theme_manager
        self._data: MilestoneData | None = None
        self.setObjectName("secondary_button")
        self.setFixedHeight(36)
        self.setToolTip("実績")
        self.clicked.connect(self._on_clicked)

    def set_data(self, data: MilestoneData) -> None:
        """実績データを設定する.

        Args:
            data: 実績データ.
        """
        self._data = data
        logger.debug(
            f"MilestoneButton data updated: "
            f"total_hours={data.total_hours}, "
            f"study_days={data.study_days}, "
            f"current_streak={data.current_streak}, "
            f"{len(data.achieved)} achieved"
        )

    def _on_clicked(self) -> None:  # pragma: no cover
        """ボタンクリック時にポップアップを表示する."""
        if self._data is None:
            return
        popup = MilestonePopup(self._data, self._theme_manager, self)
        popup.exec()
