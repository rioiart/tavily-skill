#!/usr/bin/env python3
"""
Tavily Map - Discover URLs on a website (faster than crawl)

Usage:
    uv run scripts/tavily_map.py <url> [options]

Options:
    --max-depth N              Crawl depth 1-5 (default: 1)
    --max-breadth N            Links per page (default: 20)
    --limit N                  Total URLs cap (default: 50)
    --instructions TEXT        Natural language focus guidance
    --select-paths P1,P2       Regex patterns to include
    --exclude-paths P1,P2      Regex patterns to exclude
    --allow-external           Allow external domain links (default)
    --no-allow-external        Stay on same domain
    --json                     Output raw JSON response

Environment:
    TAVILY_API_KEY             Your Tavily API key (required)

Examples:
    uv run scripts/tavily_map.py https://docs.example.com
    uv run scripts/tavily_map.py https://docs.example.com --max-depth 2 --limit 100
    uv run scripts/tavily_map.py https://example.com --instructions "Find API docs" --select-paths "/docs/.*,/api/.*"
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TAVILY_API_URL = "https://api.tavily.com/map"


def map_urls(
    url: str,
    api_key: str,
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = 50,
    instructions: str = None,
    select_paths: list = None,
    exclude_paths: list = None,
    allow_external: bool = True,
) -> dict:
    """Discover URLs on a website using Tavily."""

    payload = {
        "url": url,
        "max_depth": max_depth,
        "max_breadth": max_breadth,
        "limit": limit,
        "allow_external": allow_external,
    }

    if instructions:
        payload["instructions"] = instructions
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
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Tavily API error {e.code}: {error_body}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def format_results(response: dict) -> str:
    """Format map results for human reading."""
    lines = []

    base_url = response.get("base_url", "")
    results = response.get("results", [])

    lines.append(f"## Site Map: {base_url}")
    lines.append(f"{len(results)} URLs found")
    lines.append("")

    for i, url in enumerate(results, 1):
        lines.append(f"{i}. {url}")

    response_time = response.get("response_time")
    if response_time:
        lines.append("")
        lines.append(f"*Completed in {response_time:.1f}s*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Discover URLs on a website using Tavily")
    parser.add_argument("url", help="Root URL to map")
    parser.add_argument("--max-depth", type=int, default=1,
                        help="Crawl depth 1-5 (default: 1)")
    parser.add_argument("--max-breadth", type=int, default=20,
                        help="Links per page (default: 20)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Total URLs cap (default: 50)")
    parser.add_argument("--instructions",
                        help="Natural language focus guidance")
    parser.add_argument("--select-paths",
                        help="Comma-separated regex patterns to include")
    parser.add_argument("--exclude-paths",
                        help="Comma-separated regex patterns to exclude")
    parser.add_argument("--allow-external", action="store_true", default=True,
                        help="Allow external domain links (default)")
    parser.add_argument("--no-allow-external", action="store_false", dest="allow_external",
                        help="Stay on same domain")
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

    try:
        response = map_urls(
            url=args.url,
            api_key=api_key,
            max_depth=args.max_depth,
            max_breadth=args.max_breadth,
            limit=args.limit,
            instructions=args.instructions,
            select_paths=select_paths,
            exclude_paths=exclude_paths,
            allow_external=args.allow_external,
        )

        if args.json:
            print(json.dumps(response, indent=2))
        else:
            print(format_results(response))

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
