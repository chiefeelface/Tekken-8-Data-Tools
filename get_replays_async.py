import requests, time, datetime, math, os, pandas as pd, aiohttp, asyncio
from tqdm import trange, tqdm
from enums.characters import Characters
from enums.battle_types import BattleTypes
from enums.ranks import Ranks
from models.replay_data import ReplayData
from models.simplified_replay_data import SimplifiedReplayData

MAX_BUFFER_SIZE = 100_000
MAX_RETRIES = 5
FETCH_INTERVAL = 1
CSV_FILE_BASE_NAME = f'replay_data'

START_DATE = datetime.datetime(2025, 6, 1)
END_DATE = datetime.datetime(2025, 7, 31)

async def fetch_replays_async(session: aiohttp.ClientSession, before: int, max_retries=MAX_RETRIES):
    url = f'https://wank.wavu.wiki/api/replays?before={before}'
    for retry in range(1, max_retries + 1):
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f'HTTP {response.status}')
                return await response.json()
        except Exception as e:
            wait_time = FETCH_INTERVAL * (2**(retry - 1))
            tqdm.write(f'[Fetch Retry {retry}/{max_retries}] {e} | Retrying in {wait_time:.2f}')
            await asyncio.sleep(wait_time)
    raise Exception(f'Fetch failed, all {max_retries} retries failed for URL: {url}')

async def fetch_and_buffer(
        session: aiohttp.ClientSession,
        queue: asyncio.Queue,
        buffer: list[dict],
        before: int,
        progress,
        buffer_lock
    ):
    try:
        data = await fetch_replays_async(session, before)
        if not isinstance(data, list):
            raise ValueError('Expect list of dicts from API')
        
        async with buffer_lock:
            buffer.extend(data)
            if len(buffer) >= MAX_BUFFER_SIZE:
                await queue.put(buffer.copy())
                buffer.clear()
        
        progress.update(1)
    except Exception as e:
        tqdm.write(f'[Request Error] {e}')

async def producer(queue: asyncio.Queue):
    # Add 1 day to end_date since time is midnight
    end = math.trunc((END_DATE + datetime.timedelta(days=1)).timestamp())
    loops_required = math.ceil(
        (
            end -
            math.trunc(START_DATE.timestamp())
        )
    / 700)
    before = end

    async with aiohttp.ClientSession() as session:
        buffer = []
        buffer_lock = asyncio.Lock()
        success_count = 0
        with tqdm(total=loops_required + 1, desc='Downloading Replay Sets', ncols=100, unit=' replay sets', mininterval=0.25) as progress:
            while success_count < loops_required:
                try:
                    data = await fetch_replays_async(session, before)
                    if not isinstance(data, list):
                        raise ValueError('Expect list of dicts from API')

                    buffer.extend(data)
                    success_count += 1
                    progress.update(1)

                    if len(buffer) >= MAX_BUFFER_SIZE:
                        await queue.put(buffer.copy())
                        buffer.clear()
                except Exception as e:
                    tqdm.write(f'[Producer error] {e} | Retrying fetch in {FETCH_INTERVAL}s')
                
                await asyncio.sleep(FETCH_INTERVAL)
        
        if buffer:
            await queue.put(buffer)
            tqdm.write(f'[Producer] Final batch')
        await queue.put(None)

async def consumer(queue: asyncio.Queue):
    while True:
        batch = await queue.get()
        try:
            df = pd.DataFrame(batch)
            file_name = CSV_FILE_BASE_NAME + f'{START_DATE.date()}_{END_DATE.date()}.csv'
            if not os.path.exists(file_name):
                df.to_csv(file_name, mode='a', header=True, index=False)
            else:
                df.to_csv(file_name, mode='a', header=False, index=False)
            tqdm.write(f'[Consumer Success] | Succesfully saved batch of {df.size} replays to {file_name}')
        except Exception as e:
            tqdm.write(f'[Consumer Error] {e} | Failed to save batch, adding back to queue')
            await queue.put(batch)
        finally:
            queue.task_done()

async def main():
    queue = asyncio.Queue()
    await asyncio.gather(
        producer(queue),
        consumer(queue)
    )

if __name__ == '__main__':
    start_time = time.perf_counter()
    asyncio.run(main())
    #downloaded_replays = asyncio.run(get_replay_data_async(start_date, end_date)) #get_replay_data(start_date, end_date)
    #print(f'Finished gathering {downloaded_replays} replays in a total of {round(time.perf_counter() - start_time, 2)} seconds')