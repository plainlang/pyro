# Changelog

All notable changes to this project are documented here. The file is generated
by [python-semantic-release](https://python-semantic-release.readthedocs.io)
from conventional commits — `rc` prereleases write their own sections, and the
release PR adds the stable release's section on top. Do not edit by hand; new
entries go directly below the marker.

<!-- version list -->

## v0.3.0 (2026-09-05)

### Continuous Integration

- Retarget PRs opened against main to dev
  ([`5b8fa52`](https://github.com/plainlang/pyro/commit/5b8fa52033b5fb15a1a78873b161dbfca5068ee4))

### Features

- Add copy_folder script for cross-platform folder copies
  ([`5a35f24`](https://github.com/plainlang/pyro/commit/5a35f241a70e0ccdbeb2ceea6b0a6114c14269c7))

- Clean up installed artifacts in mod.cleanup
  ([`3809030`](https://github.com/plainlang/pyro/commit/380903082ad457c494e2ab260d1cf3b372130caf))

- Use copy_folder script in SKILL.md copy steps
  ([`d6e4656`](https://github.com/plainlang/pyro/commit/d6e46563a54f02a208c6c50ed3b55ac72a7cd8df))


## v0.2.0 (2026-09-04)

### Bug Fixes

- Drop argument-hint from the skill frontmatter
  ([`0c0ee69`](https://github.com/plainlang/pyro/commit/0c0ee69a688c4f08ba1a871c3ed702cefa45274c))

### Continuous Integration

- Bump actions to Node 24 runtimes
  ([`a1be818`](https://github.com/plainlang/pyro/commit/a1be81851af5c8f9717244a981961d7ae62887fb))

- Check the version copies stay in sync on PRs
  ([`37f5adf`](https://github.com/plainlang/pyro/commit/37f5adf18e3278fc50f69200c4c71ec5359247b5))

- Disable npm audit in the commitlint step
  ([`343a8a5`](https://github.com/plainlang/pyro/commit/343a8a5dc469a91d1e57defd23acd8903b46f288))

- Lint commit messages on PRs only
  ([`534755b`](https://github.com/plainlang/pyro/commit/534755b1f06a18fe91d8beba2c43869729b6f82a))

- Move commitlint into a consolidated pr-checks workflow
  ([`5e515f8`](https://github.com/plainlang/pyro/commit/5e515f86113e29a6e36c05fd49291369a2fcafa5))

- Run the python test suite on PRs
  ([`f49cb64`](https://github.com/plainlang/pyro/commit/f49cb64acc77e9e13d200328a527db492dcc6bb1))

- Validate the plugin manifests on PRs
  ([`ab47000`](https://github.com/plainlang/pyro/commit/ab47000c729e4648938e7880317b1cbbe7c9a90d))

- Validate the skill against the Agent Skills spec on PRs
  ([`5def60e`](https://github.com/plainlang/pyro/commit/5def60e8da090104a010f56a3fc0a2aad3a7b83f))

### Documentation

- Link the PR-into-dev mention to a preset compare page
  ([`faaad9d`](https://github.com/plainlang/pyro/commit/faaad9d8760385fdbc3ff22a49f39fb17e9fd790))

- Reset changelog
  ([`c37025a`](https://github.com/plainlang/pyro/commit/c37025a31c1349fcc34a1593eec3737040173430))

- Update dev section
  ([`4441be4`](https://github.com/plainlang/pyro/commit/4441be44ef2dd545295d5603c8b7b873295ef561))

- Update usage and minor fixes
  ([`2582798`](https://github.com/plainlang/pyro/commit/2582798f3f0cc5314d430dbdcde9873c48358169))

### Features

- Add check_version script
  ([`544312c`](https://github.com/plainlang/pyro/commit/544312c3160de6999a43c6c452ea565505ce43a1))

- Warn when a newer release is available
  ([`d1825f8`](https://github.com/plainlang/pyro/commit/d1825f84c227371b40f26f849e25dbf804f8c9b4))


## v0.1.0 (2026-09-03)

### Initial release of pyro
