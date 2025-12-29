import sqlite3, src.config as config, polars as pl, src.utils.logger as logger
from pathlib import Path
from src.utils.timer import Timer
from src.enums import *

def _get_data_from_table(file_path, table, columns=['*']):
    with sqlite3.connect(file_path) as connection:
        return pl.read_database(f'select {', '.join(columns)} from {table}', connection)

def _calculate_character_win_rate(replay_df: pl.DataFrame):
    chara_lookup = pl.DataFrame({
        'chara_id': [chara.value for chara in Characters],
        'chara_name': [chara.name.replace('_', ' ') for chara in Characters]
    })
    characters_df = (
        replay_df
        .join(chara_lookup.rename({"chara_id": "p1_chara_id", "chara_name": "p1_chara"}), on="p1_chara_id", how="left")
        .join(chara_lookup.rename({"chara_id": "p2_chara_id", "chara_name": "p2_chara"}), on="p2_chara_id", how="left")
    )
    characters_df = characters_df.with_columns([
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
        pl
        .when(pl.col('winner') == 3)
        .then(pl.col('p1_chara'))
        .otherwise(None)
        .alias('Tie1'),
        pl
        .when(pl.col('winner') == 3)
        .then(pl.col('p2_chara'))
        .otherwise(None)
        .alias('Tie2')
    ])
    wins = (
        characters_df
        .group_by('Winner')
        .agg(pl.count().alias('Wins'))
        .rename({'Winner': 'Character'})
        .select('Character', 'Wins')
    )
    losses = (
        characters_df
        .group_by('Loser')
        .agg(pl.count().alias('Losses'))
        .rename({'Loser': 'Character'})
        .select('Character', 'Losses')
    )
    ties = (
        characters_df
        .select(['Tie1', 'Tie2'])
        .unpivot(variable_name='Slot', value_name='Character')
        .drop_nulls()
        .group_by('Character')
        .agg(pl.count().alias('Ties'))
        .select('Character', 'Ties')
    )
    picks = (
        wins
        .join(losses, on='Character', how='inner', coalesce=True)
        .join(ties, on='Character', how='full', coalesce=True)
    )
    total_picks = picks.select(pl.col('Wins') + pl.col('Losses') + pl.col('Ties')).sum().to_series(0)[0]

    stats = (
        wins
        .join(losses, on='Character', how='full', coalesce=True)
        .join(ties, on='Character', how='full', coalesce=True)
        .join(picks, on='Character', how='full', coalesce=True)
        .fill_null(0)
        .with_columns([
            (pl.col('Wins') + pl.col('Losses') + pl.col('Ties')).alias('TotalGames'),
            (pl.col('Wins') / (pl.col('Wins') + pl.col('Losses'))).alias('RawWinRate'),
            ((pl.col('Wins') + pl.col('Losses') + pl.col('Ties')) / total_picks).alias('PickRate')
        ])
    )

    return stats.select(
        'Character',
        'Wins',
        'Losses',
        'Ties',
        'TotalGames',
        'RawWinRate',
        'PickRate'
    ).sort('RawWinRate', descending=True)

