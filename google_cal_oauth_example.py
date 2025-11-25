"""
Example Flask routes for Google Calendar OAuth in a web app

This shows how to integrate Google Calendar API with your Flask app
"""

from flask import Flask, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = 'client_secret.json'  # Download from Google Cloud Console
REDIRECT_URI = 'http://localhost:3000/oauth2callback'  # Update for production


@app.route('/authorize')
def authorize():
    """Step 1: User requests authorization"""
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Enables refresh token
        include_granted_scopes='true'
    )

    # Store state in session to verify callback
    session['state'] = state

    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    """Step 2: User grants permission, Google redirects here"""
    # Verify state token
    state = session['state']

    # Exchange authorization code for access token
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

    # Fetch token
    flow.fetch_token(authorization_response=request.url)

    # Get credentials
    credentials = flow.credentials

    # Store credentials in session (or better: in database per user)
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # In production, save to Firebase:
    # user_id = get_current_user_id()
    # db.collection('users').document(user_id).set({
    #     'google_calendar_credentials': session['credentials']
    # }, merge=True)

    return redirect(url_for('calendar_test'))


@app.route('/calendar_test')
def calendar_test():
    """Test route that uses the stored credentials"""
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

    from api_interaction.google_cal_api import GoogleCalendarAPI
    from datetime import datetime, timedelta

    # Load credentials from session (or from database in production)
    cal_api = GoogleCalendarAPI(user_credentials=session['credentials'])

    # Create a test event
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    result = cal_api.create_event(
        summary="Test Event from Web App",
        start_datetime=start_time,
        end_datetime=end_time,
        description="Created via Flask web app",
        color_id='9'
    )

    return f"Event created: {result}"


@app.route('/revoke')
def revoke():
    """Revoke current credentials"""
    if 'credentials' in session:
        # In production, also remove from database
        del session['credentials']
    return 'Credentials revoked'


if __name__ == '__main__':
    # IMPORTANT: For production, use HTTPS
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for local development
    app.run(port=3000, debug=True)
