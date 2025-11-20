import json

def print_node(node, indent=0):
    print("  " * indent + f"- {node.get('name')}  [{node.get('type')}]  id={node.get('id')}")
    for child in node.get("children", []):
        print_node(child, indent + 1)

with open("cache/f6gbTssaVTU0ik3u1q0cxL.json", "r") as f:
    data = json.load(f)

print("\nFigma Node Tree:\n")
print_node(data["document"])
