---
name: install-github-app-safely
description: >
  Install the Claude Code GitHub App with DDoS/abuse safeguards. Runs the
  standard install, then hardens fork PR workflows, audits the workflow file
  for unsafe triggers, and reminds about API spend limits.
license: MIT
metadata:
  author: cameronsjo
  version: "1.0"
---

# Install GitHub App Safely

Install the Claude Code GitHub App on the current repository, then apply
safeguards to prevent abuse from external contributors running up your API bill.

## Process

### Step 1: Verify Prerequisites

1. Confirm we're in a git repo with a GitHub remote
2. Confirm `gh` CLI is authenticated
3. Confirm user has admin access to the repo (required for settings changes)

```bash
gh repo view --json nameWithOwner,isPrivate --jq '.nameWithOwner + " (private: " + (.isPrivate | tostring) + ")"'
```

### Step 2: Run the Standard Install

Run the built-in `/install-github-app` command to set up the Claude GitHub App
and configure secrets.

**IMPORTANT**: Pause here and let the user complete the interactive install
flow. Wait for confirmation before proceeding.

After the install completes, **pull remote changes** — the install creates a
branch with the workflow file and merges it remotely, so your local repo will
be behind:

```bash
git pull
```

If there's a merge conflict on `.github/workflows/claude.yml`, resolve it by
keeping the remote version (it uses the official `@v1` action with
`claude_code_oauth_token`), then layer on any hardening changes in Step 4.

### Step 3: Harden Fork PR Workflows

Get the repo owner/name for API calls:

```bash
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
```

Check current fork PR approval policy:

```bash
gh api "repos/${REPO}/actions/permissions/fork-pr-contributor-approval" -q '.approval_policy'
```

Set it to require approval for all outside collaborators:

```bash
gh api -X PUT "repos/${REPO}/actions/permissions/fork-pr-contributor-approval" \
  --field approval_policy=all_external_contributors
```

**Manual verification URL** (in case the API call fails):
`https://github.com/{owner}/{repo}/settings/actions` — look under
"Fork pull request workflows" and select "Require approval for all outside
collaborators".

### Step 4: Audit the Workflow File

Find and review the Claude Code Action workflow:

```bash
grep -rl "claude" .github/workflows/ 2>/dev/null
```

Check for these safety issues:

1. **Trigger events**: Should use `pull_request` NOT `pull_request_target`
   (the latter runs with base repo secrets and is dangerous for forks)
2. **Permissions**: Should be minimal (`contents: read`, `pull-requests: write`,
   `issues: write`)
3. **Concurrency**: Should have concurrency limits to prevent parallel abuse

If the workflow uses `pull_request_target`, warn the user loudly and offer to
change it to `pull_request`.

If no concurrency block exists, add one:

```yaml
concurrency:
  group: claude-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

### Step 5: Check API Spend Limits

Remind the user to set a spend limit on their Anthropic API account:

1. Visit https://console.anthropic.com/settings/limits
2. Set a monthly spend limit that matches their budget
3. Optionally set up usage alerts

### Step 6: Summary

Report what was configured:

```
GitHub App Safety Checklist:
  [x] Claude GitHub App installed
  [x] Remote workflow pulled and merged
  [x] Fork PR workflows require approval (via API)
  [x] Workflow uses safe trigger events (pull_request, not pull_request_target)
  [x] Workflow has minimal permissions
  [x] Concurrency limits configured
  [ ] API spend limit set (manual - visit console.anthropic.com)

Remaining manual steps:
  - Set API spend limit at https://console.anthropic.com/settings/limits
```
