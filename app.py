from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import requests
from user import User
from notion_client import Client
import logging
from textbot import Textbot
from notion_api import NotionAPI
from ai_model import AIModel

# Load environment variables
load_dotenv()

# goal for today:
# - make it so other people can use this bot

PUBLIC_URL = "https://textbot-service-939342988447.us-central1.run.app"
LOCAL_URL = "https://fine-prawn-driven.ngrok-free.app"
IS_PUBLIC = False

USERS = {"+19162206037": User("+19162206037", os.getenv("HASAN_NOTION_API_KEY"), "Hasan"),
"+14049199353": User("+14049199353", os.getenv("FAKE_HASAN_NOTION_API_KEY"), "Fake_Hasan")}

# Set up basic config — do this once, near the top of your app
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"

reply_webhook_url = PUBLIC_URL if IS_PUBLIC else LOCAL_URL

@app.route('/api/handleSmsReply', methods=['POST'])
def handle_sms_reply():
    print("Received reply")
    data = request.get_json()
    text_id = data.get('textId')
    from_number = data.get('fromNumber')
    text = data.get('text')

    print(f"📩 Received reply from {from_number}: '{text}' (textId: {text_id})")
    
    ai_model = AIModel()
    notion_key = USERS[from_number].notion_api_key

    notion_api = NotionAPI(notion_key, database_id, ai_model)
    notion_api.create_note_with_tags(text)

    send_sms(from_number, "Logged to Notion")

    return '', 200  # Respond OK so Textbelt knows you received it

def send_sms(phone_number, message):
    textbot = Textbot(reply_webhook_url)
    response = textbot.send_text(message, phone_number)
    logging.info(response)

@app.route('/api/text_all_users', methods=['GET'])
def text_all_users():
    textbot = Textbot(reply_webhook_url)
    ai_model = AIModel()
    for user in USERS:
        textbot.send_text(ai_model.first_message(), user)
    return '', 200  # Respond OK so Textbelt knows you received it

@app.route('/api/text_all_users_test', methods=['GET'])
def text_all_users_test():
    textbot = Textbot(reply_webhook_url)

    ai_model = AIModel()
    for user in USERS:
        if user == "+19162206037":
            textbot.send_text(ai_model.first_message("tracking daily journaling + prayer log"), user)
    return '', 200  # Respond OK so Textbelt knows you received it


if __name__ == '__main__':
    app.run(port=3000)
