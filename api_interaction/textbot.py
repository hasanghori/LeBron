import os
import requests
import logging

class Textbot:
    def __init__(self, reply_webhook_url):
        self.reply_webhook_url = reply_webhook_url
        print("PRINT Textbot initialized with reply_webhook_url: %s", self.reply_webhook_url)

    def send_text(self, text: str, phone_number: str):
        phone_number = phone_number.strip("+")
        logging.info(f"Sending text to {phone_number}: {text}")
        resp = requests.post('https://textbelt.com/text', {
            'phone': str(phone_number),
            'message': text,
            'key': os.getenv('TEXTBELT_INTERNATIONAL_KEY'), 
            'replyWebhookUrl': self.reply_webhook_url + '/api/handleSmsReply'
        })
        logging.info("Textbot response: %s", str(resp.json()))
        print("PRINT Textbot response: %s", str(resp.json()))
        return resp.json()