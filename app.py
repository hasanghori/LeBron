import string
from ai_model import AIModel
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request, jsonify
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
database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"

reply_webhook_url = PUBLIC_URL if IS_PUBLIC else LOCAL_URL

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
        else:
            send_sms(from_number, "Error: User not found in database")
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


if __name__ == '__main__':
    app.run(port=3000)
