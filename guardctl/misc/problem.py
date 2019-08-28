from poodle import schedule
from poodle.schedule import SchedulingError

class ProblemTemplate:
    def __init__(self):
        self.plan = None
        self.objectList = []
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

    def addObject(self, obj):
        self.objectList.append(obj)
        return obj
    def run(self, timeout=30):
        self.problem()
        try:
            self.plan = schedule(
                methods=[getattr(self,m) for m in dir(self) if callable(getattr(self,m))], 
                space=list(self.__dict__.values())+self.objectList,
                goal=lambda:(self.goal()),
                timeout=timeout
                #exit=self.exit
            )
        except SchedulingError:
            pass