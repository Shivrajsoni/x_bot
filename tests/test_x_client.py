import unittest
from unittest.mock import patch, MagicMock

from x_client import verify_credentials, post_tweet, get_last_tweet_time

class TestXClient(unittest.TestCase):

    @patch('x_client.requests.get')
    def test_verify_credentials_success(self, mock_get):
        """Test successful credential verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "123", "username": "testuser"}}
        mock_get.return_value = mock_response

        user_id = verify_credentials()
        self.assertEqual(user_id, "123")

    @patch('x_client.requests.post')
    def test_post_tweet_success(self, mock_post):
        """Test successful tweet posting."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        success = post_tweet("Hello, world!")
        self.assertTrue(success)

    @patch('x_client.requests.get')
    def test_get_last_tweet_time_success(self, mock_get):
        """Test successfully fetching the last tweet time."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"created_at": "2023-01-01T12:00:00Z"}]}
        mock_get.return_value = mock_response

        last_tweet_time = get_last_tweet_time("123")
        self.assertIsNotNone(last_tweet_time)

if __name__ == '__main__':
    unittest.main()