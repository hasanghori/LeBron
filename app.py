import string
from ai_model import AIModel
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request, jsonify, redirect, session
import json
import logging
from api_interaction.notion_api import NotionAPI
from notion_client import Client
import os
import requests
from api_interaction.textbot import Textbot
from user import User
from dotenv import load_dotenv
from constants.action_types import ActionType
from api_interaction.habitify_api import HabitifyAPI
from api_interaction.google_cal_api import GoogleCalendarAPI
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
try:
    load_dotenv()
except:
    pass

PUBLIC_URL = "https://textbot-service-939342988447.us-central1.run.app"
LOCAL_URL = "https://fine-prawn-driven.ngrok-free.app"
IS_PUBLIC = True

cred_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
cred = credentials.Certificate(cred_info)
firebase_admin.initialize_app(cred)

db = firestore.client()

# Set up basic config — do this once, near the top of your app
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key-here")  # Change this in production
database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"

reply_webhook_url = PUBLIC_URL if IS_PUBLIC else LOCAL_URL

# Google OAuth Configuration
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_OAUTH_REDIRECT_URI = f"{PUBLIC_URL if IS_PUBLIC else LOCAL_URL}/api/auth/google/callback"

def send_sms(phone_number, message):
    textbot = Textbot(reply_webhook_url)
    response = textbot.send_text(message, phone_number)
    logging.info(response)

def find_user_key(phone_number: string, key_type: ActionType):
    users_ref = db.collection('users')
    print(phone_number)
    docs = users_ref.where('PhoneNumber', '==', phone_number).stream()

    for doc in docs:
        user_data = doc.to_dict()
        return user_data[key_type.value]

    return None

def get_google_calendar_credentials(phone_number: string):
    """
    Retrieves and refreshes Google Calendar credentials for a user
    Returns a valid Credentials object or None if not found
    """
    from google.auth.transport.requests import Request

    users_ref = db.collection('users')
    docs = users_ref.where('PhoneNumber', '==', phone_number).stream()

    for doc in docs:
        user_data = doc.to_dict()
        creds_data = user_data.get('GoogleCalendarCreds')

        if not creds_data:
            logging.warning(f"No Google Calendar credentials found for {phone_number}")
            return None

        # Reconstruct Credentials object from stored data
        creds = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )

        # Check if token is expired and refresh if needed
        if creds.expired and creds.refresh_token:
            try:
                logging.info(f"Refreshing expired token for {phone_number}")
                creds.refresh(Request())

                # Update stored credentials with new token
                updated_creds_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                doc.reference.update({'GoogleCalendarCreds': updated_creds_data})
                logging.info(f"Token refreshed and updated for {phone_number}")

            except Exception as e:
                logging.error(f"Error refreshing token for {phone_number}: {e}")
                return None

        return creds

    logging.warning(f"User not found: {phone_number}")
    return None

# Core Function for this App
# 1) Receive Message from User
# 2) Determine Action Type
# 3) Perform Action
@app.route('/api/handleSmsReply', methods=['POST'])
def handle_sms_reply():
    data = request.get_json()
    text_id: string = data.get('textId')
    from_number: string = data.get('fromNumber')
    text: string = data.get('text')

    logging.info(f"📩 Received reply from {from_number}: '{text}' (textId: {text_id})")
    
    ai_model: AIModel = AIModel()
    
    action_type: ActionType = ai_model.choose_action_type(text)
    
    try:
        if action_type == ActionType.NOTION:
            action_key = find_user_key(from_number, action_type)

            notion_api = NotionAPI(action_key, database_id, ai_model)
            notion_api.create_note_with_tags(text)
            send_sms(from_number, "Logged to Notion")

        elif action_type == ActionType.CALENDAR or action_type == ActionType.GOOGLE_CALENDAR:
            # Get user's Google Calendar credentials
            creds = get_google_calendar_credentials(from_number)

            if not creds:
                # User needs to authenticate first
                send_sms(from_number, "Please authenticate your Google Calendar first. Visit: " +
                        f"{PUBLIC_URL if IS_PUBLIC else LOCAL_URL}/api/auth/google/start")
                return '', 200

            # Parse the event details from the text using AI
            event_details = ai_model.parse_calendar_event(text)

            # Create credentials dictionary for GoogleCalendarAPI
            creds_dict = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }

            # Initialize Google Calendar API and create event
            calendar_api = GoogleCalendarAPI(creds_dict)
            result = calendar_api.create_event(
                summary=event_details['summary'],
                start_datetime=event_details['start_datetime'],
                end_datetime=event_details['end_datetime'],
                description=event_details.get('description', ''),
                timezone='America/Los_Angeles'
            )

            if result['status'] == 'success':
                send_sms(from_number, f"Event created: {result['summary']}\n{result['link']}")
            else:
                send_sms(from_number, f"Error creating event: {result['message']}")

        else:
            send_sms(from_number, "Error: User not found in database or unsupported action")
    except Exception as e:
        logging.error(f"Error: {e}")
        send_sms(from_number, "Error: " + str(e))

    return '', 200  # Respond OK so Textbelt knows you received it

