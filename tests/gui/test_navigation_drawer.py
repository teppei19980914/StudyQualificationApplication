"""NavigationDrawerのテスト."""

from PySide6.QtCore import Qt

from study_python.gui.widgets.navigation_drawer import (
    SETTINGS_PAGE_INDEX,
    DrawerOverlay,
    NavigationDrawer,
)


class TestNavigationDrawer:
    """NavigationDrawerのテスト."""

    def test_create(self, qtbot):
        """生成テスト."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert drawer is not None

    def test_object_name(self, qtbot):
        """objectNameが設定される."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert drawer.objectName() == "navigation_drawer"

    def test_fixed_width(self, qtbot):
        """固定幅が260px."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert drawer.width() == 260

    def test_has_nav_buttons(self, qtbot):
        """ナビゲーションボタンが6個ある（5ページ+設定）."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert len(drawer._buttons) == 6

    def test_first_button_checked(self, qtbot):
        """最初のボタンが選択されている."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert drawer._buttons[0].isChecked()

    def test_nav_item_clicked_signal(self, qtbot):
        """ナビボタンクリックでnav_item_clickedシグナルが発火する."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        drawer.show()
        with qtbot.waitSignal(drawer.nav_item_clicked, timeout=1000) as blocker:
            qtbot.mouseClick(drawer._buttons[1], Qt.MouseButton.LeftButton)
        assert blocker.args == [1]

    def test_settings_clicked_signal(self, qtbot):
        """設定ボタンクリックでsettings_clickedシグナルが発火する."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        drawer.show()
        with qtbot.waitSignal(drawer.settings_clicked, timeout=1000):
            qtbot.mouseClick(
                drawer._buttons[SETTINGS_PAGE_INDEX], Qt.MouseButton.LeftButton
            )

    def test_set_checked_button(self, qtbot):
        """set_checked_buttonでボタンが選択される."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        drawer.set_checked_button(2)
        assert drawer._buttons[2].isChecked()

    def test_set_checked_button_settings(self, qtbot):
        """設定ボタンを選択できる."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        drawer.set_checked_button(SETTINGS_PAGE_INDEX)
        assert drawer._buttons[SETTINGS_PAGE_INDEX].isChecked()

    def test_set_checked_button_out_of_range(self, qtbot):
        """範囲外インデックスでエラーが発生しない."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        drawer.set_checked_button(99)
        # 範囲外なのでボタンは変更されない
        assert drawer._buttons[0].isChecked()

    def test_buttons_are_checkable(self, qtbot):
        """全ボタンがチェック可能."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        for btn in drawer._buttons:
            assert btn.isCheckable()

    def test_buttons_have_sidebar_button_object_name(self, qtbot):
        """ボタンのobjectNameがsidebar_button."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        for btn in drawer._buttons:
            assert btn.objectName() == "sidebar_button"

    def test_buttons_fixed_height(self, qtbot):
        """ボタンの固定高さが44px."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        for btn in drawer._buttons:
            assert btn.minimumHeight() == 44
            assert btn.maximumHeight() == 44

    def test_initially_hidden(self, qtbot):
        """初期状態で非表示."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert not drawer.isVisible()

    def test_settings_page_index_constant(self):
        """SETTINGS_PAGE_INDEXが5."""
        assert SETTINGS_PAGE_INDEX == 5

    def test_exclusive_button_group(self, qtbot):
        """ボタングループが排他選択."""
        drawer = NavigationDrawer()
        qtbot.addWidget(drawer)
        assert drawer._button_group.exclusive()


class TestDrawerOverlay:
    """DrawerOverlayのテスト."""

    def test_create(self, qtbot):
        """生成テスト."""
        overlay = DrawerOverlay()
        qtbot.addWidget(overlay)
        assert overlay is not None

    def test_object_name(self, qtbot):
        """objectNameが設定される."""
        overlay = DrawerOverlay()
        qtbot.addWidget(overlay)
        assert overlay.objectName() == "drawer_overlay"

    def test_initially_hidden(self, qtbot):
        """初期状態で非表示."""
        overlay = DrawerOverlay()
        qtbot.addWidget(overlay)
        assert not overlay.isVisible()

    def test_clicked_signal(self, qtbot):
        """クリックでclickedシグナルが発火する."""
        overlay = DrawerOverlay()
        qtbot.addWidget(overlay)
        overlay.show()
        overlay.resize(100, 100)
        with qtbot.waitSignal(overlay.clicked, timeout=1000):
            qtbot.mouseClick(overlay, Qt.MouseButton.LeftButton)
