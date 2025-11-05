import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from constants.action_types import ActionType

# Load environment variables
load_dotenv()


class TestAppHelperFunctions(unittest.TestCase):
    """Test suite for helper functions in app.py"""
    def __init__(self):
        super().__init__()
        self.test_phone_number = "+19162206037"
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_phone_number = "+19162206037"

    def find_user_key_test(self):
        from app import find_user_key
        result = find_user_key(self.test_phone_number, ActionType.NOTION)
        print(f"PRINT result - {result}")

if __name__ == '__main__':
    # Run tests with verbosity
    test_app_helper_functions = TestAppHelperFunctions()
    test_app_helper_functions.find_user_key_test()
