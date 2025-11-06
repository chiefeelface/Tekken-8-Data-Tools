import time, datetime, math, os, polars as pl, gc, src.config as config, questionary as q, requests, src.utils.logger as logger
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
    overall_timer = Timer()
    overall_timer.start()
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
                logger.io('Attempting to delete duplicate database file')
                try:
                    os.remove(file_name)
                except Exception as e:
                    logger.io_error('Failed to  delete duplicate database file', e, timer.stop_get_elapsed_reset())
                else:
                    logger.io('Succesfully deleted duplicate database file', timer.stop_get_elapsed_reset())
        timer.start()
        logger.io('Attempting to create tables with primary and foreign keys')
        e = create_tables(file_name)
        if e:
            logger.io_error('Failed to create tables', e, timer.stop_get_elapsed_reset())
        else:
            logger.io('Sucessfully created tables', timer.stop_get_elapsed_reset())
        timer.start()
        logger.io('Attempting to populate lookup tables')
        e = populate_lookup_tables(file_name)
        if e:
            logger.io_error('Failed to populate lookup tables', e, timer.stop_get_elapsed_reset())
        else:
            logger.io('Sucessfully populated lookup tables', timer.stop_get_elapsed_reset())
    else:
        file_name = config.CSV_FILE_BASE_NAME + f'_{start_date.date()}_{end_date.date()}.csv'
        if os.path.exists(file_name):
            if q.confirm('Duplicate CSV file found, would you like to delete it?').ask():
                timer.start()
                logger.io('Attempting to delete duplicate CSV file')
                try:
                    os.remove(file_name)
                except Exception as e:
                    logger.io_error('Failed to  delete duplicate CSV file', e, timer.stop_get_elapsed_reset())
                else:
                    logger.io('Succesfully deleted duplicate CSV file', timer.stop_get_elapsed_reset())

    loops_required = math.ceil((end - start) / 700)
    loops = 0
    logger.download(f'Beginning download of {loops_required :,} sets of replays')
    
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
                    logger.download_error_tqdm(f'Encountered an error while attempting to download set {loops + 1} of {loops_required:,}, retrying', e)
                    attempts = 0
                    sleep_time = (attempts + 1) * 1.005
                    while attempts < config.MAX_RETRIES:
                        downloaded = None
                        try:
                            time.sleep(sleep_time)
                            downloaded = _download_replays(before)
                            logger.download_error_tqdm(f'Retry {attempts + 1} succeeded, the set was succesfully downloaded, resuming normal operation')
                            break
                        except Exception as e:
                            attempts += 1
                            sleep_time = (attempts + 1) * 1.005
                            logger.download_error_tqdm(f'Retry {attempts} failed, waiting {sleep_time} second(s) and trying again')
                    else:
                        logger.download_error_tqdm(f'All retry attempts failed for set {loops + 1} of {loops_required:,} with before value {before}, and will not be included in the final output')                        
                    
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
        logger.download('Execution interrupted')
        if replays:
            _save_replay_data_to_file(replays, file_name, use_sql, True)
        if downloaded:
            logger.download(f'Replay set from before value {before} possibly lost')
        return total_replays

    logger.download(f'Finished gathering {total_replays:,} replays', overall_timer.stop_get_elapsed_reset())
    return total_replays

def _save_replay_data_to_file(replay_data: list[ReplayData], file_name: str, use_sql: bool, use_indexes: bool=False):
    timer = Timer()
    logger.io_tqdm(f'Attempting to save {len(replay_data):,} replays to file')
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
            logger.io_tqdm(f'Successfully saved {len(replay_data):,} replays to file', timer.stop_get_elapsed_reset())
            if use_indexes:
                timer.start()
                logger.io_tqdm('Attempting to create indexes')
                e = create_indexes(file_name)
                if e:
                    logger.io_error_tqdm('Failed to create indexes', e, timer.stop_get_elapsed_reset())
                else:
                    logger.io_tqdm('Successfully created indexes', timer.stop_get_elapsed_reset())
        else:
            # FIXME: This is really fucked up and there is probably a better way to do this
            global first_save
            with open(file_name, mode='a', encoding='utf8') as file:
                replays_df.write_csv(file, include_header=first_save)
                first_save = False
            logger.io_tqdm(f'Successfully saved {len(replay_data):,} replays to file', timer.stop_get_elapsed_reset())
        
    except Exception as e:
        logger.io_error_tqdm(f'Failed to save {len(replay_data):,} replays to file, resuming normal execution', e, timer.stop_get_elapsed_reset())
    
    # In attempt to reduce memory leaks
    try:
        del replays_df
    except:
        pass
    uncollected_items = gc.collect()
    logger.log('system', f'Garbage manually collected, {uncollected_items} item(s) left uncollected', use_tqdm=True)