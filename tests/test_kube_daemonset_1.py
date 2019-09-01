import pytest
from poodle import * 
from  tests.problem.goals import *
from guardctl.misc.const import *

# @pytest.mark.skip(reason="no way of currently testing this")
def test():
    p = TestServiceInterrupted()
    print(p.plan)
    assert p.plan