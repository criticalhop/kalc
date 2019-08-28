
import poodle.problem
from guardctl.model.object.k8s_classes import *

class ProblemTemplate(poodle.problem.Problem):
    constSymbol = {}
    pod = []
    node = []
    kubeProxy = []
    loadbalancer = []
    service = []
    daemonSet = []
    request = []
    containerConfig = []
    priorityDict = {}
    
    def __init__(self):
        super().__init__() 
        self.constSymbol = {}
        self.pod = []
        self.node = []
        self.kubeProxy = []
        self.loadbalancer = []
        self.service = []
        self.daemonSet = []
        self.request = []
        self.containerConfig = []
        self.priorityDict = {}

 
    def problem(self):
         pass