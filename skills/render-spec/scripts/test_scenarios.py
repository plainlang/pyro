#!/usr/bin/env python3
# Collect the test scenarios of one module from its test plain files.
#
# Usage: test_scenarios.py [--output <path>] <module.plain>
#
# The scenarios of a functionality live in a test plain file, never in the spec plain file. A
# test plain file carries the frontmatter keys `module:` and `func_id:` and the two sections
# ***conformance tests*** and ***acceptance tests***, each holding `# <scenario-id>` scenarios.
#
# This script reads the `# <func-id>` headings of the module's ***functional specs***, scans
# `<module folder>/tests` for every .plain file, binds each one to a functionality by its
# frontmatter, merges the scenarios of all files bound to the same functionality, and prints
# them grouped by func-id in render order. The output is the complete and only list of tests
# the renderer implements for the module - it never invents a scenario of its own.
#
# A functionality with no test plain file, or one whose file holds no scenario, is a warning:
# the module still renders, that functionality just gets no conformance tests.
#
# --output <path> (or --output=<path>) writes the result to <path> instead of stdout, creating
# missing parent folders, for the same reason plain_sections.py has it: a Windows PowerShell
# redirect would hand later steps UTF-16LE. Warnings and errors stay on stderr.
#
# Portability: the standard library only, Python 3.8+, no shell - the same command line works
# from sh, PowerShell and cmd alike. Output is written as bytes to keep it UTF-8 with LF
# endings on every platform.
#
# Exit: 0 ok (missing or empty test plain files only warn), 1 a spec in the syntax pyro no
#       longer renders, a malformed id, an unreadable file or an unwritable --output path,
#       2 usage error.

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plain_sections  # noqa: E402  - the sibling script in this same folder
from plain_sections import byte_sink, extract, read_lines, write_text  # noqa: E402

PROG = os.path.basename(sys.argv[0])

USAGE = """usage: %(prog)s [--output <path>] <module.plain>
"""

# A func-id or a scenario-id: lowercase letters, digits and hyphens.
ID_RE = re.compile(r"^[a-z0-9-]+$")
HEADING_RE = re.compile(r"^#[ \t]+(.*?)[ \t]*$")
FRONT_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)[ \t]*:[ \t]*(.*?)[ \t]*$")

TESTS_FOLDER = "tests"


def error(message):
    write_text(byte_sink(sys.stderr), "%s: error: %s\n" % (PROG, message))


def warning(message):
    write_text(byte_sink(sys.stderr), "%s: warning: %s\n" % (PROG, message))


def usage():
    write_text(byte_sink(sys.stderr), USAGE % {"prog": PROG})
    sys.exit(2)


def show(path, start):
    """`path` relative to `start`, with forward slashes, so it reads the same on Windows."""
    try:
        return os.path.relpath(path, start).replace(os.sep, "/")
    except ValueError:  # a different drive on Windows
        return path.replace(os.sep, "/")


def frontmatter(path):
    """The `key: value` pairs of the YAML frontmatter; {} when the file has none."""
    lines = read_lines(path)
    if not lines or lines[0].strip() != "---":
        return {}
    pairs = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return pairs
        match = FRONT_KEY_RE.match(line)
        if match is not None:
            pairs[match.group(1)] = match.group(2).strip("'\"")
    return {}  # no closing marker: the file has no usable frontmatter


def scenarios(body, where):
    """[(scenario-id, [body lines])] in file order, from a section body or None."""
    found = []
    if body is None:
        return found
    for line in body.split("\n"):
        match = HEADING_RE.match(line)
        if match is not None:
            found.append((match.group(1), []))
        elif found:
            found[-1][1].append(line)
        elif line != "":
            warning("%s: text before the first `# <scenario-id>` heading is ignored" % where)
    for _, body in found:  # the blank lines that separated the scenarios
        while body and body[-1] == "":
            body.pop()
    return found


def func_ids(spec):
    """The func-ids of the module's ***functional specs***, in render order."""
    body = extract(spec, "functional specs", False)
    if body is None:
        warning("no functional specs in %s" % spec)
        return []

    lines = body.split("\n")
    for line in lines:
        if plain_sections.marker_name(line) == "acceptance tests":
            error(
                "%s holds a nested ***acceptance tests*** block. pyro renders the current "
                "syntax only: every functionality is a `# <func-id>` heading and its scenarios "
                "live in a test plain file under %s/." % (spec, TESTS_FOLDER)
            )
            return None

    found = []
    for line in lines:
        match = HEADING_RE.match(line)
        if match is None:
            continue
        if ID_RE.match(match.group(1)) is None:
            error("%s: `# %s` is not a func-id (lowercase letters, digits and hyphens)"
                  % (spec, match.group(1)))
            return None
        if match.group(1) in found:
            error("%s: the func-id `%s` is used twice" % (spec, match.group(1)))
            return None
        found.append(match.group(1))

    if not found:
        error(
            "%s has no `# <func-id>` heading in ***functional specs***. pyro renders the "
            "current syntax only: every functionality is a `# <func-id>` heading and its "
            "scenarios live in a test plain file under %s/." % (spec, TESTS_FOLDER)
        )
        return None
    return found


