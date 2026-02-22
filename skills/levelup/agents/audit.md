---
name: levelup-audit
description: Detect current tooling and generate upgrade recommendations
---

# Audit Agent

Scan the current directory to detect tooling and recommend upgrades.

## Detection Procedure

### Step 1: Identify Project Type

Check for these files to determine project type(s):

```bash
# Node/JS/TS project
ls package.json 2>/dev/null

# Python project
ls pyproject.toml setup.py setup.cfg requirements.txt Pipfile 2>/dev/null

# Go project
ls go.mod 2>/dev/null

# Rust project
ls Cargo.toml 2>/dev/null

# .NET project
ls *.csproj *.sln 2>/dev/null
```

### Step 2: Detect Version Management

| File | Tool | Recommendation |
|------|------|----------------|
| `.nvmrc` | nvm | `/levelup mise` |
| `.node-version` | nodenv/fnm | `/levelup mise` |
| `.python-version` | pyenv | `/levelup mise` (future) |
| `.ruby-version` | rbenv | `/levelup mise` (future) |
| `.tool-versions` | asdf | `/levelup mise` |
| `.mise.toml` | mise | Already modern |

### Step 3: Detect JS/TS Tooling

| File Pattern | Tool | Recommendation |
|--------------|------|----------------|
| `.eslintrc*`, `eslint.config.js` | ESLint | `/levelup biome` |
| `.prettierrc*`, `prettier.config.js` | Prettier | `/levelup biome` |
| Both ESLint + Prettier | Both | `/levelup biome` (high priority) |
| `biome.json` | Biome | Already modern |

Check package.json devDependencies for:
- `eslint`, `@eslint/*`, `eslint-plugin-*`, `eslint-config-*`
- `prettier`, `prettier-plugin-*`

### Step 4: Detect Python Tooling

| File/Pattern | Tool | Recommendation |
|--------------|------|----------------|
| `requirements.txt` only | pip | `/levelup python` |
| `setup.py`, `setup.cfg` | setuptools | `/levelup python` |
| `Pipfile` | pipenv | `/levelup python` |
| `poetry.lock` | Poetry | `/levelup python` |
| `.flake8` | flake8 | `/levelup python` |
| `pyproject.toml` + `[tool.black]` | black | `/levelup python` |
| `pyproject.toml` + `[tool.isort]` | isort | `/levelup python` |
| `pyproject.toml` + `[tool.ruff]` | ruff | Already modern |
| `uv.lock` | uv | Already modern |

### Step 5: Check Dotfiles (Optional)

If `--dotfiles` flag or running `/levelup dotfiles`:

```bash
# Check for nvm in dotfiles
grep -l "NVM_DIR\|nvm.sh" ~/.zshrc ~/.bashrc 2>/dev/null

# Check Brewfile for nvm
grep "nvm" Brewfile 2>/dev/null

# Check for mise
command -v mise
```

## Output Format

### Summary Mode

```
Project: {project_name}

Detected:
  {icon} {description}
  ...

Recommendations:
  1. /levelup {cmd}  - {reason}
  2. /levelup {cmd}  - {reason}
  ...

Run /levelup all to apply all, or run individually.
```

### Verbose Mode (--explain)

After each recommendation, include educational block:

```
Why {new_tool} over {old_tool}?
---------------------------------------------
- {point 1}
- {point 2}
- {point 3}
---------------------------------------------
```

## Priority Ordering

When multiple upgrades are recommended, order by:

1. **Version management** (mise) - Foundation for everything else
2. **Linting/formatting** (biome, ruff) - Immediate DX improvement
3. **Package management** (uv) - Build/install speed
4. **Config modernization** (pyproject.toml) - Standards compliance

## No Recommendations Case

If project is already modern:

```
Project: {project_name}

All tooling is up to 2026 standards.

Detected:
  .mise.toml (mise for version management)
  biome.json (unified lint/format)
  pyproject.toml with [tool.ruff] (modern Python)

No upgrades needed.
```

## Edge Cases

### Monorepo Detection

If `packages/`, `apps/`, or `workspaces` in package.json:
- Note it's a monorepo
- Recommend running audit in each package
- Or offer to scan all packages

### Mixed Projects

If both package.json and pyproject.toml exist:
- Run both JS/TS and Python detection
- Combine recommendations

### No Recognizable Project

If no project files found:
- Check if in home directory or dotfiles
- Suggest `/levelup dotfiles` if applicable
- Otherwise report "No project detected"
