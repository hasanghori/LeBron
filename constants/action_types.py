from enum import Enum

class ActionType(Enum):
    NOTION = "NotionAPI"
    CALENDAR = "Calendar"
    ERROR = "Error"