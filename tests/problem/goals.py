import sys
from poodle import * 
from guardctl.misc.const import *
from tests.problem.kubeproblem1 import * 



class TestServiceInterrupted(Problem2):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED
