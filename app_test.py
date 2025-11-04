import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from constants.action_types import ActionType

# Load environment variables
load_dotenv()


class TestAppHelperFunctions(unittest.TestCase):
    """Test suite for helper functions in app.py"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_phone_number = "+19162206037"

    @patch('app.db')
    def test_find_user_key_for_notion(self, mock_db):
        """Test find_user_key when looking for a Notion API key"""
        from app import find_user_key

        # Mock the database response
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            'PhoneNumber': self.test_phone_number,
            'UserInterests': 'fitness, productivity',
            ActionType.NOTION: 'notion_key'
        }

        mock_collection = Mock()
        mock_where = Mock()
        mock_where.stream.return_value = [mock_doc]
        mock_collection.where.return_value = mock_where
        mock_db.collection.return_value = mock_collection

        # Call the function to find the Notion API key
        result = find_user_key(self.test_phone_number, ActionType.NOTION)

        # Verify the result matches the expected Notion API key
        self.assertEqual(result, 'notion_key')

        # Verify database was queried correctly
        mock_db.collection.assert_called_once_with('users')
        mock_collection.where.assert_called_once_with(
            'PhoneNumber', '==', self.test_phone_number
        )


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
