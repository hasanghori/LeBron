from enum import Enum

class ActionType(Enum):
    NOTION = "NotionAPI"
    CALENDAR = "Calendar"
    GOOGLE_CALENDAR = "GoogleCalendarCreds"
    ERROR = "Error"