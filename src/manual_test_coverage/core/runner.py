"""Native Frida coverage runner core."""

from dataclasses import dataclass
import logging
import sys

from PyQt5.QtCore import QObject, pyqtSignal

from manual_test_coverage.core.coverage_lifecycle import CoverageLifecycleManager
from manual_test_coverage.core.coverage_store import CoverageStore
from manual_test_coverage.core.frida_session_manager import (
    FridaSessionConfig,
    FridaSessionManager,
)
from manual_test_coverage.core.module_registry import ModuleRegistry
from manual_test_coverage.core.runner_config import RunnerConfig

logging.basicConfig(
    format="[%(process)d] %(asctime)s: %(filename)s - %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

CPP_REPORT_NAME = "cpp_report.xml"


@dataclass
class RunnerState:
    """State of the coverage runner."""

    target_running: bool = True
    current_test: str | None = None

    def as_dict(self):
        """Return the state representation consumed by the UI."""
        return {
            "target_running": self.target_running,
            "current_test": self.current_test,
        }


class FridaRunner(QObject):
    """Attach Frida to native processes and collect coverage traces."""

    state_changed = pyqtSignal(dict)

    def __init__(self, config: RunnerConfig, pid):
        super().__init__()

        self._pid = pid
        self._config = config

        self._runner_state = RunnerState()

        self._coverage_store = CoverageStore()
        self._module_registry = ModuleRegistry(
            function_infos_dir=self._config.function_infos,
        )
        self._module_registry.load_all(self._config.included_modules)
        self._session_manager = FridaSessionManager(
            coverage_store=self._coverage_store,
            config=FridaSessionConfig(
                module_offsets_map=self._module_registry.offsets,
                agent_script_path=self._config.agent_script_path,
            ),
            on_detached=self._handle_session_detached,
        )

        self._coverage_lifecycle = CoverageLifecycleManager(
            session_manager=self._session_manager,
            coverage_store=self._coverage_store,
            function_infos=self._module_registry.function_infos,
        )

    def run(self):
        """Schedule the native Frida startup work."""
        self._session_manager.run(self._pid)

    def _stop_if_idle(self):
        """Stop the Frida reactor when no tracked sessions remain."""
        if self._session_manager.session_count == 0:
            self._session_manager.stop()
            self._runner_state.target_running = False
            self.state_changed.emit(self.state)

    @property
    def state(self):
        """Expose the runner state to the UI."""
        return self._runner_state.as_dict()

    def _handle_session_detached(self):
        """Clean up state when a traced process exits."""
        self._session_manager.schedule(self._stop_if_idle, delay=0.5)

    def event_start_test(self, test_name):
        """Reset native coverage on test start."""
        logging.debug("Event start: %s", test_name)
        self._runner_state.current_test = test_name
        self._coverage_lifecycle.reset_coverage()
        self.state_changed.emit(self.state)

    def event_end_test(self, tester_id):
        """Write a native coverage report and clear state."""
        logging.debug("Event end")
        self._coverage_lifecycle.dump_coverage()

        self._coverage_lifecycle.write_report(
            output_dir=self._config.output_dir,
            tester_id=tester_id,
            test_name=self._runner_state.current_test,
            start_pid=self._pid,
        )

        self._runner_state.current_test = None
        self.state_changed.emit(self.state)
