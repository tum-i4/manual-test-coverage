"""Report generation service for native coverage data."""

from pathlib import Path

from manual_test_coverage.helpers import add_timestamp
from manual_test_coverage.reporting.cobertura import to_cobertura_xml


class ReportService:
    """Generate native coverage reports from normalized coverage data."""

    def build_report_dir(self, output_root, tester_id, test_name, start_pid):
        """Create the per-test report directory for a native coverage run."""
        report_dir = add_timestamp(test_name) + f"_{start_pid}"
        report_dir_path = Path(output_root) / tester_id / report_dir
        report_dir_path.mkdir(parents=True, exist_ok=True)
        return report_dir_path

    def write_report(self, coverage_store, function_infos, output_file: Path):
        """Write a Cobertura XML report from the current normalized coverage store."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        coverage_map = coverage_store.as_dict()
        coverage_data = {}

        for module_name, covered_offsets in coverage_map.items():
            if not covered_offsets:
                continue

            coverage_data[module_name] = {}
            function_info_list = function_infos.get(module_name, [])
            for function_name, _, source_file, address_offset in function_info_list:
                source_data = coverage_data[module_name].setdefault(source_file, {})
                source_data[function_name] = address_offset in covered_offsets

        if not coverage_data:
            return None

        to_cobertura_xml(coverage_data, output_file)
        return output_file
