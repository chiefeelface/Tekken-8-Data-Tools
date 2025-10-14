import os, src.config as config, time, pathlib

def create_replay_dir():
    if not os.path.exists(config.REPLAY_DIR):
        os.makedirs(config.REPLAY_DIR)

def ensure_file_exists(file: str | pathlib.Path): 
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file, 'a'): pass

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