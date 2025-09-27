import requests, time, datetime, math, os, pandas as pd, gc
from tqdm import trange, tqdm
from models import ReplayData
import sqlite3

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
    
    # TODO: Create mapping tables for the enums
    if USE_SQLITE:
        pass

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
        tqdm.write(f'[I/O] | Successfully saved {len(replay_data):,} replays to file')

if __name__ == '__main__':
    start_time = time.perf_counter()
    downloaded_replays = get_replay_data(START_DATE, END_DATE)
    tqdm.write(f'[Download] | Finished gathering {downloaded_replays} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')