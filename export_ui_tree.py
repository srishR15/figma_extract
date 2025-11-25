import json
import sys
import os
from pathlib import Path

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
    # Include ALL CRITICAL STYLE AND LAYOUT KEYS for generalization
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
        "layoutMode",         # Auto-layout
        "primaryAxisAlignItems",
        "counterAxisAlignItems",
        "paddingTop",           # Crucial for height/spacing
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
    
    # Recursively clean children
    if "children" in node:
        clean["children"] = [clean_figma_node(child) for child in node["children"]]
    return clean

def export_clean_ui_tree(figma_json):
    # Find the outermost node
    root_node = figma_json.get("document") or figma_json.get("root") or figma_json
    
    # Target the main design FRAME (ID 1:75 equivalent)
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
    if len(sys.argv) != 2:
        print("Usage: python export_ui_tree.py <figma_json_file>")
        sys.exit(1)
    
    # Assuming the Figma JSON file is in the current directory (or cache, as per original logic)
    input_path = sys.argv[1]
    input_path = os.path.join("cache", input_path)
    
    with open(input_path, "r", encoding="utf-8") as f:
        figma_json = json.load(f)
    export_clean_ui_tree(figma_json)