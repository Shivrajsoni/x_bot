import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from main import Bot

class TestBot(unittest.TestCase):

    def setUp(self):
        self.bot = Bot()

    @patch('main.verify_credentials')
    def test_initialize_success(self, mock_verify_credentials):
        """Test successful bot initialization."""
        mock_verify_credentials.return_value = "12345"
        self.assertTrue(self.bot.initialize())
        self.assertEqual(self.bot.user_id, "12345")

    @patch('main.verify_credentials')
    def test_initialize_failure(self, mock_verify_credentials):
        """Test failed bot initialization."""
        mock_verify_credentials.return_value = None
        self.assertFalse(self.bot.initialize())
        self.assertIsNone(self.bot.user_id)

    @patch('main.get_last_tweet_time')
    def test_should_post_no_recent_tweets(self, mock_get_last_tweet_time):
        """Test should_post when no recent tweets are found."""
        mock_get_last_tweet_time.return_value = None
        self.assertTrue(self.bot.should_post(3600))

    @patch('main.get_last_tweet_time')
    def test_should_post_with_recent_tweet(self, mock_get_last_tweet_time):
        """Test should_post when a recent tweet is found."""
        mock_get_last_tweet_time.return_value = datetime.now(timezone.utc) - timedelta(minutes=30)
        self.assertFalse(self.bot.should_post(3600))

    @patch('main.get_last_tweet_time')
    def test_should_post_with_old_tweet(self, mock_get_last_tweet_time):
        """Test should_post when the last tweet is older than the interval."""
        mock_get_last_tweet_time.return_value = datetime.now(timezone.utc) - timedelta(hours=2)
        self.assertTrue(self.bot.should_post(3600))

    @patch('main.generate_post_content')
    def test_create_post(self, mock_generate_post_content):
        """Test post creation."""
        mock_generate_post_content.return_value = ("Test content", None)
        content = self.bot.create_post()
        self.assertEqual(content, "Test content")

    @patch('main.post_tweet')
    def test_publish_post_success(self, mock_post_tweet):
        """Test successful post publishing."""
        self.bot.publish_post("Test content")
        mock_post_tweet.assert_called_once_with("Test content")

    @patch('main.post_tweet')
    def test_publish_post_too_long(self, mock_post_tweet):
        """Test that a post that is too long is not published."""
        long_content = "a" * 281
        self.bot.publish_post(long_content)
        mock_post_tweet.assert_not_called()

    @patch('main.post_tweet')
    def test_publish_post_empty(self, mock_post_tweet):
        """Test that an empty post is not published."""
        self.bot.publish_post("")
        mock_post_tweet.assert_not_called()

if __name__ == '__main__':
    unittest.main()
