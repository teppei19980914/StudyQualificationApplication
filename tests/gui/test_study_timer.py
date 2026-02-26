"""StudyTimerWidgetのテスト."""

from study_python.gui.widgets.study_timer import StudyTimerWidget


class TestStudyTimerWidgetCreate:
    """生成テスト."""

    def test_create_widget(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        assert timer.is_running is False
        assert timer.elapsed_seconds == 0
        assert timer.current_task_id == ""

    def test_initial_display(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        assert timer._time_label.text() == "00:00:00"
        assert "タスクを選択" in timer._status_label.text()

    def test_buttons_initial_state(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        assert timer._start_btn.isEnabled() is False
        assert timer._stop_btn.isEnabled() is False


class TestStudyTimerWidgetSetTask:
    """set_taskのテスト."""

    def test_set_task(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テストタスク")
        assert timer.current_task_id == "task-1"
        assert "テストタスク" in timer._status_label.text()
        assert timer._start_btn.isEnabled() is True

    def test_set_task_resets_elapsed(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "タスク1")
        timer._elapsed_seconds = 100
        timer.set_task("task-2", "タスク2")
        assert timer.elapsed_seconds == 0


class TestStudyTimerWidgetStartStop:
    """開始/停止のテスト."""

    def test_start_timer(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._on_start()
        assert timer.is_running is True
        assert timer._stop_btn.isEnabled() is True
        assert timer._start_btn.isEnabled() is False
        # クリーンアップ
        timer._timer.stop()
        timer._is_running = False

    def test_start_without_task_does_nothing(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer._on_start()
        assert timer.is_running is False

    def test_stop_emits_signal(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._on_start()
        timer._elapsed_seconds = 150  # 2分30秒
        with qtbot.waitSignal(timer.timer_stopped) as blocker:
            timer._on_stop()
        assert blocker.args == ["task-1", 3]  # 切り上げで3分

    def test_stop_minimum_1_minute(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._on_start()
        timer._elapsed_seconds = 10  # 10秒
        with qtbot.waitSignal(timer.timer_stopped) as blocker:
            timer._on_stop()
        assert blocker.args == ["task-1", 1]  # 最小1分

    def test_stop_resets_elapsed(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._on_start()
        timer._elapsed_seconds = 60
        timer._on_stop()
        assert timer.elapsed_seconds == 0

    def test_stop_when_not_running_does_nothing(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer._on_stop()
        assert timer.is_running is False

    def test_set_task_stops_running_timer(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "タスク1")
        timer._on_start()
        timer._elapsed_seconds = 120
        with qtbot.waitSignal(timer.timer_stopped):
            timer.set_task("task-2", "タスク2")
        assert timer.is_running is False
        assert timer.current_task_id == "task-2"


class TestStudyTimerWidgetTick:
    """_on_tickのテスト."""

    def test_tick_increments_seconds(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._on_start()
        timer._on_tick()
        # _on_start doesn't increment, but _on_tick does
        # elapsed starts at 0, then +1 from tick
        assert timer.elapsed_seconds == 1
        timer._timer.stop()
        timer._is_running = False

    def test_display_updates_on_tick(self, qtbot):
        timer = StudyTimerWidget()
        qtbot.addWidget(timer)
        timer.set_task("task-1", "テスト")
        timer._elapsed_seconds = 3661  # 1h 1m 1s
        timer._update_display()
        assert timer._time_label.text() == "01:01:01"
