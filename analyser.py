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
        self.pips = tuple(sorted(pips))
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

def multinomial(lst):
    """
    Multinomial coefficient function. Copied from stackexchange - thanks Reiner
    Martin!
    """
    res, i = 1, 1
    for a in lst:
        for j in range(1,a+1):
            res *= i
            res //= j
            i += 1
    return res

def transition_probability(hold, R, S):
    """
    Compute the probability that pips R becomes S when hold are held and the
    rest are rerolled.
    """
    kept = [x for x, h in zip(R, hold) if h]
    kept_counts = np.array([kept.count(x) for x in die_spots])
    S_counts = np.array([S.count(x) for x in die_spots])
    need_counts = S_counts - kept_counts
    if (need_counts < 0).any():
        return 0
    else:
        return multinomial(need_counts)/6.0**sum(need_counts)

def gen_tensors():
    """
    Return the propagation tensor and weight vector. 

    The propagation tensor is a 32x252x252 tensor. The first component
    corresponds to the subset of the five dice to be held. The second and third
    correspond to dice pips. Then the entry in the (h, R, S) position is the
    probability that R becomes S when h is held.

    The weight tensor is a length 252 (co)vector, whose component corresonds to
    dice pips. The value in a position is the probability that five dice will
    give that result when thrown.
    """
    prop_tensor = np.empty((32,252,252), dtype=np.dtype('d'))
    for hold_index, hold in enumerate(product([False, True], repeat=5)):
        for R_index, R in enumerate(
                combinations_with_replacement(die_spots, 5)):
            for S_index, S in enumerate(
                    combinations_with_replacement(die_spots, 5)):
                prop_tensor[hold_index, R_index, S_index] = \
                        transition_probability(hold, R, S)
    weight_vector = prop_tensor[0,0,:].copy()
    return prop_tensor,weight_vector






