"""Sidebarのテスト."""

from study_python.gui.widgets.sidebar import Sidebar, SidebarButton


class TestSidebarButton:
    """SidebarButtonのテスト."""

    def test_create_button(self, qtbot):
        btn = SidebarButton("icon", "label")
        qtbot.addWidget(btn)
        assert btn.isCheckable()
        assert "icon" in btn.text()
        assert "label" in btn.text()
        assert btn.objectName() == "sidebar_button"


class TestSidebar:
    """Sidebarのテスト."""

    def test_create_sidebar(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        assert sidebar.objectName() == "sidebar"
        assert sidebar.width() == 220

    def test_has_navigation_buttons(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        assert len(sidebar._buttons) == 5

    def test_first_button_checked(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        assert sidebar._buttons[0].isChecked()

    def test_page_changed_signal(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        with qtbot.waitSignal(sidebar.page_changed, timeout=1000) as blocker:
            sidebar._buttons[1].click()
        assert blocker.args == [1]

    def test_theme_indicator_dark(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        sidebar.set_theme_indicator(True)
        assert "ライトモード" in sidebar.theme_button.text()

    def test_theme_indicator_light(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        sidebar.set_theme_indicator(False)
        assert "ダークモード" in sidebar.theme_button.text()

    def test_has_theme_button(self, qtbot):
        sidebar = Sidebar()
        qtbot.addWidget(sidebar)
        assert sidebar.theme_button is not None
        assert sidebar.theme_button.objectName() == "secondary_button"
