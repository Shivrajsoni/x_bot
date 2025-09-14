import unittest
from unittest.mock import patch, MagicMock
import os
import requests
import logging

# Set a dummy API_KEY for testing purposes
os.environ['NEWS_API_KEY'] = 'dummynewsapikey'

from content import _get_news_from_api

class TestContentFunctions(unittest.TestCase):

    def setUp(self):
        """Disable logging for the duration of the tests."""
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after the tests."""
        logging.disable(logging.NOTSET)

    @patch('content.requests.get')
    def test_get_news_from_api_success(self, mock_get):
        """Test a successful call to the News API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {"title": "Test Article", "description": "A test description."}
            ]
        }
        mock_get.return_value = mock_response

        article = _get_news_from_api("tech")
        
        self.assertIsNotNone(article)
        self.assertEqual(article["title"], "Test Article")
        mock_get.assert_called_once()

    @patch('content.requests.get')
    def test_get_news_from_api_http_error(self, mock_get):
        """Test a call to the News API that results in an HTTP error."""
        mock_response = MagicMock()
        # The raise_for_status method should raise a RequestException for non-2xx codes
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("HTTP 500 Error")
        mock_get.return_value = mock_response

        article = _get_news_from_api("world")

        self.assertIsNone(article)

    @patch('content.requests.get')
    def test_get_news_from_api_no_articles(self, mock_get):
        """Test a successful API call that returns no articles."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 0,
            "articles": []
        }
        mock_get.return_value = mock_response

        article = _get_news_from_api("tech")

        self.assertIsNone(article)

    @patch.dict(os.environ, {"NEWS_API_KEY": ""})
    @patch('content.requests.get')
    def test_get_news_from_api_no_key(self, mock_get):
        """Test that the API is not called if the API key is missing."""
        article = _get_news_from_api("tech")

        self.assertIsNone(article)
        mock_get.assert_not_called() # Ensure we didn't even try to make a request

if __name__ == '__main__':
    unittest.main()
