import numpy as np
from itertools import combinations_with_replacement, product

die_spots = range(1,7)

categories = {'Ones', 'Twos', 'Threes', 'Fours', 'Fives', 'Sixes', 
        'Three of a kind', 'Four of a kind', 'Full house', 'Small straight',
        'Large straight', 'Yahtzee', 'Chance'}

upper_categories = {'Ones': 1, 'Twos': 2, 'Threes': 3, 'Fours': 4, 
        'Fives': 5, 'Sixes': 6}

straights = {'Small straight': [range(1,5), range(2,6), range(3,7)],
        'Large straight': [range(1,6), range(2,7)]}

# To simplify things, (and I suppose to minimise storage), each game state will
# be single integer with at most 19 bits. The least significant 13 bits
# correspond to the categories being open, with the least significant
# corresponding to 'Ones', and the next 6 corresond to the upper section score,
# with the integer 63 representing all numbers 63+.

def upper_score(state):
    return state >> 13

def fill_cat(state, cat_code):
    return state | 1 << cat_code

class DiceRoll():

    def __init__(self, pips):
        self.pips = pips.sorted()
        self.scores = {cat: self.score_as(cat) for cat in categories.keys}
        self.upper = {cat: self.upper_score(cat) for cat in categories.keys}

    def score_as(self, cat):
        if cat is in upper_categories:
            return sum([x for x in self.pips if x == upper_categories[cat]])
        else if cat == 'Three of a kind':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) >= 3:
                return sum(self.pips)
            else:
                return 0
        else if cat == 'Four of a kind':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) >= 4:
                return sum(self.pips)
            else:
                return 0
        else if cat == 'Full house':
            counts = [self.pips.count(x) for x in die_spots].sorted()
            if counts[3] == 2 and counts[4] == 3:
                return 25
            else:
                return 0
        else if cat is in straights:
            if [[x is in self.pips for x in strt].all() 
                    for strt in straights[cat]].any():
                return 30
            else:
                return 0
        else if cat == 'Yahtzee':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) == 5:
                return sum(self.pips)
            else:
                return 0
        else if cat == 'Chance':
            return sum(self.pips)


    def upper_score(self, cat):
        if cat is in upper_categories:
            return sum([x for x in self.pips if x == upper_categories[cat]])
        else:
            return 0

def roll_lookup():
    """
    Returns a dictionary to resolve a tuple of pips to a corresonding DiceRoll
    object, to that only 252 DiceRoll objects ever need to be evaluated.
    """
    rolls = {}
    for roll in combinations_with_replacement(die_spots, 5):
        rolls[roll] = DiceRoll(roll)
    for roll in product(die_spots, repeat=5):
        rolls[roll] = rolls[roll.sorted()]
    return rolls

def propagation_tensor():