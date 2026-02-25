"""Study Plannerアプリケーションのエントリポイント."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from study_python.gui.main_window import MainWindow
from study_python.logging_config import setup_logging


def main() -> None:
    """アプリケーションを起動する."""
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("Study Planner")
    app.setOrganizationName("StudyPython")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
