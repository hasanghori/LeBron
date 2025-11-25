from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarAPI:
    """
    Google Calendar API wrapper for web applications

    For web apps, you need to:
    1. Store user tokens in a database (like Firebase)
    2. Pass the credentials when initializing this class
    3. Handle OAuth flow in your Flask routes (see google_cal_oauth_example.py)
    """

    def __init__(self, user_credentials: dict = None):
        """
        Initialize with user's OAuth credentials

        Args:
            user_credentials: Dictionary with OAuth token info
                             (token, refresh_token, token_uri, client_id, client_secret)
        """
        self.service = None
        if user_credentials:
            self.creds = Credentials.from_authorized_user_info(user_credentials, SCOPES)
            self._build_service()

    def _build_service(self):
        """Build the Google Calendar service"""
        if self.creds and self.creds.valid:
            self.service = build('calendar', 'v3', credentials=self.creds)
        elif self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
            self.service = build('calendar', 'v3', credentials=self.creds)
        else:
            raise Exception("Invalid credentials")

    def create_event(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: str = "",
        calendar_id: str = 'primary',
        color_id: str = None,
        timezone: str = 'America/Los_Angeles'
    ) -> dict:
        """
        Create a calendar event

        Args:
            summary: Event title
            start_datetime: Start date and time
            end_datetime: End date and time
            description: Event description
            calendar_id: Calendar ID (default: 'primary')
            color_id: Color ID (1-11)
            timezone: Timezone for the event

        Returns:
            dict: Created event details
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': timezone,
            },
        }

        if color_id:
            event['colorId'] = str(color_id)

        try:
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()

            logging.info(f"Event created: {event.get('summary')}")
            return {
                'status': 'success',
                'event_id': event['id'],
                'link': event.get('htmlLink'),
                'summary': event.get('summary')
            }

        except HttpError as error:
            logging.error(f"Error creating event: {error}")
            return {
                'status': 'error',
                'message': str(error)
            }

    def get_event(self, event_id: str, calendar_id: str = 'primary') -> dict:
        """
        Get a specific calendar event

        Args:
            event_id: ID of the event to retrieve
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            dict: Event details
        """
        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return {
                'status': 'success',
                'event': {
                    'id': event['id'],
                    'summary': event.get('summary'),
                    'description': event.get('description', ''),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'link': event.get('htmlLink'),
                    'status': event.get('status')
                }
            }

        except HttpError as error:
            logging.error(f"Error getting event: {error}")
            return {
                'status': 'error',
                'message': str(error)
            }

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> dict:
        """
        Delete a calendar event

        Args:
            event_id: ID of the event to delete
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            dict: Status of the deletion
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            logging.info(f"Event {event_id} deleted successfully")
            return {
                'status': 'success',
                'event_id': event_id,
                'message': 'Event deleted successfully'
            }

        except HttpError as error:
            logging.error(f"Error deleting event: {error}")
            return {
                'status': 'error',
                'message': str(error)
            }
