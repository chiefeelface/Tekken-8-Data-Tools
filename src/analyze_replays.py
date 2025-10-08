import sqlite3, tkinter as tk, src.config as config, polars as pl, numpy as np
from tkinter import filedialog as fd
from pathlib import Path
from src.utils import *
from src.enums import *

def _get_data_from_table(file_path, table, columns=['*']):
    with sqlite3.connect(file_path) as connection:
        return pl.read_database(f'select {', '.join(columns)} from {table}', connection)

def analyze_replay_data():
    root = tk.Tk()
    root.withdraw()
    timer = Timer()

    replay_data_file_path = fd.askopenfilename(title='Select Replay Data File', filetypes=(('All', ['*.csv', '*.db']), ('CSV Files', '*.csv'), ('SQLite Files', '*.db')))
    is_sql = Path(replay_data_file_path).suffix == '.db'

    print('[I/O] | Attempting to get all replays from file.')
    timer.start()
    if is_sql:
        replay_df = _get_data_from_table(replay_data_file_path, config.Tables.ReplayData, ['p1_chara_id', 'p2_chara_id', 'winner'])
    else:
        replay_df = pl.read_csv(replay_data_file_path)
    print(f'[I/O] | Succesfully got all replays from file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    print('[I/O] | Attempting to calculate win rates.')
    timer.start()
    chara_lookup = pl.DataFrame({
        'chara_id': [chara.value for chara in Characters],
        'chara_name': [chara.name for chara in Characters]
    })
    replay_df = (
        replay_df
        .join(chara_lookup.rename({"chara_id": "p1_chara_id", "chara_name": "p1_chara"}), on="p1_chara_id", how="left")
        .join(chara_lookup.rename({"chara_id": "p2_chara_id", "chara_name": "p2_chara"}), on="p2_chara_id", how="left")
    )
    replay_df = replay_df.with_columns([
        pl
        .when(pl.col('winner') == 1)
        .then(pl.col('p1_chara'))
        .otherwise(pl.col('p2_chara'))
        .alias('Winner'),
        pl
        .when(pl.col('winner') == 2)
        .then(pl.col('p1_chara'))
        .otherwise(pl.col('p2_chara'))
        .alias('Loser'),
    ])
    wins = (
        replay_df
        .group_by('Winner')
        .agg(pl.count().alias('Wins'))
        .rename({'Winner': 'Character'})
    )
    losses = (
        replay_df
        .group_by('Loser')
        .agg(pl.count().alias('Losses'))
        .rename({'Loser': 'Character'})
    )
    stats = (
        wins
        .join(losses, on='Character', how='outer')
        .drop('Character_right')
        .fill_null(0)
        .with_columns([
            pl.col('Wins'),
            pl.col('Losses'),
            (pl.col('Wins') + pl.col('Losses')).alias('TotalGames'),
            (pl.col('Wins') / (pl.col('Wins') + pl.col('Losses'))).alias('RawWinRate')
        ])
        .sort('RawWinRate', descending=True)
    )
    print(f'[I/O] | Succesfully calculated win rates. [{timer.stop_get_elapsed_reset():,.2f}s]')
    print(stats)

if __name__ == '__main__':
    analyze_replay_data()