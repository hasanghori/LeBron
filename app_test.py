import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from constants.action_types import ActionType
from ai_model import AIModel

# Load environment variables
load_dotenv()


class TestAppHelperFunctions(unittest.TestCase):
    """Test suite for helper functions in app.py"""
    def __init__(self):
        super().__init__()
        self.test_phone_number = "+19162206037"
        self.test_text = "I want to create a habit to drink water every day"
        self.test_action_key = "f07c1938616196c078733ddcfb41392a183eb68f193b6cf8b2806f4b03b764fa"
        self.test_ai_model = AIModel()

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_phone_number = "+19162206037"

    def find_user_key_test(self):
        from app import find_user_key
        result = find_user_key(self.test_phone_number, ActionType.NOTION)
        print(f"PRINT result - {result}")
    
    def process_habitify_action_test(self):
        from app import process_habitify_action
        result = process_habitify_action(self.test_text, self.test_action_key, self.test_ai_model)
        print(f"PRINT result - {result}")

if __name__ == '__main__':
    # Run tests with verbosity
    test_app_helper_functions = TestAppHelperFunctions()
    test_app_helper_functions.find_user_key_test()
