import csv, matplotlib.pyplot as plt, math, numpy as np
from tqdm import tqdm
from tkinter import filedialog as fd
from collections import defaultdict
from scipy.stats import gmean
from src.enums import Characters
from src.enums import BattleTypes
from src.enums import Ranks
from src.models import ReplayData
from src.models import SimplifiedReplayData

REPLAY_FILE_PATH = 'replay_data.csv'

def get_sorted_data(data, metric_func, value_func=None, reverse=True):
    sorted_data = sorted(data.items(), key=lambda item: metric_func(item[1]), reverse=reverse)
    names = [item[0] for item in sorted_data]
    values = [round(value_func(item[1]), 2) if value_func else round(metric_func(item[1]), 2) for item in sorted_data]
    return names, values

def wilson_score(wins, total_games, confidence=1.96):
    if total_games == 0:
        return 0
    
    p_hat = wins / total_games
    denominator = 1 + confidence**2 / total_games
    center_adjusted_probability = p_hat + confidence**2 / (2 * total_games)
    adjusted_standard_deviation = math.sqrt(
        (p_hat * (1 - p_hat) + confidence**2 / (4 * total_games)) / total_games
    )
    lower_bound = (center_adjusted_probability - confidence * adjusted_standard_deviation) / denominator
    return lower_bound * 100

def bayesian_score(mu, k, replay_data_dict):
    for key in replay_data_dict:
        character = replay_data_dict[key]
        w = character['wins']
        n = character['wins'] + character['losses']
        adjusted_win_rate = (w + k * mu) / (n + k)
        character['win_rate_bayesian'] = adjusted_win_rate * 100

def calculate_win_rates(replay_data_dict):
    win_rate_list = []
    play_count_list = []

    for key in replay_data_dict:
        character = replay_data_dict[key]

        wins, losses = character['wins'], character['losses']
        win_rate_list.append(wins / (wins + losses))
        play_count_list.append(wins + losses)

        character['win_rate'] = wins/ (wins + losses) * 100
        character['win_rate_wilson'] = wilson_score(wins, wins + losses)
    
    mu = sum(win_rate_list) / (len(win_rate_list) + 1)
    k = gmean(play_count_list)

    bayesian_score(mu, k, replay_data_dict)

def process_replay_data(replay_data: list[ReplayData]):
    simplified_replay_data: list[SimplifiedReplayData] = []
    while replay_data:
        replay: ReplayData = replay_data.pop()
        simplified_replay: SimplifiedReplayData = {
            "battle_at": replay["battle_at"],
            "battle_type": BattleTypes(replay["battle_type"]).name,
            "p1_character": Characters(replay["p1_chara_id"]).name,
            "p1_power": replay["p1_power"],
            "p1_rank": replay["p1_rank"],
            "p1_rank_name": Ranks(replay["p1_rank"]).name,
            "p2_character": Characters(replay["p2_chara_id"]).name,
            "p2_power": replay["p2_power"],
            "p2_rank": replay["p2_rank"],
            "p2_rank_name": Ranks(replay["p2_rank"]).name,
            "winner": replay["winner"]
        }
        simplified_replay_data.append(simplified_replay)
    return simplified_replay_data

def process_one_replay(replay: ReplayData) -> SimplifiedReplayData:
    return {
        "battle_at": replay["battle_at"],
        "battle_type": BattleTypes(int(replay["battle_type"])).name,
        "p1_character": Characters(int(replay["p1_chara_id"])).name,
        "p1_power": replay["p1_power"],
        "p1_rank": replay["p1_rank"],
        "p1_rank_name": Ranks(int(replay["p1_rank"])).name,
        "p2_character": Characters(int(replay["p2_chara_id"])).name,
        "p2_power": replay["p2_power"],
        "p2_rank": replay["p2_rank"],
        "p2_rank_name": Ranks(int(replay["p2_rank"])).name,
        "winner": replay["winner"]
    }

