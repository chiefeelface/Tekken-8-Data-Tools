import time, datetime, math, os, polars as pl, gc, src.config as config, questionary as q, requests
from tqdm import tqdm
from src.models import ReplayData
from src.utils.sql_utils import create_tables, create_indexes, populate_lookup_tables
from src.utils.timer import Timer
from src.utils.file_utils import create_replay_dir

START_DATE = datetime.datetime(2025, 9, 1).replace(tzinfo=datetime.timezone.utc)
END_DATE = datetime.datetime(2025, 9, 2).replace(tzinfo=datetime.timezone.utc)

first_save: bool = True

def _download_replays(before: int) -> list[ReplayData]:
    request = f'https://wank.wavu.wiki/api/replays?before={before}'
    replay_data = requests.get(request).json()
    return replay_data

def get_replay_data(start_date: datetime.datetime, end_date: datetime.datetime, use_sql: bool):
    timer = Timer()
    total_replays: int = 0
    replays: list[ReplayData] = []

    # Get local time zone
    local_offset_hours = time.localtime().tm_gmtoff // 3600
    local_offset_minutes = (time.localtime().tm_gmtoff % 3600) // 60
    local_timezone = datetime.timezone(datetime.timedelta(hours=local_offset_hours, minutes=local_offset_minutes))

    # Apply to start and end dates while getting truncated timestamp
    start = math.trunc(start_date.replace(tzinfo=local_timezone).timestamp())
    end = math.trunc(end_date.replace(hour=23,minute=59,second=59, tzinfo=local_timezone).timestamp())

    # now will already have correct timestamp so we are good
    now = math.trunc(datetime.datetime.now().timestamp())

    if end > now:
        print('[Download] | End date has not happened or is not over, setting to the current time.')
        end = now
    before = start

    if use_sql:
        timer.start()
        file_name = config.DB_FILE_BASE_NAME + f'_{start_date.date()}_{end_date.date()}.db'
        if os.path.exists(file_name):
            if q.confirm('Duplicate database file found, would you like to delete it?').ask():
                print('[I/O] | Attempting to delete duplicate database file.')
                try:
                    os.remove(file_name)
                except Exception as e:
                    print(f'[I/O Error] {e} | Failed to  delete duplicate database file. [{timer.stop_get_elapsed_reset():,.2f}s]')
                else:
                    print(f'[I/O] | Succesfully deleted duplicate database file. [{timer.stop_get_elapsed_reset():,.2f}s]')
        timer.start()
        print('[I/O] | Attempting to create tables with primary and foreign keys.')
        if e := create_tables(file_name) != None:
            print(f'[I/O Error] {e} | Failed to create tables. [{timer.stop_get_elapsed_reset():,.2f}s]')
        else:
            print(f'[I/O] | Sucessfully created tables. [{timer.stop_get_elapsed_reset():,.2f}s]')
        timer.start()
        print(f'[I/O] | Attempting to populate lookup tables.')
        if e := populate_lookup_tables(file_name) != None:
            print(f'[I/O Error] {e} | Failed to populate lookup tables. [{timer.stop_get_elapsed_reset():,.2f}s]')
        else:
            print(f'[I/O] | Sucessfully populated lookup tables. [{timer.stop_get_elapsed_reset():,.2f}s]')
    else:
        timer.start()
        file_name = config.CSV_FILE_BASE_NAME + f'_{start_date.date()}_{end_date.date()}.csv'
        if os.path.exists(file_name):
            if q.confirm('Duplicate CSV file found, would you like to delete it?').ask():
                print('[I/O] | Attempting to delete duplicate CSV file.')
                try:
                    os.remove(file_name)
                except Exception as e:
                    print(f'[I/O Error] {e} | Failed to  delete duplicate CSV file. [{timer.stop_get_elapsed_reset():,.2f}s]')
                else:
                    print(f'[I/O] | Succesfully deleted duplicate CSV file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    loops_required = math.ceil((end - start) / 700)
    loops = 0
    print(f'[Download] | Beginning download of {loops_required :,} sets of replays.')
    
    try:
        with tqdm(
            total=loops_required,
            ncols=75,
            bar_format='[Download] | {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
            mininterval=0.2
        ) as progress:
            while before < end:
                start_time = time.perf_counter()

                before += 700

                try:
                    downloaded = _download_replays(before)
                except Exception as e:
                    tqdm.write(f'[Download Error] {e} | Encountered an error while attempting to download set {loops + 1} of {loops_required:,}, retrying.')
                    attempts = 0
                    sleep_time = (attempts + 1) * 1.005
                    while attempts < config.MAX_RETRIES:
                        downloaded = None
                        try:
                            time.sleep(sleep_time)
                            downloaded = _download_replays(before)
                            tqdm.write(f'[Download Error] | Retry {attempts + 1} succeeded, the set was succesfully downloaded, resuming normal operation.')
                            break
                        except Exception as e:
                            attempts += 1
                            sleep_time = (attempts + 1) * 1.005
                            tqdm.write(f'[Download Error] | Retry {attempts} failed, waiting {sleep_time} second(s) and trying again.')
                    else:
                        tqdm.write(f'[Download Error] | All retry attempts failed for set {loops + 1} of {loops_required:,} with before value {before}, and will not be included in the final output.')
                    
                    if downloaded:
                        replays.extend(downloaded)
                        total_replays += len(downloaded)
                        del downloaded [:]
                    loops += 1
                    time.sleep(1.005)
                    continue
                
                replays.extend(downloaded)
                total_replays += len(downloaded)
                del downloaded [:]
                if len(replays) > config.MAX_REPLAY_THRESHOLD:
                    _save_replay_data_to_file(replays, file_name, use_sql)
                    del replays[:]
                
                loops += 1
                progress.update(1)
                elapsed_time = time.perf_counter() - start_time 
                if elapsed_time - 0.005 < 1:
                    time.sleep(1 - elapsed_time + 0.005)
                
            if replays:
                _save_replay_data_to_file(replays, file_name, use_sql, True)
    except KeyboardInterrupt:
        print('[Download] | Execution interrupted.')
        if replays:
            _save_replay_data_to_file(replays, file_name, use_sql, True)
        if downloaded:
            print(f'[Download] | Replay set from before value {before} possibly lost.')
        return total_replays

    print(f'[Download] | Finished gathering {total_replays:,} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')
    return total_replays

def _save_replay_data_to_file(replay_data: list[ReplayData], file_name: str, use_sql: bool, use_indexes: bool=False):
    timer = Timer()
    tqdm.write(f'[I/O] | Attempting to save {len(replay_data):,} replays to file.')
    try:
        timer.start()
        replays_df = pl.DataFrame(replay_data)
        create_replay_dir()
        if use_sql:
            connection = config.SQLITE_URI + file_name
            replays_df.write_database(
                table_name=config.Tables.ReplayData,
                connection=connection,
                if_table_exists='append'
            )
            tqdm.write(f'[I/O] | Successfully saved {len(replay_data):,} replays to file. [{timer.stop_get_elapsed_reset():,.2f}s]')
            if use_indexes:
                timer.start()
                tqdm.write(f'[I/O] | Attempting to create indexes.')
                if e := create_indexes(file_name) != None:
                    tqdm.write(f'[I/O Error] {e} | Failed to create indexes. [{timer.stop_get_elapsed_reset():,.2f}s]')
                else:
                    tqdm.write(f'[I/O] | Successfully created indexes. [{timer.stop_get_elapsed_reset():,.2f}s]')
        else:
            # FIXME: This is really fucked up and there is probably a better way to do this
            global first_save
            with open(file_name, mode='a', encoding='utf8') as file:
                replays_df.write_csv(file, include_header=first_save)
                first_save = False
            tqdm.write(f'[I/O] | Successfully saved {len(replay_data):,} replays to file. [{timer.stop_get_elapsed_reset():,.2f}s]')
        
    except Exception as e:
        tqdm.write(f'[I/O Error] {e} | Failed to save {len(replay_data):,} replays to file, resuming normal execution. [{timer.stop_get_elapsed_reset():,.2f}s]')
    
    # In attempt to reduce memory leaks
    try:
        del replays_df
    except:
        pass
    gc.collect()