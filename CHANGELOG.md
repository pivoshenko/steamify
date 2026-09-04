# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-09-04

### Build

- Update dependencies
- Refresh uv.lock
- **deps**: Update dependencies
- **deps**: Update dependencies
- Sync lockfile to 1.2.4

### CI/CD

- Ignore rules newly stabilized in ruff 0.16
- Drop ruff format --check from lint; suppress more ty rules
- Use uv run pytest for project venv; format example file
- Fix action versions and test recipe failures
- Drop hashFiles guard; move .no-tests sentinel handling into justfile
- Flatten to one job per language
- Bump action versions to latest major
- Standardize workflow to per-language parallel pipelines on ubuntu-24.04-arm

### Documentation

- Document both conversion directions
- Add pull request template
- Regenerate CLAUDE.md
- Document the module docstring convention
- Normalize module and package docstrings
- Normalize heading case in readme, contributing, security
- Strip AI tells and redundant code comments
- Refresh CLAUDE.md for current justfile + CI shape
- **ci**: Document required secrets at top of workflow files

### Features

- Add to_markdown for converting Steam markup back to Markdown

### Miscellaneous

- Remove local pull request template
- **deps**: Update locked dependencies
- Update dependency lockfile
- Add editorconfig
- **justfile**: Use uv lock --upgrade for update, scope pyupgrade to . excluding .venv
- Standardize justfile recipes and refresh CLAUDE.md
- Simplify pytest addopts
- Remove issue templates

### Refactor

- Rename package to steamify and split pipeline by direction

## [1.2.4] - 2026-05-31

### Build

- Sync lockfile to 1.2.3

### Documentation

- Drop license badge from readme
- Drop redundant table of contents
- Simplify pull request template

### Miscellaneous

- Expand gitignore with editors, env, logs

### Release

- V1.2.4

## [1.2.3] - 2026-05-30

### Documentation

- Add features section and rename examples to usage

### Miscellaneous

- Remove unused release recipe stub

### Release

- V1.2.3

## [1.2.2] - 2026-05-30

### Build

- Update dev dependencies
- Update dev dependencies
- Update dev dependencies
- Update dev dependencies

### CI/CD

- Rename labels workflow file to update-labels
- Rename workflow and job for updating labels

### Miscellaneous

- Align repository with hygiene standard
- Add CLAUDE instructions
- Update pyupgrade version in justfile
- Remove invalid file
- Add update command to justfile and CLAUDE.md
- Update .gitignore and remove .python-version

### Release

- V1.2.2

### Style

- Format justfile and .editorconfig indentation

## [1.2.1] - 2026-03-29

### Build

- Remove unused pytest-lazy-fixture, upgrade pytest
- Replace poethepoet with just
- Update dependency specifications
- Update dependencies
- **deps**: Bump tornado from 6.5.4 to 6.5.5
- Update dev dependencies

### CI/CD

- Add workflow_dispatch to labels, remove dependabot
- Migrate release to workflow_dispatch with version override
- Consolidate linters and tests into unified CI workflow

### Documentation

- Add CLAUDE.md
- Update badges

## [1.2.0] - 2026-03-08

### Bug fixes

- Update metadata

## [1.1.3] - 2026-03-07

### Build

- **deps**: Bump crazy-max/ghaction-github-labeler from 5 to 6
- Update dev dependencies
- Update dev dependencies
- **deps**: Bump urllib3 from 2.6.2 to 2.6.3

### Documentation

- Add TOC

### Features

- Replace mypy with ty

### Miscellaneous

- Update chore files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files
- Sync repository standards files

## [1.1.2] - 2026-01-10

### Build

- Update dev dependencies
- Update dev dependencies

### CI/CD

- Upgrade actions

### Documentation

- Update license

## [1.1.1] - 2025-12-15

### Build

- Update dev dependencies
- Update dev dependencies
- Update dev dependencies
- Update dev dependencies

### CI/CD

- Upgrade actions/checkout to v6 in workflows
- Update semantic release action version

### Documentation

- Update notes

### Miscellaneous

- Update CodeCov config

## [1.1.0] - 2025-11-02

### Refactor

- Add type ignores for regex match functions

## [1.0.0] - 2025-11-02

### CI/CD

- Add core components

### Documentation

- Add core components

### Features

- Initial commit

