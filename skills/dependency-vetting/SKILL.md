---
name: dependency-vetting
description: >
  Evaluate third-party dependencies for trust and security before adoption.
  Use when installing MCP servers, CLI tools with credentials, packages with
  network access, or any dependency from an unknown author. Runs a structured
  5-phase assessment: author identity, dependency tree, source audit, build
  pipeline, and risk scoring.
---

# Dependency Vetting

Structured trust evaluation for third-party tools and dependencies before installation.

## When to Use

- Installing an MCP server that receives API keys, passwords, or tokens
- Adding a CLI tool that runs with elevated access
- Adopting a dependency that makes network calls on your behalf
- Any binary or package from an unknown author
- User asks "is this safe?", "should I trust this?", "vet this dependency"

## Process

Run all five phases. Use WebSearch and Bash (`gh` CLI) to gather evidence — don't guess.

### Phase 1: Author Identity

**Goal:** Establish who made this and whether they have a verifiable track record.

| Check | What to Look For | Red Flag |
|-------|-----------------|----------|
| Account age | Years on GitHub, not days/weeks | Account < 6 months old |
| Real identity | Name, blog, LinkedIn, company | Anonymous with no history |
| Repo portfolio | Consistent pattern of work in the domain | Single repo, no other activity |
| OSS contributions | Merged PRs to established projects | Zero external contributions |
| Community presence | Followers, stars on other projects | Completely isolated |

**Strongest trust signal:** Merged PRs to well-known projects with real code review gates (CNCF, Apache, major frameworks).

**How to check:**

```bash
gh api users/<author> --jq '{login, name, company, bio, created_at, public_repos, followers}'
gh api users/<author>/repos --jq '.[] | {name, stargazers_count, language, updated_at}' | head -20
```

### Phase 2: Dependency Tree

**Goal:** Verify the dependency count is proportional to scope and nothing suspicious is pulled in.

| Check | What to Look For | Red Flag |
|-------|-----------------|----------|
| Direct deps | Expected libraries for stated purpose | Analytics SDKs, telemetry, unknown network libs |
| Dep count | Proportional to project scope | 50+ deps for a simple tool |
| Known packages | Standard ecosystem packages | Obscure packages with few downloads |
| Pinning | Lock files present, versions pinned | No lock file, floating major versions |

**How to check:**

- **Go:** Read `go.mod` and `go.sum`
- **Node:** Read `package.json` and `package-lock.json`, run `npm audit`
- **Python:** Read `pyproject.toml` or `requirements.txt`, run `pip audit` or `uv pip audit`

### Phase 3: Source Code Audit

**Goal:** Search the source for patterns that indicate exfiltration, credential harvesting, or hidden behavior.

| Search For | Why | Suspicious If Found |
|-----------|-----|---------------------|
| Outbound HTTP calls (outside stated purpose) | Exfiltration, telemetry | `fetch()`, `http.Get()`, `requests.post()` to unknown URLs |
| Environment variable enumeration | Credential harvesting | `os.Environ()`, `process.env` iteration, `os.environ` dumps |
| Credential logging | Exposure | API keys, passwords, tokens in log statements |
| Encoded/obfuscated strings | Hidden behavior | Base64 URLs, hex-encoded hostnames |
| File system writes (outside stated purpose) | Persistence, staging | Writing to temp dirs, home directory, cron |
| Process spawning or shell invocation | Arbitrary command running | Shell commands with interpolated variables |

**What you want to see:** Credentials read from env vars, passed to a single SDK client constructor, never logged or transmitted elsewhere.

**How to check:** Clone the repo and use Grep to search for the patterns above.

### Phase 4: Build Pipeline

**Goal:** Verify the binary can be traced back to source.

| Check | What to Look For | Red Flag |
|-------|-----------------|----------|
| CI/CD | GitHub Actions, verifiable workflow files | Manual uploads, no CI |
| Action pinning | Actions pinned by SHA, not floating tags | `actions/checkout@v4` (unpinned) |
| Checksums | SHA256 in releases | No integrity verification |
| Signing | Cosign, SLSA provenance (ideal but rare) | Absence is common, not suspicious |
| Docker | Non-root user, pinned base image, minimal surface | Root user, `latest` tag |
| Reproducibility | Can you build from source? | Source and binary diverge |

**Strongest assurance:** Build from source yourself.

### Phase 5: Risk Score

Score each dimension 1-3 and compute:

| Dimension | Low (1) | Medium (2) | High (3) |
|-----------|---------|------------|----------|
| **Credential sensitivity** | Read-only, no secrets | API key to non-critical service | Admin creds to infrastructure |
| **Network access** | Local only | Outbound to known services | Arbitrary outbound |
| **Execution privilege** | Sandboxed | User-level | Root/admin |
| **Author trust** | Known contributor, long history | Established, some history | New account, no history |
| **Code auditability** | Small, readable | Medium, compiled but open source | Large, obfuscated, binary-only |

**Risk = Sensitivity x Access x Privilege x (4 - Trust) x (4 - Auditability)**

High score means slow down and verify more carefully, not reject outright.

## Output Format

After running all phases, produce this summary:

```
## Dependency: <name>
Author: <name> (GitHub: <handle>, account age: <years>)
Purpose: <what it does for us>
Credential exposure: <what secrets it receives>
Trust signals: <strongest evidence of legitimacy>
Concerns: <anything that gave pause>
Verdict: ADOPT / ADOPT WITH MITIGATIONS / REJECT
Mitigations: <if applicable>
```

## Mitigations for Medium Trust

- **Build from source** instead of using pre-built binaries
- **Pin the version** — don't auto-update
- **Create scoped credentials** — read-only API key, dedicated service account, minimum privilege
- **Network isolation** — run in a container with no outbound access except the target service
- **Monitor** — watch for unexpected network calls after installation
- **Review diffs on updates** — `git diff` between versions before upgrading
