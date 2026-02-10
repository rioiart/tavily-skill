#!/usr/bin/env python3
"""
Tavily Research - AI-synthesized research with citations

Usage:
    uv run scripts/tavily_research.py <input> [options]

Options:
    --model mini|pro|auto         Research model (default: auto)
    --citation-format FORMAT      Citation style: numbered, mla, apa, chicago (default: numbered)
    --output-schema JSON          JSON schema for structured output
    --output-file PATH            Save results to file
    --json                        Output raw JSON response

Environment:
    TAVILY_API_KEY                Your Tavily API key (required)

Examples:
    uv run scripts/tavily_research.py "What is retrieval augmented generation?"
    uv run scripts/tavily_research.py "LangGraph vs CrewAI" --model pro
    uv run scripts/tavily_research.py "EV market analysis" --model pro --output-file ev-report.md
    uv run scripts/tavily_research.py "fintech startups" --output-schema '{"properties":{"summary":{"type":"string","description":"Overview"}},"required":["summary"]}'
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TAVILY_API_URL = "https://api.tavily.com/research"


def research(
    input_text: str,
    api_key: str,
    model: str = "auto",
    citation_format: str = "numbered",
    output_schema: dict = None,
) -> dict:
    """Execute Tavily research."""

    payload = {
        "input": input_text,
        "model": model,
        "stream": False,
        "citation_format": citation_format,
    }

    if output_schema:
        payload["output_schema"] = output_schema

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


def format_results(response: dict) -> str:
    """Format research results for human reading."""
    lines = []

    content = response.get("content", "")
    if content:
        lines.append(content)
        lines.append("")

    sources = response.get("sources", [])
    if sources:
        lines.append("## Sources")
        for i, s in enumerate(sources, 1):
            title = s.get("title", "Untitled")
            url = s.get("url", "")
            lines.append(f"{i}. [{title}]({url})")
        lines.append("")

    response_time = response.get("response_time")
    if response_time:
        lines.append(f"*Research completed in {response_time:.1f}s*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tavily AI-synthesized research with citations")
    parser.add_argument("input", help="Research topic or question")
    parser.add_argument("--model", choices=["mini", "pro", "auto"], default="auto",
                        help="Research model (default: auto)")
    parser.add_argument("--citation-format", choices=["numbered", "mla", "apa", "chicago"],
                        default="numbered", help="Citation format (default: numbered)")
    parser.add_argument("--output-schema",
                        help="JSON schema string for structured output")
    parser.add_argument("--output-file",
                        help="Save results to file")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")

    args = parser.parse_args()

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set", file=sys.stderr)
        print("Get your free API key at https://app.tavily.com", file=sys.stderr)
        sys.exit(1)

    output_schema = None
    if args.output_schema:
        try:
            output_schema = json.loads(args.output_schema)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --output-schema: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Researching: {args.input} (model: {args.model})", file=sys.stderr)
    print("This may take 30-120 seconds...", file=sys.stderr)

    try:
        response = research(
            input_text=args.input,
            api_key=api_key,
            model=args.model,
            citation_format=args.citation_format,
            output_schema=output_schema,
        )

        if args.json:
            output = json.dumps(response, indent=2)
        else:
            output = format_results(response)

        print(output)

        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(output)
            print(f"\nSaved to: {args.output_file}", file=sys.stderr)

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
