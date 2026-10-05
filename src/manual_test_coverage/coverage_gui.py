"""GUI to control a running coverage agent."""

import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QMessageBox
from PyQt5.QtCore import Qt
from manual_test_coverage.event_handler import TestEventHandler

logging.basicConfig(
    format="[%(process)d] %(asctime)s: %(filename)s - %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

VALID_TEST_NAME_REGEX = r"^[\w\-.][\w\-. ]*$"

mainwindow_file = Path(os.path.abspath(os.path.dirname(__file__))) / "mainwindow.ui"
startdialog_file = Path(os.path.abspath(os.path.dirname(__file__))) / "dialog_start.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(mainwindow_file)

TESTCASE_LABEL_NONE = "No test case active."
TARGET_LABEL_RUNNING = "Target running."
TARGET_LABEL_STOPPED = "Target stopped."


class StartDialog(QDialog):
    """Dialog for setting a test case name/ID."""
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(startdialog_file, self)
        self.setMaximumSize(self.frameGeometry().width(),self.frameGeometry().height())
        self.errorLabel.setVisible(False)
        self.buttonBox.accepted.connect(self.validate_accept)

    def validate_accept(self):
        """Accept if test case name conforms to requirements."""
        text = self.testcaseLineEdit.text()
        if re.match(VALID_TEST_NAME_REGEX, text):
            self.accept()
        else:
            self.errorLabel.setVisible(True)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main GUI window"""
    def __init__(self, runner):
        QMainWindow.__init__(self, None, Qt.WindowStaysOnTopHint)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.handler = TestEventHandler(runner)
        # Move window to top left corner
        self.setMaximumSize(self.frameGeometry().width(),self.frameGeometry().height())
        top_left_point = QApplication.desktop().availableGeometry().topLeft()
        self.move(top_left_point)

        runner.state_changed.connect(self.update_state)
        self.startButton.clicked.connect(self.start_clicked)
        self.endButton.clicked.connect(self.end_clicked)
        self.clearButton.clicked.connect(self.clear_clicked)

        self.update_state(runner.state)

    def add_log_message(self, message):
        """Append a message to the log text area."""
        logging.info(message)
        current_time = datetime.now()
        timestamp = current_time.strftime("%H:%M:%S")
        self.logTextEdit.append(f"[{timestamp}] {message}")

    def update_state(self, state: dict):
        """Update GUI from runner's state."""
        # Test case name
        if state["current_test"]:
            testcase_text = f"Test case: {state['current_test']}"
        else:
            testcase_text = TESTCASE_LABEL_NONE
        self.testcaseLabel.setText(testcase_text)

        # Target running
        if state["target_running"]:
            self.targetLabel.setText(TARGET_LABEL_RUNNING)
        else:
            self.targetLabel.setText(TARGET_LABEL_STOPPED)

    def start_clicked(self):
        """Show StartDialog and start new test case."""
        dialog = StartDialog(self)
        result = dialog.exec()
        if result:
            test_name = dialog.testcaseLineEdit.text()
            self.add_log_message(f"Starting new test case: '{test_name}'")
            self.toggle_buttons()
            self.handler.event_start(test_name)

    def end_clicked(self):
        """Show confirmation dialog and end test case."""
        if QMessageBox.question(
            self,
            "End test case?",
            "End current test case and save coverage report?"
        ) == QMessageBox.StandardButton.Yes:
            self.add_log_message("Ending current test case...")
            self.toggle_buttons()
            tester_id = self.testerIdLineEdit.text().strip()
            self.handler.event_end(tester_id)

    def clear_clicked(self):
        """Clear log text area."""
        self.logTextEdit.clear()

    def toggle_buttons(self):
        """Toggle the start/end buttons enabled state."""
        self.startButton.setEnabled(not self.startButton.isEnabled())
        self.endButton.setEnabled(not self.endButton.isEnabled())

class CoverageGui:
    """GUI controller for a coverage runner."""
    def __init__(self, runner):
        self.runner = runner
        self.app = QApplication(sys.argv)
        self.window = MainWindow(runner)

    def run(self):
        """Show and start GUI window."""
        self.window.show()
        self.app.exec()
        logging.info("GUI shutting down...")
