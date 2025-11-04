import os
import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from api_interaction.notion_api import NotionAPI
from ai_model import AIModel
from notion_client import APIResponseError

# Load environment variables
load_dotenv()


class TestNotionAPI(unittest.TestCase):
    """Test suite for NotionAPI class"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used across all tests"""
        cls.notion_api_key = os.getenv('HASAN_NOTION_API_KEY')
        cls.database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"  # Default database from app.py

        if not cls.notion_api_key:
            raise ValueError("HASAN_NOTION_API_KEY environment variable not set")

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_ai_model = Mock(spec=AIModel)
        self.mock_ai_model.choose_tag.return_value = "General"
        self.mock_ai_model.choose_title.return_value = "Test Note"

        self.notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id=self.database_id,
            ai_model=self.mock_ai_model
        )

    def test_initialization(self):
        """Test that NotionAPI initializes correctly"""
        self.assertIsNotNone(self.notion_api)
        self.assertEqual(self.notion_api.database_id, self.database_id)
        self.assertIsNotNone(self.notion_api.notion)
        self.assertIsNotNone(self.notion_api.ai_model)

    def test_get_all_tags(self):
        """Test retrieving all tags from the database"""
        tags = self.notion_api.get_all_tags()
        print(f"Tags: {tags}")

        # Verify that tags were retrieved
        self.assertIsInstance(tags, list)
        # If database has tags configured, list should not be empty
        # Uncomment if you know your database has tags:
        # self.assertGreater(len(tags), 0)

    def test_get_all_tags_with_invalid_database(self):
        """Test get_all_tags with invalid database ID"""
        invalid_notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id="invalid-database-id",
            ai_model=self.mock_ai_model
        )

        tags = invalid_notion_api.get_all_tags()

        # Should return empty list on error
        self.assertEqual(tags, [])

    @patch('notion_api.logging')
    def test_create_note_with_tags_success(self, mock_logging):
        """Test creating a note with tags successfully"""
        test_content = "This is a test note about productivity"

        # Configure mock AI model responses
        self.mock_ai_model.choose_tag.return_value = "Work"
        self.mock_ai_model.choose_title.return_value = "Productivity Test"

        # Create the note
        result = self.notion_api.create_note_with_tags(test_content)

        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

        # Verify AI model was called
        self.mock_ai_model.choose_tag.assert_called_once()
        self.mock_ai_model.choose_title.assert_called_once_with(test_content)

        # Verify logging
        mock_logging.info.assert_called()

    @patch('notion_api.logging')
    def test_create_note_with_tags_error_handling(self, mock_logging):
        """Test error handling when creating a note fails"""
        # Use invalid database ID to trigger an error
        invalid_notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id="00000000-0000-0000-0000-000000000000",
            ai_model=self.mock_ai_model
        )

        test_content = "This should fail"
        result = invalid_notion_api.create_note_with_tags(test_content)

        # Verify error was handled
        self.assertEqual(result.get("status"), "error")
        self.assertIn("message", result)

        # Verify error was logged
        mock_logging.error.assert_called()

    def test_ai_model_integration(self):
        """Test that AI model is properly integrated"""
        test_content = "Meeting notes from team sync"
        all_tags = ["Work", "Personal", "Ideas"]

        self.mock_ai_model.choose_tag.return_value = "Work"
        self.mock_ai_model.choose_title.return_value = "Team Sync"

        # Mock get_all_tags to return our test tags
        with patch.object(self.notion_api, 'get_all_tags', return_value=all_tags):
            result = self.notion_api.create_note_with_tags(test_content)

        # Verify AI model was called with correct parameters
        self.mock_ai_model.choose_tag.assert_called_once_with(test_content, all_tags)
        self.mock_ai_model.choose_title.assert_called_once_with(test_content)

    @patch('sys.stdout')
    def test_list_accessible_databases(self, _mock_stdout):
        """Test listing accessible databases"""
        # This test just verifies the method runs without errors
        # The actual output goes to stdout
        try:
            self.notion_api.list_accessible_databases()
            # If no exception is raised, test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"list_accessible_databases raised an exception: {e}")

    def test_notion_client_authentication(self):
        """Test that Notion client is properly authenticated"""
        # Try to retrieve database info (this requires authentication)
        try:
            database = self.notion_api.notion.databases.retrieve(
                database_id=self.database_id
            )
            self.assertIsNotNone(database)
            self.assertEqual(database['id'], self.database_id)
        except APIResponseError as e:
            self.fail(f"Authentication failed: {e}")

    def test_create_note_with_special_characters(self):
        """Test creating a note with special characters"""
        test_content = "Test note with special chars: @#$%^&*() and �mojis <�"

        result = self.notion_api.create_note_with_tags(test_content)

        # Should handle special characters gracefully
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

    def test_create_note_with_long_content(self):
        """Test creating a note with long content"""
        test_content = "This is a very long note. " * 100  # Create long content

        result = self.notion_api.create_note_with_tags(test_content)

        # Should handle long content
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

    def test_create_note_with_empty_content(self):
        """Test creating a note with empty content"""
        test_content = ""

        result = self.notion_api.create_note_with_tags(test_content)

        # Should still create the note (or handle gracefully)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        # Verify page was created
        if result.get("status") == "ok":
            self.assertIsNotNone(result.get("page_id"))


