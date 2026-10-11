---
name: github-trending
description: "Search popular GitHub repositories and discover recently trending projects. Also analyze a given GitHub repo: fetch its README, generate Chinese usage docs, applicable scenarios, and similar project recommendations. Use when the user asks for '热门项目', 'GitHub 热门', 'trending GitHub', '最近流行项目', 'search GitHub repos', '查找 GitHub 项目', 'GitHub 榜单', '介绍/分析/总结这个项目', '这个仓库怎么用', '推荐类似项目', or any request to find/popular/trending GitHub repositories by language, topic, or keyword."
version: 2.0.0
license: MIT
compatibility: "Requires python3 (stdlib only, no pip install). Optional env var GITHUB_TOKEN raises GitHub API rate limits from 10/hr to 5,000/hr. Needs outbound HTTPS to api.github.com and github.com."
metadata:
  repository: https://github.com/h2uan3g/github-trending-skill
  author: h2uan3g
---

# GitHub Trending & Popular Projects

Three modes: **popular search** (GitHub API), **trending** (github.com/trending page parser), and **repo analysis** (fetch README + generate Chinese docs).

## Script Location

Both helper scripts are bundled next to this `SKILL.md`. Resolve paths from **this skill's directory** — never assume an install location. The shell examples below use `$SKILL_DIR`, which stands for the absolute path of the directory containing this file (Pi prints that path when it advertises the skill):

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
ls "$SKILL_DIR"   # trending.py  repo_analyze.py  SKILL.md
```

Run the scripts from any working directory; they take arguments only and write JSON to stdout.

**Streams:** each script prints progress (`→ Fetching README ...`, warnings, errors) on **stderr** and the JSON payload on **stdout**. When parsing output, capture stdout only — do not merge `2>&1`.

## Quick Start

### Mode A — Popular Search (GitHub REST API)

```bash
# Top Python repos by stars
curl -s "https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc&per_page=10" \
  -H "User-Agent: github-trending-skill"

# With GITHUB_TOKEN (optional, raises rate limit from 10 to 5,000/hr)
curl -s "https://api.github.com/search/repositories?q=llm+language:python&sort=stars&order=desc&per_page=10" \
  -H "User-Agent: github-trending-skill" \
  -H "Authorization: Bearer $GITHUB_TOKEN"
```

**Query building:**

| Qualifier   | Example                                  |
| ----------- | ---------------------------------------- |
| `language:` | `language:python`, `language:TypeScript` |
| `topic:`    | `topic:ai`, `topic:machine-learning`     |
| `stars:`    | `stars:>1000`, `stars:500..5000`         |
| `created:`  | `created:>2024-01-01`                    |
| `pushed:`   | `pushed:>2024-06-01`                     |
| `is:`       | `is:public`, `is:featured`               |

Combine with `+` or space:

```
q=topic:ai+language:python+stars:>500&sort=stars&order=desc
```

**Response fields (per repo):** `full_name`, `description`, `stargazers_count`, `forks_count`, `language`, `html_url`, `created_at`, `updated_at`, `topics[]`, `owner.login`, `owner.avatar_url`.

### Mode B — Trending (GitHub Trending Page)

The community trending APIs (deno deploy, vercel) are no longer available. Use the bundled parser script instead:

```bash
# Daily trending (all languages)
python3 "$SKILL_DIR/trending.py" daily

# Daily trending in a specific language
python3 "$SKILL_DIR/trending.py" Python daily
python3 "$SKILL_DIR/trending.py" JavaScript weekly

# Valid periods: daily, weekly, monthly
python3 "$SKILL_DIR/trending.py" Go weekly
```

Supported languages (first arg): Python, JavaScript, Java, C++, TypeScript, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, Haskell, Clojure, Elixir, Dart, Lua, Perl, Shell, PowerShell, Objective-C, C#, F#, Groovy, Julia, Erlang, OCaml, Crystal, Nim, Zig, Elm, Solidity, Wasm, Fortran, Pascal, Ada, COBOL, Delphi.

**Output:** JSON array to stdout. Each entry:

```json
{
  "owner": "calesthio",
  "name": "OpenMontage",
  "full_name": "calesthio/OpenMontage",
  "url": "https://github.com/calesthio/OpenMontage",
  "description": "World's first open-source, agentic video production system...",
  "language": "Python",
  "total_stars": "52,359",
  "total_forks": "6,559",
  "period_stars": "1,292 stars today"
}
```

## Query-to-Mode Decision

| User intent                                | Mode         | Example command                                 |
| ------------------------------------------ | ------------ | ----------------------------------------------- |
| "热门 Python 项目"                         | A (search)   | `q=language:python&sort=stars`                  |
| "最近火的项目"                             | B (trending) | `trending.py daily`                             |
| "GitHub 上 stars 最多的 AI 项目"           | A (search)   | `q=topic:ai&sort=stars`                         |
| "这周最 trending 的 Go 项目"               | B (trending) | `trending.py Go weekly`                         |
| "推荐几个好用的开源库"                     | A (search)   | `q=topic:library+language:python&sort=stars`    |
| "介绍/分析这个项目 https://github.com/..." | C (analyze)  | `repo_analyze.py https://github.com/owner/repo` |
| "这个仓库怎么用？"                         | C (analyze)  | `repo_analyze.py owner/repo`                    |

