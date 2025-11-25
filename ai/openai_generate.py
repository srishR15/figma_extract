import json
import os
import re
from pathlib import Path
from openai import OpenAI

# ------------------------
# CONFIG
# ------------------------
MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.1
OUTPUT_DIR = "outputAI"
CSS_FILENAME = "styles.css" # Define filename once
HTML_FILENAME = "output.html"
CSS_FILE = os.path.join(OUTPUT_DIR, CSS_FILENAME)
HTML_FILE = os.path.join(OUTPUT_DIR, HTML_FILENAME)
UI_TREE_PATH = "UITree/ui.json"

# ------------------------
# LOAD UI TREE JSON
# ------------------------
def load_ui_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------------------
# HELPER: DETERMINE GENERALIZED CONTRAST BACKGROUND
# ------------------------
def get_contrast_background(ui_tree: dict) -> str:
    """Analyzes the root frame color for light/dark and suggests a contrasting background."""
    # Find the main design frame (the top-level child of the CANVAS)
    root_fills = ui_tree.get("children", [{}])[0].get("fills", []) if ui_tree.get("type") == "CANVAS" else ui_tree.get("fills", [])
    
    if not root_fills:
        # If no fill is found, default to a dark background for contrast
        return "#1A1A1A"

    first_fill = root_fills[0]
    if first_fill.get("type") == "SOLID":
        color = first_fill["color"]
        # Simplified Luma calculation for brightness
        brightness = (0.299 * color.get("r", 0) + 0.587 * color.get("g", 0) + 0.114 * color.get("b", 0))

        # Check if the frame color is light (brightness > 0.5)
        if brightness > 0.5:
            return "#1A1A1A"  # Dark background for light frame
        else:
            return "#EAEAEA" # Light background for dark frame
    
    # Default for gradients or other complex fills
    return "#1A1A1A"


# ------------------------
# CALL OPENAI API
# ------------------------
def call_openai(ui_tree: dict, contrast_bg: str):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set.")
        
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Updated Prompt: Strict adherence to box model and input field sizing
#     prompt = f"""
# You are an expert senior frontend engineer specializing in pixel-perfect conversion of design specs to code.
# You will receive a CLEANED UI tree generated from a Figma file.
# Your job is to produce the *pixel-accurate HTML + CSS* that perfectly represents the design.

# CRITICAL REQUIREMENTS FOR PIXEL PERFECTION:
# 1.  **Form Elements:** For the input fields, you MUST use the native **<input>** tag with a **placeholder** attribute.
# 2.  **POSITIONING FIX (MANDATORY):** The main frame (the root element in the JSON) MUST have `position: relative;`. All of its children that are not part of an Auto-Layout (like .headline, .input-container, .sign-in-button) **MUST** use `position: absolute;`. You **MUST** calculate and set the `top` and `left` properties for these absolute elements by referencing the coordinates in the UI tree. **Do not omit the 'top' property.**
# 3.  **Input Style:** The resulting CSS must apply the text styles (font-family, font-size, color, etc.) to the **<input>** element itself.
# 4.  **CSS Box Model Fix:** You MUST apply `box-sizing: border-box;` globally (to all elements using `*`).
# 5.  **Generalized Contrast:** Set the `<body>` background color to **{contrast_bg}**. The main frame must be centered.
# 6.  **Data Adherence:** Maintain ALL styling, dimensions, radii, gradients, and **all effects** (box-shadow/blur).
# 7.  **CSS Link:** The generated HTML MUST include `<link rel="stylesheet" href="{CSS_FILENAME}">` inside the `<head>` tag.

# OUTPUT FORMAT (STRICTLY ADHERE TO THIS):
# - Output TWO separate blocks, enclosed by the markers below.
# - DO NOT use markdown code fences or add any comments or explanations.

# ===HTML_START===
# <full html document, including <html>, <head>, and <body>>

