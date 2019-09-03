import sys
from poodle import * 
from guardctl.misc.const import *
from tests.problem.kubeproblem1 import * 
from guardctl.model.search import *



class Test_case_1(Problem2,K8SearchEviction ):
    def goal(self):
        self.pod[0].status_phase == STATUS_POD_RUNNING

class Test_case_2(Problem2,K8SearchEviction ):
    def goal(self):
        self.pod[1].status_phase == STATUS_POD_PENDING

class Test_case_3(Problem2,K8SearchEviction ):
    def goal(self):
        self.pod[0].status_phase == STATUS_POD_KILLING

class TestServiceInterrupted(Problem2,K8SearchEviction ):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED
