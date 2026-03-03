"""HeaderBarのテスト."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from study_python.gui.widgets.header_bar import HeaderBar


class TestHeaderBar:
    """HeaderBarのテスト."""

    def test_create(self, qtbot):
        """生成テスト."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        assert bar is not None

    def test_object_name(self, qtbot):
        """objectNameが設定される."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        assert bar.objectName() == "header_bar"

    def test_fixed_height(self, qtbot):
        """固定高さが48px."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        assert bar.minimumHeight() == 48
        assert bar.maximumHeight() == 48

    def test_hamburger_button_exists(self, qtbot):
        """ハンバーガーボタンが存在する."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        buttons = bar.findChildren(QPushButton, "hamburger_button")
        assert len(buttons) == 1

    def test_hamburger_button_text(self, qtbot):
        """ハンバーガーボタンのテキストが☰."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        btn = bar.findChild(QPushButton, "hamburger_button")
        assert btn.text() == "\u2630"

    def test_hamburger_button_size(self, qtbot):
        """ハンバーガーボタンが36x36."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        btn = bar.findChild(QPushButton, "hamburger_button")
        assert btn.minimumWidth() == 36
        assert btn.maximumWidth() == 36
        assert btn.minimumHeight() == 36
        assert btn.maximumHeight() == 36

    def test_title_label_exists(self, qtbot):
        """タイトルラベルが存在する."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        labels = bar.findChildren(QLabel, "header_title")
        assert len(labels) == 1

    def test_default_title(self, qtbot):
        """デフォルトタイトルがダッシュボード."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        label = bar.findChild(QLabel, "header_title")
        assert label.text() == "ダッシュボード"

    def test_set_title(self, qtbot):
        """set_titleでタイトルが変更される."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        bar.set_title("テスト")
        label = bar.findChild(QLabel, "header_title")
        assert label.text() == "テスト"

    def test_hamburger_clicked_signal(self, qtbot):
        """ハンバーガーボタンクリックでシグナルが発火する."""
        bar = HeaderBar()
        qtbot.addWidget(bar)
        btn = bar.findChild(QPushButton, "hamburger_button")
        with qtbot.waitSignal(bar.hamburger_clicked, timeout=1000):
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