class TestNotionAPIWithRealAIModel(unittest.TestCase):
    """Integration tests with real AI model (requires API keys)"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.notion_api_key = os.getenv('HASAN_NOTION_API_KEY')
        cls.database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"

        if not cls.notion_api_key:
            raise ValueError("HASAN_NOTION_API_KEY environment variable not set")

        # Check if OpenAI or Grok API key is available
        cls.has_ai_api_key = bool(os.getenv('OPENAI_API_KEY') or os.getenv('GROK_API_KEY'))

    def setUp(self):
        """Set up test fixtures before each test"""
        if not self.has_ai_api_key:
            self.skipTest("AI API key not available")

        self.ai_model = AIModel()
        self.notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id=self.database_id,
            ai_model=self.ai_model
        )

    def test_full_integration_create_note(self):
        """Full integration test: create a note with real AI model"""
        test_content = "Integration test: Testing the full flow of creating a Notion note"

        result = self.notion_api.create_note_with_tags(test_content)

        # Verify the note was created successfully
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

        # Note: You may want to clean up the test note after this test
        # by deleting it from Notion using result["page_id"]


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)

import os
import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from api_interaction.notion_api import NotionAPI
from ai_model import AIModel
from notion_client import APIResponseError

# Load environment variables
load_dotenv()


class TestNotionAPI(unittest.TestCase):
    """Test suite for NotionAPI class"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used across all tests"""
        cls.notion_api_key = os.getenv('HASAN_NOTION_API_KEY')
        cls.database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"  # Default database from app.py

        if not cls.notion_api_key:
            raise ValueError("HASAN_NOTION_API_KEY environment variable not set")

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_ai_model = Mock(spec=AIModel)
        self.mock_ai_model.choose_tag.return_value = "General"
        self.mock_ai_model.choose_title.return_value = "Test Note"

        self.notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id=self.database_id,
            ai_model=self.mock_ai_model
        )

    def test_initialization(self):
        """Test that NotionAPI initializes correctly"""
        self.assertIsNotNone(self.notion_api)
        self.assertEqual(self.notion_api.database_id, self.database_id)
        self.assertIsNotNone(self.notion_api.notion)
        self.assertIsNotNone(self.notion_api.ai_model)

    def test_get_all_tags(self):
        """Test retrieving all tags from the database"""
        tags = self.notion_api.get_all_tags()
        print(f"Tags: {tags}")

        # Verify that tags were retrieved
        self.assertIsInstance(tags, list)
        # If database has tags configured, list should not be empty
        # Uncomment if you know your database has tags:
        # self.assertGreater(len(tags), 0)

    def test_get_all_tags_with_invalid_database(self):
        """Test get_all_tags with invalid database ID"""
        invalid_notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id="invalid-database-id",
            ai_model=self.mock_ai_model
        )

        tags = invalid_notion_api.get_all_tags()

        # Should return empty list on error
        self.assertEqual(tags, [])

    @patch('notion_api.logging')
    def test_create_note_with_tags_success(self, mock_logging):
        """Test creating a note with tags successfully"""
        test_content = "This is a test note about productivity"

        # Configure mock AI model responses
        self.mock_ai_model.choose_tag.return_value = "Work"
        self.mock_ai_model.choose_title.return_value = "Productivity Test"

        # Create the note
        result = self.notion_api.create_note_with_tags(test_content)

        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

        # Verify AI model was called
        self.mock_ai_model.choose_tag.assert_called_once()
        self.mock_ai_model.choose_title.assert_called_once_with(test_content)

        # Verify logging
        mock_logging.info.assert_called()

    @patch('notion_api.logging')
    def test_create_note_with_tags_error_handling(self, mock_logging):
        """Test error handling when creating a note fails"""
        # Use invalid database ID to trigger an error
        invalid_notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id="00000000-0000-0000-0000-000000000000",
            ai_model=self.mock_ai_model
        )

        test_content = "This should fail"
        result = invalid_notion_api.create_note_with_tags(test_content)

        # Verify error was handled
        self.assertEqual(result.get("status"), "error")
        self.assertIn("message", result)

        # Verify error was logged
        mock_logging.error.assert_called()

    def test_ai_model_integration(self):
        """Test that AI model is properly integrated"""
        test_content = "Meeting notes from team sync"
        all_tags = ["Work", "Personal", "Ideas"]

        self.mock_ai_model.choose_tag.return_value = "Work"
        self.mock_ai_model.choose_title.return_value = "Team Sync"

        # Mock get_all_tags to return our test tags
        with patch.object(self.notion_api, 'get_all_tags', return_value=all_tags):
            result = self.notion_api.create_note_with_tags(test_content)

        # Verify AI model was called with correct parameters
        self.mock_ai_model.choose_tag.assert_called_once_with(test_content, all_tags)
        self.mock_ai_model.choose_title.assert_called_once_with(test_content)

    @patch('sys.stdout')
    def test_list_accessible_databases(self, _mock_stdout):
        """Test listing accessible databases"""
        # This test just verifies the method runs without errors
        # The actual output goes to stdout
        try:
            self.notion_api.list_accessible_databases()
            # If no exception is raised, test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"list_accessible_databases raised an exception: {e}")

    def test_notion_client_authentication(self):
        """Test that Notion client is properly authenticated"""
        # Try to retrieve database info (this requires authentication)
        try:
            database = self.notion_api.notion.databases.retrieve(
                database_id=self.database_id
            )
            self.assertIsNotNone(database)
            self.assertEqual(database['id'], self.database_id)
        except APIResponseError as e:
            self.fail(f"Authentication failed: {e}")

    def test_create_note_with_special_characters(self):
        """Test creating a note with special characters"""
        test_content = "Test note with special chars: @#$%^&*() and �mojis <�"

        result = self.notion_api.create_note_with_tags(test_content)

        # Should handle special characters gracefully
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

    def test_create_note_with_long_content(self):
        """Test creating a note with long content"""
        test_content = "This is a very long note. " * 100  # Create long content

        result = self.notion_api.create_note_with_tags(test_content)

        # Should handle long content
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

    def test_create_note_with_empty_content(self):
        """Test creating a note with empty content"""
        test_content = ""

        result = self.notion_api.create_note_with_tags(test_content)

        # Should still create the note (or handle gracefully)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        # Verify page was created
        if result.get("status") == "ok":
            self.assertIsNotNone(result.get("page_id"))


