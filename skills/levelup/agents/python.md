---
name: levelup-python
description: Upgrade Python projects to uv + ruff + modern pyproject.toml
---

# Python Migration Agent

Upgrade legacy Python projects to modern tooling: uv, ruff, and PEP 621 pyproject.toml.

## Prerequisites Check

```bash
# Check for Python project indicators
if [ ! -f requirements.txt ] && [ ! -f setup.py ] && [ ! -f setup.cfg ] && [ ! -f pyproject.toml ] && [ ! -f Pipfile ]; then
    echo "Error: No Python project detected."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
    echo "Installing ruff..."
    uv tool install ruff
fi
```

## Detection

### Identify Current Setup

```bash
# Package management
ls requirements.txt requirements-dev.txt requirements/*.txt 2>/dev/null  # pip
ls Pipfile Pipfile.lock 2>/dev/null  # pipenv
ls poetry.lock 2>/dev/null  # poetry
ls uv.lock 2>/dev/null  # uv (already modern)

# Legacy packaging
ls setup.py setup.cfg MANIFEST.in 2>/dev/null

# Linting/formatting
ls .flake8 2>/dev/null  # flake8
ls .isort.cfg 2>/dev/null  # isort
ls .black.toml pyproject.toml 2>/dev/null  # black config

# Check pyproject.toml sections
if [ -f pyproject.toml ]; then
    grep -q "\[tool.poetry\]" pyproject.toml && echo "Poetry detected"
    grep -q "\[tool.black\]" pyproject.toml && echo "Black detected"
    grep -q "\[tool.isort\]" pyproject.toml && echo "isort detected"
    grep -q "\[tool.ruff\]" pyproject.toml && echo "Ruff detected (modern)"
fi
```

## Migration Steps

### Step 1: Extract Dependencies

**From requirements.txt:**
```bash
# Parse requirements, strip comments and versions for analysis
cat requirements.txt | grep -v "^#" | grep -v "^$"
```

**From Pipfile:**
```bash
# Extract [packages] section
cat Pipfile | sed -n '/\[packages\]/,/\[/p' | grep "="
```

**From poetry.lock / pyproject.toml (Poetry):**
```bash
# Extract from [tool.poetry.dependencies]
cat pyproject.toml | sed -n '/\[tool.poetry.dependencies\]/,/\[/p'
```

**From setup.py:**
```bash
# Look for install_requires
grep -A 20 "install_requires" setup.py
```

### Step 2: Create/Update pyproject.toml

Use `templates/pyproject.toml` as base:

```toml
[project]
name = "{project_name}"
version = "0.1.0"
description = "{from setup.py or README}"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    # Migrated from requirements.txt/Pipfile/poetry
]

[project.optional-dependencies]
dev = [
    "ruff>=0.8.0",
    "pytest>=8.0.0",
    "mypy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "SIM",    # flake8-simplify
    "RUF",    # ruff-specific
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.mypy]
python_version = "3.12"
strict = true
```

### Step 3: Map Existing Configuration

**From .flake8:**
```ini
# Old .flake8
[flake8]
max-line-length = 120
ignore = E203, W503
```

Maps to:
```toml
[tool.ruff]
line-length = 120

[tool.ruff.lint]
ignore = ["E203", "W503"]
```

**From black config:**
```toml
# Old [tool.black]
line-length = 100
target-version = ['py311']
```

Maps to:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
```

**From isort config:**
```toml
# Old [tool.isort]
profile = "black"
line_length = 100
```

Maps to:
```toml
[tool.ruff.lint]
select = ["I"]  # Enable isort rules

[tool.ruff.lint.isort]
# ruff's isort is black-compatible by default
```

### Step 4: Remove Old Files

```bash
# Legacy packaging (if all metadata migrated to pyproject.toml)
rm -f setup.py setup.cfg MANIFEST.in

# Old linting configs
rm -f .flake8 .isort.cfg

# Remove [tool.black] and [tool.isort] from pyproject.toml
# (Keep the file, just remove those sections)

# Old package management
rm -f Pipfile Pipfile.lock
rm -f requirements.txt requirements-dev.txt  # After confirming deps migrated

# Poetry remnants (if migrating from Poetry)
rm -f poetry.lock
# Remove [tool.poetry] section from pyproject.toml
```

### Step 5: Initialize uv Environment

```bash
# Create virtual environment
uv venv

# Install dependencies from pyproject.toml
uv pip install -e ".[dev]"

# Generate lockfile (optional but recommended)
uv pip compile pyproject.toml -o requirements.lock
```

### Step 6: Update .gitignore

Ensure these are present:
```
.venv/
__pycache__/
*.pyc
.ruff_cache/
.mypy_cache/
*.egg-info/
dist/
build/
```

### Step 7: Stage Changes

```bash
git add pyproject.toml .gitignore
git add -u  # Stage deletions
git status
```

### Step 8: Verify

```bash
# Activate venv
source .venv/bin/activate

# Check ruff
ruff check .
ruff format --check .

# Run tests if they exist
pytest 2>/dev/null || echo "No tests found"
```

## Educational Content (--explain)

```
Why uv + ruff?
---------------------------------------------
uv (package management):
- 10-100x faster than pip (written in Rust)
- Drop-in replacement: uv pip install works like pip
- Better dependency resolution
- Built-in venv management

ruff (linting + formatting):
- Replaces flake8, black, isort, pyupgrade, bandit, and more
- 100x faster than the tools it replaces
- Single config in pyproject.toml
- Growing rule set covers most use cases

pyproject.toml (PEP 621):
- Modern standard for Python project metadata
- All config in one file
- Works with all modern tools (uv, ruff, pytest, mypy)
- No more setup.py/setup.cfg fragmentation
---------------------------------------------
```

## Special Cases

### Poetry Project

If migrating from Poetry:
1. Extract dependencies from `[tool.poetry.dependencies]`
2. Convert to PEP 621 format in `[project.dependencies]`
3. Convert dev dependencies from `[tool.poetry.group.dev.dependencies]`
4. Remove `[tool.poetry]` section entirely
5. Change build-backend from poetry to hatchling

### Pipenv Project

If migrating from Pipenv:
1. Extract from `[packages]` section of Pipfile
2. Convert to pyproject.toml dependencies
3. Extract from `[dev-packages]` for dev dependencies
4. Remove Pipfile and Pipfile.lock

### requirements.txt Only

Simplest case:
1. Parse requirements.txt
2. Add to pyproject.toml `[project.dependencies]`
3. Keep requirements.txt as backup until confirmed working
4. Delete after verification

## Rollback

```bash
# Restore from git
git checkout HEAD -- setup.py setup.cfg requirements.txt Pipfile pyproject.toml

# Remove new files
rm -rf .venv uv.lock

# Unstage changes
git reset HEAD
```
