from enum import Enum

class Characters(Enum):
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
    God_of_Destruction_Top = 100

    @classmethod
    def _missing_(cls, value):
        return Ranks.God_of_Destruction

class BattleTypes(Enum):
    Quick_Match = 1
    Ranked_Match = 2
    Group_Match = 3
    Player_Match = 4