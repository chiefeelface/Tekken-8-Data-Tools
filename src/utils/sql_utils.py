import sqlite3, src.config as config, src.enums as enums, polars as pl
from src.utils.file_utils import create_replay_dir, ensure_file_exists
from enum import Enum

def create_tables(database_file: str):
    create_replay_dir()
    ensure_file_exists(database_file)
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
    ensure_file_exists(database_file)
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

def _write_enum_to_table(enum, table, connection):
    pl.DataFrame(_enum_to_dict(enum)).write_database(
        table_name=table,
        connection=connection,
        if_table_exists='append'
    )

def populate_lookup_tables(database_file: str): 
    create_replay_dir()
    ensure_file_exists(database_file)
    try:
        connection = config.SQLITE_URI + database_file
        _write_enum_to_table(enums.Characters, config.Tables.Characters, connection)
        _write_enum_to_table(enums.Ranks, config.Tables.Ranks, connection)
        _write_enum_to_table(enums.BattleTypes, config.Tables.BattleTypes, connection)
        _write_enum_to_table(enums.Regions, config.Tables.Regions, connection)
        _write_enum_to_table(enums.Stages, config.Tables.Stages, connection)
    except Exception as e:
        return e
    return None