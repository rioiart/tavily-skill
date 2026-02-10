#!/usr/bin/env python3
"""
Tavily Extract - Extract full content from URLs

Usage:
    uv run scripts/tavily_extract.py <url1> [url2 ...] [options]

Options:
    --depth basic|advanced    Extraction depth (default: basic)
    --include-images          Include images from pages
    --json                    Output raw JSON response

Environment:
    TAVILY_API_KEY            Your Tavily API key (required)

Cost:
    - Basic: 1 credit per 5 successful extractions
    - Advanced: 2 credits per 5 successful extractions
    - Max 20 URLs per request

Examples:
    uv run scripts/tavily_extract.py https://example.com/article
    uv run scripts/tavily_extract.py url1 url2 url3 --depth advanced
    uv run scripts/tavily_extract.py https://docs.python.org/3/library/asyncio.html --json
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TAVILY_API_URL = "https://api.tavily.com/extract"
MAX_URLS = 20


def extract(
    urls: list,
    api_key: str,
    extract_depth: str = "basic",
    include_images: bool = False,
) -> dict:
    """Extract content from URLs using Tavily."""
    
    if len(urls) > MAX_URLS:
        raise ValueError(f"Maximum {MAX_URLS} URLs per request (got {len(urls)})")
    
    payload = {
        "urls": urls,
        "extract_depth": extract_depth,
        "include_images": include_images,
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
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
    """Format extraction results for human reading."""
    lines = []
    
    results = response.get("results", [])
    failed = response.get("failed_results", [])
    
    if results:
        lines.append(f"## Extracted Content ({len(results)} pages)")
        lines.append("")
        
        for i, r in enumerate(results, 1):
            lines.append(f"### {i}. {r.get('url', 'Unknown URL')}")
            lines.append("")
            
            content = r.get("raw_content", "")
            if content:
                # Truncate very long content for display
                if len(content) > 5000:
                    lines.append(content[:5000])
                    lines.append(f"\n... [truncated, {len(content)} chars total]")
                else:
                    lines.append(content)
            else:
                lines.append("*No content extracted*")
            
            # Images
            images = r.get("images", [])
            if images:
                lines.append("")
                lines.append(f"**Images ({len(images)}):**")
                for img in images[:5]:  # Limit to first 5
                    lines.append(f"- {img}")
                if len(images) > 5:
                    lines.append(f"- ... and {len(images) - 5} more")
            
            lines.append("")
            lines.append("---")
            lines.append("")
    
    if failed:
        lines.append(f"## Failed Extractions ({len(failed)})")
        for f in failed:
            url = f.get("url", "Unknown")
            error = f.get("error", "Unknown error")
            lines.append(f"- {url}: {error}")
        lines.append("")
    
    # Usage info
    usage = response.get("usage", {})
    if usage:
        lines.append(f"*Credits used: {usage.get('credits', 'N/A')}*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract content from URLs using Tavily")
    parser.add_argument("urls", nargs="+", help="URLs to extract (max 20)")
    parser.add_argument("--depth", choices=["basic", "advanced"], default="basic",
                        help="Extraction depth (default: basic)")
    parser.add_argument("--include-images", action="store_true",
                        help="Include images from pages")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set", file=sys.stderr)
        print("Get your free API key at https://app.tavily.com", file=sys.stderr)
        sys.exit(1)
    
    if len(args.urls) > MAX_URLS:
        print(f"Error: Maximum {MAX_URLS} URLs per request", file=sys.stderr)
        sys.exit(1)
    
    try:
        response = extract(
            urls=args.urls,
            api_key=api_key,
            extract_depth=args.depth,
            include_images=args.include_images,
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
