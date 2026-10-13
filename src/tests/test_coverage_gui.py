"""Exercise the Designer forms and PySide6 signal connections headlessly."""

import threading

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QMessageBox

from manual_test_coverage.coverage_gui import MainWindow, StartDialog


@pytest.fixture(scope="module")
def app():
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("QT_QPA_PLATFORM", "offscreen")
        application = QApplication.instance() or QApplication([])
        yield application
        application.quit()


class GuiRunner(QObject):
    state_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.state = {"current_test": None, "target_running": True}


@pytest.fixture
def window(app):
    runner = GuiRunner()
    controller = MainWindow(runner)
    yield controller, runner
    controller.close()
    controller.deleteLater()
    app.processEvents()


@pytest.mark.parametrize("test_name", ["", "../test", "test/name"])
def test_start_dialog_rejects_invalid_names(app, test_name):
    dialog = StartDialog()
    dialog.testcaseLineEdit.setText(test_name)
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).click()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert not dialog.errorLabel.isHidden()
    dialog.close()


def test_start_dialog_accepts_valid_name(app):
    dialog = StartDialog()
    dialog.testcaseLineEdit.setText("Smoke test-1.2")
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).click()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.errorLabel.isHidden()
    dialog.close()


def test_start_dialog_cancel_uses_designer_connection(app):
    dialog = StartDialog()
    rejected = []
    dialog.rejected.connect(lambda: rejected.append(True))
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).click()

    assert rejected == [True]
    dialog.close()


def test_main_window_loads_widgets_and_receives_worker_state(app, window):
    controller, runner = window
    assert controller.windowTitle() == "Coverage Controller"
    assert controller.testcaseLabel.text() == "No test case active."
    assert controller.targetLabel.text() == "Target running."
    assert controller.startButton.isEnabled()
    assert not controller.endButton.isEnabled()

    worker = threading.Thread(
        target=runner.state_changed.emit,
        args=({"current_test": "Smoke test", "target_running": False},),
    )
    worker.start()
    worker.join()
    # Widget updates must wait for the GUI thread's event loop.
    assert controller.testcaseLabel.text() == "No test case active."
    app.processEvents()

    assert controller.testcaseLabel.text() == "Test case: Smoke test"
    assert controller.targetLabel.text() == "Target stopped."


def test_main_window_buttons_delegate_test_events(window, monkeypatch):
    controller, _ = window
    events = []

    def accept_dialog(dialog):
        dialog.testcaseLineEdit.setText("Smoke test")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(StartDialog, "exec", accept_dialog)
    monkeypatch.setattr(controller.handler, "event_start", events.append)
    monkeypatch.setattr(controller.handler, "event_end", events.append)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )

    controller.startButton.click()
    assert events == ["Smoke test"]
    assert not controller.startButton.isEnabled()
    assert controller.endButton.isEnabled()

    controller.testerIdLineEdit.setText(" tester-1 ")
    controller.endButton.click()
    assert events == ["Smoke test", "tester-1"]
    assert controller.startButton.isEnabled()
    assert not controller.endButton.isEnabled()

    assert controller.logTextEdit.toPlainText()
    controller.clearButton.click()
    assert controller.logTextEdit.toPlainText() == ""
