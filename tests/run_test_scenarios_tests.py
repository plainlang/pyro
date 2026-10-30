#!/usr/bin/env python3
# Tests for skills/render-spec/scripts/test_scenarios.py.
#
# Usage: python3 tests/run_test_scenarios_tests.py   (normally via tests/run_tests.py)
# Exit:  0 all assertions passed, 1 something failed.
#
# The assertion helpers live in tests/harness.py: byte-exact comparisons, every
# child process run with sys.executable, no shell anywhere.
#
# Most cases build a throwaway module in a temporary folder, because what is under test is
# how the script pairs a module spec with the test plain files next to it - a shape that a
# fixed fixture tree can only show once.

import os
import shutil
import sys
import tempfile

import harness
from harness import assert_rc, assert_stdout, bad, ok, read, run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "render-spec", "scripts", "test_scenarios.py")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
EXPECTED = os.path.join(ROOT, "tests", "expected")

SAMPLE = os.path.join(FIXTURES, "sample.plain")
OLD_SYNTAX = os.path.join(FIXTURES, "old-syntax.plain")
EMPTY = os.path.join(FIXTURES, "no-sections.plain")

harness.set_script(SCRIPT)

SPEC = """---
description: A module built for one assertion.
---

***functional specs***

# alpha
The first functionality.

# beta
The second functionality.
"""


def write(path, text, newline="\n"):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "wb") as handle:
        handle.write(text.replace("\n", newline).encode("utf-8"))
    return path


def module(tmp, name, spec=SPEC):
    """A fresh folder holding `name`.plain, returned as the path of that spec."""
    folder = os.path.join(tmp, name)
    return write(os.path.join(folder, name + ".plain"), spec)


def test_file(spec, module_name, func_id, body, name=None, newline="\n"):
    """A test plain file under the spec's tests/ folder, at the conventional path."""
    folder = os.path.dirname(spec)
    leaf = (name or func_id) + ".plain"
    return write(os.path.join(folder, "tests", module_name, leaf), body, newline)


