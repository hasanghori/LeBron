import os
from notion_client import Client, APIResponseError
from ai_model import AIModel
import logging


# What Does this class do?
# Create Notion API Object
# Writes a note to a database with tags
# Decides what tags to add to a note
# Decides what title to use for a note

# Long Term
#   - Could I parse a note and maybe separate certain data 
#   and store that in a different note with a different title/ tag?
#   - Can I query my notion to get information about me?

class NotionAPI:
    def __init__(self, notion_api_key: str, database_id: str, ai_model: AIModel):
        # self.notion_api_key = notion_api_key
        self.database_id = database_id
        self.ai_model = ai_model
        logging.info(f"Notion API key for initialization: {notion_api_key}")
        self.notion = Client(auth=notion_api_key)

    def list_accessible_databases(self):
        print("Listing accessible databases")
        response = self.notion.search(
            filter={"property": "object", "value": "database"}
        )

        for db in response["results"]:
            title = db.get("title", [])
            title_text = title[0]["plain_text"] if title else "(Untitled)"
            print(f"📄 Title: {title_text}")
            print(f"🆔 ID: {db['id']}")
            print("------")
    
    # Looks like there is an error with retrieving stuff from notion
    def get_all_tags(self):
        """Retrieve all available tags from the database's Tags property"""
        try:
            # Get database schema to access multi-select options
            database = self.notion.databases.retrieve(database_id=self.database_id)

            # Extract Tags property options
            tags_property = database['properties'].get('Tags', {})
            if tags_property.get('type') == 'multi_select':
                tag_options = tags_property['multi_select']['options']
                return [option['name'] for option in tag_options]

            return []

        except APIResponseError as e:
            logging.error("❌ Failed to retrieve tags: %s", e)
            return []

    
    def create_note_with_tags(self, content):
        try:
            all_tags = self.get_all_tags()
            logging.info(f"All tags: {all_tags}")
            tags = [self.ai_model.choose_tag(content, all_tags)]
            title = self.ai_model.choose_title(content)

            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {"text": {"content": title}}
                        ]
                    },
                    "Tags": {
                        "multi_select": [{"name": tag} for tag in tags]
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ]
            )

            logging.info("✅ Note created successfully. ID: %s", response["id"])
            return {"status": "ok", "page_id": response["id"]}

        except APIResponseError as e:
            logging.error("❌ Failed to create Notion note: %s", e)
            return {"status": "error", "message": str(e)}
    