# Pyro

Pyro is an open-source renderer for ***plain specifications. It's packaged as an agentic skill
that renders a `.plain` spec into working and tested code.

Invoke it from your agent with:

```
/pyro:render-spec <plain-spec-filename>   # Claude Code plugin install
/render-spec <plain-spec-filename>        # npx skills install or manual copy
```

The skill resolves the modules the target spec requires or imports, renders them
in dependency order, and writes:
* intermediate implementation code to `plain_modules/<module>/code/`
* conformance tests to `plain_modules/<module>/tests/`
* the target module's output to `dist/`

## Installation

### Claude Code plugin

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

### Installation with npx skills

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

Copy the `skills/render-spec` folder from this repo into your agent's skills
folder. For Codex that is `.codex/skills/` in your project (or `~/.codex/skills/`
for every project); other agents have an equivalent folder — see their docs.
Update it by pulling this repo and copying the folder again.

## Requirements

Rendering needs **Python 3.8 or newer** on the machine — nothing else, no
third-party packages. The skill finds the interpreter itself, trying `py -3`,
`python3`, and `python` in that order, and stops with a clear message if none of
them works.

## Tests

Each helper script has its own `tests/run_<name>_tests.py` suite;
`tests/run_tests.py` discovers and runs them all, anywhere Python does:

```bash
python3 tests/run_tests.py
```

## Development workflow

### Branches and commits

The project uses two channel branches, `dev` and `main`, which share the same
git history.

`main` always points at the latest stable release — the commit that Claude and
Codex plugin installs fetch. It never gets its own commits; it only
fast-forwards to a commit already on `dev`.

All development lands on `dev` first: open a feature branch as a
[PR into `dev`](https://github.com/plainlang/pyro/compare/dev...dev?expand=1)
and rebase-merge it. Commit messages must follow
[conventional commits](https://www.conventionalcommits.org) (enforced by CI).

### Versioning

Agent plugins are installed from the repo URL, and the installed version is
read from manifest files. This has two consequences:
* `main`'s HEAD must always point at the latest stable version
* the version must be stamped into the manifest files — a git tag is not enough

Therefore every release gets a release commit that stamps the version into
those files.

Versions are computed from the commit history by
[python-semantic-release](https://python-semantic-release.readthedocs.io).
`CHANGELOG.md` and the version fields in `pyproject.toml`, `plugin.json`, and
`SKILL.md` are written by the release tooling — never edit them by hand.

### Releases

**Releasing means merging a release PR.** A bot maintains a release PR into
`dev` holding the next version's changelog and version stamps. Rebase-merge it
and the release is tagged and published on GitHub automatically.

There are two kinds of release, and they differ in how the PR opens:

- **Stable release** (`release-next` → `dev`): the PR opens and stays current
  on its own whenever `dev` has unreleased changes. Merging it also moves
  `main` to the release.

- **Prerelease** (`prerelease-next` → `dev`): the PR never opens on its own —
  run the *Release PR* workflow manually to open it. Merging it releases the
  next prerelease `x.y.z-rc.N` and does not touch `main`.
