import sys
from poodle import * 
from guardctl.importers.problemConfigLoad import KubernetesYAMLLoad
from guardctl.model.object.k8s_classes import *

class TestServiceInterrupted(KubernetesYAMLLoad):
    def goal(self):
        self.service[0].status == self.constSymbol["statusServInterrupted"]

