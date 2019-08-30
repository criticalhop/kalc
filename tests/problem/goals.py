import sys
from poodle import * 
from guardctl.model.full import FullModel


class TestServiceInterrupted(FullModel):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED

def solve(run):
    plan = FullModel(self.state_objects).run()