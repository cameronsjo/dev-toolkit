---
name: levelup
description: Audit and upgrade projects to 2026 tooling standards. Supports mise, Biome, uv+ruff migrations.
---

# /levelup - Modern Tooling Upgrades

Audit existing projects and migrate to 2026 tooling standards. Works on existing repos or sets up tooling from scratch.

## Commands

```
/levelup                    # Audit current project, show recommendations
/levelup audit              # Same as above
/levelup audit --explain    # Verbose with educational context

/levelup mise               # Migrate to mise (Node version management)
/levelup biome              # Migrate JS/TS to Biome (replaces ESLint+Prettier)
/levelup python             # Upgrade to uv + ruff + pyproject.toml
/levelup dotfiles           # Update dotfiles (mise, remove nvm)

/levelup all                # Run all applicable migrations
```

## Execution Flow

### 1. Branch Safety (ALWAYS FIRST)

Before ANY migration, ensure git safety:

```bash
# Check git status
git status --porcelain

# If dirty or on main/master/develop, create new branch
git checkout -b levelup/migrate-<tool>-$(date +%Y%m%d-%H%M%S)
```

**CRITICAL:** Never make changes on main/master. Always create a feature branch.

### 2. Parse Subcommand

| Argument | Action |
|----------|--------|
| (none) or `audit` | Run audit agent |
| `mise` | Run mise agent |
| `biome` | Run biome agent |
| `python` | Run python agent |
| `dotfiles` | Run dotfiles migration (part of mise agent with flag) |
| `all` | Run audit, then execute all recommended migrations |

### 3. Handle Flags

| Flag | Behavior |
|------|----------|
| `--explain` | Enable verbose educational output |
| `--dotfiles` | Include dotfiles migration (for mise) |
| `--dry-run` | Show what would change without making changes |

### 4. Dispatch to Agent

Based on subcommand, load and execute the appropriate agent:

- **audit**: `agents/audit.md` - Detect tooling, generate recommendations
- **mise**: `agents/mise.md` - nvm → mise migration
- **biome**: `agents/biome.md` - ESLint+Prettier → Biome migration
- **python**: `agents/python.md` - Legacy Python → uv + ruff

## Output Style

### Summary Mode (Default)

```
Project: my-app

Detected:
  package.json (Node project)
  .nvmrc (Node 20.11.0)
  .eslintrc.js + .prettierrc (separate lint/format)

Recommendations:
  1. /levelup mise     - Replace .nvmrc with .mise.toml
  2. /levelup biome    - Consolidate ESLint+Prettier into Biome

Run /levelup all to apply both, or run individually.
```

### Verbose Mode (--explain)

Include educational blocks:

```
Why mise over nvm?
---------------------------------------------
- nvm uses shims adding ~120ms to every Node call
- mise modifies PATH directly—zero overhead
- mise manages Node, Python, Go, Rust, 100+ tools
- .mise.toml is cleaner than multiple .*-version files
---------------------------------------------
```

## Git Behavior

1. **Check status** - Abort if uncommitted changes (unless user confirms)
2. **Create branch** - `levelup/migrate-<tool>-<timestamp>`
3. **Make changes** - Execute migration
4. **Stage files** - `git add` changed files
5. **Report** - Show what was staged, user commits manually

**NEVER:**
- Auto-commit changes
- Push to remote
- Make changes on main/master

## Error Handling

If a migration fails partway:
1. Report what succeeded and what failed
2. Keep changes staged (don't auto-revert)
3. Suggest manual steps to complete or rollback

## Supported Ecosystems (Phase 1)

| Ecosystem | Status | Agent |
|-----------|--------|-------|
| JS/TS | Supported | mise, biome |
| Python | Supported | python |
| Shell/Dotfiles | Supported | mise --dotfiles |
| Go | Future | - |
| Rust | Future | - |
| C#/.NET | Future | - |
