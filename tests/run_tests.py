#!/usr/bin/env python3
# Entry point for the whole test suite: discovers every tests/run_*_tests.py
# and runs each with this same interpreter. CI and humans call only this file,
# so a newly added suite is picked up with no workflow edit.
#
# Usage: python3 tests/run_tests.py        (Windows: py -3 tests\run_tests.py)
# Exit:  0 every suite passed, 1 something failed.
#
# The glob matches run_<name>_tests.py only, so it skips this file (nothing
# between run_ and _tests) and harness.py (shared helpers, not a suite).
# Suites run with sys.executable and no shell, same as the assertions inside
# them (see tests/harness.py).

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    suites = sorted(glob.glob(os.path.join(HERE, "run_*_tests.py")))
    if not suites:
        print("No run_*_tests.py suites found in %s" % HERE)
        return 1
    failed = []
    for suite in suites:
        name = os.path.basename(suite)
        # Flush so the header lands before the child's output when piped (CI logs).
        print("== %s ==" % name, flush=True)
        if subprocess.run([sys.executable, suite]).returncode != 0:
            failed.append(name)
        print("", flush=True)
    if failed:
        print("FAILED suites: %s" % ", ".join(failed))
        return 1
    print("all %d suites passed" % len(suites))
    return 0


if __name__ == "__main__":
    sys.exit(main())
