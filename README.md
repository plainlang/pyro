# Pyro

Pyro is an open-source renderer for ***plain specifications. It's packaged as an agentic skill
that renders a `.plain` spec into working and tested code.

Invoke it from your agent with:

```
/pyro-render <plain-spec-filename>
```

The skill resolves the modules the target spec requires or imports, renders them
in dependency order, and writes:
* intermediate implementation code to `plain_modules/`
* conformance tests to `conf_tests/`
* the target module's output to `dist/`

## Installation

If you have Node available, install the skill with the `npx skills` tool:

```bash
cd project
npx skills add https://github.com/Codeplain-ai/pyro --agent claude-code
```

### Manual installation

Copy the `pyro-render` folder from this repo into your agent's skills folder.
For Claude Code that is `.claude/skills/` in your project.

## Using the skill

Once the skill is installed, start Claude from your project's working dir and prompt `/pyro-render <plain-spec-filename>`.

## Requirements

Rendering needs **Python 3.8 or newer** on the machine — nothing else, no
third-party packages. The skill finds the interpreter itself, trying `py -3`,
`python3`, and `python` in that order, and stops with a clear message if none of
them works.

## Tests

The helper scripts have a test suite that runs anywhere Python does:

```bash
python3 tests/run_tests.py
```