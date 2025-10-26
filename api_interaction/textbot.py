import os
import requests
import logging
from notion_client import Client

class Textbot:
    def __init__(self, reply_webhook_url):
        self.reply_webhook_url = reply_webhook_url

    def send_text(self, text, phone_number):
        phone_number = phone_number.replace("+", "")
        resp = requests.post('https://textbelt.com/text', {
            'phone': phone_number,
            'message': text,
            'key': os.getenv('TEXTBELT_INTERNATIONAL_KEY'), 
            'replyWebhookUrl': self.reply_webhook_url + '/api/handleSmsReply'
        })
        logging.info("Textbot response: %s", str(resp.json()))
        return resp.json()