# ===CSS_START===
# <full css for the html>
# """
    prompt = f"""
You are an expert senior frontend engineer specializing in pixel-perfect,
data-faithful conversion of structured Figma JSON trees into HTML and CSS.

You will receive a CLEANED UI tree. You MUST obey the data exactly.

------------------------------------------------------------
ABSOLUTE RULES (DO NOT VIOLATE):
------------------------------------------------------------
1.  **FRAME HANDLING**
    - The root node of the JSON MUST become a centered container
      with: `position: relative`, fixed pixel width & height, overflow hidden.

2.  **POSITIONING**
    - If a node has explicit x/y coordinates → YOU MUST use:
        position: absolute;
        top: <y>px;
        left: <x>px;
    - NEVER invent, modify, or ignore coordinates.
    - Maintain exact width and height from the JSON.
2.1 BOTTOM ANCHORING (IMPORTANT)
    - If (y + height) is within 12px of the root frame’s height,
      the node is bottom-anchored.
    - Use:
          position: absolute;
          bottom: root.height - (y + height) px;
          left: <x>px;
    - DO NOT use "top" for bottom-anchored nodes.

3.  **AUTO-LAYOUT**
    - Only use flexbox if the JSON node contains:
        layoutMode
        itemSpacing
        padding values
      Otherwise, DO NOT use flexbox.

4.  **INPUTS**
    - If a Figma node has “characters” and looks like a text *label* inside a box → render as <div>.
    - If it is truly an interactive field → use <input>.
    - If using <input>, map:
        characters → placeholder
        style → CSS properties
    - NEVER duplicate text inside an input. One placeholder only.

5.  **TEXT**
    - All typography (font-family, size, weight, color, line-height, letter-spacing)
      MUST come directly from the JSON “style” object.

6.  **VISUAL ACCURACY**
    - EXACT radii
    - EXACT borders
    - EXACT gradients
    - EXACT fills (convert Figma RGB to CSS rgba)
    - EXACT shadows & blurs

7.  **GENERALIZED BACKGROUND**
    - The <body> background MUST be: {contrast_bg}
    - The main frame must be centered both horizontally and vertically.

8.  **GLOBAL CSS**
    - You MUST include:
        * {{ box-sizing: border-box; margin: 0; padding:0; }}

------------------------------------------------------------
OUTPUT FORMAT (DO NOT BREAK FORMAT):
------------------------------------------------------------

===HTML_START===
<full html document with <head>, <link rel="stylesheet" href="{CSS_FILENAME}">, and <body>>

===CSS_START===
<full CSS>

------------------------------------------------------------

Now produce HTML + CSS from the following UI tree:

{json.dumps(ui_tree, indent=2)}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": "You are a specialized AI that converts structured JSON UI trees into pixel-perfect HTML and CSS code."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# ------------------------
# PARSE HTML + CSS FROM THE RESPONSE (Robust Parsing)
# ------------------------
def split_output(text: str):
    # Fix: Robust parsing using regex to find markers and remove code fences
    html_match = re.search(r'===HTML_START===(.*?)===CSS_START===', text, re.DOTALL | re.IGNORECASE)
    css_match = re.search(r'===CSS_START===(.*)', text, re.DOTALL | re.IGNORECASE)

    if not html_match or not css_match:
        raise ValueError(f"Failed to parse HTML/CSS blocks from response.")

    html = html_match.group(1).strip()
    css = css_match.group(1).strip()

    # Clean up common LLM errors (markdown fences)
    html = re.sub(r'```(html)?', '', html).strip()
    css = re.sub(r'```(css)?', '', css).strip()

    return html, css

# ------------------------
# WRITE FILES
# ------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
def save_files(html, css):
    Path(HTML_FILE).write_text(html, encoding="utf-8")
    Path(CSS_FILE).write_text(css, encoding="utf-8")
    print(f"[OK] Saved {HTML_FILE} and {CSS_FILE} in the '{OUTPUT_DIR}' directory.")

# ------------------------
# MAIN
# ------------------------
def main():
    try:
        print(f"[*] Loading UI tree from {UI_TREE_PATH}…")
        ui_tree = load_ui_json(UI_TREE_PATH)
    except FileNotFoundError:
        print(f"[ERROR] UI tree file not found at {UI_TREE_PATH}. Did you run 'python export_ui_tree.py <figma_json_file>' first?")
        return

    # Determine contrast background color
    contrast_bg = get_contrast_background(ui_tree)
    print(f"[*] Determined generalized contrast background: {contrast_bg}")

    print("[*] Calling OpenAI to generate code…")
    try:
        response_text = call_openai(ui_tree, contrast_bg)
    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return

    print("[*] Parsing output…")
    try:
        html, css = split_output(response_text)
    except ValueError:
        return

    print("[*] Writing files…")
    save_files(html, css)

    print(f"\nSUCCESS! Open {HTML_FILE} in your browser to view the result.\n")

if __name__ == "__main__":
    main()