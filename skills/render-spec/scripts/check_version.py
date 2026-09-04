#!/usr/bin/env python3
# Report the render-spec skill's own version and whether a newer stable
# release has been published.
#
# Usage: check_version.py current [--skill-md <path>]
#        check_version.py latest  [--url <url>]
#        check_version.py check   [--skill-md <path>] [--url <url>]
#        check_version.py --check
#
# current  prints the version this copy of the skill ships with, read from
#          the `metadata: version:` field of the SKILL.md next to this script.
# latest   prints the latest published stable version, read from the
#          [project] version in pyproject.toml on the repository's main
#          branch. The release workflow fast-forwards main only when a stable
#          release is published, so main's pyproject version IS the latest
#          stable release - no git and no GitHub API (and its rate limits)
#          needed. Exits 1 if it cannot be determined.
# check    prints both plus a verdict, one `key: value` per line:
#              current: 0.1.0
#              latest: 0.2.0
#              status: update-available
#          status is one of:
#              update-available  a newer stable release is published
#              up-to-date        this copy is the latest stable release
#              ahead             this copy is newer (a dev or rc checkout)
#              unknown           the latest version could not be determined
#          Unlike `latest`, network trouble is not an error here: check
#          degrades to `latest: unknown` / `status: unknown` and exits 0,
#          because an update hint must never break a render.
#
# --skill-md <path> and --url <url> (also the = spellings) override where the
# current and latest versions are read from; the tests use them with fixture
# files and file:// URLs.
#
# --check takes no other arguments: it verifies the interpreter is a usable
# Python 3, prints "ok" and exits 0, so a caller can test-drive this script
# before relying on it.
#
# Versions are `X.Y.Z` with an optional `-rc.N` prerelease, and a release
# outranks its own release candidates: 0.1.0 < 0.2.0-rc.1 < 0.2.0.
#
# Portability: the standard library only, Python 3.8+, no shell, no git. The
# output is written as bytes to stay UTF-8 with LF endings on every platform.
#
# Exit: 0 ok, 1 SKILL.md missing or without a parseable version (or `latest`
#       could not be determined), 2 usage error.

import os
import re
import sys

# Deliberately no f-strings anywhere in this file: it has to stay parseable by Python 2 so
# that a probe landing on an old `python` reaches this guard and gets a clear message instead
# of a SyntaxError traceback.
if sys.version_info < (3, 8):
    sys.stderr.write(
        "check_version.py: error: Python 3.8 or newer is required, found %s\n"
        % ".".join(str(part) for part in sys.version_info[:3])
    )
    sys.exit(1)

PROG = os.path.basename(sys.argv[0])

LATEST_URL = "https://raw.githubusercontent.com/plainlang/pyro/main/pyproject.toml"
FETCH_TIMEOUT = 10  # seconds
SKILL_MD = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "SKILL.md")
)

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?$")

USAGE = """usage: %(prog)s current [--skill-md <path>]
       %(prog)s latest  [--url <url>]
       %(prog)s check   [--skill-md <path>] [--url <url>]
       %(prog)s --check

current  print this skill's own version (from SKILL.md metadata)
latest   print the latest published stable version (pyproject.toml on main)
check    print both and a status: update-available | up-to-date | ahead | unknown
""" % {"prog": PROG}


def emit(text):
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def version_key(version):
    """Sort key for a version string, or None if it is not one we understand.

    A release sorts above its own release candidates: (X, Y, Z, 1, 0) for a
    release, (X, Y, Z, 0, N) for X.Y.Z-rc.N.
    """
    match = VERSION_RE.match(version)
    if not match:
        return None
    major, minor, patch, rc = match.groups()
    if rc is None:
        return (int(major), int(minor), int(patch), 1, 0)
    return (int(major), int(minor), int(patch), 0, int(rc))


def read_current(skill_md):
    """The version from SKILL.md's frontmatter, or None.

    The stdlib has no YAML parser, so this scans only the frontmatter block
    (between the opening and closing --- lines) for the one indented
    `version:` key, which lives under `metadata:`.
    """
    try:
        with open(skill_md, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    frontmatter = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        frontmatter.append(line)
    match = re.search(
        r"(?m)^[ \t]+version:[ \t]*[\"']?([^\"'\s]+)", "\n".join(frontmatter)
    )
    return match.group(1) if match else None


def fetch_latest(url):
    """The [project] version from the pyproject.toml at `url`, or None.

    Any failure - offline, DNS, TLS, HTTP error, timeout, garbage payload,
    a version string that does not parse - just makes the latest version
    unknown; the caller decides how loud to be. A non-None result is always
    a valid version.
    """
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as response:
            text = response.read().decode("utf-8", "replace")
    except Exception:
        return None
    project = re.search(r"(?ms)^\[project\][ \t]*\r?$(.*?)(?=^\[|\Z)", text)
    if not project:
        return None
    match = re.search(r"(?m)^version[ \t]*=[ \t]*[\"']([^\"']+)[\"']", project.group(1))
    if not match or version_key(match.group(1)) is None:
        return None
    return match.group(1)


def compare(current, latest):
    if latest is None:
        return "unknown"
    current_key = version_key(current)
    latest_key = version_key(latest)
    if latest_key > current_key:
        return "update-available"
    if latest_key < current_key:
        return "ahead"
    return "up-to-date"


def parse_args(argv):
    command = None
    options = {"--skill-md": SKILL_MD, "--url": LATEST_URL}
    index = 0
    while index < len(argv):
        name, equals, value = argv[index].partition("=")
        if name in options:
            if not equals:
                index += 1
                if index >= len(argv):
                    usage_error("%s needs a value" % name)
                value = argv[index]
            options[name] = value
        elif name in ("current", "latest", "check", "--check") and not equals:
            if command is not None:
                usage_error("only one command allowed, got %r after %r" % (name, command))
            command = name
        else:
            usage_error("unknown argument %r" % argv[index])
        index += 1
    if command is None:
        usage_error("a command is required")
    return command, options["--skill-md"], options["--url"]


def usage_error(message):
    sys.stderr.write("%s: error: %s\n\n%s" % (PROG, message, USAGE))
    sys.exit(2)


def main(argv):
    command, skill_md, url = parse_args(argv)

    if command == "--check":
        emit("ok\n")
        return 0

    if command == "latest":
        latest = fetch_latest(url)
        if latest is None:
            sys.stderr.write(
                "%s: error: could not determine the latest published version\n" % PROG
            )
            return 1
        emit(latest + "\n")
        return 0

    current = read_current(skill_md)
    if current is None or version_key(current) is None:
        sys.stderr.write(
            "%s: error: no parseable metadata version in %s\n" % (PROG, skill_md)
        )
        return 1

    if command == "current":
        emit(current + "\n")
        return 0

    # check: never fail on account of the network.
    latest = fetch_latest(url)
    emit(
        "current: %s\nlatest: %s\nstatus: %s\n"
        % (current, latest or "unknown", compare(current, latest))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
