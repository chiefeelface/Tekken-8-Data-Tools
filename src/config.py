MAX_REPLAY_THRESHOLD = 1_000_000
MAX_RETRIES = 5
REPLAY_DIR = 'downloaded_replays'
RESULTS_DIR = 'results'
CSV_FILE_BASE_NAME = DB_FILE_BASE_NAME = REPLAY_DIR + '/replay_data'
XLSX_FILE_BASE_NAME = RESULTS_DIR + '/'

USE_SQLITE = True
QUERY_FOLDER_PATH = 'queries/'
# I think this is what you need to use for relative file paths
SQLITE_URI = 'sqlite:///'

# Prompt configuration
DOWNLOAD = 'Download Replays'
ANALYZE = 'Analyze Replays'
HELP = 'Help'
QUIT = 'Quit'
SQLITE = 'SQLite Database'
CSV = 'CSV'
BACK = '← Back'

class Tables:
    ReplayData = 'ReplayData'
    BattleTypes = 'BattleTypes'
    Characters = 'Characters'
    Regions = 'Regions'
    Ranks = 'Ranks'
    Stages = 'Stages'