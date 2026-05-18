# Prehistorian

[![CI](https://github.com/fahiiim/prehistorian/actions/workflows/ci.yml/badge.svg)](https://github.com/fahiiim/prehistorian/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/prehistorian)](https://pypi.org/project/prehistorian/)
[![Python](https://img.shields.io/pypi/pyversions/prehistorian)](https://pypi.org/project/prehistorian/)
[![Downloads](https://img.shields.io/pypi/dm/prehistorian)](https://pypi.org/project/prehistorian/)
[![License](https://img.shields.io/github/license/fahiiim/prehistorian)](LICENSE)
[![Stars](https://img.shields.io/github/stars/fahiiim/prehistorian)](https://github.com/fahiiim/prehistorian/stargazers)
[![Issues](https://img.shields.io/github/issues/fahiiim/prehistorian)](https://github.com/fahiiim/prehistorian/issues)
[![Last Commit](https://img.shields.io/github/last-commit/fahiiim/prehistorian)](https://github.com/fahiiim/prehistorian/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/fahiiim/prehistorian)](https://github.com/fahiiim/prehistorian)
[![Code Size](https://img.shields.io/github/languages/code-size/fahiiim/prehistorian)](https://github.com/fahiiim/prehistorian)

Prehistorian is a **predictive codebase cartographer**. It analyzes Git history to uncover hidden, undocumented behavioral dependencies between files and warns you when a change is likely missing a related update.

It is **CLI-only**, **LLM-free**, and **CPU-only** by design.

---

## Why Prehistorian

Static imports and direct references show only explicit dependencies. Real-world teams rely on patterns that rarely show up in the import graph: files that consistently change together across many commits. Prehistorian surfaces those patterns and turns them into practical, low-noise warnings.

---

## At a Glance

- **Signals**: Hidden co-change dependencies discovered from Git history.
- **Safety**: Pre-commit warnings that never block your commit.
- **Performance**: Sparse matrices keep memory use low on large repos.
- **Transparency**: Simple, explainable $P(B|A)$ confidence score.

---

## How It Works (Pipeline)

1. **Ingestion**: `git log --all --name-only --pretty=format:"COMMIT_START:%H"`
2. **Filtering**:
   - Drop commits touching more than 15 files.
   - Remove noise files (lockfiles, images).
3. **Matrix Creation**: Build a sparse commit-file matrix.
4. **Math Engine**:
   - `mlxtend.fpgrowth` finds frequent co-change pairs.
   - Markov co-change confidence: $P(B|A) = \frac{Count(A \cap B)}{Count(A)}$.
5. **Caching**: Save the model to `.prehistorian/model.joblib`.

---

## Features

- **CLI-only** workflow, no UI or server required.
- **Sparse data pipeline** for large repositories.
- **Fast co-change discovery** via `fpgrowth`.
- **Actionable warnings** without blocking commits.

---

## Installation

```bash
pip install .
```

Development dependencies:

```bash
pip install .[dev]
```

---

## Quick Start

```bash
prehistorian scan
prehistorian query path/to/file.py
prehistorian hook-install
```

If the `prehistorian` command is not on PATH:

```bash
python -m prehistorian scan
```

---

## Guided Usage

### 1) Build the model

Command:

```bash
prehistorian scan
```

Expected output:

```
Prehistorian analyzed 842 commits. Found 126 behavioral dependencies. Model saved.
```

### 2) Query co-change dependencies

Command:

```bash
prehistorian query path/to/file.py
```

Expected output:

```
Co-change Dependencies for 'path/to/file.py'
File Path                          Co-change Confidence (%)
src/core/scheduler.py             88.24%
src/core/config.py                75.61%
```

If there is no model yet:

```
Model not found. Run `prehistorian scan` first.
```

### 3) Install the pre-commit hook

Command:

```bash
prehistorian hook-install
```

Expected output:

```
Successfully installed pre-commit hook at .git/hooks/pre-commit
```

### 4) Pre-commit check (runs automatically)

Manual command (optional):

```bash
prehistorian pre-commit-check
```

Expected warning (commit never blocked):

```
[PREHISTORIAN WARNING] You are committing 'A', but historically you also change 'B' 85% of the time. Did you forget to stage it?
```

---

## Commands

| Command | Description |
| --- | --- |
| `prehistorian scan` | Build and cache the co-change model. |
| `prehistorian query <file_path>` | Show top co-changing files and confidence. |
| `prehistorian hook-install` | Install a git pre-commit hook. |
| `prehistorian pre-commit-check` | Warn about missing co-changed files. |

---

## Pre-commit Warnings

During `git commit`, Prehistorian checks the **top 2** co-changed files for every staged file. If a highly correlated file is missing (>= 75%), it prints a warning but **never blocks the commit**.

---

## Testing and CI

```bash
python -m pytest
```

GitHub Actions runs the tests on pushes and pull requests.

---

## Release (PyPI + GitHub)

The release workflow publishes to PyPI and creates a GitHub Release when a version tag is pushed.

For this release, use tag `1.1.2`:

```bash
git tag 1.1.2
git push origin 1.1.2
```

---

## Notes and Limitations

- Must be run inside a Git repository.
- Commits that touch more than 15 files are skipped.
- Noise files (lockfiles and images) are filtered out.
- Delete `.prehistorian/` at any time to rebuild the model.

---

## License

MIT License. See LICENSE.