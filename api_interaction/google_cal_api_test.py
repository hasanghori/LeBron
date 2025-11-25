import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarAPI:
    def __init__(self, credentials_path='calendar_creds.json', token_path='token.json'):
        """Initialize the Google Calendar API client"""
        self.creds = None
        self.service = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing expired token...")
                self.creds.refresh(Request())
            else:
                print("Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=8080)

            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
            print(" Authentication successful!")

        self.service = build('calendar', 'v3', credentials=self.creds)

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

            print(f" Event created: {event.get('summary')}")
            print(f"   Link: {event.get('htmlLink')}")
            return {
                'status': 'success',
                'event_id': event['id'],
                'link': event.get('htmlLink'),
                'summary': event.get('summary')
            }

        except HttpError as error:
            print(f"L Error creating event: {error}")
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

            print(f"\n=� Event Details:")
            print(f"   Title: {event.get('summary')}")
            print(f"   Description: {event.get('description', 'No description')}")
            print(f"   Start: {event['start'].get('dateTime', event['start'].get('date'))}")
            print(f"   End: {event['end'].get('dateTime', event['end'].get('date'))}")
            print(f"   Link: {event.get('htmlLink')}")
            print(f"   Status: {event.get('status')}")

            return {
                'status': 'success',
                'event': event
            }

        except HttpError as error:
            print(f"L Error getting event: {error}")
            return {
                'status': 'error',
                'message': str(error)
            }

    def list_upcoming_events(self, max_results: int = 10, calendar_id: str = 'primary') -> list:
        """
        List upcoming events

        Args:
            max_results: Maximum number of events to return
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            list: List of upcoming events
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            print(f'\n=� Getting the upcoming {max_results} events...')

            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                print('No upcoming events found.')
                return []

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   - {event['summary']} (ID: {event['id'][:20]}...)")
                print(f"     Start: {start}")

            return events

        except HttpError as error:
            print(f"L Error listing events: {error}")
            return []

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

            print(f" Event deleted successfully")
            return {
                'status': 'success',
                'event_id': event_id,
                'message': 'Event deleted successfully'
            }

        except HttpError as error:
            print(f"L Error deleting event: {error}")
            return {
                'status': 'error',
                'message': str(error)
            }


def main():
    """Interactive test of Google Calendar API"""
    print("=== Google Calendar API Test ===\n")

    # Initialize API (will prompt for auth if needed)
    print("Step 1: Authenticating...")
    cal_api = GoogleCalendarAPI()
    print()

    # Create an event
    print("Step 2: Creating a test event...")
    start_time = datetime.now() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=1)

    create_result = cal_api.create_event(
        summary="Test Event from Python API",
        start_datetime=start_time,
        end_datetime=end_time,
        description="This is a test event to verify the Google Calendar API is working",
        calendar_id='primary',
        color_id='9',  # Blueberry color
        timezone='America/Los_Angeles'
    )

    if create_result['status'] != 'success':
        print("Failed to create event. Exiting.")
        return

    event_id = create_result['event_id']
    print()

    # List upcoming events
    print("Step 3: Listing upcoming events...")
    cal_api.list_upcoming_events(max_results=5)
    print()

    # Get the specific event we just created
    print("Step 4: Getting the event we just created...")
    cal_api.get_event(event_id)
    print()

    # Ask user if they want to delete the event
    print("Step 5: Deleting the test event...")
    response = input("Do you want to delete the test event? (y/n): ").strip().lower()

    if response == 'y':
        delete_result = cal_api.delete_event(event_id)
        print()

        if delete_result['status'] == 'success':
            print(" Test completed successfully!")
        else:
            print("� Test completed but deletion failed")
    else:
        print(f"\n� Test event was NOT deleted. Event ID: {event_id}")
        print("You can manually delete it from Google Calendar or run this again.")

    print("\n=== Test Complete ===")


if __name__ == '__main__':
    main()
