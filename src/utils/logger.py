from typing import Literal
from tqdm import tqdm

def log(log_type: Literal['io', 'download'], message: str, error: bool=False, error_message: Exception | None=None, time: float | None=None, use_tqdm: bool=False):
    out = ''
    if log_type == 'io':
        out = 'I/O'
    elif log_type == 'download':
        out = 'Download'
    else:
        raise ValueError(f'Unknown log_type "{log_type}".')
    
    if error:
        out += ' Error'
        out = f'[{out}] {error_message} | {message}.'
    else:
        out = f'[{out}] | {message}.'
    
    if time:
        out += f' [{time:,.2f}s]'
    
    if use_tqdm:
        tqdm.write(out)
    else:
        print(out)

def io(message: str, time: float | None=None, use_tqdm: bool=False):
    log('io', message, False, None, time, use_tqdm)

def io_error(message: str, error_message: Exception | None=None, time: float | None=None, use_tqdm: bool=False):
    log('io', message, True, error_message, time, use_tqdm)

def download(message: str, time: float | None=None, use_tqdm: bool=False):
    log('download', message, False, None, time, use_tqdm)

def download_error(message: str, error_message: Exception | None=None, time: float | None=None, use_tqdm: bool=False):
    log('download', message, True, error_message, time, use_tqdm)

def io_tqdm(message: str, time: float | None=None):
    io(message, time, True)

def io_error_tqdm(message: str, error_message: Exception | None=None, time: float | None=None):
    io_error(message, error_message, time, True)

def download_tqdm(message: str, time: float | None=None):
    download(message, time, True)

def download_error_tqdm(message: str, error_message: Exception | None=None, time: float | None=None):
    download_error(message, error_message, time, True)

if __name__ == '__main__':
    io('Yes, this is IO yes for sure wowee', 1.45)