import sqlite3, src.config as config, polars as pl, xlsxwriter
from pathlib import Path
from src.utils.timer import Timer
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
        .drop('Character_right') # Need this since a duplicate Character column is made when aggregating winners and losers
        .fill_null(0)
        .with_columns([
            pl.col('Wins'),
            pl.col('Losses'),
            (pl.col('Wins') + pl.col('Losses')).alias('TotalGames'),
            (pl.col('Wins') / (pl.col('Wins') + pl.col('Losses'))).alias('RawWinRate')
        ])
        .sort('RawWinRate', descending=True)
    )

def _get_unique_players(replay_df: pl.DataFrame):
    # Data to get from players:
    # wins, losses, total games, most played character, most played character games, win rate, highest rank, average rank
    # Step 1: Normalize players into one row per player per match
    players_df = pl.DataFrame({
        "battle_at": pl.concat([replay_df["battle_at"]] * 2),
        "PolarisId": pl.concat([replay_df["p1_polaris_id"], replay_df["p2_polaris_id"]]),
        "PlayerName": pl.concat([replay_df["p1_name"], replay_df["p2_name"]]),
        "CharaId": pl.concat([replay_df["p1_chara_id"], replay_df["p2_chara_id"]]),
        "Rank": pl.concat([replay_df["p1_rank"], replay_df["p2_rank"]]),
        "IsWin": pl.concat([
            (replay_df["winner"] == 1).cast(pl.Int8),
            (replay_df["winner"] == 2).cast(pl.Int8)
        ])
    })

    # Step 2: Get the most recent player name per player
    latest_names = (
        players_df
        .sort('battle_at', descending=True)
        .group_by('PolarisId')
        .agg([pl.first('PlayerName')])
    )

    # Step 3: Aggregate stats per player
    stats = (
        players_df
        .group_by('PolarisId')
        .agg([
            pl.count().alias('TotalGames'),
            pl.sum('IsWin').cast(pl.Int64).alias('Wins'),
            (pl.count() - pl.sum('IsWin')).cast(pl.Int64).alias('Losses'),
            (pl.mean('IsWin')).alias('WinRate'),
            pl.max('Rank').alias('HighestRank'),
            pl.col('Rank').median().cast(pl.Int64).alias('MedianRank'),
            pl.col('Rank').mode().first().alias('ModeRank')
        ])
    )

    # Step 4: Most played character per player (with count)
    chara_counts = (
        players_df
        .group_by(['PolarisId', 'CharaId'])
        .agg(pl.count().alias('GamesPlayed'))
    )

    # Get top character per player
    most_played_chara = (
        chara_counts
        .sort(['PolarisId', 'GamesPlayed'], descending=[False, True])
        .unique(subset='PolarisId', keep='first')
        .select(['PolarisId', 'CharaId', 'GamesPlayed'])
        .rename({'CharaId': 'MostPlayedChara', 'GamesPlayed': 'MostPlayedCharaGames'})
    )

    chara_id_to_name = {chara.value: chara.name.replace('_', ' ') for chara in Characters}
    rank_id_to_name = {rank.value: rank.name.replace('_', ' ') for rank in Ranks}

    # Step 5: Join all results together
    player_stats = (
        stats
        .join(latest_names, on='PolarisId', how='left')
        .join(most_played_chara, on='PolarisId', how='left')
        .with_columns([
            pl.col('WinRate'),
            pl.col('MostPlayedChara').cast(pl.Utf8).replace(chara_id_to_name).alias('MostPlayedChara'),
            pl.col('HighestRank').cast(pl.Utf8).replace(rank_id_to_name).alias('HighestRankName'),
            pl.col('MedianRank').cast(pl.Utf8).replace(rank_id_to_name).alias('MedianRankName'),
            pl.col('ModeRank').cast(pl.Utf8).replace(rank_id_to_name).alias('ModeRankName')
        ])
    )

    return player_stats.select([
        'PolarisId',
        'PlayerName',
        'Wins',
        'Losses',
        'TotalGames',
        'WinRate',
        'HighestRank', 'HighestRankName',
        'MedianRank', 'MedianRankName',
        'ModeRank', 'ModeRankName',
        'MostPlayedChara',
        'MostPlayedCharaGames',
    ])

def analyze_replay_data(file_path: str):
    timer = Timer()

    # Get replay data
    timer.start()
    is_sql = Path(file_path).suffix == '.db'
    print('[I/O] | Attempting to get game stats from file.')
    if is_sql:
        replay_df = _get_data_from_table(file_path, config.Tables.ReplayData, ['p1_chara_id', 'p2_chara_id', 'winner'])
    else:
        replay_df = pl.read_csv(file_path, columns=['p1_chara_id', 'p2_chara_id', 'winner'])
    print(f'[I/O] | Succesfully got all game stats from file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    # Get win rates
    timer.start()
    print('[I/O] | Attempting to calculate win rates.')
    stats = _calculate_raw_win_rate(replay_df)
    # Free up memory
    del replay_df
    print(f'[I/O] | Succesfully calculated win rates. [{timer.stop_get_elapsed_reset():,.2f}s]')
    print(stats)

    timer.start()
    # FIXME: No need to do this twice, get all this stuff in the first read from file
    print('[I/O] | Attempting to get all player stats from file.')
    if is_sql:
        replay_df = _get_data_from_table(file_path, config.Tables.ReplayData, ['battle_at', 'p1_polaris_id', 'p1_chara_id', 'p1_name', 'p2_polaris_id', 'p2_chara_id', 'p2_name', 'winner'])
    else:
        replay_df = pl.read_csv(file_path, columns=['battle_at', 'p1_polaris_id', 'p1_chara_id', 'p1_name', 'p1_rank', 'p2_polaris_id', 'p2_chara_id', 'p2_name', 'p2_rank', 'winner'])
    print(f'[I/O] | Succesfully got all player stats from file. [{timer.stop_get_elapsed_reset():,.2f}s]')

    timer.start()
    print('[I/O] | Attempting to consolidate player stats.')
    player_stats = _get_unique_players(replay_df)
    del replay_df
    print(f'[I/O] | Succesfully consolidated player stats. [{timer.stop_get_elapsed_reset():,.2f}s]')
    print(player_stats)

    return stats, player_stats