def _get_unique_players_stats(replay_df: pl.DataFrame):
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
        ]),
        "IsTie": pl.concat([
            ((replay_df["winner"].is_null()) | (replay_df["winner"] == 3)).cast(pl.Int8),
            ((replay_df["winner"].is_null()) | (replay_df["winner"] == 3)).cast(pl.Int8)
        ]),
    })

    # Step 2: Get the most recent player name per player
    latest_player_info = (
        players_df
        .sort('battle_at', descending=True)
        .group_by('PolarisId')
        .agg([
            pl.first('PlayerName'),
            #pl.first('Rank').alias('MostRecentRank')
        ])
    )

    # Step 3: Aggregate stats per player
    stats = (
        players_df
        .group_by('PolarisId')
        .agg([
            pl.count().alias('TotalGames'),
            pl.sum('IsWin').cast(pl.Int64).alias('Wins'),
            (pl.count() - pl.sum('IsWin') - pl.sum('IsTie')).cast(pl.Int64).alias('Losses'),
            pl.sum('IsTie').cast(pl.Int64).alias('Ties'),
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
        .join(latest_player_info, on='PolarisId', how='left')
        .join(most_played_chara, on='PolarisId', how='left')
        .with_columns([
            pl.col('WinRate'),
            pl.col('MostPlayedChara').cast(pl.Utf8).replace(chara_id_to_name).alias('MostPlayedChara'),
            pl.col('HighestRank').cast(pl.Utf8).replace(rank_id_to_name).alias('HighestRankName'),
            pl.col('MedianRank').cast(pl.Utf8).replace(rank_id_to_name).alias('MedianRankName'),
            pl.col('ModeRank').cast(pl.Utf8).replace(rank_id_to_name).alias('ModeRankName'),
        ])
    )

    return player_stats.select([
        'PolarisId',
        'PlayerName',
        'Wins',
        'Losses',
        'Ties',
        'TotalGames',
        'WinRate',
        'HighestRank', 'HighestRankName',
        'MedianRank', 'MedianRankName',
        'ModeRank', 'ModeRankName',
        'MostPlayedChara',
        'MostPlayedCharaGames',
    ]).sort('TotalGames', descending=True)

def _get_rank_percentiles_and_distribution(player_stats_df: pl.DataFrame):
    rank_counts = player_stats_df.group_by(['ModeRank', 'ModeRankName']).agg(
        [pl.count().alias('Players')]
    ).sort('ModeRank')
    total_players = player_stats_df.height
    rank_distribution = rank_counts.with_columns(
        (pl.col('Players') / total_players).alias('ModeRankDistribution')
    )
    rank_percentiles = rank_counts.with_columns(
        pl.col('Players').cum_sum().shift().fill_null(0).alias('CumulativePlayers')
    )
    rank_percentiles = rank_percentiles.with_columns(
        (pl.col('CumulativePlayers') / total_players).alias('ModeRankPercentile')
    )
    return rank_percentiles.join(rank_distribution, 'ModeRank').select([
        'ModeRank',
        'ModeRankName',
        'ModeRankPercentile',
        'ModeRankDistribution',
        'Players'
    ])

def _calculate_character_win_rate_by_rank(replay_df: pl.DataFrame):
    # Split all matches into 2 rows, one for winner and one for loser
    # The columns should be chara, rank, winner
    chara_lookup = pl.DataFrame({
        'chara_id': [chara.value for chara in Characters],
        'chara_name': [chara.name.replace('_', ' ') for chara in Characters]
    })
    rank_id_to_name = {rank.value: rank.name.replace('_', ' ') for rank in Ranks}
    characters_df = (
        replay_df
        .join(chara_lookup.rename({"chara_id": "p1_chara_id", "chara_name": "p1_chara"}), on="p1_chara_id", how="left")
        .join(chara_lookup.rename({"chara_id": "p2_chara_id", "chara_name": "p2_chara"}), on="p2_chara_id", how="left")
    )
    # The selects here treat ties as losses, so not quite accurate but should be fine
    characters_df = (
        pl.concat([
            characters_df.select([
                pl.col('p1_chara').alias('Character'),
                pl.col('p1_rank').alias('Rank'),
                pl.when(pl.col('winner') == 1).then(pl.lit('win'))
                  .when(pl.col('winner') == 3).then(pl.lit('tie'))
                  .otherwise(pl.lit('loss'))
                .alias('Outcome')
            ]),
            characters_df.select([
                pl.col('p2_chara').alias('Character'),
                pl.col('p2_rank').alias('Rank'),
                pl.when(pl.col('winner') == 2).then(pl.lit('win'))
                  .when(pl.col('winner') == 3).then(pl.lit('tie'))
                  .otherwise(pl.lit('loss'))
                .alias('Outcome')
            ])
        ])
        .group_by(['Character', 'Rank'])
        .agg([
            (pl.col('Outcome') == 'win').sum().alias('Wins'),
            (pl.col('Outcome') == 'loss').sum().alias('Losses'),
            (pl.col('Outcome') == 'tie').sum().alias('Ties'),
            pl.len().alias('TotalGames')
        ])
        .with_columns(
            (pl.col('Wins') / (pl.col('Wins') + pl.col('Losses'))).alias('RawWinRate')
        )
    )
    return dict(sorted({
        rank[0]: (
            df
            .sort('RawWinRate', descending=True)
            .drop('Rank')
        )
        for rank, df in characters_df.partition_by(
            'Rank',
            as_dict=True,
            maintain_order=True
        ).items()
    }.items()))

def analyze_replay_data(file_path: str):
    timer = Timer()

    # Get replay data
    timer.start()
    is_sql = Path(file_path).suffix == '.db'
    logger.io('Attempting to get game stats from file')
    if is_sql:
        replay_df = _get_data_from_table(file_path, config.Tables.ReplayData, ['battle_at', 'p1_polaris_id', 'p1_chara_id', 'p1_name', 'p1_rank', 'p2_polaris_id', 'p2_chara_id', 'p2_name', 'p2_rank', 'winner'])
    else:
        replay_df = pl.read_csv(file_path, columns=['battle_at', 'p1_polaris_id', 'p1_chara_id', 'p1_name', 'p1_rank', 'p2_polaris_id', 'p2_chara_id', 'p2_name', 'p2_rank', 'winner'])
    logger.io('Succesfully got all game stats from file', timer.stop_get_elapsed_reset())

    timer.start()
    logger.io('Attempting to calculate win rates')
    win_rates = _calculate_character_win_rate(replay_df)
    logger.io('Succesfully calculated win rates', timer.stop_get_elapsed_reset())
    print(win_rates)

    timer.start()
    logger.io('Attempting to consolidate player stats')
    player_stats = _get_unique_players_stats(replay_df)
    logger.io('Succesfully consolidated player stats', timer.stop_get_elapsed_reset())
    print(player_stats)

    timer.start()
    logger.io('Attempting to calculate rank percentiles and distribution')
    rank_percentiles_and_distribution = _get_rank_percentiles_and_distribution(player_stats)
    logger.io('Succesfully calculated rank percentiles and distribution', timer.stop_get_elapsed_reset())
    print(rank_percentiles_and_distribution)

    timer.start()
    logger.io('Attempting to calculate win rates by rank')
    win_rates_by_rank = _calculate_character_win_rate_by_rank(replay_df)
    logger.io('Succesfully calculated win rates by rank', timer.stop_get_elapsed_reset())

    return win_rates, player_stats, rank_percentiles_and_distribution, win_rates_by_rank