import argparse
from pathlib import Path
from figma_api import get_file, find_node_by_id
from mapper import map_figma_to_ui, apply_absolute_layout
from css_html import generate_css, generate_html

def parse_args():
    parser = argparse.ArgumentParser(description="Figma → HTML/CSS exporter (Softlight assignment).")
    parser.add_argument("file_key", help="Figma file key from the URL")
    parser.add_argument("--node", dest="node_id", help="Optional node/frame id (from node-id in Figma URL)")
    return parser.parse_args()

def assign_classes(node, id_to_class, prefix="node"):
    """
    Assign a unique CSS class to every node based on its ID.
    """
    safe = node["id"].replace(":", "-").replace(";", "-")
    cls = f"{prefix}-{safe}"
    id_to_class[node["id"]] = cls

    for c in node.get("children", []):
        assign_classes(c, id_to_class, prefix)

def main():
    args = parse_args()
    file_data = get_file(args.file_key)
    document = file_data["document"]

    # locate requested node
    node = document
    if args.node_id:
        found = find_node_by_id(document, args.node_id)
        if found:
            node = found
        else:
            print("Node ID not found — exporting root")

    # Map figma JSON → UiNode structure
    ui_root = map_figma_to_ui(node)
    apply_absolute_layout(ui_root)
    # Assign CSS classes BEFORE generating CSS
    id_to_class = {}
    assign_classes(ui_root, id_to_class)

    # Generate CSS + HTML
    css = generate_css(ui_root, id_to_class)
    html = generate_html(ui_root, id_to_class)

    # Write output
    out = Path("output")
    out.mkdir(exist_ok=True)

    (out / "styles.css").write_text(css, encoding="utf-8")
    (out / "index.html").write_text(html, encoding="utf-8")

    print("Export complete → output/index.html")

if __name__ == "__main__":
    main()