@app.route('/api/text_test', methods=['GET'])
def text_test():
    textbot = Textbot(reply_webhook_url)
    ai_model = AIModel()
    
    # Fetch all users from the database
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    for doc in docs:
        user_data = doc.to_dict()
        phone_number = user_data.get('PhoneNumber')
        interests = user_data.get('UserInterests')
        print(f"PRINT phone_number - {phone_number}")
        if phone_number == "+19162206037":
            # textbot should send message to whatever the user wants
            message = ai_model.first_message(interests)
            logging.info(f"Sending message to {phone_number}: {message}")
            send_sms(phone_number, message)
    
    return '', 200  # Respond OK so Textbelt knows you received it

#TODO: Add Registration API Call
# Should be triggered when we receive a text from a user that is not registered
# Should respond with probably a notion api sign in page thing/ A thing for people to sign into
# any Action they want

# Google Calendar Authentication Endpoints
@app.route('/api/auth/google/start', methods=['POST'])
def start_google_auth():
    """
    Initiates Google Calendar OAuth flow for a user
    Expected JSON body: {"phone_number": "+1234567890"}
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')

        if not phone_number:
            return jsonify({'error': 'phone_number is required'}), 400

        # Create OAuth flow
        flow = Flow.from_client_secrets_file(
            'calendar_creds.json',
            scopes=GOOGLE_CALENDAR_SCOPES,
            redirect_uri=GOOGLE_OAUTH_REDIRECT_URI
        )

        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )

        # Store state and phone number in session for callback
        session['state'] = state
        session['phone_number'] = phone_number

        # Send SMS with authorization link
        message = f"Please authorize Google Calendar access by clicking this link: {authorization_url}"
        send_sms(phone_number, message)

        logging.info(f"Sent Google Calendar auth link to {phone_number}")

        return jsonify({
            'status': 'success',
            'message': 'Authorization link sent via SMS',
            'auth_url': authorization_url
        }), 200

    except Exception as e:
        logging.error(f"Error starting Google auth: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/google/callback', methods=['GET'])
def google_auth_callback():
    """
    Handles the OAuth callback from Google
    """
    try:
        # Get state from session
        state = session.get('state')
        phone_number = session.get('phone_number')

        if not state or not phone_number:
            return "Error: Session expired or invalid. Please start the authentication process again.", 400

        # Create flow with the same state
        flow = Flow.from_client_secrets_file(
            'calendar_creds.json',
            scopes=GOOGLE_CALENDAR_SCOPES,
            state=state,
            redirect_uri=GOOGLE_OAUTH_REDIRECT_URI
        )

        # Exchange authorization code for credentials
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials

        # Prepare credentials data for storage
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        # Store credentials in Firestore
        users_ref = db.collection('users')
        docs = users_ref.where('PhoneNumber', '==', phone_number).stream()

        user_found = False
        for doc in docs:
            # Update existing user with Google Calendar credentials
            doc.reference.update({
                'GoogleCalendarCreds': creds_data
            })
            user_found = True
            logging.info(f"Updated Google Calendar credentials for user {phone_number}")
            break

        if not user_found:
            # Create new user if not found
            users_ref.add({
                'PhoneNumber': phone_number,
                'GoogleCalendarCreds': creds_data
            })
            logging.info(f"Created new user {phone_number} with Google Calendar credentials")

        # Send confirmation SMS
        send_sms(phone_number, "Google Calendar has been successfully connected to your account!")

        # Clear session
        session.pop('state', None)
        session.pop('phone_number', None)

        return """
        <html>
            <body>
                <h1>Success!</h1>
                <p>Google Calendar has been successfully connected to your account.</p>
                <p>You can close this window and return to your text messages.</p>
            </body>
        </html>
        """, 200

    except Exception as e:
        logging.error(f"Error in Google auth callback: {e}")
        phone_number = session.get('phone_number')
        if phone_number:
            send_sms(phone_number, f"Error connecting Google Calendar: {str(e)}")
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(port=3000)
