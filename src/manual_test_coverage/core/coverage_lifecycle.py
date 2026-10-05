"""Lifecycle helper for native coverage collection and reporting."""

from manual_test_coverage.core.report_service import ReportService


CPP_REPORT_NAME = "cpp_report.xml"


class CoverageLifecycleManager:
    """Coordinate coverage reset, dump, and report generation."""

    def __init__(self, session_manager, coverage_store, function_infos, report_service=None):
        self._session_manager = session_manager
        self._coverage_store = coverage_store
        self._report_service = report_service or ReportService()
        self._function_infos = function_infos

    def clear_coverage(self):
        """Clear Frida coverage state and cached coverage data."""
        self._session_manager.clear_cpp_coverage()

    def reset_coverage(self):
        """Reset Frida coverage state and clear the normalized coverage store."""
        self.clear_coverage()
        self._coverage_store.clear()

    def dump_coverage(self):
        """Ask Frida to dump the current native coverage traces."""
        self._session_manager.dump_cpp_coverage()

    def write_report(self, output_dir, tester_id, test_name, start_pid):
        """Create a report directory and write the Cobertura XML report."""
        report_dir = self._report_service.build_report_dir(
            output_root=output_dir,
            tester_id=tester_id,
            test_name=test_name,
            start_pid=start_pid,
        )
        output_file = report_dir / CPP_REPORT_NAME
        return self._report_service.write_report(
            coverage_store=self._coverage_store,
            function_infos=self._function_infos,
            output_file=output_file,
        )
