"""Search the web using the Brave Search API.

Free tier: 2,000 queries/month, no credit card required.
Sign up at https://brave.com/search/api/ and set BRAVE_API_KEY in .env.

If no API key is set, falls back to a stub response so the harness
still works end-to-end for testing.
"""

import json
import os
import urllib.request
import urllib.parse
import urllib.error

NAME = "web_search"
DESCRIPTION = "Search the web for current information on a topic. Returns titles, URLs, and snippets."
PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query",
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return (default: 5)",
            "default": 5,
        },
    },
    "required": ["query"],
}


def execute(query: str, num_results: int = 5) -> str:
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return (
            f"[web_search] No BRAVE_API_KEY set. Query: '{query}'\n"
            f"Get a free key at https://brave.com/search/api/ (2,000 queries/month).\n"
            f"Add BRAVE_API_KEY=your_key to .env and re-run."
        )

    params = urllib.parse.urlencode({"q": query, "count": min(num_results, 20)})
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                import gzip
                raw = gzip.decompress(raw)
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        return f"Brave Search API error: {e.code} {e.reason}"
    except Exception as e:
        return f"Web search failed: {e}"

    results = data.get("web", {}).get("results", [])
    if not results:
        return f"No results found for: {query}"

    lines = []
    for i, r in enumerate(results[:num_results], 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("description", "No description")
        lines.append(f"{i}. {title}\n   {url}\n   {snippet}\n")

    return f"Search results for '{query}':\n\n" + "\n".join(lines)
