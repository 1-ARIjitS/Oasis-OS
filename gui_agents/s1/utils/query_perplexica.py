import os
import json
import requests
from typing import Dict, Any, Optional

def query_perplexica(query: str):
    """Query Perplexica API for web search results"""
    url = os.getenv("PERPLEXICA_URL")
    
    if not url:
        error_message = (
            "PERPLEXICA_URL environment variable not set. "
            "Please set it to your Perplexica API endpoint.\n"
            "Example: export PERPLEXICA_URL='http://localhost:3001/api/search'\n"
            "The port number should match your Perplexica configuration in config.toml"
        )
        print(f"Warning: {error_message}")
        return {"error": "Perplexica not configured", "message": error_message}

    try:
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "query": query,
            "search_type": "web",
            "focus_mode": "web"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.ConnectionError:
        error_message = f"Cannot connect to Perplexica at {url}. Please ensure Perplexica is running."
        print(f"Error: {error_message}")
        return {"error": "Connection failed", "message": error_message}
        
    except requests.exceptions.Timeout:
        error_message = "Perplexica request timed out after 30 seconds."
        print(f"Error: {error_message}")
        return {"error": "Timeout", "message": error_message}
        
    except requests.exceptions.HTTPError as e:
        error_message = f"Perplexica API returned HTTP error: {e}"
        print(f"Error: {error_message}")
        return {"error": "HTTP error", "message": error_message}
        
    except Exception as e:
        error_message = f"Unexpected error querying Perplexica: {e}"
        print(f"Error: {error_message}")
        return {"error": "Unexpected error", "message": error_message}


def query_duckduckgo(query: str) -> Dict[str, Any]:
    """Query DuckDuckGo search API (free, no API key required)"""
    try:
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Format response to match expected structure
        if data.get("AbstractText"):
            return {
                "results": [{
                    "title": data.get("Heading", query),
                    "content": data.get("AbstractText", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo"
                }],
                "source": "duckduckgo"
            }
        elif data.get("Answer"):
            return {
                "results": [{
                    "title": query,
                    "content": data.get("Answer", ""),
                    "url": "",
                    "source": "DuckDuckGo"
                }],
                "source": "duckduckgo"
            }
        else:
            return {
                "results": [{
                    "title": query,
                    "content": f"Search performed for: {query}. DuckDuckGo instant answers not available for this query.",
                    "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                    "source": "DuckDuckGo"
                }],
                "source": "duckduckgo"
            }
            
    except Exception as e:
        return {"error": f"DuckDuckGo search failed: {e}", "source": "duckduckgo"}


def query_searxng(query: str, instance_url: Optional[str] = None) -> Dict[str, Any]:
    """Query SearXNG instance (free, open-source search)"""
    try:
        # Use provided instance or default public instance
        base_url = instance_url or os.getenv("SEARXNG_URL", "https://searx.be")
        
        url = f"{base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "categories": "general",
            "engines": "google,bing,duckduckgo"
        }
        
        headers = {
            "User-Agent": "Oasis-OS/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for result in data.get("results", [])[:5]:  # Limit to top 5 results
            results.append({
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "source": "SearXNG"
            })
        
        return {
            "results": results,
            "source": "searxng",
            "query": query
        }
        
    except Exception as e:
        return {"error": f"SearXNG search failed: {e}", "source": "searxng"}


def query_brave_search(query: str) -> Dict[str, Any]:
    """Query Brave Search API (free tier available)"""
    api_key = os.getenv("BRAVE_API_KEY")
    
    if not api_key:
        return {
            "error": "BRAVE_API_KEY not set. Get a free API key from https://api.search.brave.com/app/keys",
            "source": "brave"
        }
    
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }
        params = {
            "q": query,
            "count": 5
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for result in data.get("web", {}).get("results", []):
            results.append({
                "title": result.get("title", ""),
                "content": result.get("description", ""),
                "url": result.get("url", ""),
                "source": "Brave Search"
            })
        
        return {
            "results": results,
            "source": "brave",
            "query": query
        }
        
    except Exception as e:
        return {"error": f"Brave Search failed: {e}", "source": "brave"}


def search_web(query: str, search_engine: str = "auto") -> Dict[str, Any]:
    """
    Universal web search function that tries multiple search engines
    
    Args:
        query: Search query string
        search_engine: Preferred search engine ("perplexica", "duckduckgo", "searxng", "brave", "auto")
    
    Returns:
        Search results dictionary
    """
    
    # If auto, try engines in order of preference
    if search_engine == "auto":
        # Try Perplexica first if configured
        if os.getenv("PERPLEXICA_URL"):
            result = query_perplexica(query)
            if "error" not in result:
                return result
        
        # Try Brave Search if API key is available
        if os.getenv("BRAVE_API_KEY"):
            result = query_brave_search(query)
            if "error" not in result:
                return result
        
        # Try SearXNG
        result = query_searxng(query)
        if "error" not in result:
            return result
        
        # Fall back to DuckDuckGo
        return query_duckduckgo(query)
    
    # Use specific search engine
    elif search_engine == "perplexica":
        return query_perplexica(query)
    elif search_engine == "duckduckgo":
        return query_duckduckgo(query)
    elif search_engine == "searxng":
        return query_searxng(query)
    elif search_engine == "brave":
        return query_brave_search(query)
    else:
        return {"error": f"Unknown search engine: {search_engine}"}


# Test Code
if __name__ == "__main__":
    query = "What is Agent S GUI automation?"
    
    print("Testing search engines:")
    print("=" * 50)
    
    # Test DuckDuckGo
    print("1. DuckDuckGo:")
    result = query_duckduckgo(query)
    print(json.dumps(result, indent=2)[:500] + "...")
    print()
    
    # Test SearXNG
    print("2. SearXNG:")
    result = query_searxng(query)
    print(json.dumps(result, indent=2)[:500] + "...")
    print()
    
    # Test auto search
    print("3. Auto search:")
    result = search_web(query, "auto")
    print(json.dumps(result, indent=2)[:500] + "...")
