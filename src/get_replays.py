import time, datetime, math, os, pandas as pd, gc, sqlite3, src.config as config
from tqdm import tqdm
from src.models import ReplayData
from src.utils import *

START_DATE = datetime.datetime(2025, 9, 1)
END_DATE = datetime.datetime(2025, 9, 2)

def get_replay_data(start_date: datetime.datetime, end_date: datetime.datetime):
    total_replays: int = 0
    replays: list[ReplayData] = []
    start = math.trunc(start_date.timestamp())
    # Add 1 day and subtract 1 millisecond to end_date since time is midnight
    end = math.trunc((end_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).timestamp())
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if end > now:
        tqdm.write('[Download] | End date has not happened yet, setting to the current time.')
        end = now
    loops_required = math.ceil((end - start) / 700)
    before = start
    if config.USE_SQLITE:
        tqdm.write('[I/O] | Attempting to generate tables with primary and foreign keys.')
        if e := create_tables(start_date, end_date) != None:
            tqdm.write(f'[I/O Error] {e} | Failed to generate tables.')
        else:
            tqdm.write(f'[I/O] | Sucessfully generated tables.')
        tqdm.write(f'[I/O] | Attempting to populate helper tables.')
        if e := fill_tables_for_enums(start_date, end_date) != None:
            tqdm.write(f'[I/O Error] {e} | Failed to populate helper tables.')
        else:
            tqdm.write(f'[I/O] | Sucessfully populated helper tables.')
    tqdm.write(f'[Download] | Beginning download of {loops_required:,} sets of replays.')
    loops = 0
    with tqdm(total=loops_required + 1, desc='Downloading Replay Sets', ncols=100, unit=' replay sets') as progress:
        while before < end:
            start_time = time.perf_counter()

            before += 700

            try:
                downloaded = download_replays(before)
            except KeyboardInterrupt:
                tqdm.write(f'[Download] | Execution cancelled by user.')
                total_replays += len(replays)
                save_replay_data_to_file(replays, start_date, end_date)
                return total_replays
            except Exception as e:
                tqdm.write(f'[Download Error] {e} | Encountered an error while attempting to download set {loops + 1} of {loops_required:,}, retrying.')
                attempts = 0
                while attempts < config.MAX_RETRIES:
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
                    tqdm.write(f'[Download Error] | All retry attempts failed for set {loops + 1} of {loops_required:,} with before value {before}, and will not be included in the final output.')
                
                if downloaded:
                    replays.extend(downloaded)
                    total_replays += len(downloaded)
                    del downloaded [:]
                time.sleep(1.005)
                continue
            
            replays.extend(downloaded)
            total_replays += len(downloaded)
            del downloaded [:]
            if len(replays) > config.MAX_REPLAY_THRESHOLD:
                save_replay_data_to_file(replays, start_date, end_date)
                del replays[:]
            
            loops += 1
            progress.update(1)
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
        if config.USE_SQLITE:
            file_name = config.DB_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.db'
            # Ensure file exists
            open(file_name, 'a').close()
            with sqlite3.connect(file_name) as connection:
                replays_df.to_sql(config.SQLITE_TABLE_NAME, connection, if_exists='append', index=False)
        else:
            file_name = config.CSV_FILE_BASE_NAME + f'_{start_date.date()}_{(end_date).date()}.csv'
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

if __name__ == '__main__':
    start_time = time.perf_counter()
    downloaded_replays = get_replay_data(START_DATE, END_DATE)
    tqdm.write(f'[Download] | Finished gathering {downloaded_replays:,} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')