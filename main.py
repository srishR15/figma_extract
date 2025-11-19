import argparse
from pathlib import Path

from figma_api import get_file, find_node_by_id
from mapper import map_figma_to_ui
from css_html import generate_css, generate_html


def parse_args():
    parser = argparse.ArgumentParser(
        description="Figma → HTML/CSS exporter (Softlight assignment)."
    )
    parser.add_argument("file_key", help="Figma file key from the URL")
    parser.add_argument(
        "--node",
        dest="node_id",
        help="Optional node/frame id (from node-id in Figma URL) to export",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"Fetching Figma file {args.file_key} ...")
    data = get_file(args.file_key)
    document = data["document"]

    if args.node_id:
        print(f"Searching for node {args.node_id} ...")
        node = find_node_by_id(document, args.node_id)
        if not node:
            print("Node not found; exporting full document instead.")
            node = document
    else:
        node = document

    ui_root = map_figma_to_ui(node)
    css, mapping = generate_css(ui_root)
    html = generate_html(ui_root, mapping)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    (out_dir / "styles.css").write_text(css, encoding="utf-8")
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    print("Export complete. Open output/index.html in your browser.")


if __name__ == "__main__":
    main()