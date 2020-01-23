from poodle import Object
import operator as op
from functools import reduce
    # Python3 program to calculate nPr  
import math 
class Combinations(Object):
    number: int
    combinations: int
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.number = 0
        self.combinations = 0
    
    def __str__(self): return str(self.combinations)

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

class Permutations(Object):
    number: int
    permutations: int
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.number = 0
        self.permutations = 0
    
    def __str__(self): return str(self.permutations)


def fact(n):  
    if (n <= 1): 
        return 1
          
    return n * fact(n - 1)  
  
def nPr(n, r):  
    
    return math.floor(fact(n) /
                fact(n - r))  
      
permutation_list = []
for i in range(10):
    permutation0 = Permutations(i)
    permutation0.number = i
    permutation0.permutations = int(nPr(i,2))
    permutation_list.append(permutation0)