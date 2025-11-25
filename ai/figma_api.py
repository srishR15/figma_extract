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

"""
def get_file(file_key: str) -> Dict[str, Any]:
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    url = f"{BASE_URL}/files/{file_key}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def find_node_by_id(root: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    stack = [root]
    while stack:
        node = stack.pop()
        if node.get("id") == node_id:
            return node
        for child in node.get("children", []):
            stack.append(child)
    return None
"""

# ------------------------------
# CACHE SETUP
# ------------------------------
CACHE_DIR = "../cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(file_key: str) -> str:
    return os.path.join(CACHE_DIR, f"{file_key}.json")


# ------------------------------
# MAIN FUNCTION WITH CACHING
# ------------------------------
def get_file(file_key: str) -> Dict[str, Any]:
    """
    Loads Figma JSON from cache if available.
    Otherwise fetches from Figma API once & stores it.
    """

    cache_file = _cache_path(file_key)

    # 1) CHECK CACHE FIRST
    if os.path.exists(cache_file):
        print(f"[CACHE] Loaded file JSON from {cache_file}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2) FETCH FROM FIGMA API
    print("[API] Fetching file from Figma…")
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    url = f"{BASE_URL}/files/{file_key}"
    resp = requests.get(url, headers=headers)

    # Throw errors normally
    resp.raise_for_status()

    data = resp.json()

    # 3) SAVE TO CACHE
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