if __name__ == '__main__':
    replay_file = fd.askopenfilename(title='Select Replay Data File', filetypes=(('CSV Files', '*.csv'),))
    replay_data_dict = defaultdict(lambda: {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'win_rate_wilson': 0.0, 'win_rate_bayesian': 0.0})
    total_games = 0
    with open(replay_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in tqdm(reader, desc='Replays Analyzed', unit=' replays', mininterval=0.2):
            processed = process_one_replay(row) # type: ignore
            if processed['winner'] == '1':
                replay_data_dict[processed['p1_character']]['wins'] += 1
                replay_data_dict[processed['p2_character']]['losses'] += 1
            elif processed['winner'] == '2':
                replay_data_dict[processed['p2_character']]['wins'] += 1
                replay_data_dict[processed['p1_character']]['losses'] += 1
    
    calculate_win_rates(replay_data_dict)

    characters_win_rate, win_rate = get_sorted_data(
        replay_data_dict,
        lambda d: d['win_rate']
    )

    characters_play_count, play_count = get_sorted_data(
        replay_data_dict,
        lambda d: d['win_rate'],
        lambda d: d['wins'] + d['losses']
    )

    characters_win_rate_wilson, win_rate_wilson = get_sorted_data(
        replay_data_dict,
        lambda d: d['win_rate'],
        lambda d: d['win_rate_wilson']
    )

    characters_win_rate_bayesian, win_rate_bayesian = get_sorted_data(
        replay_data_dict,
        lambda d: d['win_rate'],#d['win_rate_bayesian']
        lambda d: d['win_rate_bayesian']
    )
    x = np.arange(len(characters_win_rate))
    width = 0.2

    fig, ax1 = plt.subplots(figsize=(20, 8))

    win_rate_bar = ax1.bar(x - 1.5 * width, win_rate, width, label='Win Rate', color='skyblue')
    win_rate_bayesian_bar = ax1.bar(x - 0.5 * width, win_rate_bayesian, width, label='Bayesian Adjusted Win Rate', color='orange')
    win_rate_wilson_bar = ax1.bar(x + 0.5 * width, win_rate_wilson, width, label='Wilson Score Interval Win Rate', color='green')

    ax2 = ax1.twinx()
    games_played_bar = ax2.bar(x + 1.5 * width, play_count, width, label='Games Played', color='orchid')

    ax1.set_ylabel('Win Rate')
    ax1.set_ylim(0, 100)
    ax2.set_ylabel('Games Played')
    ax2.set_ylim(0, max(play_count) * 1.2)

    ax1.set_title('Raw vs Bayesian Adjusted vs Wilson Score Interval Win Rates and Games Played by Character')
    ax1.set_xticks(x)
    ax1.set_xticklabels(characters_win_rate)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper left')

    for bars in [win_rate_bar + win_rate_bayesian_bar + win_rate_wilson_bar]:
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(
                f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom'
            )
    
    for bar in games_played_bar:
        height = bar.get_height()
        ax2.annotate(
            f'{int(height):,}', 
            xy=(bar.get_x() + bar.get_width()/2, height),
            xytext=(0, 3), textcoords="offset points",
            ha='center', va='bottom'
        )
    
    plt.tight_layout()
    plt.show()
    exit(0)

    plt.figure(figsize=(20, 8))
    bars = plt.bar(characters_win_rate, win_rate, width=0.3)
    plt.bar_label(bars)
    plt.title('Character Win Rates')
    plt.xlabel('Characters')
    plt.ylabel('Win Rates')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('win_rates.svg')

    plt.figure(figsize=(20, 8))
    bars = plt.bar(characters_play_count, play_count, width=0.3)
    plt.bar_label(bars, labels=[f'{v:,}' for v in play_count])
    plt.title('Character Play Rates')
    plt.xlabel('Characters')
    plt.ylabel('Play Rates')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('play_rates.svg')

    plt.figure(figsize=(20, 8))
    bars = plt.bar(characters_win_rate_wilson, win_rate_wilson, width=0.3)
    plt.bar_label(bars)
    plt.title('Character Win Rates (Wilson)')
    plt.xlabel('Characters')
    plt.ylabel('Win Rates (Wilson)')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('win_rates_wilson.svg')

    plt.figure(figsize=(20, 8))
    bars = plt.bar(characters_win_rate_bayesian, win_rate_bayesian, width=0.3)
    plt.bar_label(bars)
    plt.title('Character Win Rates (Bayesian)')
    plt.xlabel('Characters')
    plt.ylabel('Win Rates (Bayesian)')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig('win_rates_bayesian.svg')

    plt.show()