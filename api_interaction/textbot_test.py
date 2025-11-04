import unittest
import os
from pathlib import Path
from app import send_sms
from api_interaction.textbot import Textbot
from dotenv import load_dotenv

# Load .env from project root (parent directory of api_interaction)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

LOCAL_URL = "https://fine-prawn-driven.ngrok-free.app"

class TestTextbot(unittest.TestCase):
    def test_send_text(self):
        print("PRINT Testing send_text")
        textbot = Textbot(LOCAL_URL)
        textbot.send_text("Hello, how are you?", "+19162206037")

        send_sms("+19162206037", "Does this function work?")

if __name__ == "__main__":
    # unittest.main()
    test_textbot = TestTextbot()
    test_textbot.test_send_text()