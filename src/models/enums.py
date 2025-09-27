"""
Enum definitions for Tekken game data.
"""

from enum import Enum


class Characters(Enum):
    """Tekken 8 character IDs."""
    Paul = 0
    Law = 1
    King = 2
    Yoshimitsu = 3
    Hwoarang = 4
    Xiaoyu = 5
    Jin = 6
    Bryan = 7
    Kazuya = 8
    Steve = 9
    Jack_8 = 10
    Asuka = 11
    Devil_Jin = 12
    Feng = 13
    Lili = 14
    Dragunov = 15
    Leo = 16
    Lars = 17
    Alisa = 18
    Claudio = 19
    Shaheen = 20
    Nina = 21
    Lee = 22
    Kuma = 23
    Panda = 24
    Zafina = 28
    Leroy = 29
    Jun = 32
    Reina = 33
    Azucena = 34
    Victor = 35
    Raven = 36
    Eddy = 38
    Lidia = 39
    Heihachi = 40
    Clive = 41
    Anna = 42
    Fahkumram = 43


class Ranks(Enum):
    """Tekken 8 rank system."""
    Beginner = 0
    First_Dan = 1
    Second_Dan = 2
    Fighter = 3
    Strategist = 4
    Combatant = 5
    Brawler = 6
    Ranger = 7
    Cavalry = 8
    Warrior = 9
    Assailant = 10
    Dominator = 11
    Vanquisher = 12
    Destroyer = 13
    Eliminator = 14
    Garyu = 15
    Shinryu = 16
    Tenryu = 17
    Mighty_Ruler = 18
    Flame_Ruler = 19
    Battle_Ruler = 20
    Fujin = 21
    Raijin = 22
    Kishin = 23
    Bushin = 24
    Tekken_King = 25
    Tekken_Emperor = 26
    Tekken_God = 27
    Tekken_God_Supreme = 28
    God_of_Destruction = 29
    God_of_Destruction_1 = 30
    God_of_Destruction_2 = 31
    God_of_Destruction_3 = 32
    God_of_Destruction_4 = 33
    God_of_Destruction_5 = 34
    God_of_Destruction_6 = 35
    God_of_Destruction_7 = 36
    God_of_Destruction_Infinity = 1000

    @classmethod
    def _missing_(cls, value):
        """Handle unknown rank values (likely GoD∞)."""
        return Ranks.God_of_Destruction_Infinity


class BattleTypes(Enum):
    """Types of battles/matches."""
    Quick_Match = 1
    Ranked_Match = 2
    Group_Match = 3
    Player_Match = 4


class Regions(Enum):
    """Geographic regions."""
    Asia = 0
    Middle_East = 1
    Oceania = 2
    America = 3
    Europe = 4
    Africa = 5


class Platforms(Enum):
    """Gaming platforms."""
    PC = 3
    PlayStation = 8
    Xbox = 9


class Stages(Enum):
    """Tekken 8 stages."""
    Arena = 100
    Arena_Underground = 101
    Urban_Square = 200
    Urban_Square_Evening = 201
    Yakushima = 300
    Coliseum_of_Fate = 400
    Rebel_Hangar = 500
    Fallen_Destiny = 700
    Descent_Into_Subconscious = 900
    Sanctum = 1000
    Into_the_Stratosphere = 1100
    Ortiz_Farm = 1200
    Celebration_On_The_Seine = 1300
    Secluded_Training_Ground = 1400
    Elegant_Palace = 1500
    Midnight_Siege = 1600
