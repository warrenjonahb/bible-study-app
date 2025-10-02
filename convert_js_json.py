import re
import json

def convert_js_to_json(js_file, json_file):
    with open(js_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove JS comments (/* ... */ and // ...)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)  # block comments
    content = re.sub(r"//.*", "", content)  # line comments

    # Remove "var strongsGreekDictionary =" (or any var ... =) prefix
    content = re.sub(r"var\s+\w+\s*=\s*", "", content, count=1)

    # Find the first { and the last }
    start = content.find("{")
    end = content.rfind("}") + 1
    content = content[start:end]

    # Now it's valid JSON
    data = json.loads(content)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Converted {js_file} → {json_file}")

# Example usage:
convert_js_to_json("strongs-hebrew-dictionary.js", "hebrew.json")
