import requests
import json
import os

# ---------- GET SECRETS FROM ENVIRONMENT VARIABLES ----------
# These are set up in the GitHub Action workflow
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")
# ------------------------------------------------------------

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

# Fetch all pages from the database
pages = fetch_all_pages()

output = []
for page in pages:
    props = page["properties"]
    
    # ---------- ADAPT FIELD NAMES TO YOUR DATABASE ----------
    # Change "Title", "Image", "Link", "Slug" to match your Notion property names
    title_field = props.get("Title", {})
    title_value = title_field.get("title", [])
    title_text = title_value[0]["plain_text"] if title_value else ""
    
    image_field = props.get("Image", {})
    image_url = ""
    if image_field.get("type") == "files" and image_field.get("files"):
        image_url = image_field["files"][0].get("file", {}).get("url", "")
    
    link_field = props.get("Link", {})
    link_url = link_field.get("url", "")
    
    slug_field = props.get("Slug", {})
    slug_value = slug_field.get("rich_text", [])
    slug_text = slug_value[0]["plain_text"] if slug_value else ""
    # --------------------------------------------------------
    
    output.append({
        "Title": title_text,
        "Image": {"url": image_url} if image_url else "",
        "Link": link_url,
        "Slug": slug_text,
    })

# Save to a file
with open("output.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"✅ Exported {len(output)} items to output.json")
