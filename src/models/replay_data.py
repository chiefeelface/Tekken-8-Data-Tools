"""
Data models for replay data structures.
"""

from typing import TypedDict, Optional


class ReplayData(TypedDict):
    """Raw replay data structure from the API."""
    battle_at: int
    battle_id: str
    battle_type: int
    game_version: int
    p1_area_id: Optional[int]
    p1_chara_id: int
    p1_lang: Optional[str]
    p1_name: str
    p1_polaris_id: str
    p1_power: int
    p1_rank: int
    p1_rating_before: Optional[int]
    p1_rating_change: Optional[int]
    p1_region_id: Optional[int]
    p1_rounds: int
    p1_user_id: int
    p2_area_id: Optional[int]
    p2_chara_id: int
    p2_lang: Optional[str]
    p2_name: str
    p2_polaris_id: str
    p2_power: int
    p2_rank: int
    p2_rating_before: Optional[int]
    p2_rating_change: Optional[int]
    p2_region_id: Optional[int]
    p2_rounds: int
    p2_user_id: int
    stage_id: int
    winner: int


class SimplifiedReplayData(TypedDict):
    """Simplified replay data for analysis."""
    battle_at: int
    battle_type: str
    p1_character: str
    p1_power: int
    p1_rank: int
    p1_rank_name: str
    p2_character: str
    p2_power: int
    p2_rank: int
    p2_rank_name: str
    winner: int
