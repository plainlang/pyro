#!/usr/bin/env python3
# Tests for skills/render-spec/scripts/check_version.py.
#
# Usage: python3 tests/run_check_version_tests.py   (normally via tests/run_tests.py)
# Exit:  0 all assertions passed, 1 something failed.
#
# The assertion helpers live in tests/harness.py: byte-exact comparisons, every
# child process run with sys.executable, no shell anywhere. The network is never
# touched: `latest` is exercised through --url with file:// URLs pointing at
# fixture pyproject.toml files written into a temp dir, so the suite passes
# offline on every platform the skill claims to support.

import os
import pathlib
import re
import shutil
import sys
import tempfile

import harness
from harness import assert_rc, assert_stdout, bad, ok, run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "render-spec", "scripts", "check_version.py")

harness.set_script(SCRIPT)


def write_skill_md(tmp, name, version):
    path = os.path.join(tmp, name)
    with open(path, "wb") as handle:
        handle.write(
            (
                "---\n"
                "name: render-spec\n"
                "description: >-\n"
                "  A fixture. Mentions version: 9.9.9 to prove only the key counts.\n"
                "metadata:\n"
                '  version: "%s"\n'
                "---\n"
                "\n"
                "# Body\n"
                "version: 8.8.8 outside the frontmatter must be ignored.\n" % version
            ).encode("utf-8")
        )
    return path


def write_pyproject(tmp, name, version, project_section=True):
    # Decoy version keys outside [project] prove the parser scopes correctly.
    path = os.path.join(tmp, name)
    body = "[build-system]\nrequires = []\n\n"
    if project_section:
        body += '[project]\nname = "pyro"\nversion = "%s"\n\n' % version
    body += '[tool.semantic_release]\ntag_format = "v{version}"\nversion = "7.7.7"\n'
    with open(path, "wb") as handle:
        handle.write(body.encode("utf-8"))
    return pathlib.Path(path).as_uri()


def check_wants(current, latest, status):
    return ("current: %s\nlatest: %s\nstatus: %s\n" % (current, latest, status)).encode(
        "utf-8"
    )


def main():
    tmp = tempfile.mkdtemp()
    try:
        run_suite(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return harness.finish()


def run_suite(tmp):
    skill_010 = write_skill_md(tmp, "skill-0.1.0.md", "0.1.0")
    skill_rc = write_skill_md(tmp, "skill-rc.md", "0.2.0-rc.1")
    url_010 = write_pyproject(tmp, "py-0.1.0.toml", "0.1.0")
    url_020 = write_pyproject(tmp, "py-0.2.0.toml", "0.2.0")
    url_no_project = write_pyproject(tmp, "py-none.toml", "", project_section=False)
    url_garbage = write_pyproject(tmp, "py-garbage.toml", "not.a.version")
    url_missing = pathlib.Path(os.path.join(tmp, "no-such-file.toml")).as_uri()

    # 1. Interpreter probe.
    assert_stdout("--check prints ok", b"ok\n", "--check")

    # 2. current: fixture and the real SKILL.md this repo ships.
    assert_stdout("current from fixture", b"0.1.0\n", "current", "--skill-md", skill_010)
    assert_stdout("current, = spelling", b"0.1.0\n", "current", "--skill-md=" + skill_010)
    rc, out, err = run("current")
    if rc == 0 and re.match(rb"^\d+\.\d+\.\d+(-rc\.\d+)?\n$", out):
        ok("current from the shipped SKILL.md")
    else:
        bad(
            "current from the shipped SKILL.md",
            "exit %d, stdout %r, stderr %r" % (rc, out, err),
        )

    # 3. latest: scoped to [project], loud when unavailable.
    assert_stdout("latest from fixture", b"0.2.0\n", "latest", "--url", url_020)
    assert_rc("latest with unreachable url exits 1", 1, "latest", "--url", url_missing)
    assert_rc("latest without [project] exits 1", 1, "latest", "--url", url_no_project)
    assert_rc("latest with unparseable version exits 1", 1, "latest", "--url", url_garbage)

    # 4. check: every status.
    assert_stdout(
        "check update-available",
        check_wants("0.1.0", "0.2.0", "update-available"),
        "check", "--skill-md", skill_010, "--url", url_020,
    )
    assert_stdout(
        "check up-to-date",
        check_wants("0.1.0", "0.1.0", "up-to-date"),
        "check", "--skill-md", skill_010, "--url", url_010,
    )
    assert_stdout(
        "check ahead (rc newer than stable)",
        check_wants("0.2.0-rc.1", "0.1.0", "ahead"),
        "check", "--skill-md", skill_rc, "--url", url_010,
    )
    assert_stdout(
        "check rc loses to its own release",
        check_wants("0.2.0-rc.1", "0.2.0", "update-available"),
        "check", "--skill-md", skill_rc, "--url", url_020,
    )

    # 5. check degrades softly: still exit 0, status unknown.
    assert_stdout(
        "check with unreachable url degrades to unknown",
        check_wants("0.1.0", "unknown", "unknown"),
        "check", "--skill-md", skill_010, "--url", url_missing,
    )
    assert_stdout(
        "check without [project] degrades to unknown",
        check_wants("0.1.0", "unknown", "unknown"),
        "check", "--skill-md", skill_010, "--url", url_no_project,
    )
    assert_stdout(
        "check with unparseable latest degrades to unknown",
        check_wants("0.1.0", "unknown", "unknown"),
        "check", "--skill-md", skill_010, "--url", url_garbage,
    )

    # 6. A broken own version is a hard error.
    assert_rc(
        "missing SKILL.md exits 1",
        1,
        "check", "--skill-md", os.path.join(tmp, "absent.md"), "--url", url_010,
    )
    no_version = write_skill_md(tmp, "skill-bad.md", "not-a-version")
    assert_rc(
        "unparseable version exits 1",
        1,
        "check", "--skill-md", no_version, "--url", url_010,
    )

    # 7. Usage errors.
    assert_rc("no command exits 2", 2)
    assert_rc("unknown command exits 2", 2, "frobnicate")
    assert_rc("two commands exit 2", 2, "check", "latest")
    assert_rc("--skill-md without value exits 2", 2, "current", "--skill-md")
    assert_rc("--check with a command exits 2", 2, "check", "--check")


if __name__ == "__main__":
    sys.exit(main())
