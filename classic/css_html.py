from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any

# NOTE: UiNode is a TypedDict in mapper.py, but we avoid importing typing here
# to keep this file compatible with your current project.

def _rgba_from_color(c: Dict[str, Any], opacity: float | None = None) -> str:
    if not c:
        return "rgba(0,0,0,0)"
    r = int(round(c.get("r", 0) * 255))
    g = int(round(c.get("g", 0) * 255))
    b = int(round(c.get("b", 0) * 255))
    a = 1.0
    if opacity is not None:
        a = opacity
    else:
        a = c.get("a", 1.0)
    return f"rgba({r}, {g}, {b}, {a})"

def _gradient_from_paint(paint: Dict[str, Any]) -> str | None:
    stops = paint.get("gradientStops") or []
    if not stops:
        return None
    parts = []
    for s in stops:
        col = s["color"]
        pos = int(round(s.get("position", 0) * 100))
        parts.append(f"{_rgba_from_color(col)} {pos}%")
    # Simplified: use left-to-right gradient
    return "linear-gradient(90deg, " + ", ".join(parts) + ")"

def _extract_fill(styles: Dict[str, Any]) -> str | None:
    fills = styles.get("fills") or []
    if not fills:
        return None
    p = fills[0]
    t = p.get("type", "")
    if t == "SOLID":
        color = p.get("color", {})
        opacity = p.get("opacity", color.get("a", 1.0))
        return _rgba_from_color(color, opacity)
    if "GRADIENT" in t:
        g = _gradient_from_paint(p)
        return g
    return None

def _extract_stroke(styles: Dict[str, Any]) -> str | None:
    strokes = styles.get("strokes") or []
    if not strokes:
        return None
    s = strokes[0]
    if s.get("type") == "SOLID":
        col = s.get("color", {})
        opacity = s.get("opacity", col.get("a", 1.0))
        weight = styles.get("strokeWeight", 1)
        return f"{weight}px solid {_rgba_from_color(col, opacity)}"
    return None

def _text_style_css(text_style: Dict[str, Any]) -> list[str]:
    decls = []
    if not text_style:
        return decls
    if "fontFamily" in text_style:
        # fallback sans-serif
        decls.append(f"font-family: '{text_style['fontFamily']}', sans-serif;")
    if "fontSize" in text_style:
        decls.append(f"font-size: {text_style['fontSize']}px;")
    if "fontWeight" in text_style:
        decls.append(f"font-weight: {int(text_style['fontWeight'])};")
    if "lineHeightPx" in text_style:
        decls.append(f"line-height: {text_style['lineHeightPx']}px;")
    if "letterSpacing" in text_style:
        decls.append(f"letter-spacing: {text_style['letterSpacing']}px;")
    align = text_style.get("textAlignHorizontal")
    if align:
        mapping = {"LEFT":"left","CENTER":"center","RIGHT":"right","JUSTIFIED":"justify"}
        decls.append(f"text-align: {mapping.get(align,'left')};")
    return decls

