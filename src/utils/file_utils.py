import os, src.config as config, time, pathlib, polars as pl, xlsxwriter
from src.utils.timer import Timer

DATAFRAME = 0
WORKSHEET = 1

def _create_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def create_replay_dir():
    _create_dir(config.REPLAY_DIR)

def create_results_dir():
    _create_dir(config.RESULTS_DIR)

def ensure_file_exists(file: str | pathlib.Path): 
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file, 'a'): pass

def write_results_to_excel(replay_file, results: list[tuple[pl.DataFrame, str]]):
    timer = Timer()
    timer.start()
    print('[I/O] | Attempting to save results to an excel file.')
    create_results_dir()
    with xlsxwriter.Workbook(config.XLSX_FILE_BASE_NAME + pathlib.Path(replay_file).stem.replace('replay_data', 'results') + '.xlsx') as wb:
        for result in results:
            try:
                result[DATAFRAME].write_excel(wb, worksheet=result[WORKSHEET])
            except:
                print(f'[I/O] | Failed to save worksheet {result[WORKSHEET]} to file.')
            print(f'[I/O] | Successfully saved worksheet {result[WORKSHEET]} to file.')
    print(f'[I/O] | Succesfully saved all results to an excel file. [{timer.stop_get_elapsed_reset():,.2f}s]')

def try_remove_file(path: str | pathlib.Path, max_retries: int=10, delay: float=0.1):   
    if not os.path.exists(path):
        return
    for _ in range(max_retries):
        try:
            os.remove(path)
            return
        except FileNotFoundError:
            print('File not found.')
            return
        except Exception as e:
            print(f'Could not delete file. {e}')
            time.sleep(delay)