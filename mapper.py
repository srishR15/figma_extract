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

def map_figma_to_ui(node: Dict[str, Any]) -> UiNode:
    kind = _detect_kind(node)
    styles: Dict[str, Any] = {}
    box = node.get("absoluteBoundingBox")
    if box:
        styles["layout"] = {
            "x": box.get("x", 0),
            "y": box.get("y", 0),
            "width": box.get("width", 0),
            "height": box.get("height", 0),
        }
    layout_mode = node.get("layoutMode")
    if layout_mode and layout_mode != "NONE":
        styles["flex"] = {
            "direction": "row" if layout_mode == "HORIZONTAL" else "column",
            "gap": node.get("itemSpacing", 0),
            "primaryAlign": node.get("primaryAxisAlignItems"),
            "counterAlign": node.get("counterAxisAlignItems"),
        }

    fills = node.get("fills") or []
    if fills:
        styles["fills"] = fills

    strokes = node.get("strokes") or []
    if strokes:
        styles["strokes"] = strokes

    styles["strokeWeight"] = node.get("strokeWeight", 1)
    styles["strokeAlign"] = node.get("strokeAlign")

    if "cornerRadius" in node:
        styles["cornerRadius"] = node["cornerRadius"]

    if "rectangleCornerRadii" in node:
        styles["cornerRadii"] = node["rectangleCornerRadii"]

    if kind == "text" and node.get("style"):
        styles["textStyle"] = node["style"]

    padding = {}
    for key in ("paddingLeft", "paddingRight", "paddingTop", "paddingBottom"):
        if key in node:
            padding[key] = node[key]

    if padding:
        styles["padding"] = padding


    # ---------------------------------------------------
    # ⭐ CREATE UI NODE *FIRST*
    # ---------------------------------------------------
    ui: UiNode = {
        "id": node["id"],
        "name": node.get("name", ""),
        "kind": kind,
        "styles": styles,
        "children": []
    }

    if kind == "text":
        ui["text"] = node.get("characters", "")

    # ---------------------------------------------------
    # ⭐ NOW build children, attach parent
    # ---------------------------------------------------
    seen_ids = set()

    for c in node.get("children", []):
        if not c.get("visible", True):
            continue
        cid = c["id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        child_ui = map_figma_to_ui(c)
        #child_ui["parent"] = ui       # <-- NOW VALID
        ui["children"].append(child_ui)

    return ui

def apply_absolute_layout(node, root_x=None, root_y=None):
    layout = node.get("styles", {}).get("layout", {})

    # First call → record root's global top-left
    if root_x is None and root_y is None:
        root_x = layout.get("x", 0)
        root_y = layout.get("y", 0)

    abs_x = layout.get("x", 0) - root_x
    abs_y = layout.get("y", 0) - root_y

    layout["abs_x"] = abs_x
    layout["abs_y"] = abs_y

    for child in node.get("children", []):
        apply_absolute_layout(child, root_x, root_y)
