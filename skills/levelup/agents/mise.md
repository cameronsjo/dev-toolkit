---
name: levelup-mise
description: Migrate from nvm/nodenv/asdf to mise for version management
---

# Mise Migration Agent

Replace nvm (or similar) with mise for Node version management.

## Prerequisites Check

```bash
# Check if mise is installed
if ! command -v mise &> /dev/null; then
    echo "Installing mise via Homebrew..."
    brew install mise
fi

# Verify installation
mise --version
```

## Detection

### Find Version Files

```bash
# Node version files
ls -la .nvmrc .node-version 2>/dev/null

# asdf version file
ls -la .tool-versions 2>/dev/null

# Check package.json engines
cat package.json | jq -r '.engines.node // empty' 2>/dev/null
```

### Extract Version

Priority order:
1. `.nvmrc` content
2. `.node-version` content
3. `.tool-versions` node line
4. `package.json` engines.node

```bash
# Example extraction
if [ -f .nvmrc ]; then
    NODE_VERSION=$(cat .nvmrc | tr -d 'v')
elif [ -f .node-version ]; then
    NODE_VERSION=$(cat .node-version | tr -d 'v')
elif [ -f .tool-versions ]; then
    NODE_VERSION=$(grep "^nodejs" .tool-versions | awk '{print $2}')
fi
```

## Migration Steps

### Step 1: Create .mise.toml

Use the template from `templates/mise.toml`, customized with detected version:

```toml
[tools]
node = "{detected_version}"  # e.g., "20.11.0" or "lts"

[settings]
experimental = true
```

If `.tool-versions` had other tools, migrate them too:
```toml
[tools]
node = "20.11.0"
python = "3.12"  # if was in .tool-versions
```

### Step 2: Remove Old Version Files

```bash
# Remove nvm file
git rm .nvmrc 2>/dev/null || rm -f .nvmrc

# Remove nodenv/other file
git rm .node-version 2>/dev/null || rm -f .node-version

# Remove asdf file (if ONLY had node)
# If .tool-versions had other tools, migrate them first
git rm .tool-versions 2>/dev/null || rm -f .tool-versions
```

### Step 3: Stage Changes

```bash
git add .mise.toml
git status
```

### Step 4: Verify

```bash
# Trust the mise config
mise trust

# Install the specified version
mise install

# Verify correct version
node --version
```

## Dotfiles Migration (--dotfiles flag)

If `--dotfiles` flag is passed, also update shell configuration:

### Update Brewfile

Edit `Brewfile`:

```ruby
# Comment out nvm (keep for reference)
# brew "nvm"  # Replaced by mise (YYYY-MM-DD)

# Add mise
brew "mise"
```

### Update dot_zshrc

Edit `~/.zshrc`:

**Remove nvm block:**
```bash
# DELETE these lines:
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Also remove any lazy-loading nvm functions
```

**Add mise activation:**
```bash
# mise - unified version manager (replaces nvm, pyenv, etc.)
eval "$(mise activate zsh)"
```

### Create Global Config

Create `~/.config/mise/config.toml`:

```toml
[tools]
node = "lts"  # Default to LTS for new projects

[settings]
experimental = true
```

### Apply Changes

```bash
# Restart shell or source
source ~/.zshrc
```

If using a dotfiles manager (chezmoi, stow, etc.), apply via your usual workflow.

### Suggest Cleanup

After confirming mise works:

```
mise is now active. To complete cleanup:

1. Verify Node works: node --version
2. Remove old nvm directory: rm -rf ~/.nvm
3. Commit changes if using a dotfiles repo
```

**Do NOT auto-delete ~/.nvm** - let user do it after verification.

## Educational Content (--explain)

```
Why mise over nvm?
---------------------------------------------
Performance:
- nvm uses shims that add ~120ms latency to EVERY node/npm call
- mise modifies PATH directly—zero runtime overhead
- Shell startup is faster without nvm's initialization

Unified tooling:
- mise manages Node, Python, Go, Rust, Ruby, and 100+ more tools
- One tool, one config file format, one mental model
- .mise.toml replaces .nvmrc, .python-version, .ruby-version, etc.

Better DX:
- `which node` shows real path (not a shim)
- Automatic version switching when entering directories
- Clear error messages when version not installed

Security:
- mise has addressed supply chain concerns that affect asdf plugins
- Default registry is curated and maintained
---------------------------------------------
```

## Rollback

If something goes wrong:

```bash
# Restore old files from git
git checkout HEAD -- .nvmrc .node-version .tool-versions

# Remove mise config
rm .mise.toml

# Unstage changes
git reset HEAD
```

For dotfiles:
```bash
git checkout HEAD -- Brewfile
source ~/.zshrc
```
