"""Session orchestration for native Frida coverage instrumentation."""

from dataclasses import dataclass, field
import logging
import threading
from pathlib import Path

import frida
from frida_tools.application import Reactor


@dataclass
class FridaSessionConfig:
    """Static inputs for Frida session instrumentation."""

    module_offsets_map: dict
    agent_script_path: Path

    def __post_init__(self):
        self.agent_script_path = Path(self.agent_script_path)


@dataclass
class FridaRuntime:
    """Own the Frida device, reactor, and stop signal."""

    device: object = field(default_factory=frida.get_local_device)
    reactor: object | None = None
    _stop_requested: threading.Event = field(default_factory=threading.Event)

    def __post_init__(self):
        if self.reactor is None:
            self.reactor = Reactor(
                run_until_return=lambda reactor: self._stop_requested.wait()
            )

    def schedule(self, callback, delay=0):
        """Schedule work on the Frida reactor."""
        self.reactor.schedule(callback, delay=delay)

    def run(self):
        """Run the Frida reactor."""
        self.reactor.run()

    def stop(self):
        """Stop the Frida reactor."""
        self._stop_requested.set()


class FridaSessionManager:
    """Manage Frida sessions, message dispatch, and native child-process setup."""

    def __init__(
        self,
        coverage_store,
        config,
        on_detached=None,
        runtime=None,
    ):
        self._runtime = runtime or FridaRuntime()
        self._coverage_store = coverage_store
        self._config = config

        self._sessions = set()
        self._agents = {}

        self._on_detached = on_detached

    @property
    def sessions(self):
        """Return live Frida sessions."""
        return self._sessions

    @property
    def session_count(self):
        """Return how many Frida sessions are currently attached."""
        return len(self._sessions)

    @property
    def agents(self):
        """Return the currently attached Frida agents."""
        return dict(self._agents)

    def start(self, pid):
        """Start Frida instrumentation for a target PID."""
        try:
            self._runtime.device.resume(pid)
        except frida.InvalidArgumentError:
            logging.info("Process already resumed.")

        self._instrument(pid)

    def run(self, pid):
        """Schedule startup and run the Frida reactor."""
        self._runtime.schedule(lambda: self.start(pid))
        self._runtime.run()

    def schedule(self, callback, delay=0):
        """Schedule work on the Frida reactor."""
        self._runtime.schedule(callback, delay=delay)

    def stop(self):
        """Stop the Frida reactor."""
        self._runtime.stop()

    def _instrument(self, pid):
        """Attach Frida to a process and set up the agent."""
        session = self._runtime.device.attach(pid)
        session.on("detached", lambda reason, session=session: self._runtime.schedule(
            lambda: self._handle_detached(pid, session, reason)
        ))

        script = session.create_script(
            self._config.agent_script_path.read_text(encoding="utf-8"))
        script.on("message", lambda message, data: self._runtime.schedule(
            lambda: self._handle_message(message)))
        script.load()
        self._sessions.add(session)

        agent = script.exports_sync
        self._agents[pid] = agent

        try:
            agent.setup_cpp(self._config.module_offsets_map, pid)
        except frida.InvalidOperationError:
            logging.error(
                "Unable to setup native agent for pid=%s. Process might not be running.", pid)

    def _handle_message(self, message):
        """Dispatch Frida events to the runner callbacks."""
        if "payload" not in message:
            logging.error("Unknown message format: %s", message)
            return

        payload = message["payload"]
        if "coverage" in payload:
            self._store_coverage(payload["coverage"])
        elif "childProcess" in payload:
            threading.Thread(target=lambda: self._handle_child_process(
                payload["childProcess"])).start()
        elif "error" in payload:
            self._handle_error(payload["error"])
        else:
            logging.debug("Unknown message format: %s", message)

    def _store_coverage(self, modules_covered):
        """Normalize and store coverage payloads in the common coverage store."""
        for module_name, function_offsets in modules_covered.items():
            self._coverage_store.add(module_name, function_offsets)

    def _handle_child_process(self, process_info):
        """Instrument newly spawned native child processes."""
        # Child-process filtering can be added here if needed.
        child_pid, cmd_line_args = process_info
        logging.info(
            f"Child process spawned: pid={child_pid}, info={cmd_line_args}")
        self._instrument(child_pid)

    def _handle_error(self, error):
        """Handle Frida error message."""
        logging.error(f"Frida error: {error}")

    def _handle_detached(self, pid, session, reason):
        """Clean up state when a traced process exits."""
        logging.info("detached: pid=%s, reason='%s'", pid, reason)
        self._sessions.discard(session)
        self._agents.pop(pid, None)
        if self._on_detached:
            self._on_detached()

    def clear_cpp_coverage(self):
        """Clear native coverage state across all active agents."""
        for pid, agent in list(self._agents.items()):
            try:
                agent.clear_cpp_coverage()
            except frida.InvalidOperationError:
                logging.error(
                    "Error when clearing coverage for process %s.", pid)

    def dump_cpp_coverage(self):
        """Ask each active agent to dump its collected native coverage."""
        for pid, agent in list(self._agents.items()):
            try:
                agent.dump_cpp_coverage()
            except frida.InvalidOperationError:
                logging.error(
                    "Error when dumping coverage for process %s.", pid)
