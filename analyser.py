import numpy as np
from itertools import combinations_with_replacement, product

die_spots = range(1,7)

categories = ['Ones', 'Twos', 'Threes', 'Fours', 'Fives', 'Sixes', 
        'Three of a kind', 'Four of a kind', 'Full house', 'Small straight',
        'Large straight', 'Yahtzee', 'Chance']

upper_categories = {'Ones': 1, 'Twos': 2, 'Threes': 3, 'Fours': 4, 
        'Fives': 5, 'Sixes': 6}

small_straights = {range(1,5), range(2,6), range(3,7)}
large_straights = {range(1,6), range(2,7)}

# To simplify things, (and I suppose to minimise storage), each game state will
# be single integer with at most 19 bits. The least significant 13 bits
# correspond to the categories being open, with the least significant
# corresponding to 'Ones', and the next 6 corresond to the upper section score,
# with the integer 63 representing all numbers 63+.

def upper_score(state):
    return state >> 13

def open_cats(state):
    return state & 0x1FFF

class DiceRoll():

    def __init__(self, pips):
        self.pips = tuple(sorted(list(pips)))
        self.scores = {cat: self.score_as(cat) for cat in categories}
        self.upper = {cat: self.upper_score(cat) for cat in categories}

    def best_score(self, state, forward_scores):
        """
        Choose the best category in which to score this roll, taking into
        account the state and the potential for future scores. Return the
        optimal score.
        """
        best = 0
        for i, cat in enumerate(categories):
            if state >> i & 1:
                upper_total = upper_score(state) + self.upper[cat]
                new_upper = min(upper_total, 63)
                new_open = (open_cats(state) & ~(1 << i)) & 0x1FFF
                new_state = new_upper << 13 | new_open
                forward = forward_scores[new_state]
                if upper_total >= 63:
                    upper_bonus = 35
                else:
                    upper_bonus = 0
                present = upper_bonus + self.scores[cat]
                if forward + present > best:
                    best = forward + present
        return best

    def score_as(self, cat):
        if cat in upper_categories:
            return sum([x for x in self.pips if x == upper_categories[cat]])
        elif cat == 'Three of a kind':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) >= 3:
                return sum(self.pips)
            else:
                return 0
        elif cat == 'Four of a kind':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) >= 4:
                return sum(self.pips)
            else:
                return 0
        elif cat == 'Full house':
            counts = sorted([self.pips.count(x) for x in die_spots])
            if counts[-1] == 3 and counts[-2] == 2:
                return 25
            else:
                return 0
        elif cat == 'Small straight':
            if any([all([x in self.pips for x in strt]) 
                    for strt in small_straights]):
                return 30
            else:
                return 0
        elif cat == 'Large straight':
            if any([all([x in self.pips for x in strt]) 
                    for strt in large_straights]):
                return 40
            else:
                return 0
        elif cat == 'Yahtzee':
            counts = [self.pips.count(x) for x in die_spots]
            if max(counts) == 5:
                return 50
            else:
                return 0
        elif cat == 'Chance':
            return sum(self.pips)

    def upper_score(self, cat):
        if cat in upper_categories:
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
        rolls[roll] = rolls[sorted(roll)]
    return rolls

