from manual_test_coverage.cli import resolve_agent_script_path
from manual_test_coverage.core.coverage_store import CoverageStore
from manual_test_coverage.core.frida_session_manager import (
    FridaRuntime,
    FridaSessionConfig,
    FridaSessionManager,
)


class DummySession:
    def __init__(self):
        self.detached_callbacks = []

    def on(self, event_name, callback):
        if event_name == "detached":
            self.detached_callbacks.append(callback)

    def create_script(self, script_text):
        return DummyScript(script_text)


class DummyScript:
    def __init__(self, script_text):
        self.script_text = script_text
        self.message_callbacks = []
        self.exports_sync = DummyAgent()

    def on(self, event_name, callback):
        if event_name == "message":
            self.message_callbacks.append(callback)

    def load(self):
        return None


class DummyAgent:
    def setup_cpp(self, module_offsets_map, pid):
        self.module_offsets_map = module_offsets_map
        self.pid = pid

    def clear_cpp_coverage(self):
        return None

    def dump_cpp_coverage(self):
        return None


class DummyDevice:
    def __init__(self):
        self.session = DummySession()
        self.resumed = []

    def resume(self, pid):
        self.resumed.append(pid)

    def attach(self, pid):
        return self.session


class DummyReactor:
    def __init__(self):
        self.run_called = False

    def schedule(self, callback, delay=0):
        callback()

    def run(self):
        self.run_called = True


def test_session_manager_stores_coverage_and_tracks_detach():
    device = DummyDevice()
    reactor = DummyReactor()
    coverage_store = CoverageStore()
    calls = []

    manager = FridaSessionManager(
        runtime=FridaRuntime(device=device, reactor=reactor),
        coverage_store=coverage_store,
        config=FridaSessionConfig(
            module_offsets_map={"demo.exe": [10]},
            agent_script_path=resolve_agent_script_path(),
        ),
        on_detached=lambda: calls.append(("detach")),
    )

    manager.run(123)

    assert manager.session_count == 1
    assert device.resumed == [123]
    assert reactor.run_called
    assert coverage_store.as_dict() == {}

    manager._handle_message({"payload": {"coverage": {"demo.exe": [10, 20]}}})
    assert coverage_store.as_dict() == {"demo.exe": [10, 20]}

    manager._handle_detached(123, device.session, "ok")
    assert manager.session_count == 0
    assert calls == [("detach")]
