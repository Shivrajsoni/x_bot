import unittest
from unittest.mock import patch, MagicMock
from main import main

class TestMain(unittest.TestCase):

    @patch('main.verify_credentials')
    @patch('main.generate_post_content')
    @patch('main.post_tweet')
    def test_main_success(self, mock_post_tweet, mock_generate_content, mock_verify_credentials):
        """Test the main function for a successful post."""
        mock_verify_credentials.return_value = "12345"
        mock_generate_content.return_value = ("Test tweet", None)
        mock_post_tweet.return_value = True

        main()

        mock_verify_credentials.assert_called_once()
        mock_generate_content.assert_called_once()
        mock_post_tweet.assert_called_once_with("Test tweet")

    @patch('main.verify_credentials')
    @patch('main.post_tweet')
    def test_main_verify_fails(self, mock_post_tweet, mock_verify_credentials):
        """Test that the script exits if credential verification fails."""
        mock_verify_credentials.return_value = None

        main()

        mock_post_tweet.assert_not_called()

    @patch('main.verify_credentials')
    @patch('main.generate_post_content')
    @patch('main.post_tweet')
    def test_main_content_too_long(self, mock_post_tweet, mock_generate_content, mock_verify_credentials):
        """Test that the script does not post if the content is too long."""
        mock_verify_credentials.return_value = "12345"
        mock_generate_content.return_value = ("a" * 281, None)

        main()

        mock_post_tweet.assert_not_called()

if __name__ == '__main__':
    unittest.main()
