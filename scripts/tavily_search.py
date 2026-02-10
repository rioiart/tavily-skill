#!/usr/bin/env python3
"""
Tavily Search - Web search optimized for LLMs

Usage:
    uv run scripts/tavily_search.py <query> [options]

Options:
    --depth DEPTH             Search depth: ultra-fast, fast, basic, advanced (default: basic)
    --topic general|news|finance    Search topic (default: general)
    --max-results N           Max results to return (default: 5)
    --include-answer          Include AI-generated answer
    --include-raw-content     Include full page content (not just snippets)
    --include-images          Include image results
    --days N                  Filter to last N days
    --time-range RANGE        Filter: day, week, month, year
    --chunks-per-source N     Chunks per source 1-5 (advanced/fast only)
    --include-domains d1,d2   Only search these domains
    --exclude-domains d1,d2   Exclude these domains
    --json                    Output raw JSON response

Environment:
    TAVILY_API_KEY            Your Tavily API key (required)

Examples:
    uv run scripts/tavily_search.py "What is RAG in AI?"
    uv run scripts/tavily_search.py "latest AI news" --topic news --days 7
    uv run scripts/tavily_search.py "NVDA stock analysis" --topic finance --depth advanced
    uv run scripts/tavily_search.py "AI news this week" --topic news --time-range week
    uv run scripts/tavily_search.py "site:docs.python.org async" --include-raw-content
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TAVILY_API_URL = "https://api.tavily.com/search"


def search(
    query: str,
    api_key: str,
    search_depth: str = "basic",
    topic: str = "general",
    max_results: int = 5,
    include_answer: bool = False,
    include_raw_content: bool = False,
    include_images: bool = False,
    days: int = None,
    time_range: str = None,
    chunks_per_source: int = None,
    include_domains: list = None,
    exclude_domains: list = None,
) -> dict:
    """Execute a Tavily search."""

    payload = {
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": include_images,
    }

    if days:
        payload["days"] = days
    if time_range:
        payload["time_range"] = time_range
    if chunks_per_source:
        payload["chunks_per_source"] = chunks_per_source
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

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
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Tavily API error {e.code}: {error_body}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def format_results(response: dict, show_raw: bool = False) -> str:
    """Format search results for human reading."""
    lines = []
    
    # Answer (if present)
    if response.get("answer"):
        lines.append("## Answer")
        lines.append(response["answer"])
        lines.append("")
    
    # Results
    results = response.get("results", [])
    if results:
        lines.append(f"## Results ({len(results)} found)")
        lines.append("")
        
        for i, r in enumerate(results, 1):
            lines.append(f"### {i}. {r.get('title', 'No title')}")
            lines.append(f"**URL:** {r.get('url', 'N/A')}")
            if r.get("score"):
                lines.append(f"**Relevance:** {r['score']:.2f}")
            lines.append("")
            
            if show_raw and r.get("raw_content"):
                lines.append("**Content:**")
                lines.append(r["raw_content"][:2000])
                if len(r.get("raw_content", "")) > 2000:
                    lines.append("... [truncated]")
            elif r.get("content"):
                lines.append(r["content"])
            lines.append("")
    
    # Usage info
    usage = response.get("usage", {})
    if usage:
        lines.append(f"---")
        lines.append(f"*Credits used: {usage.get('credits', 'N/A')}*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tavily web search for LLMs")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--depth", choices=["ultra-fast", "fast", "basic", "advanced"],
                        default="basic", help="Search depth (default: basic)")
    parser.add_argument("--topic", choices=["general", "news", "finance"], default="general",
                        help="Search topic (default: general)")
    parser.add_argument("--max-results", type=int, default=5,
                        help="Max results (default: 5)")
    parser.add_argument("--include-answer", action="store_true",
                        help="Include AI-generated answer")
    parser.add_argument("--include-raw-content", action="store_true",
                        help="Include full page content")
    parser.add_argument("--include-images", action="store_true",
                        help="Include image results")
    parser.add_argument("--days", type=int,
                        help="Filter to last N days")
    parser.add_argument("--time-range", choices=["day", "week", "month", "year"],
                        help="Filter by time range")
    parser.add_argument("--chunks-per-source", type=int,
                        help="Chunks per source 1-5 (advanced/fast only)")
    parser.add_argument("--include-domains",
                        help="Comma-separated domains to include")
    parser.add_argument("--exclude-domains",
                        help="Comma-separated domains to exclude")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set", file=sys.stderr)
        print("Get your free API key at https://app.tavily.com", file=sys.stderr)
        sys.exit(1)
    
    include_domains = args.include_domains.split(",") if args.include_domains else None
    exclude_domains = args.exclude_domains.split(",") if args.exclude_domains else None
    
    try:
        response = search(
            query=args.query,
            api_key=api_key,
            search_depth=args.depth,
            topic=args.topic,
            max_results=args.max_results,
            include_answer=args.include_answer,
            include_raw_content=args.include_raw_content,
            include_images=args.include_images,
            days=args.days,
            time_range=args.time_range,
            chunks_per_source=args.chunks_per_source,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        
        if args.json:
            print(json.dumps(response, indent=2))
        else:
            print(format_results(response, show_raw=args.include_raw_content))
            
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
