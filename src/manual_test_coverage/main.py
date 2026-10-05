"""Native-only Frida coverage launcher and GUI bootstrap."""

import logging
import sys
import threading

from manual_test_coverage.cli import build_runner, parse_arguments
from manual_test_coverage.coverage_gui import CoverageGui
from manual_test_coverage.version import __version__

logging.basicConfig(
    format="[%(process)d] %(asctime)s: %(filename)s - %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

def main():
    """Main entry point."""
    logging.info(f"Running coverage agent: version {__version__}")
    args = parse_arguments()

    runner = build_runner(args)
    runner_thread = threading.Thread(target=runner.run, daemon=True)
    runner_thread.start()

    gui = CoverageGui(runner=runner)
    gui.run()

    runner_thread.join()
    logging.info("All target processes exited - shutting down...")

if __name__ == "__main__":
    main()
