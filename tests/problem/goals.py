import sys
from poodle import * 
from guardctl.misc.problem import ProblemTemplate
from guardctl.misc.const import *


class TestServiceInterrupted(ProblemTemplate):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED
