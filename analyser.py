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
                new_open = (state & ~(1 << i)) & 0x1FFF
                new_state = new_upper << 13 | new_open
                value = forward_scores[new_state] + self.scores[cat]
                best = max(best, value)
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

class StateAnalyser():

    def __init__(self, generate_roll_lookup=True, generate_tensors=True,
            evaluate_forward_values=False):

        if generate_roll_lookup:
            self.gen_roll_lookup()
        else:
            self.roll_lookup=None

        if generate_tensors:
            self.gen_tensors()
        else:
            self.weight_vector, self.prop_tensor = None,None

        self.forward_values = np.full(2**19, np.nan, dtype=np.dtype('d'))
        if evaluate_forward_values:
            self.evaluate_forward_values()

    def gen_roll_lookup(self):
        """
        Return a dictionary to lookup a roll, returning a DiceRoll object
        corresponding to that (sorted) roll.
        """

        self.roll_lookup = {}
        for roll in combinations_with_replacement(die_spots, 5):
            self.roll_lookup[roll] = DiceRoll(roll)

    def gen_tensors(self):
        """
        Return the propagation tensor and weight vector. 

        The propagation tensor is a 32x252x252 tensor. The first component
        corresponds to the subset of the five dice to be held. The second and
        third correspond to dice pips. Then the entry in the (h, R, S)
        position is the probability that R becomes S when h is held.

        The weight tensor is a length 252 (co)vector, whose component
        corresonds to dice pips. The value in a position is the probability
        that five dice will give that result when thrown.
        """
        self.prop_tensor = np.empty((32,252,252), dtype=np.dtype('d'))
        for hold_index, hold in enumerate(product([False, True], repeat=5)):
            for R_index, R in enumerate(
                    combinations_with_replacement(die_spots, 5)):
                for S_index, S in enumerate(
                        combinations_with_replacement(die_spots, 5)):
                    self.prop_tensor[hold_index, R_index, S_index] = \
                            transition_probability(hold, R, S)
        self.weight_vector = self.prop_tensor[0,0,:].copy()

    def score_state(self,state):
        if open_cats(state) == 0:
            return 0 if upper_score(state) < 63 else 35
        score_vector = np.empty(252, dtype=np.dtype('d'))
        for index, roll in enumerate(
                combinations_with_replacement(die_spots, 5)):
            score_vector[index] = \
                    self.roll_lookup[roll].best_score(state,
                            self.forward_values)
        for i in range(2):
            score_options = np.dot(self.prop_tensor, score_vector)
            score_vector = score_options.max(axis=0)
        return np.dot(self.weight_vector, score_vector)

    def evaluate_forward_values(self):
        all_states = list(range(2**19))
        all_states.sort(key = lambda x: bin(x & 0x1FFF).count("1"))
        for state in all_states:
            self.forward_values[state] = self.score_state(state)

