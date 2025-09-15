import requests, time, datetime, math, os, pandas as pd, gc
from tqdm import trange, tqdm
from enums import Characters
from enums import BattleTypes
from enums import Ranks
from models import ReplayData
from models import SimplifiedReplayData

MAX_REPLAY_THRESHOLD = 1_000_000
MAX_RETRIES = 3
CSV_FILE_BASE_NAME = f'downloaded_replays/replay_data'

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
    for i in trange(loops_required + 1, desc='Downloading Replay Sets', ncols=100, unit=' replay sets'):
        start_time = time.perf_counter()

        try:
            downloaded = download_replays(before)
        except Exception as e:
            tqdm.write(f'Encountered an error while attempting to download set {i + 1} of {loops_required}, retrying.')
            attempts = 0
            while attempts < MAX_RETRIES:
                downloaded = None
                try:
                    time.sleep(1.005)
                    downloaded = download_replays(before)
                    tqdm.write(f'Retry {attempts + 1} succeeded!')
                    break
                except Exception as e:
                    tqdm.write(f'Retry {attempts + 1} failed, waiting 1 second and trying again.')
                    attempts += 1
            else:
                tqdm.write(f'All retry attempts failed for set {i + 1} of {loops_required} with before value {before}, and will not be included in the final output.')
            
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
        
def process_replay_data(replay_data: list[ReplayData]):
    simplified_replay_data: list[SimplifiedReplayData] = []
    while replay_data:
        replay: ReplayData = replay_data.pop()
        simplified_replay: SimplifiedReplayData = {
            "battle_at": replay["battle_at"],
            "battle_type": BattleTypes(replay["battle_type"]).name,
            "p1_character": Characters(replay["p1_chara_id"]).name,
            "p1_power": replay["p1_power"],
            "p1_rank": replay["p1_rank"],
            "p1_rank_name": Ranks(replay["p1_rank"]).name,
            "p2_character": Characters(replay["p2_chara_id"]).name,
            "p2_power": replay["p2_power"],
            "p2_rank": replay["p2_rank"],
            "p2_rank_name": Ranks(replay["p2_rank"]).name,
            "winner": replay["winner"]
        }
        simplified_replay_data.append(simplified_replay)
    return simplified_replay_data

def save_replay_data_to_file(replay_data: list[ReplayData], start_date: datetime.datetime, end_date: datetime.datetime):
    replays_df = pd.DataFrame(replay_data)
    file_name = CSV_FILE_BASE_NAME + f'_{start_date.date()}--{(end_date).date()}.csv'
    if not os.path.exists(file_name):
        replays_df.to_csv(file_name, mode='a', header=True, index=False)
    else:
        replays_df.to_csv(file_name, mode='a', header=False, index=False)
    
    # In attempt to reduce memory leaks
    del replays_df
    gc.collect()

if __name__ == '__main__':
    start_time = time.perf_counter()
    start_date = datetime.datetime(2025, 6, 1)
    end_date = datetime.datetime(2025,6, 2)

    downloaded_replays = get_replay_data(start_date, end_date)
    tqdm.write(f'Finished gathering {downloaded_replays} replays in a total of {round(time.perf_counter() - start_time, 2)} seconds')