import sys
from poodle import * 
from guardctl.misc.const import *
from tests.problem.kubeproblem1 import * 
from guardctl.model.search import *



class TestServiceInterrupted(Problem2,K8SearchEviction ):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED
