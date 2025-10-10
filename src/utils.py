import requests, datetime, sqlite3, src.config as config, polars as pl, src.enums as enums, os, time
from src.models import ReplayData
from enum import Enum

class Timer:
    def __init__(self) -> None:
        self._start = None
        self._end = None
    
    def start(self):
        self._start = time.perf_counter()
    
    def stop(self):
        self._end = time.perf_counter()

    def reset(self):
        self._start = None
        self._end = None

    def get_elapsed(self):
        if self._start and self._end:
            return self._end - self._start
        return None

    def stop_get_elapsed_reset(self, formatted: bool=False):
        self.stop()
        elapsed = self.get_elapsed() if not formatted else f'{self.get_elapsed():,.2f}s'
        self.reset()
        return elapsed

def try_remove_file(path, max_retries=10, delay=0.1):
    if not os.path.exists(path):
        return
    for _ in range(max_retries):
        try:
            os.remove(path)
            return
        except:
            time.sleep(delay)

def create_replay_dir():
    if not os.path.exists(config.REPLAY_DIR):
        os.makedirs(config.REPLAY_DIR)

def download_replays(before: int) -> list[ReplayData]:
    request = f'https://wank.wavu.wiki/api/replays?before={before}'
    replay_data = requests.get(request).json()
    return replay_data

def create_tables(database_file: str):
    create_replay_dir()
    # Ensure file exists
    with open(database_file, 'a'): pass
    try:
        with sqlite3.connect(database_file) as connection:
            cursor = connection.cursor()
            # Create main table
            cursor.execute(f'''
CREATE TABLE IF NOT EXISTS {config.Tables.ReplayData} (
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
            # Create lookup tables
            for table in [config.Tables.BattleTypes, config.Tables.Characters, config.Tables.Regions, config.Tables.Ranks, config.Tables.Stages]:
                cursor.execute(f'''
CREATE TABLE IF NOT EXISTS {table} (
    Id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL
);
''')
    except Exception as e:
        return e
    return None

def _create_index(cursor: sqlite3.Cursor, index_name, table, column):
    cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});')

def create_indexes(database_file: str):
    create_replay_dir()
    # Ensure file exists
    with open(database_file, 'a'): pass
    try:
        with sqlite3.connect(database_file) as connection:
            cursor = connection.cursor()
            indexes = [
                {
                    'name': f'idx_{config.Tables.ReplayData.lower()}_p1_chara_id',
                    'table': config.Tables.ReplayData,
                    'column': 'p1_chara_id'
                },
                {
                    'name': f'idx_{config.Tables.ReplayData.lower()}_p2_chara_id',
                    'table': config.Tables.ReplayData,
                    'column': 'p2_chara_id'
                },
                {
                    'name': f'idx_{config.Tables.ReplayData.lower()}_winner',
                    'table': config.Tables.ReplayData,
                    'column': 'winner'
                }
            ]
            for index in indexes:
                _create_index(cursor, index['name'], index['table'], index['column'])
    except Exception as e:
        return e
    return None

def _enum_to_dict(enum: type[Enum]):
    return [{'Id': member.value, 'Name': member.name} for member in enum]

def _write_enum_to_database(enum, table, connection):
    pl.DataFrame(_enum_to_dict(enum)).write_database(
        table_name=table,
        connection=connection,
        if_table_exists='append'
    )

def populate_lookup_tables(database_file: str):
    create_replay_dir()
    # Ensure file exists
    with open(database_file, 'a'): pass
    try:
        connection = config.SQLITE_URI + database_file
        _write_enum_to_database(enums.Characters, config.Tables.Characters, connection)
        _write_enum_to_database(enums.Ranks, config.Tables.Ranks, connection)
        _write_enum_to_database(enums.BattleTypes, config.Tables.BattleTypes, connection)
        _write_enum_to_database(enums.Regions, config.Tables.Regions, connection)
        _write_enum_to_database(enums.Stages, config.Tables.Stages, connection)
    except Exception as e:
        return e
    return None