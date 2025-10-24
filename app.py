from ai_model import AIModel
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request, jsonify
import json
import logging
from notion_api import NotionAPI
from notion_client import Client
import os
import requests
from textbot import Textbot
from user import User
from dotenv import load_dotenv

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

#TODO: This func should send an sms to a user about a specific thing
@app.route('/api/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone_number = data.get('phone_number')
    message = data.get('message')
    send_sms(phone_number, message)
    return '', 200  # Respond OK so Textbelt knows you received it


# TODO: This func must fetch notion_key from userdb
@app.route('/api/handleSmsReply', methods=['POST'])
def handle_sms_reply():
    print("Received reply")
    data = request.get_json()
    text_id = data.get('textId')
    from_number = data.get('fromNumber')
    text = data.get('text')

    print(f"📩 Received reply from {from_number}: '{text}' (textId: {text_id})")
    
    ai_model = AIModel()
    
     # Fetch user data from database
    users_ref = db.collection('users')
    docs = users_ref.where('PhoneNumber', '==', from_number).stream()
    
    notion_key = None
    for doc in docs:
        user_data = doc.to_dict()
        notion_key = user_data.get('NotionAPI')
        break  # Should only be one user with this phone number
    
    if notion_key:
        notion_api = NotionAPI(notion_key, database_id, ai_model)
        notion_api.create_note_with_tags(text)
        send_sms(from_number, "Logged to Notion")
    else:
        send_sms(from_number, "Error: User not found in database")

    return '', 200  # Respond OK so Textbelt knows you received it


@app.route('/api/text_all_users', methods=['GET'])
def text_all_users():
    textbot = Textbot(reply_webhook_url)
    ai_model = AIModel()
    
    # Fetch all users from the database
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    for doc in docs:
        user_data = doc.to_dict()
        phone_number = user_data.get('PhoneNumber')
        interests = user_data.get('UserInterests')
        if phone_number:
            # textbot should send message to whatever the user wants
            send_sms(phone_number, ai_model.first_message(interests))
    
    return '', 200  # Respond OK so Textbelt knows you received it

@app.route('/api/text_all_users_test', methods=['GET'])
def text_all_users_test():
    textbot = Textbot(reply_webhook_url)
    ai_model = AIModel()
    
    # Fetch all users from the database
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    for doc in docs:
        user_data = doc.to_dict()
        phone_number = user_data.get('PhoneNumber')
        interests = user_data.get('UserInterests')
        if phone_number == "+19162206037":
            # textbot should send message to whatever the user wants
            send_sms(phone_number, ai_model.first_message(interests))
    
    return '', 200  # Respond OK so Textbelt knows you received it


if __name__ == '__main__':
    app.run(port=3000)