class TestNotionAPIWithRealAIModel(unittest.TestCase):
    """Integration tests with real AI model (requires API keys)"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.notion_api_key = os.getenv('HASAN_NOTION_API_KEY')
        cls.database_id = "23eb9e96-e8f3-80a4-8b8d-c5e9cd16ef40"

        if not cls.notion_api_key:
            raise ValueError("HASAN_NOTION_API_KEY environment variable not set")

        # Check if OpenAI or Grok API key is available
        cls.has_ai_api_key = bool(os.getenv('OPENAI_API_KEY') or os.getenv('GROK_API_KEY'))

    def setUp(self):
        """Set up test fixtures before each test"""
        if not self.has_ai_api_key:
            self.skipTest("AI API key not available")

        self.ai_model = AIModel()
        self.notion_api = NotionAPI(
            notion_api_key=self.notion_api_key,
            database_id=self.database_id,
            ai_model=self.ai_model
        )

    def test_full_integration_create_note(self):
        """Full integration test: create a note with real AI model"""
        test_content = "Integration test: Testing the full flow of creating a Notion note"

        result = self.notion_api.create_note_with_tags(test_content)

        # Verify the note was created successfully
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("page_id", result)

        # Note: You may want to clean up the test note after this test
        # by deleting it from Notion using result["page_id"]


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
