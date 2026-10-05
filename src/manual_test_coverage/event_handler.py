"""Delegate start and end test events to the coverage runner."""

import threading

class TestEventHandler:
    """Delegate start and end test events to the coverage runner."""
    def __init__(self, runner):
        self._runner = runner

    def event_start(self, test_name):
        """Make an async call to start a test case."""
        t = threading.Thread(target=self._runner.event_start_test, args=(test_name,))
        t.start()

    def event_end(self, tester_id):
        """Make an async call to end a test case."""
        t = threading.Thread(target=self._runner.event_end_test, args=(tester_id,))
        t.start()
