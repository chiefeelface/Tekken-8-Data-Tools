import requests, datetime, sqlite3, src.config as config, pandas as pd, src.enums as enums, os
from src.models import ReplayData

def create_replay_dir():
    if not os.path.exists(config.REPLAY_DIR):
        os.makedirs(config.REPLAY_DIR)

def download_replays(before: int) -> list[ReplayData]:
    request = f'https://wank.wavu.wiki/api/replays?before={before}'
    replay_data = requests.get(request).json()
    return replay_data

def create_tables(start_date: datetime.datetime, end_date: datetime.datetime):
    file_name = config.DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
    create_replay_dir()
    # Ensure file exists
    open(file_name, 'a').close()
    try:
        with sqlite3.connect(file_name) as connection:
            cursor = connection.cursor()
            # Enable foreign keys
            cursor.execute('PRAGMA foreign_keys = ON;')

            # Create main table
            cursor.execute('''
CREATE TABLE IF NOT EXISTS ReplayData (
    battle_at INTEGER NOT NULL,
    battle_id TEXT PRIMARY KEY,
    battle_type INTEGER NOT NULL,
    game_version INTEGER NOT NULL,

    p1_area_id INTEGER,
    p1_chara_id INTEGER NOT NULL,
    p1_lang TEXT,
    p1_name TEXT NOT NULL,
    p1_polaris_id TEXT NOT NULL,
    p1_power INTEGER NOT NULL,
    p1_rank INTEGER NOT NULL,
    p1_rating_before INTEGER,
    p1_rating_change INTEGER,
    p1_region_id INTEGER,
    p1_rounds INTEGER NOT NULL,
    p1_user_id INTEGER NOT NULL,

    p2_area_id INTEGER,
    p2_chara_id INTEGER NOT NULL,
    p2_lang TEXT,
    p2_name TEXT NOT NULL,
    p2_polaris_id TEXT NOT NULL,
    p2_power INTEGER NOT NULL,
    p2_rank INTEGER NOT NULL,
    p2_rating_before INTEGER,
    p2_rating_change INTEGER,
    p2_region_id INTEGER,
    p2_rounds INTEGER NOT NULL,
    p2_user_id INTEGER NOT NULL,

    stage_id INTEGER NOT NULL,
    winner INTEGER NOT NULL,

    FOREIGN KEY (battle_type) REFERENCES BattleTypes(Id),
    FOREIGN KEY (p1_chara_id) REFERENCES Characters(Id),
    FOREIGN KEY (p2_chara_id) REFERENCES Characters(Id),
    FOREIGN KEY (p1_region_id) REFERENCES Regions(Id),
    FOREIGN KEY (p2_region_id) REFERENCES Regions(Id),
    FOREIGN KEY (p1_rank) REFERENCES Ranks(Id),
    FOREIGN KEY (p2_rank) REFERENCES Ranks(Id),
    FOREIGN KEY (stage_id) REFERENCES Stages(Id)
);
''')
            for table in [config.BATTLETYPES_TABLE_NAME, config.CHARACTERS_TABLE_NAME, config.REGIONS_TABLE_NAME, config.RANKS_TABLE_NAME, config.STAGES_TABLE_NAME]:
                cursor.execute(f'''
CREATE TABLE IF NOT EXISTS {table} (
    Id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL
);
''')
    except Exception as e:
        return e
    return None

def create_index(cursor: sqlite3.Cursor, index_name, table, column):
    cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});')

def create_indexes(start_date: datetime.datetime, end_date: datetime.datetime):
    file_name = config.DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
    create_replay_dir()
    # Ensure file exists
    open(file_name, 'a').close()
    try:
        with sqlite3.connect(file_name) as connection:
            cursor = connection.cursor()
            indexes = [
                {
                    'name': f'idx_{config.SQLITE_TABLE_NAME.lower()}_p1_chara_id',
                    'table': config.SQLITE_TABLE_NAME,
                    'column': 'p1_chara_id'
                },
                {
                    'name': f'idx_{config.SQLITE_TABLE_NAME.lower()}_p2_chara_id',
                    'table': config.SQLITE_TABLE_NAME,
                    'column': 'p2_chara_id'
                },
                {
                    'name': f'idx_{config.SQLITE_TABLE_NAME.lower()}_winner',
                    'table': config.SQLITE_TABLE_NAME,
                    'column': 'winner'
                }
            ]
            for index in indexes:
                create_index(cursor, index['name'], index['table'], index['column'])
    except Exception as e:
        return e
    return None

def _enum_to_dict(enum):
    return [{'Id': member.value, 'Name': member.name} for member in enum]

def populate_lookup_tables(start_date: datetime.datetime, end_date: datetime.datetime):
    file_name = config.DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
    create_replay_dir()
    # Ensure file exists
    open(file_name, 'a').close()
    try:
        with sqlite3.connect(file_name) as connection:
            pd.DataFrame(_enum_to_dict(enums.Characters)).to_sql('Characters', connection, if_exists='append', index=False)
            pd.DataFrame(_enum_to_dict(enums.Ranks)).to_sql('Ranks', connection, if_exists='append', index=False)
            pd.DataFrame(_enum_to_dict(enums.BattleTypes)).to_sql('BattleTypes', connection, if_exists='append', index=False)
            pd.DataFrame(_enum_to_dict(enums.Regions)).to_sql('Regions', connection, if_exists='append', index=False)
            pd.DataFrame(_enum_to_dict(enums.Stages)).to_sql('Stages', connection, if_exists='append', index=False)
    except Exception as e:
        return e
    return None