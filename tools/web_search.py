"""Web search stub. Replace with a real search API for production use.

This stub returns a canned response so the harness works end-to-end
without requiring a search API key. Swap it out for SerpAPI, Tavily,
Brave Search, or whatever you prefer.
"""

NAME = "web_search"
DESCRIPTION = "Search the web for current information on a topic. Returns a list of results with titles, URLs, and snippets."
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
    # Stub implementation. Replace the body of this function with a real
    # search API call. The harness doesn't care how you get results --
    # it only cares that this function returns a string.
    #
    # Example with Tavily:
    #   from tavily import TavilyClient
    #   client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    #   results = client.search(query, max_results=num_results)
    #   return json.dumps(results["results"], indent=2)

    return (
        f"[web_search stub] Query: '{query}'\n"
        f"This is a stub. To get real results, replace tools/web_search.py "
        f"with a real search API integration (Tavily, SerpAPI, Brave, etc.).\n"
        f"The harness will work the same way -- it just calls execute() and "
        f"logs the result."
    )
