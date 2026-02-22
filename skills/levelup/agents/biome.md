---
name: levelup-biome
description: Migrate from ESLint + Prettier to Biome for JS/TS projects
---

# Biome Migration Agent

Replace ESLint and Prettier with Biome for unified linting and formatting.

## Prerequisites Check

```bash
# Must have package.json
if [ ! -f package.json ]; then
    echo "Error: No package.json found. Not a Node project."
    exit 1
fi

# Detect package manager
if [ -f bun.lockb ]; then
    PKG_MGR="bun"
elif [ -f pnpm-lock.yaml ]; then
    PKG_MGR="pnpm"
elif [ -f yarn.lock ]; then
    PKG_MGR="yarn"
else
    PKG_MGR="npm"
fi
```

## Detection

### Find ESLint Config

```bash
# ESLint config files
ls .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json .eslintrc.yaml .eslintrc.yml eslint.config.js eslint.config.mjs 2>/dev/null

# ESLint ignore
ls .eslintignore 2>/dev/null
```

### Find Prettier Config

```bash
# Prettier config files
ls .prettierrc .prettierrc.js .prettierrc.cjs .prettierrc.json .prettierrc.yaml .prettierrc.yml prettier.config.js prettier.config.cjs 2>/dev/null

# Prettier ignore
ls .prettierignore 2>/dev/null
```

### Extract Current Settings

From Prettier config, extract:
- `tabWidth` (default: 2)
- `useTabs` (default: false)
- `semi` (default: true)
- `singleQuote` (default: false)
- `trailingComma` (default: "es5")
- `printWidth` (default: 80)

From ESLint config, identify:
- Custom rules (map to Biome equivalents)
- Plugins in use (flag if no Biome equivalent)
- Extends (identify base configs)

## Migration Steps

### Step 1: Install Biome

```bash
# Install exact version for reproducibility
$PKG_MGR install --save-dev --save-exact @biomejs/biome
```

### Step 2: Generate biome.json

Use `templates/biome.json` as base, customize with extracted settings:

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.0/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error",
        "noUnusedImports": "error"
      },
      "suspicious": {
        "noDoubleEquals": "error",
        "noConsole": "warn"
      },
      "style": {
        "noNonNullAssertion": "warn",
        "useConst": "error"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "semicolons": "always",
      "trailingCommas": "all"
    }
  },
  "files": {
    "ignore": ["node_modules", "dist", "build", ".next", "coverage"]
  }
}
```

### Step 3: Map ESLint Rules

Common mappings:

| ESLint | Biome |
|--------|-------|
| `no-unused-vars` | `correctness/noUnusedVariables` |
| `no-undef` | `correctness/noUndeclaredVariables` |
| `eqeqeq` | `suspicious/noDoubleEquals` |
| `no-console` | `suspicious/noConsole` |
| `prefer-const` | `style/useConst` |
| `no-var` | `style/noVar` |
| `@typescript-eslint/no-explicit-any` | `suspicious/noExplicitAny` |
| `@typescript-eslint/no-non-null-assertion` | `style/noNonNullAssertion` |
| `import/order` | `organizeImports` (built-in) |

**Flag rules without equivalents:**
```
Note: The following ESLint rules have no Biome equivalent:
- eslint-plugin-react-hooks/exhaustive-deps (manual review needed)
- @typescript-eslint/strict-boolean-expressions (not yet supported)

Consider keeping these rules active or adding manual checks.
```

### Step 4: Remove Old Dependencies

From package.json devDependencies, remove:

```bash
# ESLint packages
$PKG_MGR remove eslint @eslint/js eslint-plugin-* eslint-config-* @typescript-eslint/eslint-plugin @typescript-eslint/parser

# Prettier packages
$PKG_MGR remove prettier prettier-plugin-* @prettier/* eslint-config-prettier eslint-plugin-prettier
```

### Step 5: Delete Old Config Files

```bash
# ESLint configs
rm -f .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json .eslintrc.yaml .eslintrc.yml
rm -f eslint.config.js eslint.config.mjs .eslintignore

# Prettier configs
rm -f .prettierrc .prettierrc.js .prettierrc.cjs .prettierrc.json .prettierrc.yaml .prettierrc.yml
rm -f prettier.config.js prettier.config.cjs .prettierignore
```

### Step 6: Update package.json Scripts

Replace:
```json
{
  "scripts": {
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

With:
```json
{
  "scripts": {
    "lint": "biome check .",
    "lint:fix": "biome check --fix .",
    "format": "biome format --write .",
    "format:check": "biome format ."
  }
}
```

### Step 7: Stage Changes

```bash
git add biome.json package.json package-lock.json  # or pnpm-lock.yaml, etc.
git add -u  # Stage deletions
git status
```

### Step 8: Verify

```bash
# Run Biome check
$PKG_MGR run lint

# Check for issues
biome check .
```

## Educational Content (--explain)

```
Why Biome over ESLint + Prettier?
---------------------------------------------
Speed:
- Biome is written in Rust, 20-100x faster than ESLint
- Large codebases see lint times drop from minutes to seconds
- CI pipelines get faster feedback loops

Unified tooling:
- One tool for linting AND formatting (no config conflicts)
- No need for eslint-config-prettier or eslint-plugin-prettier
- Single config file instead of two

Better defaults:
- Sensible rules out of the box
- Less configuration needed
- Still fully customizable when needed

Active development:
- Backed by well-funded team
- Regular releases with new features
- Growing ecosystem and IDE support
---------------------------------------------
```

## IDE Integration Note

After migration, suggest:

```
Update your IDE settings:

VS Code:
1. Install "Biome" extension
2. Disable/remove ESLint and Prettier extensions for this workspace
3. Set Biome as default formatter:
   {
     "editor.defaultFormatter": "biomejs.biome",
     "editor.formatOnSave": true
   }

The biome.json file is automatically detected.
```

## Rollback

If something goes wrong:

```bash
# Restore from git
git checkout HEAD -- package.json .eslintrc* .prettierrc*

# Remove biome
rm biome.json
$PKG_MGR remove @biomejs/biome

# Reinstall old deps
$PKG_MGR install
```
