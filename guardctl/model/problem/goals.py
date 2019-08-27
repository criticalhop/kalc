import sys
from poodle import * 
from guardctl.importers.problemConfigLoad import KubernitesYAMLLoad
from guardctl.model.object.k8s_classes import *

class TestServiceInterrupted(KubernitesYAMLLoad):
    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED

