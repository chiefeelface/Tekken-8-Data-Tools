"""
Tests for the replay analyzer.
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd

from src.core.analyzer import ReplayAnalyzer
from src.models.replay_data import ReplayData, SimplifiedReplayData


class TestReplayAnalyzer(unittest.TestCase):
    """Test cases for ReplayAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ReplayAnalyzer()
        
        # Sample replay data
        self.sample_replay = ReplayData(
            battle_at=1640995200,
            battle_id="test_battle_1",
            battle_type=2,
            game_version=1,
            p1_area_id=1,
            p1_chara_id=6,  # Jin
            p1_lang="en",
            p1_name="Player1",
            p1_polaris_id="p1_123",
            p1_power=1000,
            p1_rank=15,
            p1_rating_before=1000,
            p1_rating_change=10,
            p1_region_id=3,
            p1_rounds=2,
            p1_user_id=12345,
            p2_area_id=1,
            p2_chara_id=8,  # Kazuya
            p2_lang="en",
            p2_name="Player2",
            p2_polaris_id="p2_456",
            p2_power=950,
            p2_rank=14,
            p2_rating_before=950,
            p2_rating_change=-10,
            p2_region_id=3,
            p2_rounds=1,
            p2_user_id=67890,
            stage_id=100,
            winner=1
        )
    
    def test_process_single_replay(self):
        """Test processing a single replay."""
        result = self.analyzer._process_single_replay(self.sample_replay)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['p1_character'], 'Jin')
        self.assertEqual(result['p2_character'], 'Kazuya')
        self.assertEqual(result['winner'], 1)
    
    def test_calculate_character_statistics(self):
        """Test character statistics calculation."""
        # Create sample data
        sample_data = [
            SimplifiedReplayData(
                battle_at=1640995200,
                battle_type="Ranked_Match",
                p1_character="Jin",
                p1_power=1000,
                p1_rank=15,
                p1_rank_name="Garyu",
                p2_character="Kazuya",
                p2_power=950,
                p2_rank=14,
                p2_rank_name="Shinryu",
                winner=1
            ),
            SimplifiedReplayData(
                battle_at=1640995300,
                battle_type="Ranked_Match",
                p1_character="Kazuya",
                p1_power=950,
                p1_rank=14,
                p1_rank_name="Shinryu",
                p2_character="Jin",
                p2_power=1000,
                p2_rank=15,
                p2_rank_name="Garyu",
                winner=2
            )
        ]
        
        stats = self.analyzer.calculate_character_statistics(sample_data)
        
        # Jin: 1 win, 1 loss
        self.assertEqual(stats['Jin']['wins'], 1)
        self.assertEqual(stats['Jin']['losses'], 1)
        
        # Kazuya: 1 win, 1 loss
        self.assertEqual(stats['Kazuya']['wins'], 1)
        self.assertEqual(stats['Kazuya']['losses'], 1)
    
    def test_wilson_score(self):
        """Test Wilson score calculation."""
        # Test with 0 games
        score = self.analyzer._wilson_score(0, 0)
        self.assertEqual(score, 0.0)
        
        # Test with some games
        score = self.analyzer._wilson_score(10, 20)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)
    
    def test_get_sorted_data(self):
        """Test data sorting functionality."""
        test_data = {
            'Character1': {'wins': 10, 'losses': 5},
            'Character2': {'wins': 15, 'losses': 3},
            'Character3': {'wins': 8, 'losses': 7}
        }
        
        names, values = self.analyzer.get_sorted_data(
            test_data, 
            lambda d: d['wins'], 
            lambda d: d['wins']
        )
        
        self.assertEqual(names[0], 'Character2')  # Highest wins
        self.assertEqual(values[0], 15)


if __name__ == '__main__':
    unittest.main()
