MAX_REPLAY_THRESHOLD = 1_000_000
MAX_RETRIES = 5
REPLAY_DIR = 'downloaded_replays'
CSV_FILE_BASE_NAME = DB_FILE_BASE_NAME = REPLAY_DIR + '/replay_data'

USE_SQLITE = True
QUERY_FOLDER_PATH = 'queries/'

class Tables:
    ReplayData = 'ReplayData'
    BattleTypes = 'BattleTypes'
    Characters = 'Characters'
    Regions = 'Regions'
    Ranks = 'Ranks'
    Stages = 'Stages'