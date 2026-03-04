---
name: skill-scout
description: Evaluate a GitHub repo — what it does, how it works, what problem it solves, when to use it, and how to invoke it. Then offers to build a Claude skill from it. Drop in any GitHub URL or owner/repo slug. Works on both github.com and GitHub Enterprise instances.
license: MIT
metadata:
  author: cameronsjo
  version: "1.0"
---

# Scout

Evaluate any GitHub repo and optionally build a Claude skill from it.

## Invocation

```
/scout https://github.com/owner/repo
/scout owner/repo
/scout github.example.com/org/repo
```

## Step 1 — Identify and fetch the repo

Parse the input to extract host + owner/repo.

> **Enterprise repos:** prefix all `gh` calls with `GH_HOST=<enterprise-hostname>`
> **Fallback:** if `gh api` fails (private/inaccessible), use `WebFetch` on the repo URL

Issue these as **parallel Bash tool calls** (separate tool invocations, not chained):

```bash
# Call 1 — Repo metadata
gh repo view owner/repo --json name,description,primaryLanguage,stargazerCount,topics,url
```

```bash
# Call 2 — README
gh api repos/owner/repo/readme --jq '.content' | base64 -d
```

```bash
# Call 3 — File tree, skill detection, package manifests
gh api repos/owner/repo/contents --jq '.[].name'
gh api repos/owner/repo/contents/package.json --jq '.content' | base64 -d 2>/dev/null
gh api repos/owner/repo/contents/pyproject.toml --jq '.content' | base64 -d 2>/dev/null
# Does this repo already ship its own Claude skill?
gh api repos/owner/repo/contents/skills --jq '.[].name' 2>/dev/null
gh api repos/owner/repo/contents/.claude-plugin --jq '.[].name' 2>/dev/null
```

Note whether a `skills/` or `.claude-plugin/` directory exists — this determines the path in Step 3.

**Verify capability claims against source** — READMEs describe aspirational or removed features. If the README mentions a specific CLI mode, transport, or feature that affects Skill potential, confirm it exists in source:

```bash
# Confirm CLI entry points actually exist
gh api repos/owner/repo/contents/pyproject.toml --jq '.content' | base64 -d | grep -A10 "\[project.scripts\]"
# or JS:
gh api repos/owner/repo/contents/package.json --jq '.content' | base64 -d | jq '.bin'
```

Document discrepancies (README claims X, source says Y) in the **How it works** section.

## Step 2 — Produce the Scout Report

Output this exact structure:

---

## 🔭 Scout: `owner/repo`

**What it does**
One or two sentences. Plain language. No jargon.

**Problem it solves**
What pain exists without this tool? What is annoying/manual/slow/impossible?

**How it works**
2–4 bullet points on the architecture or approach. Focus on what's interesting or non-obvious.

**When to use it**
Concrete scenarios. "Use when you need to X", "Good fit if Y".

**When NOT to use it**
Explicit anti-cases. "Skip if Z", "Avoid when the corpus is X".

**Integration surface** — [REST / CLI / SDK-only / binary protocol / MCP / interactive UI]
How Claude (or the user) actually calls this tool. SDK-only or binary protocol = no direct shell access → helper scripts or MCP server required.

**Runtime dependencies**
Services or infrastructure this tool needs running (Docker, Ollama, a daemon, a database). Omit if none.

**How to invoke it**
The actual commands or API calls. Copy-pasteable. Include install if needed.

**Skill potential** — [High-reference / High-integration / Medium / Low / Not a fit]
Assessment of whether this makes a good Claude skill, and what that skill would do.
- High-reference: clear CLI workflow Claude can orchestrate, OR Claude has no native knowledge of the tool's commands/config — `SKILL.md` + optional helper script
- High-integration: no direct shell access (binary protocol, daemon, SDK-only) — needs MCP server + setup runbook + helper scripts. See `~/.claude/skills/gibram/` as the pattern.
- Medium: useful reference but mostly just documentation
- Low: library/SDK — no CLI, no automation surface
- Not a fit: already covered, too narrow, or requires interactive UI

If a `skills/` or `.claude-plugin/` directory was found: note "Already skill-ready — install via `npx skills add`" and set potential to High-reference.

---

## Step 3 — Offer to build the skill

After the report, the offer depends on what was found in Step 1:

**If `skills/` or `.claude-plugin/` was found** — the repo already ships a skill. Ask:

> **Want me to install this skill?**
> - **Yes** — I'll run `npx skills add owner/repo --global --skill '*' --yes`
> - **No** — report only

**If no `skills/` dir was found** — offer to scaffold one. Ask:

> **Want me to build a skill from this?**
> - **Yes** — I'll scaffold `~/.claude/skills/<name>/SKILL.md` (and any helper scripts if needed)
> - **No** — report only

## Step 4 — If they say yes, build the skill

Patterns to reference:
- Reference skill: `~/.claude/skills/pretty-diagrams/SKILL.md`
- Action skill: `~/.claude/skills/diagram/SKILL.md`
- Integration skill: `~/.claude/skills/gibram/` (MCP server + runbook pattern)

1. **Pick the skill name** — short, verb or noun, kebab-case (e.g. `scout`, `diagram`, `pretty-diagrams`). The `name` field in frontmatter **becomes the slash command** (`/name`), so optimize for what the user would type. Shorter is better.

2. **Decide: reference, action, or integration skill?**
   - Reference skill: workflow tables, markup patterns, when-to-use — for tools Claude should *know about*
   - Action skill: numbered execution workflow at the top, detect → do → report — for tools Claude should *run* via CLI
   - Integration skill: no usable CLI (binary protocol, daemon, SDK-only) — needs `SKILL.md` + MCP server + helper scripts
   - If the tool has a CLI and Claude would run it → action skill
   - If integration surface is SDK-only or binary → integration skill
   - If it's a library or pattern guide → reference skill

3. **Write the `description` field for zero-friction invocation** — the description drives semantic matching, not the name. Pack it with natural language phrases the user would actually say:
   - Bad: `"Tool that manages X configuration"`
   - Good: `"Manage X config. Use when the user says 'set up X', 'configure X', 'sync X', 'wire up X', or asks about getting X working."`
   - For action skills especially: list 4–6 trigger phrases so it fires on casual language, not just the exact slash command

4. **Assess if a helper script is needed** — only if the tool lacks a real CLI. See `~/.local/share/mmd-render/` as the pattern for library wrappers.

5. **Write `SKILL.md` and `README.md`**
   - `SKILL.md` — what Claude executes; action skills lead with the execution flow, reference skills lead with a table
   - `README.md` — what humans read; covers what it solves, how it works, when to use it, what it doesn't do

6. **Report what was created**

## Notes

- If the README is > 3000 words, read the first 1500 and skim the rest
- For repos without a README, use the file tree + package manifest to infer purpose
- The "Skill potential" rating is the most valuable output — be honest about Low/Not a fit
