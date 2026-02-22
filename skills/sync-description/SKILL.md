---
name: sync-description
description: >
  Update GitHub repo description from README analysis. Extracts purpose and
  differentiators, generates a concise description, and applies it via gh CLI.
---

# Sync Description

Analyze the current repository's README and update its GitHub description.

## Process

### 1. Verify Git Repo

Confirm we're in a git repository and get the remote origin URL:

```bash
gh repo view --json nameWithOwner -q '.nameWithOwner'
```

### 2. Read and Analyze README

Read README.md (or README, README.rst, etc.) and extract:

- Project purpose / what it does
- Key features or differentiators
- Target audience or use case

### 3. Generate Description

Create a concise description (max 350 characters for GitHub):

- Focus on WHAT the project does and WHY it's useful
- Use action-oriented language
- Avoid generic phrases like "A tool for..." — be specific

### 4. Get Current Description

```bash
gh repo view --json description -q '.description'
```

Show the current vs proposed description side-by-side.

### 5. Update Description

After user confirms:

```bash
gh repo edit --description "NEW_DESCRIPTION"
```

Confirm the update was successful.

## Description Style Guide

- Start with the primary function (verb or noun)
- Include 1-2 key differentiators
- Keep under 350 characters
- No trailing periods
- Examples:
  - "GitOps for Docker Compose on bare metal"
  - "MCP server providing Disney parks data to Claude - attractions, dining, height requirements, and fuzzy search"
  - "Cross-platform dotfiles managed by chezmoi - zsh, starship, Ghostty, 1Password SSH signing, and utility scripts"
