import unittest, os
from src.utils import *

class Test(unittest.TestCase):
    def test_replay_download(self):
        self.assertEqual(len(download_replays(1756684800)), 4482)

    def test_table_creation(self):
        start, end = datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 2)
        failed = False
        try:
            self.assertEqual(create_tables(start, end), None)
        except Exception:
            failed = True
        # Cleanup
        if os.path.exists(config.DB_FILE_BASE_NAME + f'_{start.date()}_{(end).date()}.db'):
            os.remove(config.DB_FILE_BASE_NAME + f'_{start.date()}_{(end).date()}.db')
        if failed:
            raise Exception
        
    def test_table_fill(self):
        start, end = datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 2)
        failed = False
        try:
            self.assertEqual(fill_tables_for_enums(start, end), None)
        except Exception:
            failed = True
            # Cleanup
        if os.path.exists(config.DB_FILE_BASE_NAME + f'_{start.date()}_{(end).date()}.db'):
            os.remove(config.DB_FILE_BASE_NAME + f'_{start.date()}_{(end).date()}.db')
        if failed:
            raise Exception
    