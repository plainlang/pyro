#!/usr/bin/env python3
# Copy the complete contents of one folder into another, recursively.
#
# Usage: copy_folder.py <source> <destination>
#
# The destination folder is created if it does not exist. If it already
# exists, the source contents are merged into it and files with the same
# name are overwritten - the same semantics as `cp -r <source>/* <dest>/`
# on unix, but working identically on macOS, Linux and Windows.
#
# Exits 0 on success, 1 on error (source missing or not a directory).
#
# Requires Python 3.8+ (shutil.copytree dirs_exist_ok).

import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy the complete contents of a folder to a destination folder."
    )
    parser.add_argument("source", help="folder to copy from")
    parser.add_argument("destination", help="folder to copy into")
    args = parser.parse_args()

    source = Path(args.source)
    destination = Path(args.destination)

    if not source.exists():
        print(f"error: source does not exist: {source}", file=sys.stderr)
        return 1
    if not source.is_dir():
        print(f"error: source is not a directory: {source}", file=sys.stderr)
        return 1

    try:
        shutil.copytree(source, destination, dirs_exist_ok=True)
    except OSError as exc:
        print(f"error: copy failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
