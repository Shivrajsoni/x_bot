import unittest
from unittest.mock import patch, MagicMock
import os

# Set a dummy API_KEY for testing purposes
os.environ['GEMINI_API_KEY'] = 'dummygeminiapikey'

from content import _generate_llm_post, generate_post_content

class TestContentGeneration(unittest.TestCase):

    @patch('content.genai.GenerativeModel')
    def test_generate_llm_post_success(self, mock_generative_model):
        """Test successful content generation by the LLM."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "This is a test post."
        mock_generative_model.return_value = mock_model_instance

        content = _generate_llm_post("test prompt")
        self.assertEqual(content, "This is a test post.")

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_generate_llm_post_no_key(self):
        """Test that LLM post generation fails without an API key."""
        content = _generate_llm_post("test prompt")
        self.assertIsNone(content)

    @patch('content.genai.GenerativeModel')
    def test_generate_llm_post_api_error(self, mock_generative_model):
        """Test that LLM post generation fails on API error."""
        mock_generative_model.side_effect = Exception("API Error")

        content = _generate_llm_post("test prompt")
        self.assertIsNone(content)

    @patch('content._generate_llm_post')
    def test_generate_post_content_uses_llm(self, mock_llm_post):
        """Test that generate_post_content calls the LLM."""
        mock_llm_post.return_value = "LLM content"
        content, _ = generate_post_content("tech")
        self.assertEqual(content, "LLM content")
        mock_llm_post.assert_called_once()

    @patch('content._generate_llm_post')
    def test_generate_post_content_fallback(self, mock_llm_post):
        """Test that generate_post_content uses fallback content on LLM failure."""
        mock_llm_post.return_value = None
        content, _ = generate_post_content("tech")
        self.assertIn("Is 'cloud-native' just a fancy term for 'someone else\'s computer' again?", content)

if __name__ == '__main__':
    unittest.main()
