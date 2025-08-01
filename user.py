class User:
    def __init__(self, phone_number, notion_api_key, interests):
        self.phone_number = phone_number,
        self.notion_api_key = notion_api_key
        self.interests = interests
    
    def get_phone_number(self):
        return self.phone_number

    def get_interests(self):
        return self.interests
    
    def get_notion_api_key(self):
        return self.notion_api_key
    
    