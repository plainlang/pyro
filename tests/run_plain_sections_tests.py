#!/usr/bin/env python3
# Tests for skills/render-spec/scripts/plain_sections.py.
#
# Usage: python3 tests/run_plain_sections_tests.py   (normally via tests/run_tests.py)
# Exit:  0 all assertions passed, 1 something failed.
#
# The assertion helpers live in tests/harness.py: byte-exact comparisons, every
# child process run with sys.executable, no shell anywhere.
#
# Note on tests/expected/all.txt: the two blank lines after ***definitions*** are intended.
# Comment lines are dropped but the blank lines around them are not collapsed, so a `>` comment
# framed by blanks leaves both blanks behind. Harmless for callers; asserted so a future change
# to the blank-line buffering cannot pass unnoticed.

import os
import shutil
import sys
import tempfile

import harness
from harness import assert_rc, assert_stdout, bad, ok, read, run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "render-spec", "scripts", "plain_sections.py")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
EXPECTED = os.path.join(ROOT, "tests", "expected")

SAMPLE = os.path.join(FIXTURES, "sample.plain")
CRLF = os.path.join(FIXTURES, "sample-crlf.plain")
SECOND = os.path.join(FIXTURES, "second.plain")
EMPTY = os.path.join(FIXTURES, "no-sections.plain")

harness.set_script(SCRIPT)


def expect(name):
    return read(os.path.join(EXPECTED, name + ".txt"))


def main():
    tmp = tempfile.mkdtemp()
    try:
        run_suite(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return harness.finish()


def run_suite(tmp):
    # 1. Every section against its hand-authored expectation.
    for sec in ("defs", "impl-reqs", "test-reqs", "func-specs", "acc-tests", "all"):
        assert_stdout("section %s" % sec, expect(sec), sec, SAMPLE)

    # 2. Section aliases all resolve to the same body.
    for alias in ("definitions", "DEFS", ":plainDefinitions:", "Definitions"):
        assert_stdout("alias %s" % alias, expect("defs"), alias, SAMPLE)
    assert_stdout("alias impl", expect("impl-reqs"), "impl", SAMPLE)
    assert_stdout("alias implementation_reqs", expect("impl-reqs"), "implementation_reqs", SAMPLE)
    assert_stdout('alias "acceptance tests"', expect("acc-tests"), "acceptance tests", SAMPLE)
    assert_stdout("alias everything", expect("all"), "everything", SAMPLE)

    # 3. CRLF input yields byte-identical output to the LF fixture.
    assert_stdout("crlf fixture, all sections", expect("all"), "all", CRLF)
    assert_stdout("crlf fixture, acc-tests", expect("acc-tests"), "acc-tests", CRLF)

    # 4. --include-filename prefixes "## <path>" and a blank line.
    want_filename = ("## %s\n\n" % SAMPLE).encode("utf-8") + expect("defs")
    assert_stdout("--include-filename heading", want_filename, "--include-filename", "defs", SAMPLE)

    # 5. --output writes exactly what stdout would carry, in both spellings.
    via_stdout = run("all", SAMPLE)[1]
    via_output = os.path.join(tmp, "via-output")
    assert_rc("--output <path> exits 0", 0, "--output", via_output, "all", SAMPLE)
    if read(via_output) == via_stdout:
        ok("--output <path> matches stdout byte for byte")
    else:
        bad("--output <path> matches stdout byte for byte")
    via_output_eq = os.path.join(tmp, "via-output-eq")
    assert_rc("--output=<path> exits 0", 0, "--output=" + via_output_eq, "all", SAMPLE)
    if read(via_output_eq) == via_stdout:
        ok("--output=<path> matches stdout byte for byte")
    else:
        bad("--output=<path> matches stdout byte for byte")
    assert_rc("--output to unwritable path exits 1", 1,
              "--output", os.path.join(tmp, "no", "such", "dir", "x"), "defs", SAMPLE)

    # 5b. The written file is UTF-8 with LF endings on every platform. This is the reason
    # --output exists: PowerShell's own `>` would hand later steps UTF-16LE with CRLF.
    if b"\r" not in read(via_output):
        ok("--output keeps LF endings")
    else:
        bad("--output keeps LF endings")
    utf8_spec = os.path.join(tmp, "utf8.plain")
    with open(utf8_spec, "wb") as handle:
        handle.write("***definitions***\n\n- :Widžet: is a thing — naïve.\n".encode("utf-8"))
    utf8_out = os.path.join(tmp, "utf8.md")
    rc, out, _ = run("--output", utf8_out, "defs", utf8_spec)
    want_utf8 = "- :Widžet: is a thing — naïve.\n".encode("utf-8")
    if rc == 0 and read(utf8_out) == want_utf8:
        ok("--output keeps non-ASCII text UTF-8")
    else:
        bad("--output keeps non-ASCII text UTF-8", "got %r" % read(utf8_out))
    assert_stdout("stdout keeps non-ASCII text UTF-8", want_utf8, "defs", utf8_spec)

    # 6. Two specs in one call, separated by exactly one blank line.
    want_two = expect("defs") + b"\n" + b"- :Gadget: is another thing.\n"
    assert_stdout("two specs, one blank line between", want_two, "defs", SAMPLE, SECOND)

    # 7. --check probes the interpreter and says so.
    assert_rc("--check exits 0", 0, "--check")
    if run("--check")[1] == b"ok\n":
        ok("--check prints ok")
    else:
        bad("--check prints ok")
    unused = os.path.join(tmp, "unused")
    assert_rc("--check ignores a trailing --output", 0, "--check", "--output", unused)
    if os.path.exists(unused):
        bad("--check leaves --output path untouched")
    else:
        ok("--check leaves --output path untouched")

    # 8. Unreadable inputs exit 1.
    assert_rc("missing spec exits 1", 1, "defs", os.path.join(FIXTURES, "does-not-exist.plain"))
    assert_rc("directory argument exits 1", 1, "defs", FIXTURES)
    # ... but a readable spec later in the list is still printed.
    out = run("defs", os.path.join(FIXTURES, "does-not-exist.plain"), SAMPLE)[1]
    if out == expect("defs"):
        ok("unreadable spec does not suppress the readable one")
    else:
        bad("unreadable spec does not suppress the readable one")

    # 9. Usage errors exit 2.
    assert_rc("unknown section exits 2", 2, "nonsense", SAMPLE)
    assert_rc("no arguments exits 2", 2)
    assert_rc("section without a spec exits 2", 2, "defs")
    assert_rc("--output without a path exits 2", 2, "defs", SAMPLE, "--output")
    assert_rc("--help exits 2", 2, "--help")

    # 10. A missing section is a warning, not an error.
    assert_rc("missing section exits 0", 0, "defs", EMPTY)
    rc, out, err = run("defs", EMPTY)
    if out == b"" and err != b"":
        ok("missing section warns on stderr, stdout empty")
    else:
        bad("missing section warns on stderr, stdout empty")

    # 11. Flags are accepted after the positional arguments too.
    assert_stdout("flag after positionals", want_filename, "defs", SAMPLE, "--include-filename")


if __name__ == "__main__":
    sys.exit(main())
