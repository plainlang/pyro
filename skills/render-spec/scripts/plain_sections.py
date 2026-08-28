#!/usr/bin/env python3
# Extract one section from .plain specs and print the bodies to stdout.
#
# Usage: plain_sections.py [--include-filename] [--output <path>] <section> <spec.plain> [spec.plain ...]
#        plain_sections.py --check
#
# Sections (case-insensitive, `-` and `_` interchangeable):
#   definitions          defs        :plainDefinitions:
#   implementation-reqs  impl-reqs   impl    :plainImplementationReqs:
#   test-reqs                                :plainTestReqs:
#   functional-specs     func-specs  specs   :plainFunctionality:
#   acceptance-tests     acc-tests           :AcceptanceTests:
#   all                  all-sections everything   - every section, in file order
#
# The ***section*** marker itself is never printed, except for `all`, which keeps every
# section's own marker so the sections stay distinguishable. `>` comment lines are always
# dropped. With --include-filename each body is preceded by a "## <path>" heading.
#
# --output <path> (or --output=<path>) writes the result to <path> instead of stdout, so
# callers never need shell redirection. Windows PowerShell 5.1 writes UTF-16LE for `>` and
# `>>`, which corrupts files that later steps read back, so redirecting here rather than in
# the calling shell keeps the output UTF-8/LF on every platform. Warnings stay on stderr.
#
# --check takes no other arguments: it verifies the interpreter is a usable Python 3, prints
# "ok" and exits 0, so a caller can test-drive this script before relying on it. It returns
# before the --output redirect, so --output is ignored with --check.
#
# Portability: the standard library only, Python 3.8+, no shell and no awk - so the same
# command line works from sh, PowerShell and cmd alike. Everything is written as bytes to
# keep the output UTF-8 with LF endings even on a Windows console, whose text streams would
# otherwise re-encode to cp1252 and translate \n to \r\n.
#
# Exit: 0 ok (a missing section only warns on stderr), 1 unreadable file or unwritable
#       --output path, 2 usage error / unknown section.

import os
import re
import sys

# Deliberately no f-strings anywhere in this file: it has to stay parseable by Python 2 so
# that a probe landing on an old `python` reaches this guard and gets a clear message instead
# of a SyntaxError traceback.
if sys.version_info < (3, 8):
    sys.stderr.write(
        "plain_sections.py: error: Python 3.8 or newer is required, found %s\n"
        % ".".join(str(part) for part in sys.version_info[:3])
    )
    sys.exit(1)

PROG = os.path.basename(sys.argv[0])

USAGE = """usage: %(prog)s [--include-filename] [--output <path>] <section> <spec.plain> [spec.plain ...]
       %(prog)s --check

sections (case-insensitive, - and _ interchangeable):
  definitions          defs       :plainDefinitions:
  implementation-reqs  impl-reqs  impl    :plainImplementationReqs:
  test-reqs                               :plainTestReqs:
  functional-specs     func-specs specs   :plainFunctionality:
  acceptance-tests     acc-tests          :AcceptanceTests:
  all                  all-sections everything
"""

# Every alias, normalized, mapped to the canonical section name the parser matches on.
SECTIONS = {
    "definitions": "definitions",
    "defs": "definitions",
    "plaindefinitions": "definitions",
    "implementation reqs": "implementation reqs",
    "impl reqs": "implementation reqs",
    "impl": "implementation reqs",
    "plainimplementationreqs": "implementation reqs",
    "test reqs": "test reqs",
    "plaintestreqs": "test reqs",
    "functional specs": "functional specs",
    "func specs": "functional specs",
    "specs": "functional specs",
    "plainfunctionality": "functional specs",
    "acceptance tests": "acceptance tests",
    "acc tests": "acceptance tests",
    "acceptancetests": "acceptance tests",
    "all": "all",
    "all sections": "all",
    "everything": "all",
}

COMMENT_RE = re.compile(r"^[ \t]*>")
BLANK_RE = re.compile(r"^[ \t]*$")
MARKER_RE = re.compile(r"^[ \t]*\*\*\*(.*)\*\*\*[ \t]*$")
SPEC_ITEM_RE = re.compile(r"^-[ \t]")
TRAILING_WS_RE = re.compile(r"[ \t]+$")


def byte_sink(stream):
    """The binary writer under a text stream - or the stream itself when it already is one."""
    return getattr(stream, "buffer", stream)


def write_text(sink, text):
    """Write text as UTF-8 bytes, bypassing any encoding and newline translation on the way."""
    try:
        sink.write(text.encode("utf-8", "surrogateescape"))
    except TypeError:  # a text-only stream substituted by a caller
        sink.write(text)
    sink.flush()


def error(message):
    write_text(byte_sink(sys.stderr), "%s: error: %s\n" % (PROG, message))


def warning(message):
    write_text(byte_sink(sys.stderr), "%s: warning: %s\n" % (PROG, message))


def usage():
    write_text(byte_sink(sys.stderr), USAGE % {"prog": PROG})
    sys.exit(2)


def normalize_section(name):
    """Lowercase, - / _ -> space, collapse and trim whitespace, strip the colons of :Concept:."""
    name = " ".join(name.lower().replace("_", " ").replace("-", " ").split())
    if name.startswith(":"):
        name = name[1:]
    if name.endswith(":"):
        name = name[:-1]
    return name


