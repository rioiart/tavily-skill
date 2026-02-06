#!/usr/bin/env python3
"""
Tavily Deep Search - Search + Extract in one step

Performs a search, then extracts full content from top results.
Useful when you need comprehensive content, not just snippets.

Usage:
    tavily_deep_search.py <query> [options]

Options:
    --topic general|news|finance    Search topic (default: general)
    --max-results N                 Max results to search (default: 5)
    --extract-top N                 Extract content from top N results (default: 3)
    --days N                        Filter to last N days (news/finance only)
    --json                          Output raw JSON

Environment:
    TAVILY_API_KEY                  Your Tavily API key (required)

Cost:
    - Search: 2 credits (advanced depth)
    - Extract: 1 credit per 5 URLs
    - Typical: 3 credits for 5 results, extracting top 3

Examples:
    tavily_deep_search.py "How does RAG work in LLMs?"
    tavily_deep_search.py "Tesla earnings Q4 2025" --topic finance
    tavily_deep_search.py "AI regulation news" --topic news --days 7 --extract-top 5
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SEARCH_URL = "https://api.tavily.com/search"
EXTRACT_URL = "https://api.tavily.com/extract"


def api_request(url: str, payload: dict, api_key: str, timeout: int = 60) -> dict:
    """Make an authenticated API request."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"API error {e.code}: {error_body}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def deep_search(
    query: str,
    api_key: str,
    topic: str = "general",
    max_results: int = 5,
    extract_top: int = 3,
    days: int = None,
) -> dict:
    """Perform search + extract workflow."""
    
    # Step 1: Search with advanced depth
    search_payload = {
        "query": query,
        "search_depth": "advanced",
        "topic": topic,
        "max_results": max_results,
        "include_answer": True,
    }
    if days and topic in ("news", "finance"):
        search_payload["days"] = days
    
    search_response = api_request(SEARCH_URL, search_payload, api_key, timeout=30)
    
    # Step 2: Extract from top N results
    results = search_response.get("results", [])
    urls_to_extract = [r["url"] for r in results[:extract_top] if r.get("url")]
    
    extract_response = None
    if urls_to_extract:
        extract_payload = {
            "urls": urls_to_extract,
            "extract_depth": "basic",
        }
        extract_response = api_request(EXTRACT_URL, extract_payload, api_key, timeout=60)
    
    # Merge results
    extracted_content = {}
    if extract_response:
        for r in extract_response.get("results", []):
            extracted_content[r.get("url")] = r.get("raw_content", "")
    
    # Enhance search results with full content
    for result in results:
        url = result.get("url")
        if url in extracted_content:
            result["full_content"] = extracted_content[url]
    
    # Calculate total credits
    search_credits = search_response.get("usage", {}).get("credits", 0)
    extract_credits = extract_response.get("usage", {}).get("credits", 0) if extract_response else 0
    
    return {
        "query": query,
        "answer": search_response.get("answer"),
        "results": results,
        "failed_extractions": extract_response.get("failed_results", []) if extract_response else [],
        "usage": {
            "search_credits": search_credits,
            "extract_credits": extract_credits,
            "total_credits": search_credits + extract_credits,
        }
    }


def format_results(response: dict) -> str:
    """Format results for human reading."""
    lines = []
    
    lines.append(f"# Deep Search: {response['query']}")
    lines.append("")
    
    # Answer
    if response.get("answer"):
        lines.append("## Summary")
        lines.append(response["answer"])
        lines.append("")
    
    # Results with full content
    results = response.get("results", [])
    if results:
        lines.append(f"## Sources ({len(results)} found)")
        lines.append("")
        
        for i, r in enumerate(results, 1):
            lines.append(f"### {i}. {r.get('title', 'No title')}")
            lines.append(f"**URL:** {r.get('url', 'N/A')}")
            lines.append("")
            
            if r.get("full_content"):
                content = r["full_content"]
                if len(content) > 3000:
                    lines.append(content[:3000])
                    lines.append(f"\n... [truncated, {len(content)} chars total]")
                else:
                    lines.append(content)
            elif r.get("content"):
                lines.append(f"*Snippet:* {r['content']}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # Usage
    usage = response.get("usage", {})
    lines.append(f"*Credits: {usage.get('search_credits', 0)} search + {usage.get('extract_credits', 0)} extract = {usage.get('total_credits', 0)} total*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Deep search with content extraction")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--topic", choices=["general", "news", "finance"], default="general",
                        help="Search topic (default: general)")
    parser.add_argument("--max-results", type=int, default=5,
                        help="Max search results (default: 5)")
    parser.add_argument("--extract-top", type=int, default=3,
                        help="Extract content from top N results (default: 3)")
    parser.add_argument("--days", type=int,
                        help="Filter to last N days (news/finance only)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        response = deep_search(
            query=args.query,
            api_key=api_key,
            topic=args.topic,
            max_results=args.max_results,
            extract_top=args.extract_top,
            days=args.days,
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
