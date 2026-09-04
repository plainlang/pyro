#!/usr/bin/env python3
# Shared assertion helpers for the tests/run_*_tests.py suites. Not a suite
# itself - the run_tests.py discovery glob wants run_<name>_tests.py, which
# this filename is not.
#
# A suite calls set_script(<path to the script under test>) once, makes its
# assertions, and finishes with `return finish()`. Counters are module-level:
# one suite per process, which is how run_tests.py invokes them.
#
# Everything is compared as bytes and every child process is run with
# sys.executable, so a suite proves the same thing on every platform the skill
# claims to support - which is the point of the exercise. No shell is spawned
# anywhere.

import subprocess
import sys

_script = None
passed = 0
failed = 0


def set_script(path):
    global _script
    _script = path


def ok(desc):
    global passed
    passed += 1
    print("  ok    %s" % desc)


def bad(desc, detail=None):
    global failed
    failed += 1
    print("  FAIL  %s" % desc)
    if detail:
        print("        %s" % detail)


def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def run(*args):
    proc = subprocess.run(
        [sys.executable, _script] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


def assert_stdout(desc, want, *args):
    """Exit 0 and stdout matching `want` (bytes) exactly."""
    rc, out, err = run(*args)
    if rc != 0:
        bad("%s (exit %d)" % (desc, rc), err.decode("utf-8", "replace").strip())
    elif out != want:
        bad(desc, "want %r\n        got  %r" % (want[:200], out[:200]))
    else:
        ok(desc)


def assert_rc(desc, want, *args):
    rc = run(*args)[0]
    if rc == want:
        ok(desc)
    else:
        bad(desc, "want exit %d, got %d" % (want, rc))


def finish():
    print("\npython: %s" % sys.version.split()[0])
    print("passed: %d   failed: %d" % (passed, failed))
    return 1 if failed else 0
