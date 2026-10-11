#!/usr/bin/env python3
"""
GitHub Repo Analyzer - Fetches repo metadata, README, and similar projects.

Given a GitHub URL or owner/repo, fetches:
  - Repo metadata (stars, language, topics, description)
  - Full README.md content
  - Similar/trending projects via GitHub search API

Usage:
  python repo_analyze.py <github_url_or_owner/repo>
  python repo_analyze.py https://github.com/owner/repo
  python repo_analyze.py owner/repo

Output: JSON to stdout with keys: repo, readme, similar_projects.

Environment:
  GITHUB_TOKEN  Optional. Raises rate limits from 10 to 5,000/hr.
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse
import re
import os
import base64

GITHUB_API = "https://api.github.com"


def api_get(url, token=None):
    """GET a GitHub API URL, return parsed JSON or None on failure."""
    headers = {
        'User-Agent': 'github-repo-analyzer',
        'Accept': 'application/vnd.github.v3+json',
    }
    tok = token or os.environ.get('GITHUB_TOKEN')
    if tok:
        headers['Authorization'] = f"Bearer {tok}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"HTTP {e.code} for {url}: {body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def parse_repo_url(url):
    """Parse owner/repo from a GitHub URL or 'owner/repo' string."""
    url = url.strip().rstrip('/')
    # "owner/repo" shorthand
    if '/' in url and not url.startswith('http'):
        parts = url.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1]
    # Full URL: https://github.com/owner/repo[/...]
    m = re.search(r'github\.com/([^/]+)/([^/]+?)(?:$|/|\?)', url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def fetch_repo_info(owner, repo):
    """Fetch repo metadata from the GitHub API."""
    return api_get(f"{GITHUB_API}/repos/{owner}/{repo}")


def fetch_readme(owner, repo):
    """Fetch README.md — tries raw.githubusercontent.com first, then API."""
    # Try raw on main / master
    for branch in ('main', 'master'):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        headers = {'User-Agent': 'github-repo-analyzer'}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
        except Exception:
            continue

    # Fallback: GitHub API (base64-encoded)
    result = api_get(f"{GITHUB_API}/repos/{owner}/{repo}/readme")
    if result and 'content' in result:
        try:
            return base64.b64decode(result['content']).decode('utf-8', errors='replace')
        except Exception:
            pass
    return ""


def fetch_similar_projects(repo_info, limit=6):
    """Search GitHub for similar repos using topics + language as signals.
    Returns (repos_list, rate_limited_bool)."""
    topics = repo_info.get('topics', []) or []
    language = repo_info.get('language', '')
    owner_login = (repo_info.get('owner') or {}).get('login', '')
    repo_name = repo_info.get('name', '')
    skip_full = f"{owner_login}/{repo_name}"
    topic_set = set(t.lower() for t in topics)

    # Build ranked queries — prefer topic+language combos, then topic-only, then language
    queries = []
    if topics and language:
        top_topics = topics[:3]
        queries.append('+'.join([f'topic:{t}' for t in top_topics] + [f'language:{language}']))
    if topics:
        queries.append('+'.join(f'topic:{t}' for t in topics[:5]))
    if language:
        queries.append(f'language:{language} stars:>200')

    all_repos = []
    seen = {skip_full}
    any_success = False

    for q in queries:
        url = f"{GITHUB_API}/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page={limit + 10}"
        result = api_get(url)
        if result is None:
            continue
        any_success = True
        if 'items' in result:
            for item in result['items']:
                full = item.get('full_name', '')
                if full in seen:
                    continue
                seen.add(full)
                item_topics = set(t.lower() for t in (item.get('topics') or []))
                overlap = len(topic_set & item_topics)
                all_repos.append({
                    'full_name': full,
                    'description': item.get('description') or '',
                    'stars': item.get('stargazers_count', 0),
                    'language': item.get('language') or '',
                    'url': item.get('html_url', ''),
                    'topics': item.get('topics', []) or [],
                    'topic_overlap': overlap,
                })
        # Sort by topic overlap (desc) then stars (desc) for ranking
        if all_repos:
            all_repos.sort(key=lambda r: (r['topic_overlap'], r['stars']), reverse=True)
        if len(all_repos) >= limit:
            break

    # Trim and remove internal field
    result = []
    for r in all_repos[:limit]:
        r.pop('topic_overlap', None)
        result.append(r)
    return result, not any_success


def main():
    if len(sys.argv) < 2:
        print("Usage: python repo_analyze.py <github_url_or_owner/repo>", file=sys.stderr)
        sys.exit(1)

    owner, repo = parse_repo_url(sys.argv[1])
    if not owner or not repo:
        print(f"Could not parse GitHub repo from: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    print(f"→ Fetching repo info for {owner}/{repo} ...", file=sys.stderr)
    repo_info = fetch_repo_info(owner, repo)
    if not repo_info:
        print(f"✗ Failed to fetch repo info for {owner}/{repo}", file=sys.stderr)
        sys.exit(1)

    print(f"→ Fetching README ...", file=sys.stderr)
    readme = fetch_readme(owner, repo)
    if not readme:
        print("⚠ No README found", file=sys.stderr)

    print(f"→ Finding similar projects ...", file=sys.stderr)
    similar, search_failed = fetch_similar_projects(repo_info)
    if search_failed:
        print("⚠ GitHub API rate limit hit — similar projects unavailable. Set GITHUB_TOKEN env var for higher limits.", file=sys.stderr)

    output = {
        'repo': {
            'full_name': repo_info.get('full_name', ''),
            'description': repo_info.get('description') or '',
            'language': repo_info.get('language') or '',
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'topics': repo_info.get('topics', []) or [],
            'url': repo_info.get('html_url', ''),
            'owner': owner,
            'updated_at': repo_info.get('updated_at', ''),
            'size': repo_info.get('size', 0),
            'open_issues': repo_info.get('open_issues_count', 0),
        },
        'readme': readme,
        'similar_projects': similar,
        '_rate_limited': search_failed,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()