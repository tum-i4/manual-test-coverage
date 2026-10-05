from pathlib import Path

from manual_test_coverage.core.coverage_lifecycle import CoverageLifecycleManager


class DummySessionManager:
    def __init__(self):
        self.clear_calls = 0
        self.dump_calls = 0

    def clear_cpp_coverage(self):
        self.clear_calls += 1

    def dump_cpp_coverage(self):
        self.dump_calls += 1


class DummyCoverageStore:
    def __init__(self):
        self.clear_calls = 0

    def clear(self):
        self.clear_calls += 1


class DummyReportService:
    def __init__(self):
        self.calls = []

    def build_report_dir(self, output_root, tester_id, test_name, start_pid):
        return Path(output_root) / tester_id / f"{test_name}_{start_pid}"

    def write_report(self, coverage_store, function_infos, output_file):
        self.calls.append((coverage_store, function_infos, output_file))
        return output_file


def test_coverage_lifecycle_manager_delegates_clear_dump_and_report():
    session_manager = DummySessionManager()
    report_service = DummyReportService()
    coverage_store = DummyCoverageStore()
    function_infos = {"demo.exe": []}

    lifecycle = CoverageLifecycleManager(
        session_manager=session_manager,
        coverage_store=coverage_store,
        report_service=report_service,
        function_infos=function_infos,
    )

    lifecycle.reset_coverage()
    lifecycle.dump_coverage()
    output_path = lifecycle.write_report(
        output_dir=Path("/tmp/out"),
        tester_id="tester-1",
        test_name="sample-test",
        start_pid=4242,
    )

    assert session_manager.clear_calls == 1
    assert session_manager.dump_calls == 1
    assert coverage_store.clear_calls == 1
    assert output_path == Path("/tmp/out") / "tester-1" / "sample-test_4242" / "cpp_report.xml"
    assert report_service.calls[0][0] is coverage_store
    assert report_service.calls[0][1] is function_infos
    assert report_service.calls[0][2] == output_path