def test_plain_files(folder):
    """Every .plain file under `folder`, sorted, so the merge order is the same everywhere."""
    found = []
    for root, dirs, names in os.walk(folder):
        dirs.sort()
        for name in sorted(names):
            if name.endswith(".plain"):
                found.append(os.path.join(root, name))
    return found


def bind(spec, module, ids):
    """{func-id: [(path, conformance, acceptance)]} - the test plain files of each functionality."""
    folder = os.path.join(os.path.dirname(os.path.abspath(spec)), TESTS_FOLDER)
    bound = dict((func_id, []) for func_id in ids)
    if not os.path.isdir(folder):
        return bound

    for path in test_plain_files(folder):
        where = show(path, os.path.dirname(os.path.abspath(spec)))
        front = frontmatter(path)
        if "module" not in front or "func_id" not in front:
            warning("%s has no `module:` and `func_id:` frontmatter; skipped" % where)
            continue
        if front["module"] != module:
            continue  # a test plain file of another module
        if front["func_id"] not in bound:
            warning("%s names `%s`, which is not a functionality of %s; skipped"
                    % (where, front["func_id"], module))
            continue
        bound[front["func_id"]].append((
            where,
            scenarios(extract(path, "conformance tests", False), where),
            scenarios(extract(path, "acceptance tests", False), where),
        ))
    return bound


def section_lines(marker, merged):
    out = ["", marker]
    for scenario_id, body in merged:
        out.append("")
        out.append("# " + scenario_id)
        out.extend(body)
    return out


def merge(module, func_id, files):
    """The output block of one functionality, and whether it got any scenario."""
    out = ["## " + func_id]
    if not files:
        warning("%s:%s has no test plain file; it renders without conformance tests"
                % (module, func_id))
        out.append("")
        out.append("> no test plain file")
        return out, False

    out.append("")
    out.append("> from " + ", ".join(path for path, _, _ in files))

    merged = {"***conformance tests***": [], "***acceptance tests***": []}
    seen = {}
    for path, conformance, acceptance in files:
        for marker, found in (("***conformance tests***", conformance),
                              ("***acceptance tests***", acceptance)):
            for scenario_id, body in found:
                if ID_RE.match(scenario_id) is None:
                    warning("%s: `# %s` is not a scenario-id (lowercase letters, digits and "
                            "hyphens)" % (path, scenario_id))
                if scenario_id in seen:
                    warning("%s:%s has the scenario-id `%s` twice, in %s and %s; the second one "
                            "is skipped" % (module, func_id, scenario_id, seen[scenario_id], path))
                    continue
                seen[scenario_id] = path
                merged[marker].append((scenario_id, body))

    if not seen:
        warning("%s:%s has no test scenario; it renders without conformance tests"
                % (module, func_id))
        out.append("> no test scenarios")
        return out, False

    for marker in ("***conformance tests***", "***acceptance tests***"):
        if merged[marker]:
            out.extend(section_lines(marker, merged[marker]))
    return out, True


def report(module, ids, bound):
    out = ["# Test scenarios of " + module, ""]
    out.append("> The complete list of tests to implement for this module. The renderer")
    out.append("> implements these scenarios and no others; it never invents one.")
    for func_id in ids:
        out.append("")
        block = merge(module, func_id, bound[func_id])[0]
        out.extend(block)
    return "\n".join(out) + "\n"


def parse_args(argv):
    out = None
    positional = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--output":
            if not args:
                error("--output requires a path")
                usage()
            out = args.pop(0)
        elif arg.startswith("--output="):
            out = arg[len("--output="):]
            if out == "":
                error("--output requires a path")
                usage()
        elif arg in ("-h", "--help"):
            usage()
        else:
            positional.append(arg)
    return out, positional


def main(argv):
    out, positional = parse_args(argv)
    if len(positional) != 1:
        usage()

    spec = positional[0]
    if os.path.isdir(spec) or not os.access(spec, os.R_OK):
        error("cannot read %s" % spec)
        return 1

    try:
        ids = func_ids(spec)
    except (IOError, OSError):
        error("cannot read %s" % spec)
        return 1
    if ids is None:
        return 1

    module = os.path.basename(spec)
    if module.endswith(".plain"):
        module = module[:-len(".plain")]

    try:
        bound = bind(spec, module, ids)
    except (IOError, OSError):
        error("cannot read the test plain files of %s" % module)
        return 1

    text = report(module, ids, bound)

    if out is None:
        write_text(byte_sink(sys.stdout), text)
        return 0
    try:
        parent = os.path.dirname(out)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        handle = open(out, "wb")
    except (IOError, OSError):
        error("cannot write %s" % out)
        return 1
    try:
        write_text(handle, text)
    finally:
        handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
