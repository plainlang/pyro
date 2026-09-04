#!/usr/bin/env python3
# Tests for skills/render-spec/scripts/copy_folder.py.
#
# Usage: python3 tests/run_copy_folder_tests.py   (normally via tests/run_tests.py)
# Exit:  0 all assertions passed, 1 something failed.
#
# The assertion helpers live in tests/harness.py: byte-exact comparisons, every
# child process run with sys.executable, no shell anywhere. Fixture trees are
# built in a temp dir, so the suite passes on every platform the skill claims
# to support.

import os
import shutil
import sys
import tempfile

import harness
from harness import assert_rc, assert_stdout, bad, ok, read

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "render-spec", "scripts", "copy_folder.py")

harness.set_script(SCRIPT)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def make_source(tmp):
    src = os.path.join(tmp, "src")
    write(os.path.join(src, "a.txt"), b"alpha\n")
    write(os.path.join(src, "sub", "b.txt"), b"beta\n")
    return src


def assert_file(desc, path, want):
    if not os.path.isfile(path):
        bad(desc, "missing %s" % path)
    elif read(path) != want:
        bad(desc, "want %r, got %r" % (want, read(path)))
    else:
        ok(desc)


def main():
    tmp = tempfile.mkdtemp()
    try:
        run_suite(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return harness.finish()


def run_suite(tmp):
    src = make_source(tmp)

    # 1. Fresh copy: destination (with missing parents) is created.
    fresh = os.path.join(tmp, "deep", "fresh")
    assert_stdout("fresh copy exits 0, silent", b"", src, fresh)
    assert_file("fresh copy: top-level file", os.path.join(fresh, "a.txt"), b"alpha\n")
    assert_file("fresh copy: nested file", os.path.join(fresh, "sub", "b.txt"), b"beta\n")

    # 2. Merge into an existing destination: same names overwritten, extras kept.
    merged = os.path.join(tmp, "merged")
    write(os.path.join(merged, "a.txt"), b"stale\n")
    write(os.path.join(merged, "extra.txt"), b"keep me\n")
    assert_stdout("merge copy exits 0, silent", b"", src, merged)
    assert_file("merge: same-name file overwritten", os.path.join(merged, "a.txt"), b"alpha\n")
    assert_file("merge: nested file copied", os.path.join(merged, "sub", "b.txt"), b"beta\n")
    assert_file("merge: unrelated file kept", os.path.join(merged, "extra.txt"), b"keep me\n")

    # 3. Bad sources are hard errors.
    assert_rc("missing source exits 1", 1, os.path.join(tmp, "absent"), fresh)
    assert_rc("source that is a file exits 1", 1, os.path.join(src, "a.txt"), fresh)

    # 4. Usage errors (argparse exits 2).
    assert_rc("no args exits 2", 2)
    assert_rc("one arg exits 2", 2, src)
    assert_rc("three args exit 2", 2, src, fresh, fresh)


if __name__ == "__main__":
    sys.exit(main())