def marker_name(line):
    """Section name of a ***marker*** line, normalized; None if the line is not a marker."""
    match = MARKER_RE.match(line)
    if match is None:
        return None
    name = re.sub(r"[ \t]+", " ", match.group(1).lower()).strip(" ")
    if name == "":  # a bare ****** is not a section marker
        return None
    return name


def indent_of(line):
    width = 0
    while width < len(line) and line[width] in " \t":
        width += 1
    return width


def dedent(line, width):
    return line[min(indent_of(line), width):]


def read_lines(path):
    """Records exactly as awk would see them: split on \\n only, one trailing \\r stripped."""
    handle = open(path, "r", encoding="utf-8", errors="surrogateescape", newline="")
    try:
        text = handle.read()
    finally:
        handle.close()
    if text == "":
        return []
    if text.endswith("\n"):
        text = text[:-1]
    return [line[:-1] if line.endswith("\r") else line for line in text.split("\n")]


def extract(path, want, show_path):
    """The body of `want` in `path`, newline-terminated; None when the section is absent."""
    buf = []
    pending = 0  # blank lines held back, so a trailing run never reaches the output
    in_section = False
    in_fs = False
    in_block = False
    block_indent = 0
    block_content = False
    parent = ""
    last_parent = ""

    def flush_blanks():
        for _ in range(pending):
            buf.append("")

    for line in read_lines(path):
        marker = marker_name(line)
        col0 = line.startswith("***")

        if want == "acceptance tests":
            if marker is not None and col0:  # a top-level section starts
                in_fs = marker == "functional specs"
                in_block = False
                continue
            if not in_fs:
                continue

            if marker == "acceptance tests":  # nested, indented under one spec
                in_block = True
                block_indent = indent_of(line)
                pending = 0
                block_content = False
                if parent != "" and parent != last_parent:
                    if buf:
                        buf.append("")
                    buf.append(parent)
                    last_parent = parent
                continue
            if marker is not None:
                in_block = False
                continue

            if in_block:
                if BLANK_RE.match(line):
                    pending += 1
                    continue
                if indent_of(line) >= block_indent:
                    if COMMENT_RE.match(line):
                        continue
                    if block_content:
                        flush_blanks()
                    pending = 0  # drop blank lines right after the marker
                    block_content = True
                    buf.append(dedent(line, block_indent))
                    continue
                in_block = False  # dedented out of the block; reconsider line

            if SPEC_ITEM_RE.match(line):  # the functional spec this block belongs to
                parent = TRAILING_WS_RE.sub("", line)
            continue

        # Top-level section mode.
        if marker is not None and col0:
            if want == "all":
                if buf:
                    buf.append("")  # blank line before each new section
                buf.append(line)  # keep the ***marker*** verbatim
                in_section = True
                pending = 0
            elif marker == want:
                in_section = True
                pending = 0
            elif in_section:
                in_section = False
            continue
        if not in_section:
            continue
        if COMMENT_RE.match(line):
            continue
        if BLANK_RE.match(line):
            if buf:
                pending += 1
            continue
        flush_blanks()
        pending = 0
        buf.append(line)

    while buf and BLANK_RE.match(buf[-1]):
        buf.pop()
    if not buf:
        return None

    head = ["## " + path, ""] if show_path else []
    return "\n".join(head + buf) + "\n"


def parse_args(argv):
    """Options are recognized wherever they appear, including after the positionals."""
    show_path = False
    out = None
    check_only = False
    positional = []

    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--include-filename":
            show_path = True
        elif arg == "--check":
            check_only = True
        elif arg == "--output":
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

    return show_path, out, check_only, positional


def main(argv):
    show_path, out, check_only, positional = parse_args(argv)

    # --check proves the interpreter is a usable Python 3; anything older already exited at
    # the version guard above, so reaching here is the answer.
    if check_only:
        write_text(byte_sink(sys.stdout), "ok\n")
        return 0

    if len(positional) < 2:
        usage()

    section_arg = positional[0]
    want = SECTIONS.get(normalize_section(section_arg))
    if want is None:
        error("unknown section: %s" % section_arg)
        usage()

    # Open once, here, so every write below lands in the file. Truncating up front makes an
    # unwritable path a clean error before any spec is read.
    if out is None:
        sink = byte_sink(sys.stdout)
        handle = None
    else:
        try:
            handle = open(out, "wb")
        except (IOError, OSError):
            error("cannot write %s" % out)
            return 1
        sink = handle

    exit_status = 0
    printed = False
    try:
        for path in positional[1:]:
            if os.path.isdir(path) or not os.access(path, os.R_OK):
                error("cannot read %s" % path)
                exit_status = 1
                continue

            try:
                body = extract(path, want, show_path)
            except (IOError, OSError):
                error("cannot read %s" % path)
                exit_status = 1
                continue

            if body is None:
                if want == "all":
                    warning("no sections in %s" % path)
                else:
                    warning("no '%s' in %s" % (want, path))
                continue

            if printed:
                write_text(sink, "\n")
            write_text(sink, body)
            printed = True
    finally:
        if handle is not None:
            handle.close()

    return exit_status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
