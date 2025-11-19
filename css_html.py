from typing import Any, Dict
from mapper import UiNode

def _rgba_from_paint(paint: Dict) -> str | None:
    color = paint.get("color")
    if not color:
        return None
    r = int(round(color["r"] * 255))
    g = int(round(color["g"] * 255))
    b = int(round(color["b"] * 255))
    opacity = paint.get("opacity", color.get("a", 1))
    return f"rgba({r}, {g}, {b}, {opacity})"

def _gradient_from_paint(paint: Dict) -> str | None:
    stops = paint.get("gradientStops")
    if not stops:
        return None
    parts = []
    for stop in stops:
        c = stop["color"]
        r = int(round(c["r"] * 255))
        g = int(round(c["g"] * 255))
        b = int(round(c["b"] * 255))
        a = c.get("a", 1)
        pos = int(round(stop["position"] * 100))
        parts.append(f"rgba({r}, {g}, {b}, {a}) {pos}%")
    return "linear-gradient(90deg, " + ", ".join(parts) + ")"

def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def generate_css(root: UiNode) -> tuple[str, dict[str, str]]:
    lines = []
    id_to_class = {}

    # Global styles
    lines.append(
        "body { margin: 0; background: #111111; font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif; }"
    )
    if root.get("styles", {}).get("layout"):
        w = root["styles"]["layout"]["width"]
        h = root["styles"]["layout"]["height"]
        lines.append(f".canvas {{ margin: 0 auto; width: {w}px; height: {h}px; position: relative; }}")

    def walk(node: UiNode, parent_is_flex=False):
        node_id = node["id"]
        class_name = "node_" + "".join(c if c.isalnum() else "_" for c in node_id)
        id_to_class[node_id] = class_name

        decl = []
        styles = node.get("styles", {})

        # Flex container
        flex = styles.get("flex")
        if flex:
            decl.append("display: flex")
            decl.append(f"flex-direction: {flex.get('direction','row')}")
            if flex.get("gap"):
                decl.append(f"gap: {flex['gap']}px")
            # Map Figma alignment to CSS
            primary = flex.get("primaryAlign")
            if primary:
                mapping = {
                    "MIN": "flex-start",
                    "CENTER": "center",
                    "MAX": "flex-end",
                    "SPACE_BETWEEN": "space-between",
                }
                decl.append(f"justify-content: {mapping.get(primary,'flex-start')}")
            counter = flex.get("counterAlign")
            if counter:
                mapping = {
                    "MIN": "flex-start",
                    "CENTER": "center",
                    "MAX": "flex-end",
                }
                decl.append(f"align-items: {mapping.get(counter,'flex-start')}")
            pad = flex.get("padding", {})
            if pad:
                decl.append(
                    f"padding: {pad.get('top',0)}px {pad.get('right',0)}px {pad.get('bottom',0)}px {pad.get('left',0)}px"
                )
        else:
            # Only use absolute positioning if parent is NOT flex
            layout = styles.get("layout")
            if layout and not parent_is_flex:
                decl.append("position: absolute")
                decl.append(f"left: {layout.get('x',0)}px")
                decl.append(f"top: {layout.get('y',0)}px")
                decl.append(f"width: {layout.get('width',0)}px")
                decl.append(f"height: {layout.get('height',0)}px")

        # Fills
        fills = styles.get("fills", [])
        if fills:
            paint = fills[0]
            t = paint.get("type", "")
            if t == "SOLID":
                c = _rgba_from_paint(paint)
                if c:
                    decl.append(f"background-color: {c}")
            elif "GRADIENT" in t:
                g = _gradient_from_paint(paint)
                if g:
                    decl.append(f"background: {g}")

        # Strokes
        strokes = styles.get("strokes", [])
        if strokes:
            paint = strokes[0]
            c = _rgba_from_paint(paint)
            weight = styles.get("strokeWeight", 1)
            if c:
                decl.append(f"border: {weight}px solid {c}")

        # Border radius
        if "cornerRadius" in styles:
            decl.append(f"border-radius: {styles['cornerRadius']}px")
        elif "cornerRadii" in styles:
            tl, tr, br, bl = styles["cornerRadii"]
            decl.append(f"border-radius: {tl}px {tr}px {br}px {bl}px")

        # Text
        if node["kind"] == "text":
            ts = styles.get("textStyle", {})
            if "fontFamily" in ts:
                decl.append(f"font-family: '{ts['fontFamily']}', sans-serif")
            if "fontSize" in ts:
                decl.append(f"font-size: {ts['fontSize']}px")
            if "fontWeight" in ts:
                decl.append(f"font-weight: {int(ts['fontWeight'])}")
            if "lineHeightPx" in ts:
                decl.append(f"line-height: {ts['lineHeightPx']}px")
            if "letterSpacing" in ts:
                decl.append(f"letter-spacing: {ts['letterSpacing']}px")
            align = ts.get("textAlignHorizontal")
            if align:
                mapping = {"LEFT":"left","CENTER":"center","RIGHT":"right","JUSTIFIED":"justify"}
                decl.append(f"text-align: {mapping.get(align,'left')}")
            valign = ts.get("textAlignVertical")
            if valign:
                mapping = {"TOP":"top","CENTER":"middle","BOTTOM":"bottom"}
                decl.append(f"vertical-align: {mapping.get(valign,'top')}")
            decl.append("white-space: pre-wrap")

        # Emit CSS rule
        lines.append(f".{class_name} {{")
        for d in decl:
            lines.append(f"  {d};")
        lines.append("}")

        # Recurse into children
        for child in node.get("children", []):
            walk(child, parent_is_flex=bool(flex))

    walk(root)
    return "\n".join(lines), id_to_class

def generate_html(root: UiNode, id_to_class: dict[str,str]) -> str:
    def render(node: UiNode) -> str:
        cls = id_to_class[node["id"]]
        kind = node["kind"]
        children_html = "".join(render(c) for c in node.get("children", []))
        if kind == "text":
            inner = _escape_html(node.get("text",""))
            return f'<div class="{cls}">{inner}</div>'
        return f'<div class="{cls}">{children_html}</div>'

    body_html = render(root)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Figma Export</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="canvas">
    {body_html}
  </div>
</body>
</html>
"""
    return html
