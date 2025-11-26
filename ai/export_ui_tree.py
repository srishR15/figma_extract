import json
import sys
import os
from pathlib import Path
from util import get_figma_node

UI_TREE = "UITree"
def clean_figma_node(node):
    bbox = node.get("absoluteBoundingBox", {})
    clean = {
        "id": node.get("id"),
        "type": node.get("type"),
        "name": node.get("name"),
        "x": bbox.get("x"),
        "y": bbox.get("y"),
        "width": bbox.get("width"),
        "height": bbox.get("height"),
    }
    # Include ALL CRITICAL STYLE AND LAYOUT KEYS for generalization to provide openai with cleaned version of json file
    for key in (
        "fills", 
        "strokes", 
        "strokeWeight", 
        "cornerRadius", 
        "cornerSmoothing", 
        "effects", 
        "characters", 
        "style", 
        "opacity", 
        "layoutMode",
        "primaryAxisAlignItems",
        "counterAxisAlignItems",
        "paddingTop",
        "paddingBottom",
        "paddingLeft",
        "paddingRight",
        "itemSpacing",
        "primaryAxisSizingMode",
        "counterAxisSizingMode",
        "layoutAlign",
        "layoutGrow",
    ):
        if key in node:
            clean[key] = node[key]
    
    if "children" in node:
        clean["children"] = [clean_figma_node(child) for child in node["children"]]
    return clean

def export_clean_ui_tree(figma_json):
    # Finding the outermost node
    root_node = figma_json.get("document") or figma_json.get("root") or figma_json
    
    # Target the main design FRAME
    design_frame = root_node
    if root_node.get("children") and root_node["children"][0].get("type") in ["FRAME", "CANVAS", "COMPONENT"]:
        design_frame = root_node["children"][0]
        
    cleaned = clean_figma_node(design_frame)
    os.makedirs(UI_TREE, exist_ok=True)
    ui_file=os.path.join(UI_TREE, f"ui.json")
    with open(ui_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)
    print(f"[OK] Exported cleaned UI tree to {ui_file}")

if __name__ == "__main__":
    if len(sys.argv) <= 3:
        print("Usage: python export_ui_tree.py <figma_json_file> <node_id>")
        sys.exit(1)
    
    file_key = sys.argv[1]
    node_id = sys.argv[2] if len(sys.argv) == 3 else None
    node = get_figma_node(file_key, node_id, cache_dir="../cache")

    export_clean_ui_tree({"document": node})