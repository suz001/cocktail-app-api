"""
Test custom Django management commands.
"""
from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase

@patch('core.management.commands.wait_for_db.Command.check')
class CommendTest(SimpleTestCase):
    """Test commands"""
    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database ready."""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patch_sleep, patched_check):
        """Test waiting for database when getting Operation Error"""
        """For the first 2 times we call mock method and raise psycopg2 error, then raise operational error 3 times."""
        """When Postgre not started, it's not ready to accept any connection--->psycopg2 error"""
        """When database is ready to accept connection, but it hasn't set up the databse--->operational error"""
        """2 and 3 are arbitray number, after 5 calls return true"""
        patched_check.side_effect = [Psycopg2Error] * 2 + [OperationalError] *3 + [True]

        call_command('wait_for_db')
        self.assertEqual(patched_check.call_count, 6)
        patched_check.asset_called_with(databases=['default'])