def main():
    tmp = tempfile.mkdtemp()
    try:
        run_suite(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return harness.finish()


def run_suite(tmp):
    # 1. The fixture tree end to end: one bound file, one empty file, one functionality with
    # no file at all - and the warnings that name the last two.
    assert_stdout("fixture module, grouped by func-id",
                  read(os.path.join(EXPECTED, "scenarios.txt")), SAMPLE)
    err = run(SAMPLE)[2]
    for want in (b"sample:list-widgets has no test scenario",
                 b"sample:delete-widget has no test plain file"):
        if want in err:
            ok("warns: %s" % want.decode("utf-8"))
        else:
            bad("warns: %s" % want.decode("utf-8"), err.decode("utf-8", "replace"))
    assert_rc("a missing or empty test plain file still exits 0", 0, SAMPLE)

    # 2. Scenario bodies are copied verbatim, whatever shape they have.
    spec = module(tmp, "shapes")
    test_file(spec, "shapes", "alpha", """---
module: shapes
func_id: alpha
---

***conformance tests***

> this comment is dropped

# prose-scenario
One sentence that says what happens.

# bullet-scenario
given:
  - :App: is running
then:
  - it answers

***acceptance tests***

# rejects-nothing
Nothing is rejected.
""")
    test_file(spec, "shapes", "beta", """---
module: shapes
func_id: beta
---

***conformance tests***
***acceptance tests***
""")
    want = b"""# Test scenarios of shapes

> The complete list of tests to implement for this module. The renderer
> implements these scenarios and no others; it never invents one.

## alpha

> from tests/shapes/alpha.plain

***conformance tests***

# prose-scenario
One sentence that says what happens.

# bullet-scenario
given:
  - :App: is running
then:
  - it answers

***acceptance tests***

# rejects-nothing
Nothing is rejected.

## beta

> from tests/shapes/beta.plain
> no test scenarios
"""
    assert_stdout("scenario bodies are copied verbatim", want, spec)

    # 3. CRLF test plain files yield byte-identical output.
    crlf = module(tmp, "crlf")
    test_file(crlf, "crlf", "alpha", """---
module: crlf
func_id: alpha
---

***conformance tests***

# one-scenario
It happens.

***acceptance tests***
""", newline="\r\n")
    lf = module(tmp, "lf")
    test_file(lf, "lf", "alpha", """---
module: lf
func_id: alpha
---

***conformance tests***

# one-scenario
It happens.

***acceptance tests***
""")
    if run(crlf)[1].replace(b"crlf", b"lf") == run(lf)[1]:
        ok("crlf test plain file matches the lf one")
    else:
        bad("crlf test plain file matches the lf one")

    # 4. Two files bound to one functionality merge; a repeated scenario-id is skipped.
    merged = module(tmp, "merged")
    test_file(merged, "merged", "alpha", """---
module: merged
func_id: alpha
---

***conformance tests***

# first
From the first file.

***acceptance tests***
""", name="a-first")
    test_file(merged, "merged", "alpha", """---
module: merged
func_id: alpha
---

***conformance tests***

# second
From the second file.

# first
A repeat of a scenario-id already taken.

***acceptance tests***
""", name="b-second")
    out, err = run(merged)[1:]
    if b"# first\nFrom the first file." in out and b"# second\nFrom the second file." in out:
        ok("two files bound to one functionality merge")
    else:
        bad("two files bound to one functionality merge", out.decode("utf-8", "replace"))
    if b"A repeat of a scenario-id" not in out and b"scenario-id `first` twice" in err:
        ok("a repeated scenario-id is skipped and warned about")
    else:
        bad("a repeated scenario-id is skipped and warned about")

    # 5. Files that do not belong to this module, or to no functionality of it.
    strays = module(tmp, "strays")
    test_file(strays, "strays", "alpha", """---
module: strays
func_id: alpha
---

***conformance tests***

# bound
It is bound.

***acceptance tests***
""")
    test_file(strays, "elsewhere", "alpha", """---
module: elsewhere
func_id: alpha
---

***conformance tests***

# other-module
It belongs to another module.

***acceptance tests***
""")
    write(os.path.join(os.path.dirname(strays), "tests", "notes.plain"), "no frontmatter here\n")
    out, err = run(strays)[1:]
    if b"other-module" not in out:
        ok("another module's test plain file is left out")
    else:
        bad("another module's test plain file is left out")
    if b"elsewhere" not in err:
        ok("another module's test plain file is passed over in silence")
    else:
        bad("another module's test plain file is passed over in silence")
    if b"has no `module:` and `func_id:`" in err:
        ok("a .plain file with no frontmatter warns and is skipped")
    else:
        bad("a .plain file with no frontmatter warns and is skipped", err.decode("utf-8", "replace"))
    assert_rc("a file of another module still exits 0", 0, strays)

    # 5b. A test plain file bound to no functionality stops the run: its scenarios were written
    # for something - a renamed or deleted functionality, or a typo - and would be thrown away.
    stale = module(tmp, "stale")
    test_file(stale, "stale", "gamma", """---
module: stale
func_id: gamma
---

***conformance tests***

# orphan
It names a functionality that is gone.

***acceptance tests***
""")
    assert_rc("a test plain file bound to no functionality exits 1", 1, stale)
    err = run(stale)[2]
    if b"is not a functionality of stale" in err and b"tests/stale/gamma.plain" in err:
        ok("the stale file and its func-id are named in the error")
    else:
        bad("the stale file and its func-id are named in the error",
            err.decode("utf-8", "replace"))

    # 6. The syntax pyro no longer renders: a nested block, or bullets with no func-id.
    assert_rc("a nested acceptance tests block exits 1", 1, OLD_SYNTAX)
    if b"nested ***acceptance tests***" in run(OLD_SYNTAX)[2]:
        ok("the nested block is named in the error")
    else:
        bad("the nested block is named in the error")
    bullets = module(tmp, "bullets", """---
description: Functional specs as bullets, the shape pyro no longer renders.
---

***functional specs***

- Create a :Widget: from a name.
""")
    assert_rc("functional specs without a func-id heading exit 1", 1, bullets)
    if b"no `# <func-id>` heading" in run(bullets)[2]:
        ok("the missing heading is named in the error")
    else:
        bad("the missing heading is named in the error")

    # 7. Malformed ids. A func-id names files and render steps, so it stops the run; a
    # scenario-id only labels a test, so it warns and the scenario is still rendered.
    shouty = module(tmp, "shouty", SPEC.replace("# alpha", "# Alpha Spec"))
    assert_rc("a func-id that is not lowercase-hyphen exits 1", 1, shouty)
    loud = module(tmp, "loud")
    test_file(loud, "loud", "alpha", """---
module: loud
func_id: alpha
---

***conformance tests***

# Shouty Scenario
It still renders.

***acceptance tests***
""")
    out, err = run(loud)[1:]
    if b"is not a scenario-id" in err and b"# Shouty Scenario" in out:
        ok("a malformed scenario-id warns and the scenario is kept")
    else:
        bad("a malformed scenario-id warns and the scenario is kept")

    # 8. A module with no functional specs at all is a warning, not a failure.
    assert_rc("a spec with no functional specs exits 0", 0, EMPTY)
    if b"no functional specs" in run(EMPTY)[2]:
        ok("the empty spec warns on stderr")
    else:
        bad("the empty spec warns on stderr")

    # 9. --output writes exactly what stdout would carry, UTF-8 with LF, parents created.
    via_stdout = run(SAMPLE)[1]
    via_output = os.path.join(tmp, "out", "scenarios.md")
    assert_rc("--output creates missing parent folders", 0, "--output", via_output, SAMPLE)
    if read(via_output) == via_stdout:
        ok("--output matches stdout byte for byte")
    else:
        bad("--output matches stdout byte for byte")
    if b"\r" not in read(via_output):
        ok("--output keeps LF endings")
    else:
        bad("--output keeps LF endings")
    utf8 = module(tmp, "utf8")
    test_file(utf8, "utf8", "alpha", """---
module: utf8
func_id: alpha
---

***conformance tests***

# naive-widget
A :Widget: named "Widžet" is created - naïve.

***acceptance tests***
""")
    utf8_out = os.path.join(tmp, "utf8.md")
    assert_rc("--output=<path> exits 0", 0, "--output=" + utf8_out, utf8)
    if "Widžet".encode("utf-8") in read(utf8_out):
        ok("--output keeps non-ASCII text UTF-8")
    else:
        bad("--output keeps non-ASCII text UTF-8")
    assert_rc("--output to unwritable path exits 1", 1,
              "--output", os.path.join(via_output, "y"), SAMPLE)

    # 10. Unreadable inputs exit 1, usage errors exit 2.
    assert_rc("missing spec exits 1", 1, os.path.join(FIXTURES, "does-not-exist.plain"))
    assert_rc("directory argument exits 1", 1, FIXTURES)
    assert_rc("no arguments exits 2", 2)
    assert_rc("two specs exit 2", 2, SAMPLE, EMPTY)
    assert_rc("--output without a path exits 2", 2, SAMPLE, "--output")
    assert_rc("--help exits 2", 2, "--help")


if __name__ == "__main__":
    sys.exit(main())
