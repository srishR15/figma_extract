import os
import json
from figma_api import get_file, find_node_by_id  # adjust if import path changes

def get_figma_node(file_key, node_id=None, cache_dir="../cache"):
    cache_file = os.path.join(cache_dir, f"{file_key}.json")
    if not os.path.exists(cache_file):
        file_data = get_file(file_key)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=2)
    else:
        with open(cache_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
    document = file_data["document"]
    if node_id:
        found = find_node_by_id(document, node_id)
        return found if found else document
    else:
        return document