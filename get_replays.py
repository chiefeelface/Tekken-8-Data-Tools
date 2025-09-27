import requests, time, datetime, math, os, pandas as pd, gc, sqlite3, enums
from tqdm import trange, tqdm
from models import ReplayData

START_DATE = datetime.datetime(2025, 9, 1)
END_DATE = datetime.datetime(2025, 9, 2)

MAX_REPLAY_THRESHOLD = 1_000_000
MAX_RETRIES = 3
CSV_FILE_BASE_NAME = DB_FILE_BASE_NAME = 'downloaded_replays/replay_data'

USE_SQLITE = True
SQLITE_TABLE_NAME = 'ReplayData'

def download_replays(before: int):
    request = f'https://wank.wavu.wiki/api/replays?before={before}'
    replay_data = requests.get(request).json()
    return replay_data

def get_replay_data(start_date: datetime.datetime, end_date: datetime.datetime):
    total_replays: int = 0
    replays: list[ReplayData] = []
    start = math.trunc(start_date.timestamp())
    # Add 1 day to end_date since time is midnight
    end = math.trunc((end_date + datetime.timedelta(days=1)).timestamp())
    loops_required = math.ceil((end - start) / 700)
    before = math.trunc(end)
    if USE_SQLITE:
        create_tables(start_date, end_date)
        fill_tables_for_enums(start_date, end_date)
    tqdm.write(f'[Download] | Beginning download of {loops_required:,} sets of replays.')
    for i in trange(loops_required + 1, desc='Downloading Replay Sets', ncols=100, unit=' replay sets'):
        start_time = time.perf_counter()

        try:
            downloaded = download_replays(before)
        except Exception as e:
            tqdm.write(f'[Download Error] {e} | Encountered an error while attempting to download set {i + 1} of {loops_required:,}, retrying.')
            attempts = 0
            while attempts < MAX_RETRIES:
                downloaded = None
                try:
                    time.sleep(1.005)
                    downloaded = download_replays(before)
                    tqdm.write(f'[Download Error] | Retry {attempts + 1} succeeded, the set was succesfully downloaded, resuming normal operation.')
                    break
                except Exception as e:
                    tqdm.write(f'[Download Error] | Retry {attempts + 1} failed, waiting 1 second and trying again.')
                    attempts += 1
            else:
                tqdm.write(f'[Download Error] | All retry attempts failed for set {i + 1} of {loops_required:,} with before value {before}, and will not be included in the final output.')
            
            if downloaded:
                replays.extend(downloaded)
                total_replays += len(downloaded)
            before -= 700
            time.sleep(1.005)
            continue
        
        replays.extend(downloaded)
        total_replays += len(downloaded)
        before -= 700
        if len(replays) > MAX_REPLAY_THRESHOLD:
            save_replay_data_to_file(replays, start_date, end_date)
            del replays[:]
        
        elapsed_time = time.perf_counter() - start_time 
        if elapsed_time - 0.005 < 1:
            time.sleep(1 - elapsed_time + 0.005)
        
    if replays:
        save_replay_data_to_file(replays, start_date, end_date)

    return total_replays

def save_replay_data_to_file(replay_data: list[ReplayData], start_date: datetime.datetime, end_date: datetime.datetime):
    tqdm.write(f'[I/O] | Attempting to save {len(replay_data):,} replays to file.')
    try:
        replays_df = pd.DataFrame(replay_data)
        if USE_SQLITE:
            file_name = DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
            # Ensure file exists
            open(file_name, 'a').close()
            with sqlite3.connect(file_name) as connection:
                replays_df.to_sql(SQLITE_TABLE_NAME, connection, if_exists='append', index=False)
        else:
            file_name = CSV_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.csv'
            if not os.path.exists(file_name):
                replays_df.to_csv(file_name, mode='a', header=True, index=False)
            else:
                replays_df.to_csv(file_name, mode='a', header=False, index=False)
        
        # In attempt to reduce memory leaks
        del replays_df
        gc.collect()
    except Exception as e:
        tqdm.write(f'[I/O Error] {e} | Failed to save {len(replay_data):,} replays to file resuming normal execution.')
    else:
        tqdm.write(f'[I/O] | Successfully saved {len(replay_data):,} replays to file.')

def create_tables(start_date: datetime.datetime, end_date: datetime.datetime):
    file_name = DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
    # Ensure file exists
    open(file_name, 'a').close()
    tqdm.write('[I/O] | Attempting to generate tables with primary and foreign keys.')
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
            for table in ['BattleTypes', 'Characters', 'Regions', 'Ranks', 'Stages']:
                cursor.execute(f'''
CREATE TABLE IF NOT EXISTS {table} (
    Id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL
);
''')
    except Exception as e:
        tqdm.write(f'[I/O Error] {e} | Failed to generate tables.')
    else:
        tqdm.write(f'[I/O] | Sucessfully generated tables.')

def enum_to_dict(enum):
    return [{'Id': member.value, 'Name': member.name} for member in enum]

def fill_tables_for_enums(start_date: datetime.datetime, end_date: datetime.datetime):
    file_name = DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
    # Ensure file exists
    open(file_name, 'a').close()
    tqdm.write(f'[I/O] | Attempting to populate helper tables.')
    try:
        with sqlite3.connect(file_name) as connection:
            pd.DataFrame(enum_to_dict(enums.Characters)).to_sql('Characters', connection, if_exists='append', index=False)
            pd.DataFrame(enum_to_dict(enums.Ranks)).to_sql('Ranks', connection, if_exists='append', index=False)
            pd.DataFrame(enum_to_dict(enums.BattleTypes)).to_sql('BattleTypes', connection, if_exists='append', index=False)
            pd.DataFrame(enum_to_dict(enums.Regions)).to_sql('Regions', connection, if_exists='append', index=False)
            pd.DataFrame(enum_to_dict(enums.Stages)).to_sql('Stages', connection, if_exists='append', index=False)
    except Exception as e:
        tqdm.write(f'[I/O Error] {e} | Failed to populate helper tables.')
    else:
        tqdm.write(f'[I/O] | Sucessfully populated helper tables.')


if __name__ == '__main__':
    start_time = time.perf_counter()
    downloaded_replays = get_replay_data(START_DATE, END_DATE)
    tqdm.write(f'[Download] | Finished gathering {downloaded_replays:,} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')