# -------------------------------
# CSS generator
# -------------------------------
def generate_css(root: Dict[str, Any], id_to_class: Dict[str, str]) -> str:
    """
    Improved CSS generator:
      - Avoid absolute positioning for children of auto-layout/flex containers.
      - Do not set background on text nodes; set color instead.
      - Keep fills/strokes/cornerRadius/text styles as before.
    """
    lines: list[str] = []
    root_layout = root.get("styles", {}).get("layout", {})
    root_x = root_layout.get("abs_x", 0)
    root_y = root_layout.get("abs_y", 0)
    root_w = root_layout.get("width", 0)
    root_h = root_layout.get("height", 0)

    lines.append("/* Reset */")
    lines.append("* { box-sizing: border-box; }")
    lines.append("html, body { height: 100%; }")
    lines.append("body { margin: 0; padding: 0; background: #111;}")
    lines.append(f".canvas {{ position: relative; width: {int(root_w)}px; height: {int(root_h)}px; background: transparent; overflow: hidden; margin: 0 auto;}}")

    def walk(n: Dict[str, Any], parent_is_flex: bool = False):
        nid = n["id"]
        cls = id_to_class.get(nid, "node_"+nid.replace(":", "_"))
        styles = n.get("styles", {})
        layout = styles.get("layout", {})
        # Detect if this node is center-aligned by text style
        is_center_text = False
        if n.get("kind") == "text":
            ts = styles.get("textStyle", {})
            if ts.get("textAlignHorizontal") == "CENTER":
                is_center_text = True
        # Coordinates relative to root frame (keeps your approach)
        #x = layout.get("x", 0)
        #y = layout.get("y", 0)
        x = layout.get("abs_x", 0) - root_x
        y = layout.get("abs_y", 0) - root_y

        w = layout.get("width", 0)
        h = layout.get("height", 0)

        decls: list[str] = []
        
        if not parent_is_flex:
            # Normal absolute layout
            decls.append("position: absolute")
            decls.append(f"left: {int(x)}px")
            if should_be_bottom_anchored(y, h, root_h):  # Implement this helper
                bottom_val = root_h - (y + h)
                decls.append(f"bottom: {int(bottom_val)}px")
            else:
                decls.append(f"top: {int(y)}px")
        else:
            # Child of flex container → allow natural flow
            decls.append("position: static")
            if n.get("kind") == "text" and is_center_text:
                decls.append("align-self: center")

        # Width/Height: keep widths/heights so fixed-size children still size,
        # but for children of flex parents we avoid forcing absolute coordinates.
        # If you want children to shrink/grow, you can add flex rules here.
        decls.append(f"width: {int(w)}px")
        decls.append(f"height: {int(h)}px")

        # Auto-layout / flex for THIS node
        flex = styles.get("flex")
        if flex:
            decls.append("display: flex")
            direction = flex.get("direction", "column")
            decls.append(f"flex-direction: {direction}")
            gap = flex.get("gap", 0)
            if gap:
                decls.append(f"gap: {int(gap)}px")
            align_map = {"MIN":"flex-start","CENTER":"center","MAX":"flex-end","SPACE_BETWEEN":"space-between"}
            if flex.get("primaryAlign"):
                decls.append(f"justify-content: {align_map.get(flex['primaryAlign'],'flex-start')}")
            if flex.get("counterAlign"):
                decls.append(f"align-items: {align_map.get(flex['counterAlign'],'flex-start')}")

        # Background / fills — but DO NOT set background for text nodes (we set color instead)
        fill = _extract_fill(styles)
        if fill and n.get("kind") != "text":
            decls.append(f"background: {fill}")

        # strokes / borders
        stroke = _extract_stroke(styles)
        if stroke:
            decls.append(f"border: {stroke}")

        # corner radius
        if "cornerRadius" in styles:
            decls.append(f"border-radius: {styles['cornerRadius']}px")
        elif "cornerRadii" in styles:
            cr = styles["cornerRadii"]
            decls.append(f"border-radius: {cr[0]}px {cr[1]}px {cr[2]}px {cr[3]}px")

        # Text nodes: apply text style and color (not background)
        if n.get("kind") == "text":
            text_style = styles.get("textStyle", {})
            decls.extend(_text_style_css(text_style))
            fills = styles.get("fills") or []
            if fills:
                p = fills[0]
                if p.get("type") == "SOLID":
                    color = p.get("color", {})
                    opacity = p.get("opacity", color.get("a", 1.0))
                    decls.append(f"color: {_rgba_from_color(color, opacity)}")
            decls.append("white-space: pre-wrap")
            decls.append("display: flex")
            decls.append("align-items: center")
            align = text_style.get("textAlignHorizontal")
            if align == "CENTER":
                decls.append("text-align: center")
                decls.append("justify-content: center") 
            elif align == "RIGHT":
                decls.append("text-align: right")
            else:
                decls.append("text-align: left")

        #apply padding
        pad = styles.get("padding", {})
        if pad:
            l = pad.get("paddingLeft", 0)
            r = pad.get("paddingRight", 0)
            t = pad.get("paddingTop", 0)
            b = pad.get("paddingBottom", 0)
            decls.append(f"padding: {t}px {r}px {b}px {l}px")    

        # write CSS block
        lines.append(f".{cls} {{")
        for d in decls:
            lines.append(f"  {d};")
        lines.append("}")

        # Recurse into children
        # If this node has flex, its children should be considered inside a flex container.
        child_parent_is_flex = bool(flex)
        for c in n.get("children", []):
            walk(c, parent_is_flex=child_parent_is_flex)

    walk(root, parent_is_flex=False)
    return "\n".join(lines)

def should_be_bottom_anchored(y, h, root_h, threshold=12):
    # Anchors if the bottom is very close to the canvas's bottom edge
    return abs((y + h) - root_h) < threshold


# -------------------------------
# HTML generator using Jinja2
# -------------------------------
def generate_html(root: Dict[str, Any], id_to_class: Dict[str, str]) -> str:
    def _escape(text: str) -> str:
        return (text or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def render(node: Dict[str, Any]) -> str:
        cls = id_to_class.get(node["id"], "node_"+node["id"].replace(":", "_"))
        kind = node.get("kind", "").lower()
        name = node.get("name", "").lower()

        # text node -> div with text
        if kind == "text":
            return f'<div class="{cls}">{_escape(node.get("text",""))}</div>'

        if kind == "shape":
        # shapes normally have no text, only styles
            children_html = "".join(render(c) for c in node.get("children", []))
            return f'<div class="{cls}">{children_html}</div>'
        # inputs
        if "input" in name or "email" in name or "password" in name:
            tp = "password" if "password" in name else "text"
            placeholder = _escape(node.get("text","") or node.get("name",""))
            return f'<input class="{cls}" type="{tp}" placeholder="{placeholder}"/>'

        # buttons (heuristic)
        if "button" in name or "sign in" in name or "continue" in name or "create account" in name:
            label = _escape(node.get("text","") or node.get("name","Button"))
            return f'<button class="{cls}">{label}</button>' 

        # frames / groups -> preserve container
        children_html = "".join(render(c) for c in node.get("children", []))
        return f'<div class="{cls}">{children_html}</div>'

    #body_html = render(root)
    canvas_class = id_to_class[root["id"]]
    body_html = f'<div class="{canvas_class} canvas">{render(root)}</div>'
    env = Environment(loader=FileSystemLoader(Path("../templates")), autoescape=True)
    template = env.get_template("export.html.j2")
    return template.render(title="Figma Export", body_html=body_html)
