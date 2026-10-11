#!/usr/bin/env python3
"""
GitHub Trending Parser - Fetches trending repos from github.com/trending

Usage:
  python trending.py [language] [period]

  language: Python, JavaScript, TypeScript, Go, Rust, etc. (optional)
  period:   daily, weekly, monthly (default: daily)

Output: JSON array of repo objects to stdout.

Example:
  python trending.py Python daily
  python trending.py weekly
"""

import re
import json
import sys
import urllib.request
import urllib.error
import html as html_mod

GITHUB_TRENDING_URL = "https://github.com/trending"

# Known languages for validation
KNOWN_LANGUAGES = {
    'Python', 'JavaScript', 'Java', 'C++', 'TypeScript', 'Go', 'Rust',
    'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'Haskell', 'Clojure',
    'Elixir', 'Dart', 'Lua', 'Perl', 'Shell', 'PowerShell', 'Objective-C',
    'C#', 'F#', 'Groovy', 'Julia', 'Erlang', 'OCaml', 'Crystal', 'Nim',
    'Zig', 'Elm', 'Solidity', 'Wasm', 'Fortran', 'Pascal', 'Ada',
    'COBOL', 'Delphi', 'Haxe', 'Fantom', 'Idris', 'Agda', 'Coq',
    'Racket', 'Scheme', 'Common Lisp', 'Smalltalk', 'D', 'Vala',
    'Gradle', 'Makefile', 'CMake', 'Nix', 'HCL', ' TOML', ' YAML',
    'Jinja2', 'Markdown', 'Dockerfile', 'GraphQL', 'Protobuf', 'Thrift',
}

LANG_URL_NAMES = {
    'Python': 'python', 'JavaScript': 'javascript', 'Java': 'java',
    'C++': 'c++', 'TypeScript': 'typescript', 'Go': 'go', 'Rust': 'rust',
    'Ruby': 'ruby', 'PHP': 'php', 'Swift': 'swift', 'Kotlin': 'kotlin',
    'Scala': 'scala', 'Haskell': 'haskell', 'Clojure': 'clojure',
    'Elixir': 'elixir', 'Dart': 'dart', 'Lua': 'lua', 'Perl': 'perl',
    'Shell': 'shell', 'PowerShell': 'powershell', 'Objective-C': 'objectivec',
    'C#': 'csharp', 'F#': 'fsharp', 'Groovy': 'groovy', 'Julia': 'julia',
    'Erlang': 'erlang', 'OCaml': 'ocaml', 'Crystal': 'crystal', 'Nim': 'nim',
    'Zig': 'zig', 'Elm': 'elm', 'Solidity': 'solidity', 'Wasm': 'wasm',
    'Fortran': 'fortran', 'Pascal': 'pascal', 'Ada': 'ada',
    'COBOL': 'cobol', 'Delphi': 'delphi',
}


def fetch_trending_page(language=None, period='daily'):
    """Fetch the GitHub trending page HTML."""
    path = '/trending'
    if language:
        lang_url = LANG_URL_NAMES.get(language, language.lower())
        path = f'/trending/{lang_url}'
    
    url = f"https://github.com{path}"
    if period and period != 'daily':
        url += f"?since={period}"
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; GitHub-Trending-Skill)',
        'Accept': 'text/html,application/xhtml+xml',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code} fetching {url}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)


def parse_trending(html_content):
    """Parse trending repos from GitHub trending page HTML."""
    # Find all h2 blocks
    h2_blocks = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.DOTALL)
    
    repos = []
    for block in h2_blocks:
        if 'Navigation Menu' in block:
            continue
        
        href_match = re.search(r'href="(/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', block)
        if not href_match:
            continue
        
        href = href_match.group(1)
        # Skip non-repo links
        if any(x in href for x in ('/sponsors/', '/apps/', '/trending/', '/explore/', '/login', '/register')):
            continue
        
        # Extract owner and name from text
        text = re.sub(r'<[^>]+>', ' ', block)
        text = re.sub(r'\s+', ' ', text).strip()
        parts = re.split(r'\s*/\s*', text, maxsplit=1)
        if len(parts) != 2:
            continue
        owner = parts[0].strip()
        name = parts[1].strip()
        
        # Find context after this h2
        idx = html_content.find(f'href="{href}"')
        if idx < 0:
            continue
        h2_start = html_content.rfind('<h2', 0, idx)
        h2_end = html_content.find('</h2>', idx)
        if h2_start < 0 or h2_end < 0:
            continue
        h2_end += 5
        context = html_content[h2_end:h2_end + 8000]
        
        # Extract description
        desc = ""
        text_nodes = re.findall(r'>([^<]{10,500})<', context)
        skip_patterns = [
            r'^[\d,\s]+$',
            r'^(star|stars|fork|forks|built by|sponsor|you must be signed in)',
            r'(stars today|stars this week|stars this month)',
            r'^https?://',
            r'^<',
            r'^\s*$',
        ]
        for t in text_nodes:
            t = t.strip()
            if not t or len(t) < 10:
                continue
            should_skip = False
            for pat in skip_patterns:
                if re.search(pat, t, re.IGNORECASE):
                    should_skip = True
                    break
            if not should_skip:
                desc = t
                break
        
        # Extract language
        lang = ""
        lang_match = re.search(
            r'\b(Python|JavaScript|Java|C\+\+|TypeScript|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|Haskell|Clojure|Elixir|Dart|Lua|Perl|Shell|PowerShell|Objective-C|C#|F#|Groovy|Julia|Erlang|OCaml|Crystal|Nim|Zig|Elm|Solidity|Wasm|Fortran|Pascal|Ada|COBOL|Delphi)\b',
            context
        )
        if lang_match:
            lang = lang_match.group(1)
        
        # Extract total stars
        star_match = re.search(
            r'<a\s+href="' + re.escape(href) + r'/stargazers"[^>]*>.*?([\d,]+)\s*</a>',
            context, re.DOTALL
        )
        total_stars = star_match.group(1) if star_match else ""
        
        # Extract forks
        fork_match = re.search(
            r'<a\s+href="' + re.escape(href) + r'/forks"[^>]*>.*?([\d,]+)\s*</a>',
            context, re.DOTALL
        )
        total_forks = fork_match.group(1) if fork_match else ""
        
        # Extract period stars
        period_stars = ""
        period_match = re.search(
            r'(\d[\d,]*)\s*(stars today|stars this week|stars this month)',
            context, re.IGNORECASE
        )
        if period_match:
            period_stars = f"{period_match.group(1)} {period_match.group(2)}"
        
        repos.append({
            'owner': owner,
            'name': name,
            'full_name': f"{owner}/{name}",
            'url': f"https://github.com{href}",
            'description': desc,
            'language': lang,
            'total_stars': total_stars,
            'total_forks': total_forks,
            'period_stars': period_stars,
        })
    
    return repos


def main():
    language = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in LANG_URL_NAMES else None
    period = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ('daily', 'weekly', 'monthly') else 'daily'
    
    # If first arg is a period, treat it as such
    if not language and len(sys.argv) > 1 and sys.argv[1] in ('daily', 'weekly', 'monthly'):
        period = sys.argv[1]
    
    html_content = fetch_trending_page(language, period)
    repos = parse_trending(html_content)
    
    # Output as JSON
    print(json.dumps(repos, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()