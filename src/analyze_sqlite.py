import sqlite3, tkinter as tk, src.config as config, pandas as pd, numpy as np
from tkinter import filedialog as fd
from pathlib import Path
from src.utils import *
from src.enums import *

def get_data_from_table(file_path, table, columns='*'):
    with sqlite3.connect(file_path) as connection:
        return pd.read_sql(f'select {columns} from {table}', connection)

def get_raw_win_rate_query(file_path):
    with sqlite3.connect(file_path) as connection:
        cursor = connection.cursor()

        with open(config.QUERY_FOLDER_PATH + 'character_stats.sql') as f:
            sql_script = f.read()
        
        cursor.executescript(sql_script)

        return cursor.fetchall()
    
def get_raw_win_rate_db(replay_df: pd.DataFrame):
    pass

def analyze():
    root = tk.Tk()
    root.withdraw()
    timer = Timer()

    replay_data_file_path = fd.askopenfilename(title='Select Replay Data File', filetypes=(('All', ['*.csv', '*.db']), ('CSV Files', '*.csv'), ('SQLite Files', '*.db')))
    is_sql = Path(replay_data_file_path).suffix == '.db'

    print('[I/O] | Attempting to get all replays from file.')
    timer.start()
    if is_sql:
        replay_df = get_data_from_table(replay_data_file_path, config.Tables.ReplayData, 'p1_chara_id, p2_chara_id, winner')
    else:
        replay_df = pd.read_csv(replay_data_file_path)
    print(f'[I/O] | Succesfully got all replays from file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    print('[I/O] | Attempting to calculate win rates.')
    timer.start()
    replay_df['p1_chara'] = replay_df['p1_chara_id'].map(Characters.id_to_name)
    replay_df['p2_chara'] = replay_df['p2_chara_id'].map(Characters.id_to_name)
    replay_df['Winner'] = np.where(replay_df['winner'] == 1, replay_df['p1_chara'], replay_df['p2_chara'])
    replay_df['Loser'] = np.where(replay_df['winner'] == 2, replay_df['p1_chara'], replay_df['p2_chara'])
    wins = replay_df['Winner'].value_counts().rename_axis('Character').reset_index(name='Wins')
    losses = replay_df['Loser'].value_counts().rename_axis('Character').reset_index(name='Losses')
    stats = pd.merge(wins, losses, on='Character', how='outer').fillna(0)
    stats['Wins'] = stats['Wins'].astype(int)
    stats['Losses'] = stats['Losses'].astype(int)
    stats['TotalGames'] = stats['Wins'] + stats['Losses']
    stats['RawWinRate'] = stats['Wins'] / stats['TotalGames']
    print(stats.sort_values('RawWinRate', ignore_index=True))
    print(f'[I/O] | Succesfully calculated win rates. [{timer.stop_get_elapsed_reset():,.2f}s]')

if __name__ == '__main__':
    analyze()