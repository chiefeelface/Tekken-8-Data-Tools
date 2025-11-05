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
    create_results_dir()
    print('[I/O] | Attempting to save results to an excel file.')
    with xlsxwriter.Workbook(config.XLSX_FILE_BASE_NAME + pathlib.Path(replay_file).stem.replace('replay_data', 'results') + '.xlsx') as wb:
        for result in results:
            timer.start()
            try:
                result[DATAFRAME].write_excel(wb, worksheet=result[WORKSHEET])
            except:
                print(f'[I/O] | Failed to save worksheet {result[WORKSHEET]} to file.')
            print(f'[I/O] | Successfully saved worksheet {result[WORKSHEET]} to file. [{timer.stop_get_elapsed_reset():,.2f}s]')
        timer.start()
        print('[I/O] | Attempting to write all saved worksheets to file.')
    print(f'[I/O] | Successfully wrote all saved worksheets to file. [{timer.stop_get_elapsed_reset():,.2f}s]')