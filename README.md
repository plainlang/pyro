# Pyro

Pyro is an open-source renderer for ***plain specifications. It's packaged as an agentic skill
that renders a `.plain` spec into working and tested code.

Invoke it from your agent with:

```
/pyro:render-spec <plain-spec-filename>
```

The skill resolves the modules the target spec requires or imports, renders them
in dependency order, and writes:
* intermediate implementation code to `plain_modules/`
* conformance tests to `conf_tests/`
* the target module's output to `dist/`

## Installation

### Claude Code plugin (recommended)

```
/plugin marketplace add plainlang/pyro
/plugin install pyro@pyro
```

Plugin skills are namespaced by their plugin, so invoke this one as
`/pyro:render-spec <plain-spec-filename>`.

To stay current automatically, turn on `autoUpdate` for the marketplace in
`.claude/settings.json` (or `~/.claude/settings.json` for every project):

```json
{
  "extraKnownMarketplaces": {
    "pyro": {
      "source": { "source": "github", "repo": "plainlang/pyro" },
      "autoUpdate": true
    }
  }
}
```

Claude Code then refreshes the marketplace and its installed plugins on startup.
To update by hand instead:

```bash
claude plugin marketplace update pyro
claude plugin update pyro
```

Both also live in the in-session `/plugin` menu. A restart is needed either way
before the new version loads.

### npx skills

If you have Node available, install the skill with the `npx skills` tool:

```bash
cd project
npx skills add https://github.com/plainlang/pyro --agent claude-code
```

This copies the skill straight into your agent's skills folder, so it is not
namespaced — invoke it as `/render-spec <plain-spec-filename>`. To update:

```bash
npx skills update render-spec
```

Add `-g` for a global install, or `-p` to limit the update to the current
project.

### Manual installation

Copy the `skills/render-spec` folder from this repo into your agent's skills folder.
For Claude Code that is `.claude/skills/` in your project. Invoke it as
`/render-spec <plain-spec-filename>`, and update it by pulling this repo and
copying the folder again.

## Using the skill

Start your agent from the project's working dir and prompt it with the spec you
want rendered. The exact form depends on how you installed:

| Install | Invocation |
| --- | --- |
| Claude Code plugin | `/pyro:render-spec <plain-spec-filename>` |
| npx skills or manual copy | `/render-spec <plain-spec-filename>` |

The skill reports its own version on each run, so you can tell which build is
loaded.

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

## Branching and releases

`dev` and `main` share one linear history; `main` is a pointer that only ever
fast-forwards to a commit already on `dev`, so its HEAD is always the latest
stable release — which is what plugin installs fetch.

- **Features** land on `dev` via rebase-merged PRs with
  [conventional commits](https://www.conventionalcommits.org) (never target
  `main`).
- **Every release is a bot-maintained PR** into `dev` holding the next
  version's file stamps and changelog; **rebase-merge it** to release. The
  commit is tagged and published as a GitHub release automatically.
- **Stable releases** (`release-next` → `dev`): the PR opens on its own
  whenever `dev` has releasable commits; merging it also fast-forwards `main`.
- **Prereleases** (`prerelease-next` → `dev`): dispatch the *Release PR*
  workflow to open the PR for the next `x.y.z-rc.N`; merging it cuts the rc
  without touching `main`.

Versions are computed from the commit history by
[python-semantic-release](https://python-semantic-release.readthedocs.io);
`CHANGELOG.md` and the version fields in `pyproject.toml`, `plugin.json`, and
`SKILL.md` are written by the release tooling, never by hand.
