import unittest
from unittest.mock import patch, MagicMock
import os
import logging
from datetime import datetime, timedelta, timezone

# Set a dummy DATABASE_URL for testing purposes
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

from main import (
    init_db,
    should_post_now,
    is_post_in_db,
    save_post_to_db,
    load_unused_philosophy_quotes_from_db,
    mark_philosophy_quote_as_used,
    reset_used_philosophy_quotes
)

class TestDatabaseFunctions(unittest.TestCase):

    def setUp(self):
        """Disable logging for the duration of the tests."""
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after the tests."""
        logging.disable(logging.NOTSET)

    @patch('main.psycopg2.connect')
    def test_init_db(self, mock_connect):
        """Test that init_db executes the correct CREATE TABLE statements."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        init_db()

        self.assertEqual(mock_cur.execute.call_count, 3)
        self.assertIn('CREATE TABLE IF NOT EXISTS posts', mock_cur.execute.call_args_list[0][0][0])
        self.assertIn('CREATE TABLE IF NOT EXISTS philosophy_quotes', mock_cur.execute.call_args_list[1][0][0])
        self.assertIn('CREATE TABLE IF NOT EXISTS used_quote_ids', mock_cur.execute.call_args_list[2][0][0])
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('main.psycopg2.connect')
    def test_should_post_now_no_previous_post(self, mock_connect):
        """Test should_post_now returns True when there are no previous posts."""
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None # Simulate no posts in DB
        mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cur

        self.assertTrue(should_post_now())

    @patch('main.psycopg2.connect')
    def test_should_post_now_within_interval(self, mock_connect):
        """Test should_post_now returns False when a recent post exists."""
        now = datetime.now(timezone.utc)
        mock_cur = MagicMock()
        # Simulate a post from 1 hour ago
        mock_cur.fetchone.return_value = [now - timedelta(hours=1)]
        mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cur

        self.assertFalse(should_post_now(min_interval_hours=2, max_interval_hours=4))

    @patch('main.psycopg2.connect')
    def test_is_post_in_db_exists(self, mock_connect):
        """Test is_post_in_db returns True when a post exists."""
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = [True] # Simulate post exists
        mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cur

        self.assertTrue(is_post_in_db("An existing post."))

    @patch('main.psycopg2.connect')
    def test_save_post_to_db(self, mock_connect):
        """Test that save_post_to_db executes an INSERT statement."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        save_post_to_db("A new post", "tech")

        mock_cur.execute.assert_called_once_with(
            "INSERT INTO posts (content, topic) VALUES (%s, %s);",
            ("A new post", "tech")
        )
        mock_conn.commit.assert_called_once()

    @patch('main.psycopg2.connect')
    def test_load_unused_philosophy_quotes(self, mock_connect):
        """Test that unused quotes are loaded correctly."""
        mock_cur = MagicMock()
        # Simulate two unused quotes being returned from the DB
        mock_cur.fetchall.return_value = [
            (1, "Quote 1", "Author 1"),
            (2, "Quote 2", "Author 2")
        ]
        mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cur

        quotes = load_unused_philosophy_quotes_from_db()

        self.assertEqual(len(quotes), 2)
        self.assertEqual(quotes[0]["quote"], "Quote 1")

    @patch('main.psycopg2.connect')
    def test_mark_philosophy_quote_as_used(self, mock_connect):
        """Test that a quote is marked as used correctly."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mark_philosophy_quote_as_used(123)

        mock_cur.execute.assert_called_once_with(
            "INSERT INTO used_quote_ids (quote_id) VALUES (%s) ON CONFLICT (quote_id) DO NOTHING;",
            (123,)
        )
        mock_conn.commit.assert_called_once()

    @patch('main.psycopg2.connect')
    def test_reset_used_philosophy_quotes(self, mock_connect):
        """Test that the used_quote_ids table is cleared."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        reset_used_philosophy_quotes()

        mock_cur.execute.assert_called_once_with("DELETE FROM used_quote_ids;")
        mock_conn.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
