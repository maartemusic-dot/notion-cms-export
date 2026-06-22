import requests
import json
import os

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    raise ValueError("Missing NOTION_TOKEN or DATABASE_ID environment variables")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_all_pages():
    all_results = []
    next_cursor = None
    while True:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        
        response = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=headers,
            json=payload
        )
        data = response.json()
        all_results.extend(data.get("results", []))
        next_cursor = data.get("next_cursor")
        if not next_cursor:
            break
    return all_results

def extract_property(prop):
    """
    Extract value from a Notion property based on its type.
    Returns a string (for text, multi-select, formula) or a URL (for files).
    """
    if not prop:
        return ""
    
    prop_type = prop.get("type")
    
    # Text or Rich Text
    if prop_type in ("title", "rich_text"):
        items = prop.get(prop_type, [])
        return items[0]["plain_text"] if items else ""
    
    # Files
    if prop_type == "files":
        files = prop.get("files", [])
        if files:
            file_obj = files[0]
            # Could be a file uploaded to Notion or an external URL
            if file_obj.get("file"):
                return file_obj["file"].get("url", "")
            elif file_obj.get("external"):
                return file_obj["external"].get("url", "")
        return ""
    
    # Multi-select
    if prop_type == "multi_select":
        options = prop.get("multi_select", [])
        # Return as comma-separated string, or empty if none
        return ", ".join(opt["name"] for opt in options)
    
    # Formula – extract the result (can be string, number, boolean, etc.)
    if prop_type == "formula":
        formula = prop.get("formula", {})
        # Formula result could be in "string", "number", "boolean", "date"
        if "string" in formula:
            return formula["string"]
        elif "number" in formula:
            return str(formula["number"])
        elif "boolean" in formula:
            return str(formula["boolean"])
        elif "date" in formula:
            return formula["date"].get("start", "")
        return ""
    
    # URL (just in case)
    if prop_type == "url":
        return prop.get("url", "")
    
    # Fallback: return empty
    return ""

# Fetch all pages
pages = fetch_all_pages()

output = []
for page in pages:
    props = page["properties"]
    
    # Extract each field using the helper
    title = extract_property(props.get("Title"))
    image = extract_property(props.get("Image"))
    link = extract_property(props.get("Link"))
    slug = extract_property(props.get("Slug"))
    
    output.append({
        "Title": title,
        "Image": {"url": image} if image else "",
        "Link": link,
        "Slug": slug,
    })

# Save to file
with open("output.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"✅ Exported {len(output)} items to output.json")
