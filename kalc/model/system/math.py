from poodle import Object

class Combinations(Object):
    number: int
    combinations: int
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.number = 0
        self.combinations = 0
    
    def __str__(self): return str(self.combinations)

import operator as op
from functools import reduce

def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer / denom

combinations_list = []
for i in range(10):
    combinations0 = Combinations(i)
    combinations0.number = i
    combinations0.combinations = int(ncr(i,2))
    combinations_list.append(combinations0)