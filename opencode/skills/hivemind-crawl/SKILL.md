---
name: hivemind-crawl
description: How to crawl external documentation sites for hivemind experts. Load when the user wants to add docs to an expert, enrich an agent with web content, or crawl a URL for a named expert. Covers expert resolution, the crawler subagent spawn pattern, and prerequisites.
---

# Crawling external docs

Use when the user wants to crawl a website and save the output as
supplementary knowledge for a git-analyzed expert.

## 1. Resolve the expert

If the user named the expert ("crawl site X **for bazel**"):

- Call `list_agents(state="all")` to verify the agent exists in the
  catalog.
- If missing: "No expert named '<name>' in the catalog." The user
  needs to add it via the curator first.
- If found: confirm with the user, then spawn the crawler (step 3).

If the user did NOT name the expert ("crawl https://docs.nocobase.com"):

- Infer a candidate name from the URL hostname: strip `https://`,
  extract the primary subdomain (docs.**nocobase**.com → nocobase,
  docs.**pydantic**.dev → pydantic).
- Call `list_agents(state="all")` and case-insensitive check whether
  the candidate appears as a substring of any agent name.
- If exactly one match: present it to the user. Example: "I'll crawl
  this for **nocobase** — that expert is in the catalog."
- If zero or multiple fuzzy matches: list the candidates (or the full
  enabled agents list) and ask the user to pick. Do not guess.
- If no plausible match exists in the catalog: say so. The user needs
  to add an expert first.

## 2. Confirm

Present the resolved pair — URL + expert name — and ask the user to
confirm. Never spawn the crawler without explicit confirmation.

## 3. Spawn the crawler

```
Task(
  subagent_type="hivemind-crawler",
  background=true,
  description="crawl docs for <name>",
  prompt="Crawl <url> for <name> [with max <N> pages]",
)
```

Use `read_task_result(task_id)` to surface the crawl summary once
it completes.

Recommend `with max 100 pages` unless the user explicitly asks for
a different cap or unlimited. Uncapped crawls on large docs sites can
run for tens of minutes and produce thousands of pages.

## 4. Results

Output lands at `~/.cache/hivemind/external_docs/<name>/`. The
expert agent reads from this path natively (its deployed file grants
`external_directory: allow` on the cache tree), so no redeploy is
needed. If the expert isn't enabled, the docs still land but the
expert won't see them until it's deployed — recommend `enable_agent`
if relevant.

## Prerequisites

Sites requiring JavaScript rendering need Chromium. If the crawler
reports:

```
This site requires browser rendering, but Chromium isn't installed
```

The user must run `playwright install chromium` once on the host
machine, then retry.
