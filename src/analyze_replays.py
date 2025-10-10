import sqlite3, src.config as config, polars as pl, questionary as q
from pathlib import Path
from prompt_toolkit.shortcuts import CompleteStyle
from src.utils import *
from src.enums import *

def _get_data_from_table(file_path, table, columns=['*']):
    with sqlite3.connect(file_path) as connection:
        return pl.read_database(f'select {', '.join(columns)} from {table}', connection)

def _calculate_raw_win_rate(replay_df: pl.DataFrame):
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
    return (
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

def analyze_replay_data(file_path: str):
    timer = Timer()

    timer.start()
    is_sql = Path(file_path).suffix == '.db'
    print('[I/O] | Attempting to get all replays from file.')
    if is_sql:
        replay_df = _get_data_from_table(file_path, config.Tables.ReplayData, ['p1_chara_id', 'p2_chara_id', 'winner'])
    else:
        replay_df = pl.read_csv(file_path, columns=['p1_chara_id', 'p2_chara_id', 'winner'])
    print(f'[I/O] | Succesfully got all replays from file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    timer.start()
    print('[I/O] | Attempting to calculate win rates.')
    stats = _calculate_raw_win_rate(replay_df)
    print(f'[I/O] | Succesfully calculated win rates. [{timer.stop_get_elapsed_reset():,.2f}s]')
    
    print(stats)