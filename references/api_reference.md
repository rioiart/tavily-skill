# Tavily API Reference

## Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `search_depth` | string | "basic" | "basic" (1 credit) or "advanced" (2 credits) |
| `topic` | string | "general" | "general", "news", or "finance" |
| `max_results` | int | 5 | Number of results (1-20) |
| `include_answer` | bool | false | Include AI-generated answer |
| `include_raw_content` | bool | false | Include full page content |
| `days` | int | null | Filter by recency (news/finance only) |
| `include_domains` | list | null | Only search these domains |
| `exclude_domains` | list | null | Exclude these domains |

## Extract Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | list | required | URLs to extract (max 20) |
| `extract_depth` | string | "basic" | "basic" or "advanced" |
| `include_images` | bool | false | Include image URLs |

## Credit Costs

| Operation | Cost |
|-----------|------|
| Basic search | 1 credit |
| Advanced search | 2 credits |
| Basic extract (5 URLs) | 1 credit |
| Advanced extract (5 URLs) | 2 credits |

## Response Structure

### Search Response
```json
{
  "query": "...",
  "answer": "AI-generated answer (if requested)",
  "results": [
    {
      "title": "Page title",
      "url": "https://...",
      "content": "Snippet",
      "raw_content": "Full content (if requested)",
      "score": 0.85
    }
  ],
  "usage": {"credits": 1}
}
```

### Extract Response
```json
{
  "results": [
    {
      "url": "https://...",
      "raw_content": "Full page content",
      "images": ["url1", "url2"]
    }
  ],
  "failed_results": [
    {"url": "...", "error": "..."}
  ],
  "usage": {"credits": 1}
}
```

## Topic-Specific Tips

### General
- Default topic, works for most queries
- Good for factual questions, how-tos, explanations

### News
- Use `days` parameter to filter by recency
- Better for current events, breaking news
- Results prioritize news sources

### Finance
- Use `days` for recent market data
- Better for stock analysis, earnings, market news
- Results prioritize financial sources (Bloomberg, Reuters, etc.)
