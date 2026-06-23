#!/bin/sh
# Extract one section from .plain specs and print the bodies to stdout.
#
# Usage: plain-sections.sh [--include-filename] <section> <spec.plain> [spec.plain ...]
#
# Sections (case-insensitive, `-` and `_` interchangeable):
#   definitions          defs        :plainDefinitions:
#   implementation-reqs  impl-reqs   impl    :plainImplementationReqs:
#   test-reqs                                :plainTestReqs:
#   functional-specs     func-specs  specs   :plainFunctionality:
#   acceptance-tests     acc-tests           :AcceptanceTests:
#
# The ***section*** marker itself is never printed and `>` comment lines are dropped.
# With --include-filename each body is preceded by a "## <path>" heading.
#
# Exit: 0 ok (a missing section only warns on stderr), 1 unreadable file,
#       2 usage error / unknown section.

set -u

prog=$(basename "$0")

usage() {
    cat >&2 <<EOF
usage: $prog [--include-filename] <section> <spec.plain> [spec.plain ...]

sections (case-insensitive, - and _ interchangeable):
  definitions          defs       :plainDefinitions:
  implementation-reqs  impl-reqs  impl    :plainImplementationReqs:
  test-reqs                               :plainTestReqs:
  functional-specs     func-specs specs   :plainFunctionality:
  acceptance-tests     acc-tests          :AcceptanceTests:
EOF
    exit 2
}

# Pull --include-filename out of the argument list, wherever it appears.
show_path=0
argc=$#
while [ "$argc" -gt 0 ]; do
    arg=$1
    shift
    argc=$((argc - 1))
    case $arg in
        --include-filename) show_path=1 ;;
        -h | --help) usage ;;
        *) set -- "$@" "$arg" ;;
    esac
done

[ $# -ge 2 ] || usage

# Normalize the section argument: lowercase, - / _ -> space, collapse and trim
# whitespace, strip the colons of a :Concept: alias.
section_arg=$1
shift
norm=$(printf '%s' "$section_arg" |
    tr 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 'abcdefghijklmnopqrstuvwxyz' |
    tr '_-' '  ' | tr -s ' ' |
    sed -e 's/^ *//' -e 's/ *$//' -e 's/^://' -e 's/:$//')

case $norm in
    definitions | defs | plaindefinitions)
        want="definitions" ;;
    "implementation reqs" | "impl reqs" | impl | plainimplementationreqs)
        want="implementation reqs" ;;
    "test reqs" | plaintestreqs)
        want="test reqs" ;;
    "functional specs" | "func specs" | specs | plainfunctionality)
        want="functional specs" ;;
    "acceptance tests" | "acc tests" | acceptancetests)
        want="acceptance tests" ;;
    *)
        printf '%s: error: unknown section: %s\n' "$prog" "$section_arg" >&2
        usage ;;
esac

extract() {
    awk -v want="$want" -v path="$2" -v show_path="$1" '
    function is_comment(line) {
        return line ~ /^[ \t]*>/
    }
    # Section name of a ***marker*** line, normalized; "" if the line is not a marker.
    function marker_name(line,   s) {
        if (line !~ /^[ \t]*\*\*\*.*\*\*\*[ \t]*$/) return ""
        s = line
        sub(/^[ \t]*\*\*\*/, "", s)
        sub(/\*\*\*[ \t]*$/, "", s)
        s = tolower(s)
        gsub(/[ \t]+/, " ", s)
        sub(/^ /, "", s)
        sub(/ $/, "", s)
        return s
    }
    function indent_of(line,   s) {
        s = line
        sub(/[^ \t].*$/, "", s)
        return length(s)
    }
    function dedent(line, width,   i) {
        i = indent_of(line)
        if (i > width) i = width
        return substr(line, i + 1)
    }
    # Blank lines are buffered as pending so a trailing run never reaches the output.
    function flush_blanks() {
        while (pending > 0) { buf[++n] = ""; pending-- }
    }

    BEGIN { n = 0; pending = 0; parent = ""; last_parent = "" }

    {
        line = $0
        sub(/\r$/, "", line)
        m = marker_name(line)
        col0 = (line ~ /^\*\*\*/)

        if (want == "acceptance tests") {
            if (m != "" && col0) {          # a top-level section starts
                in_fs = (m == "functional specs")
                in_block = 0
                next
            }
            if (!in_fs) next

            if (m == "acceptance tests") {  # nested, indented under one spec
                in_block = 1
                block_indent = indent_of(line)
                pending = 0
                block_content = 0
                if (parent != "" && parent != last_parent) {
                    if (n > 0) buf[++n] = ""
                    buf[++n] = parent
                    last_parent = parent
                }
                next
            }
            if (m != "") { in_block = 0; next }

            if (in_block) {
                if (line ~ /^[ \t]*$/) { pending++; next }
                if (indent_of(line) >= block_indent) {
                    if (is_comment(line)) next
                    if (block_content) flush_blanks()
                    else pending = 0        # drop blank lines right after the marker
                    block_content = 1
                    buf[++n] = dedent(line, block_indent)
                    next
                }
                in_block = 0                # dedented out of the block; reconsider line
            }
            if (line ~ /^-[ \t]/) {         # the functional spec this block belongs to
                parent = line
                sub(/[ \t]+$/, "", parent)
            }
            next
        }

        # Top-level section mode.
        if (m != "" && col0) {
            if (m == want) { in_section = 1; pending = 0 }
            else if (in_section) in_section = 0
            next
        }
        if (!in_section) next
        if (is_comment(line)) next
        if (line ~ /^[ \t]*$/) { if (n > 0) pending++; next }
        flush_blanks()
        buf[++n] = line
    }

    END {
        while (n > 0 && buf[n] ~ /^[ \t]*$/) n--
        if (n == 0) exit 3
        if (show_path == 1) {
            print "## " path
            print ""
        }
        for (i = 1; i <= n; i++) print buf[i]
    }
    ' "$2"
}

exit_status=0
printed=0

for f in "$@"; do
    if [ -d "$f" ] || [ ! -r "$f" ]; then
        printf '%s: error: cannot read %s\n' "$prog" "$f" >&2
        exit_status=1
        continue
    fi

    body=$(extract "$show_path" "$f")
    rc=$?

    if [ "$rc" -eq 3 ]; then
        printf "%s: warning: no '%s' in %s\n" "$prog" "$want" "$f" >&2
    elif [ "$rc" -ne 0 ]; then
        printf '%s: error: failed to parse %s\n' "$prog" "$f" >&2
        exit_status=1
    else
        [ "$printed" -eq 0 ] || printf '\n'
        printf '%s\n' "$body"
        printed=1
    fi
done

exit $exit_status
