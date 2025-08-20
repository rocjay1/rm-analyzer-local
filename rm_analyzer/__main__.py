"""
Analyze a transactions CSV by generating and sending a summary email.

Usage:
------

    $ rm_analyzer [-h] [path]

    
Options:
    -h, --help  show this help message and exit
"""

# Standard library imports
import os
import argparse

import rm_analyzer
from rm_analyzer import summarize, send


def main():
    """Analyzes a transactions CSV."""
    # Parse args
    parser = argparse.ArgumentParser(description="Analyze a transactions CSV.")
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        help="path to transactions CSV or directory containing CSVs",
        default=os.path.join(os.path.expanduser("~"), "Downloads"),
    )
    args = parser.parse_args()

    # Path validation
    path = args.path
    if os.path.isdir(path):
        children = [os.path.join(path, c) for c in os.listdir(path)]
        sheets = list(filter(lambda x: x.endswith("-transactions.csv"), children))
        if sheets:
            path = max(sheets, key=os.path.getctime)
        else:
            raise FileNotFoundError(f"No transactions CSV in directory: {path}")
    elif os.path.isfile(path):
        if not path.endswith("-transactions.csv"):
            raise FileNotFoundError(f"File is not a valid transactions CSV: {path}")
    else:
        raise FileExistsError(
            f"Path specified is not a valid directory or file path: {path}"
        )

    # Main logic
    print(f"Running rm_analyzer on: {path}")
    dest, subject, html = summarize.build_summary(path, rm_analyzer.CONFIG)
    send.gmail_send_message(dest, subject, html)


if __name__ == "__main__":
    main()
