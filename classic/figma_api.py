import json
import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
if not FIGMA_TOKEN:
    raise SystemExit("Please set FIGMA_TOKEN environment variable.")
BASE_URL = "https://api.figma.com/v1"


CACHE_DIR = "../cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(file_key: str) -> str:
    return os.path.join(CACHE_DIR, f"{file_key}.json")



def get_file(file_key: str) -> Dict[str, Any]:
    """
    Loads Figma JSON from cache if available.
    Otherwise fetches from Figma API once & stores it in cache directory
    """

    cache_file = _cache_path(file_key)

    # checking cache for file key
    if os.path.exists(cache_file):
        print(f"[CACHE] Loaded file JSON from {cache_file}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # if not in cache, fetch from figma
    print("[API] Fetching file from Figma…")
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    url = f"{BASE_URL}/files/{file_key}"
    resp = requests.get(url, headers=headers)

    resp.raise_for_status()

    data = resp.json()

    # When fetched from figma, store into the cache directory
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[CACHE] Saved file JSON to {cache_file}")

    return data

def find_node_by_id(root: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    """Simple DFS to locate a node by ID in the Figma tree."""
    stack = [root]
    while stack:
        node = stack.pop()
        if node.get("id") == node_id:
            return node
        for child in node.get("children", []):
            stack.append(child)
    return None