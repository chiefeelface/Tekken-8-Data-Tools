"""
Core analyzer for Tekken replay data.
"""

import math
import csv
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gmean

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.replay_data import ReplayData, SimplifiedReplayData
from models.enums import Characters, BattleTypes, Ranks

logger = logging.getLogger(__name__)


class ReplayAnalyzer:
    """Analyzes Tekken replay data for statistics and insights."""
    
    def __init__(self):
        """Initialize the replay analyzer."""
        self.character_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'win_rate_wilson': 0.0, 'win_rate_bayesian': 0.0}
        )
    
    def process_replay_data(self, replay_data: List[ReplayData]) -> List[SimplifiedReplayData]:
        """Process raw replay data into simplified format.
        
        Args:
            replay_data: List of raw replay data.
            
        Returns:
            List of simplified replay data.
        """
        simplified_data = []
        
        for replay in replay_data:
            try:
                simplified = self._process_single_replay(replay)
                simplified_data.append(simplified)
            except Exception as e:
                logger.warning(f"Failed to process replay {replay.get('battle_id', 'unknown')}: {e}")
        
        return simplified_data
    
    def _process_single_replay(self, replay: ReplayData) -> SimplifiedReplayData:
        """Process a single replay into simplified format.
        
        Args:
            replay: Single replay data.
            
        Returns:
            Simplified replay data.
        """
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
    
    def calculate_character_statistics(self, replay_data: List[SimplifiedReplayData]) -> Dict[str, Dict[str, Any]]:
        """Calculate character win/loss statistics.
        
        Args:
            replay_data: List of simplified replay data.
            
        Returns:
            Dictionary of character statistics.
        """
        # Reset statistics
        self.character_stats = defaultdict(
            lambda: {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'win_rate_wilson': 0.0, 'win_rate_bayesian': 0.0}
        )
        
        # Count wins and losses
        for replay in replay_data:
            p1_char = replay['p1_character']
            p2_char = replay['p2_character']
            winner = replay['winner']
            
            if winner == 1:
                self.character_stats[p1_char]['wins'] += 1
                self.character_stats[p2_char]['losses'] += 1
            elif winner == 2:
                self.character_stats[p2_char]['wins'] += 1
                self.character_stats[p1_char]['losses'] += 1
        
        # Calculate win rates
        self._calculate_win_rates()
        
        return dict(self.character_stats)
    
    def _calculate_win_rates(self) -> None:
        """Calculate various win rate metrics."""
        win_rate_list = []
        play_count_list = []
        
        for character, stats in self.character_stats.items():
            wins = stats['wins']
            losses = stats['losses']
            total_games = wins + losses
            
            if total_games > 0:
                win_rate = wins / total_games
                win_rate_list.append(win_rate)
                play_count_list.append(total_games)
                
                stats['win_rate'] = win_rate * 100
                stats['win_rate_wilson'] = self._wilson_score(wins, total_games)
        
        # Calculate Bayesian adjusted win rates
        if win_rate_list and play_count_list:
            mu = sum(win_rate_list) / len(win_rate_list)
            k = gmean(play_count_list)
            self._bayesian_score(mu, k)
    
    def _wilson_score(self, wins: int, total_games: int, confidence: float = 1.96) -> float:
        """Calculate Wilson score interval for win rate.
        
        Args:
            wins: Number of wins.
            total_games: Total number of games.
            confidence: Confidence level.
            
        Returns:
            Wilson score interval.
        """
        if total_games == 0:
            return 0.0
        
        p_hat = wins / total_games
        denominator = 1 + confidence**2 / total_games
        center_adjusted_probability = p_hat + confidence**2 / (2 * total_games)
        adjusted_standard_deviation = math.sqrt(
            (p_hat * (1 - p_hat) + confidence**2 / (4 * total_games)) / total_games
        )
        lower_bound = (center_adjusted_probability - confidence * adjusted_standard_deviation) / denominator
        return lower_bound * 100
    
    def _bayesian_score(self, mu: float, k: float) -> None:
        """Calculate Bayesian adjusted win rates.
        
        Args:
            mu: Prior mean win rate.
            k: Prior strength.
        """
        for character, stats in self.character_stats.items():
            wins = stats['wins']
            total_games = wins + stats['losses']
            
            if total_games > 0:
                adjusted_win_rate = (wins + k * mu) / (total_games + k)
                stats['win_rate_bayesian'] = adjusted_win_rate * 100
    
    def get_sorted_data(
        self, 
        data: Dict[str, Dict[str, Any]], 
        metric_func: callable, 
        value_func: Optional[callable] = None, 
        reverse: bool = True
    ) -> Tuple[List[str], List[float]]:
        """Sort data by a metric function.
        
        Args:
            data: Dictionary of data to sort.
            metric_func: Function to extract metric for sorting.
            value_func: Function to extract value for display.
            reverse: Whether to sort in descending order.
            
        Returns:
            Tuple of (names, values) sorted by metric.
        """
        sorted_data = sorted(data.items(), key=lambda item: metric_func(item[1]), reverse=reverse)
        names = [item[0] for item in sorted_data]
        values = [
            round(value_func(item[1]), 2) if value_func else round(metric_func(item[1]), 2) 
            for item in sorted_data
        ]
        return names, values
    
    def create_win_rate_chart(
        self, 
        character_stats: Dict[str, Dict[str, Any]], 
        output_path: Optional[str] = None
    ) -> None:
        """Create a comprehensive win rate chart.
        
        Args:
            character_stats: Character statistics data.
            output_path: Path to save the chart.
        """
        # Get sorted data
        characters_win_rate, win_rate = self.get_sorted_data(
            character_stats, lambda d: d['win_rate']
        )
        
        characters_play_count, play_count = self.get_sorted_data(
            character_stats, lambda d: d['win_rate'], lambda d: d['wins'] + d['losses']
        )
        
        characters_win_rate_wilson, win_rate_wilson = self.get_sorted_data(
            character_stats, lambda d: d['win_rate'], lambda d: d['win_rate_wilson']
        )
        
        characters_win_rate_bayesian, win_rate_bayesian = self.get_sorted_data(
            character_stats, lambda d: d['win_rate'], lambda d: d['win_rate_bayesian']
        )
        
        # Create the chart
        x = np.arange(len(characters_win_rate))
        width = 0.2
        
        fig, ax1 = plt.subplots(figsize=(20, 8))
        
        # Win rate bars
        win_rate_bar = ax1.bar(x - 1.5 * width, win_rate, width, label='Win Rate', color='skyblue')
        win_rate_bayesian_bar = ax1.bar(x - 0.5 * width, win_rate_bayesian, width, label='Bayesian Adjusted Win Rate', color='orange')
        win_rate_wilson_bar = ax1.bar(x + 0.5 * width, win_rate_wilson, width, label='Wilson Score Interval Win Rate', color='green')
        
        # Games played (secondary axis)
        ax2 = ax1.twinx()
        games_played_bar = ax2.bar(x + 1.5 * width, play_count, width, label='Games Played', color='orchid')
        
        # Formatting
        ax1.set_ylabel('Win Rate (%)')
        ax1.set_ylim(0, 100)
        ax2.set_ylabel('Games Played')
        ax2.set_ylim(0, max(play_count) * 1.2)
        
        ax1.set_title('Character Win Rates Analysis')
        ax1.set_xticks(x)
        ax1.set_xticklabels(characters_win_rate, rotation=45, ha='right')
        
        # Legend
        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper left')
        
        # Add value labels
        for bars in [win_rate_bar, win_rate_bayesian_bar, win_rate_wilson_bar]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(
                    f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=8
                )
        
        for bar in games_played_bar:
            height = bar.get_height()
            ax2.annotate(
                f'{int(height):,}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), 
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=8
            )
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {output_path}")
        else:
            plt.show()
    
    def load_replay_data_from_csv(self, file_path: str) -> List[SimplifiedReplayData]:
        """Load replay data from a CSV file.
        
        Args:
            file_path: Path to the CSV file.
            
        Returns:
            List of simplified replay data.
        """
        replay_data = []
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert string values to appropriate types
                    processed_row = {
                        'battle_at': int(row['battle_at']),
                        'battle_type': row['battle_type'],
                        'p1_character': row['p1_character'],
                        'p1_power': int(row['p1_power']),
                        'p1_rank': int(row['p1_rank']),
                        'p1_rank_name': row['p1_rank_name'],
                        'p2_character': row['p2_character'],
                        'p2_power': int(row['p2_power']),
                        'p2_rank': int(row['p2_rank']),
                        'p2_rank_name': row['p2_rank_name'],
                        'winner': int(row['winner'])
                    }
                    replay_data.append(processed_row)
            
            logger.info(f"Loaded {len(replay_data)} replay records from {file_path}")
            return replay_data
            
        except Exception as e:
            logger.error(f"Failed to load replay data from {file_path}: {e}")
            raise
