from poodle import schedule
from poodle.schedule import SchedulingError

class ProblemTemplate:
    def __init__(self, objectList=[]):
        self.plan = None
        self.objectList = objectList
        self.pod = []
        self.node = []
        self.kubeProxy = []
        self.loadbalancer = []
        self.service = []
        self.controller = []
        self.request = []
        self.containerConfig = []
        self.priorityDict = {}
    
    def problem(self):
        pass

    def addObject(self, obj):
        self.objectList.append(obj)
        return obj
    def run(self, timeout=30):
        self.problem()
        self_methods = [getattr(self,m) for m in dir(self) if callable(getattr(self,m))]
        model_methods = []
        for obj in self.objectList:
            for m in dir(obj.__class__):
                if callable(getattr(obj.__class__, m)):
                    model_methods.append(getattr(obj.__class__, m))
        try:
            self.plan = schedule(
                methods=self_methods + model_methods, 
                space=list(self.__dict__.values())+self.objectList,
                goal=lambda:(self.goal()),
                timeout=timeout
                #exit=self.exit
            )
        except SchedulingError:
            pass