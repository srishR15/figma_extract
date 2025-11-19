from typing import Any, Dict, List, TypedDict


class UiNode(TypedDict, total=False):
    id: str
    name: str
    kind: str
    children: List["UiNode"]
    styles: Dict[str, Any]
    text: str


def _detect_kind(node: Dict[str, Any]) -> str:
    t = node.get("type")
    if t in ("FRAME", "COMPONENT", "INSTANCE"):
        return "frame"
    if t == "GROUP":
        return "group"
    if t in ("RECTANGLE", "ELLIPSE", "VECTOR", "LINE"):
        return "shape"
    if t == "TEXT":
        return "text"
    return "other"

# Convert a raw Figma node into a generic UiNode with normalized style info
def map_figma_to_ui(node: Dict[str, Any]) -> UiNode:
    kind = _detect_kind(node)
    styles: Dict[str, Any] = {}

    # Absolute position & size
    box = node.get("absoluteBoundingBox")
    if box:
        styles["layout"] = {
            "x": box.get("x", 0),
            "y": box.get("y", 0),
            "width": box.get("width", 0),
            "height": box.get("height", 0),
        }

    # Auto-layout → flexbox
    layout_mode = node.get("layoutMode")
    if layout_mode and layout_mode != "NONE":
        styles["flex"] = {
            "direction": "row" if layout_mode == "HORIZONTAL" else "column",
            "gap": node.get("itemSpacing", 0),
            "primaryAlign": node.get("primaryAxisAlignItems"),
            "counterAlign": node.get("counterAxisAlignItems"),
        }

    # Fills (solid colors, gradients)
    fills = node.get("fills") or []
    if fills:
        styles["fills"] = fills

    # Strokes (borders)
    strokes = node.get("strokes") or []
    if strokes:
        styles["strokes"] = strokes
        styles["strokeWeight"] = node.get("strokeWeight", 1)
        styles["strokeAlign"] = node.get("strokeAlign")

    # Corner radius / per-corner radii
    if "cornerRadius" in node:
        styles["cornerRadius"] = node["cornerRadius"]
    if "rectangleCornerRadii" in node:
        styles["cornerRadii"] = node["rectangleCornerRadii"]

    # Text style
    if kind == "text" and node.get("style"):
        styles["textStyle"] = node["style"]

    # Children
    children = [map_figma_to_ui(c) for c in node.get("children", [])]

    ui: UiNode = {
        "id": node["id"],
        "name": node.get("name", ""),
        "kind": kind,
        "children": children,
        "styles": styles,
    }

    if kind == "text":
        ui["text"] = node.get("characters", "")

    return ui
