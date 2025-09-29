import unittest, os
from src.utils import *

class Test(unittest.TestCase):
    def test_replay_download(self):
        timestamp = int(datetime.datetime(2025, 9, 1, tzinfo=datetime.timezone.utc).timestamp())
        self.assertEqual(len(download_replays(timestamp)), 4482)

    def test_table_creation(self):
        start, end = datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 2)
        failed = None
        try:
            self.assertEqual(create_tables(start, end), None)
        except Exception as e:
            failed = e
        # Cleanup
        if os.path.exists(config.DB_FILE_BASE_NAME + f'_{start.date()}_{end.date()}.db'):
            os.remove(config.DB_FILE_BASE_NAME + f'_{start.date()}_{end.date()}.db')
        if failed:
            raise failed
        
    def test_table_fill(self):
        start, end = datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 2)
        failed = None
        try:
            self.assertEqual(populate_lookup_tables(start, end), None)
        except Exception as e:
            failed = e
        # Cleanup
        if os.path.exists(config.DB_FILE_BASE_NAME + f'_{start.date()}_{end.date()}.db'):
            os.remove(config.DB_FILE_BASE_NAME + f'_{start.date()}_{end.date()}.db')
        if failed:
            raise failed
    