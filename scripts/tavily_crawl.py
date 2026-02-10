#!/usr/bin/env python3
"""
Tavily Crawl - Crawl websites and optionally save as markdown files

Usage:
    uv run scripts/tavily_crawl.py <url> [options]

Options:
    --max-depth N              Crawl depth 1-5 (default: 1)
    --max-breadth N            Links per page (default: 20)
    --limit N                  Total pages cap (default: 50)
    --instructions TEXT        Natural language focus guidance
    --chunks-per-source N      Chunks per page 1-5 (requires --instructions)
    --extract-depth DEPTH      basic or advanced (default: basic)
    --format FORMAT            markdown or text (default: markdown)
    --select-paths P1,P2       Regex patterns to include
    --exclude-paths P1,P2      Regex patterns to exclude
    --allow-external           Allow external domain links (default)
    --no-allow-external        Stay on same domain
    --timeout N                Max wait seconds (default: 150)
    --output-dir PATH          Save each page as a markdown file
    --json                     Output raw JSON response

Environment:
    TAVILY_API_KEY             Your Tavily API key (required)

Examples:
    uv run scripts/tavily_crawl.py https://docs.example.com
    uv run scripts/tavily_crawl.py https://docs.example.com --max-depth 2 --limit 20
    uv run scripts/tavily_crawl.py https://docs.example.com --max-depth 2 --output-dir ./docs
    uv run scripts/tavily_crawl.py https://example.com --instructions "Find API docs" --chunks-per-source 3
    uv run scripts/tavily_crawl.py https://example.com --select-paths "/docs/.*,/api/.*" --exclude-paths "/blog/.*"
"""

import argparse
import json
import os
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TAVILY_API_URL = "https://api.tavily.com/crawl"


def crawl(
    url: str,
    api_key: str,
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = 50,
    instructions: str = None,
    chunks_per_source: int = None,
    extract_depth: str = "basic",
    fmt: str = "markdown",
    select_paths: list = None,
    exclude_paths: list = None,
    allow_external: bool = True,
    timeout: int = 150,
) -> dict:
    """Crawl a website using Tavily."""

    payload = {
        "url": url,
        "max_depth": max_depth,
        "max_breadth": max_breadth,
        "limit": limit,
        "extract_depth": extract_depth,
        "format": fmt,
        "allow_external": allow_external,
        "timeout": timeout,
    }

    if instructions:
        payload["instructions"] = instructions
    if chunks_per_source:
        payload["chunks_per_source"] = chunks_per_source
    if select_paths:
        payload["select_paths"] = select_paths
    if exclude_paths:
        payload["exclude_paths"] = exclude_paths

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "x-client-source": "claude-code-skill",
    }

    req = Request(
        TAVILY_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Tavily API error {e.code}: {error_body}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def sanitize_filename(url: str) -> str:
    """Convert a URL to a safe filename."""
    name = re.sub(r'^https?://', '', url)
    name = re.sub(r'[/:?&=]', '_', name)
    return name[:100]


def save_pages(results: list, output_dir: str) -> list:
    """Save crawled pages as markdown files. Returns list of saved paths."""
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for r in results:
        url = r.get("url", "")
        content = r.get("raw_content", "")
        if not content:
            continue
        filename = sanitize_filename(url) + ".md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(f"# {url}\n\n{content}")
        saved.append(filepath)
    return saved


def format_results(response: dict) -> str:
    """Format crawl results for human reading."""
    lines = []

    base_url = response.get("base_url", "")
    results = response.get("results", [])

    lines.append(f"## Crawl Results: {base_url}")
    lines.append(f"{len(results)} pages crawled")
    lines.append("")

    for i, r in enumerate(results, 1):
        url = r.get("url", "Unknown URL")
        content = r.get("raw_content", "")
        lines.append(f"### {i}. {url}")
        lines.append("")
        if content:
            if len(content) > 2000:
                lines.append(content[:2000])
                lines.append(f"\n... [truncated, {len(content)} chars total]")
            else:
                lines.append(content)
        else:
            lines.append("*No content extracted*")
        lines.append("")
        lines.append("---")
        lines.append("")

    response_time = response.get("response_time")
    if response_time:
        lines.append(f"*Crawl completed in {response_time:.1f}s*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Crawl websites using Tavily")
    parser.add_argument("url", help="Root URL to crawl")
    parser.add_argument("--max-depth", type=int, default=1,
                        help="Crawl depth 1-5 (default: 1)")
    parser.add_argument("--max-breadth", type=int, default=20,
                        help="Links per page (default: 20)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Total pages cap (default: 50)")
    parser.add_argument("--instructions",
                        help="Natural language focus guidance")
    parser.add_argument("--chunks-per-source", type=int,
                        help="Chunks per page 1-5 (requires --instructions)")
    parser.add_argument("--extract-depth", choices=["basic", "advanced"], default="basic",
                        help="Extraction depth (default: basic)")
    parser.add_argument("--format", choices=["markdown", "text"], default="markdown",
                        dest="fmt", help="Output format (default: markdown)")
    parser.add_argument("--select-paths",
                        help="Comma-separated regex patterns to include")
    parser.add_argument("--exclude-paths",
                        help="Comma-separated regex patterns to exclude")
    parser.add_argument("--allow-external", action="store_true", default=True,
                        help="Allow external domain links (default)")
    parser.add_argument("--no-allow-external", action="store_false", dest="allow_external",
                        help="Stay on same domain")
    parser.add_argument("--timeout", type=int, default=150,
                        help="Max wait seconds (default: 150)")
    parser.add_argument("--output-dir",
                        help="Save each page as a markdown file")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")

    args = parser.parse_args()

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set", file=sys.stderr)
        print("Get your free API key at https://app.tavily.com", file=sys.stderr)
        sys.exit(1)

    select_paths = args.select_paths.split(",") if args.select_paths else None
    exclude_paths = args.exclude_paths.split(",") if args.exclude_paths else None

    print(f"Crawling: {args.url}", file=sys.stderr)

    try:
        response = crawl(
            url=args.url,
            api_key=api_key,
            max_depth=args.max_depth,
            max_breadth=args.max_breadth,
            limit=args.limit,
            instructions=args.instructions,
            chunks_per_source=args.chunks_per_source,
            extract_depth=args.extract_depth,
            fmt=args.fmt,
            select_paths=select_paths,
            exclude_paths=exclude_paths,
            allow_external=args.allow_external,
            timeout=args.timeout,
        )

        if args.output_dir:
            results = response.get("results", [])
            saved = save_pages(results, args.output_dir)
            for path in saved:
                print(f"Saved: {path}", file=sys.stderr)
            print(f"\nCrawl complete. {len(saved)} files saved to: {args.output_dir}", file=sys.stderr)

        if args.json:
            print(json.dumps(response, indent=2))
        else:
            print(format_results(response))

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
