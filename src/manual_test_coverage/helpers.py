"""Helper functions for the native Frida coverage runner."""

from datetime import datetime

def add_timestamp(string):
    """Prepend a time stamp to a string."""
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d-%H%M%S")
    return f"{string}_{timestamp}"

def get_path_from_cmd_line_args(cmd_line_args):
    """Get only the executable's path from a CreateProcess call's command line args."""
    return cmd_line_args.split("\"")[0].strip()