## Output Format

Present results as a clean markdown list. For each repo:

```
⭐ **owner/name** — description (truncated to ~120 chars)
   Language: X | ⭐ total_stars | Forks: total_forks | Updated: date
   URL: https://github.com/owner/name
```

For trending mode, add the period star gain prominently:

```
⭐ **calesthio/OpenMontage** — World's first open-source, agentic video production system...
   Language: Python | ⭐ 52,359 | +1,292 today | Forks: 6,559
   https://github.com/calesthio/OpenMontage
```

---

## Mode C — Repo Analysis (仓库分析)

Given a GitHub URL, fetches the repo's metadata + full README, then generates:

- **优化后的使用方法** — translated & restructured installation + usage docs
- **适用场景** — when to use / not use this project, based on its README and topics
- **类似项目推荐** — similar repos discovered via GitHub topic + language search

### Quick Start

```bash
# From a full URL
python3 "$SKILL_DIR/repo_analyze.py" https://github.com/owner/repo

# From owner/repo shorthand
python3 "$SKILL_DIR/repo_analyze.py" owner/repo
```

**Output:** JSON on stdout with these top-level keys:

```jsonc
{
  "repo": {              // full_name, description, language, stars, forks,
                         // topics[], url, owner, updated_at, size, open_issues
  },
  "readme": "...",       // raw README text; empty string when the repo has none
  "similar_projects": [  // { full_name, description, stars, language, url, topics }
  ],
  "_rate_limited": false // true when similar_projects came back empty due to API limits
}
```

### Agent Workflow (after running the script)

1. **Parse the README** — extract sections: features, requirements, installation, usage, API, examples, configuration, contributing
2. **Translate & optimize** — rewrite key sections into clear Chinese. Don't just translate verbatim; restructure for clarity:
   - Usage → 使用方法: extract commands, code examples, config steps
   - Requirements → 环境要求: list dependencies, language versions, OS
   - Features → 核心特性: bullet points from README headings
3. **Derive 适用场景** from the README + topics + description:
   - What problem does it solve? (from description & README intro)
   - Who is it for? (developers, researchers, designers, etc.)
   - When to use it? (specific use-cases mentioned in README)
   - When NOT to use it? (infer from limitations, issues, or what it explicitly isn't)
4. **Present similar projects** — for each, show: name, one-line description, stars, why it's similar (shared topic/language)

### Output Format

```markdown
# 📦 {repo_full_name}

> {Chinese translation of description}

## 核心特性

- 特性 1
- 特性 2
  ...

## 环境要求

- 依赖 1
- Python >= 3.8 / Node >= 18 ...

## 使用方法

### 安装

\`\`\`bash

# 安装命令

\`\`\`

### 快速开始

\`\`\`python

# 代码示例

\`\`\`

## 适用场景

✅ **适合:**

- 场景 1
- 场景 2

❌ **不适合:**

- 限制 1

## 类似项目

| 项目              | 描述 | ⭐   | 相似点        |
| ----------------- | ---- | ---- | ------------- |
| [owner/name](url) | ...  | 1.2k | 同 topic: xxx |

...

📊 数据: {stars} stars | {language} | 更新于 {date}
🔗 {url}
```

### When to Trigger Mode C

| User says                                       | Trigger   |
| ----------------------------------------------- | --------- |
| "介绍/总结/分析这个项目 https://github.com/..." | ✅ Mode C |
| "这个仓库怎么用？"                              | ✅ Mode C |
| "帮我看看 https://github.com/... 的 README"     | ✅ Mode C |
| "推荐一些类似 X 的项目" (with a repo URL)       | ✅ Mode C |
| "GitHub 上 stars 最多的 AI 项目"                | Mode A    |
| "最近火的 Python 项目"                          | Mode B    |

## Notes & Limitations

- **Rate limits (unauthenticated):** 10 requests/hour for core, 30 searches/minute for search API. If you hit `403rate limit exceeded`, set `GITHUB_TOKEN` env var.
- **Mode C makes 2-4 API calls** (repo info + readme + 1-2 search queries). Without a token, you may hit the rate limit after ~2-3 analyses. Set `GITHUB_TOKEN` for unlimited use.
- **Trending page:** The parser targets github.com/trending HTML structure. If GitHub changes their markup, update the regex patterns in `trending.py`.
- **Trending star counts** are only available from the trending page, not the official search API.
- **Topic filtering:** Use `topic:` qualifier in search queries. Trending page does not support topic filtering natively.
- **Language filtering:** Search API uses `language:` qualifier (case-sensitive, e.g. `language:TypeScript`). Trending page uses URL path (e.g. `/trending/TypeScript`).
- **Periods:** Trending supports `daily` (24h), `weekly`, `monthly`. Search API has no equivalent — use `created:` or `pushed:` qualifiers for recency.
- **README not found:** Some repos use README.md, README.rst, or no README at all. The script tries both `main` and `master` branches and falls back to the GitHub API. If no README is found, the `readme` field will be an empty string.
