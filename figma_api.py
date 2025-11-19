import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional
load_dotenv()
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")

if not FIGMA_TOKEN:
    raise SystemExit("Please set FIGMA_TOKEN environment variable.")


BASE_URL = "https://api.figma.com/v1"

# Fetch a Figma file JSON using the REST API
def get_file(file_key: str) -> Dict[str, Any]:
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    url = f"{BASE_URL}/files/{file_key}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


# DFS search for a node with a specific id in the Figma document tree
def find_node_by_id(root: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    stack = [root]
    while stack:
        node = stack.pop()
        if node.get("id") == node_id:
            return node
        for child in node.get("children", []):
            stack.append(child)
    return None
