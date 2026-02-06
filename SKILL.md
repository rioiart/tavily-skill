---
name: tavily-researcher
description: Web research using Tavily APIs. Use for factual research, current events, financial data, or when you need full content extraction from web pages. Supports search (with AI answers), content extraction from URLs, and deep search (search + extract combined). Topics: general, news, finance.
---

# Tavily Researcher

Web research via Tavily's LLM-optimized search and extraction APIs.

## When to Use

- Factual research requiring current/accurate information
- News and current events (use `--topic news`)
- Financial/market data (use `--topic finance`)
- When you need full page content, not just snippets
- Multi-source research requiring content from several URLs

## Setup

Requires `TAVILY_API_KEY` environment variable. Get a free key (1000 credits/month) at https://app.tavily.com

## Quick Start

### Basic Search
```bash
./scripts/tavily_search.py "What is retrieval augmented generation?"
```

### Search with AI Answer
```bash
./scripts/tavily_search.py "How does RAG work?" --include-answer
```

### News Search (Last 7 Days)
```bash
./scripts/tavily_search.py "AI regulation updates" --topic news --days 7
```

### Finance Search
```bash
./scripts/tavily_search.py "NVDA earnings Q4 2025" --topic finance
```

### Extract Full Content from URLs
```bash
./scripts/tavily_extract.py https://example.com/article1 https://example.com/article2
```

### Deep Search (Search + Extract Combined)
```bash
./scripts/tavily_deep_search.py "How do transformers work in NLP?" --extract-top 3
```

## Scripts

### `tavily_search.py`
Standard web search. Returns titles, URLs, snippets, and optional AI answer.

**Key options:**
- `--depth basic|advanced` — Advanced gets deeper results (2 credits vs 1)
- `--topic general|news|finance` — Optimize for content type
- `--include-answer` — Get AI-generated summary
- `--include-raw-content` — Get full page content (not just snippets)
- `--days N` — Filter by recency (news/finance only)
- `--include-domains` / `--exclude-domains` — Filter sources

### `tavily_extract.py`
Extract full content from specific URLs (up to 20 at once).

**Use when:**
- You already know which URLs have the info
- Search snippets aren't enough
- You need to analyze full articles

### `tavily_deep_search.py`
Combined workflow: search → extract top results.

**Use when:**
- You need comprehensive research on a topic
- Snippets aren't sufficient
- You want both search results and full content

**Cost:** ~3 credits (2 for advanced search + 1 for extracting 3 URLs)

## Cost Optimization

| Task | Recommended Approach | Credits |
|------|---------------------|---------|
| Quick fact check | `tavily_search.py --include-answer` | 1 |
| Deeper research | `tavily_search.py --depth advanced` | 2 |
| Full article content | `tavily_extract.py <urls>` | 1 per 5 URLs |
| Comprehensive research | `tavily_deep_search.py` | ~3 |

## Common Patterns

### Research Workflow
1. Start with `tavily_search.py --include-answer` for quick overview
2. Review results, identify promising URLs
3. Use `tavily_extract.py` on best sources for full content
4. Synthesize findings

### One-Shot Deep Research
Use `tavily_deep_search.py` when you want search + extraction in one call.

### Domain-Specific Research
```bash
# Only search specific sites
./scripts/tavily_search.py "async python" --include-domains docs.python.org,realpython.com

# Exclude unreliable sources
./scripts/tavily_search.py "health advice" --exclude-domains reddit.com,quora.com
```

## API Reference

See `references/api_reference.md` for full parameter documentation.
