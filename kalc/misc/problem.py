from poodle import schedule, xschedule
from poodle.schedule import SchedulingError
from kalc.misc.math import permutation_list

class ProblemTemplate:
    def __init__(self, objectList=None):
        if objectList is None: self.objectList = []
        else: self.objectList = objectList
        self.objectList.extend(permutation_list)
        self.plan = None
        self.pod = []
        self.node = []
        self.kubeProxy = []
        self.loadbalancer = []
        self.service = []
        self.controller = []
        self.request = []
        self.containerConfig = []
        self.priorityDict = {}
        self.goals_in = []
        self.goals_eq = []
        self.external_actions = []
        self.lambda_goal = []
        self.script = []
    
    def problem(self):
        pass
        
    def addObject(self, obj):
        self.objectList.append(obj)
        return obj

    # fill object with corresponding list (list instance in lower case)
    def fillObjectLists(self):
        requiredObject = ['Pod', "Node", "Service", "LoadBalancer", "DaemonSet", "Deployment"]
        for obj in self.objectList:
            if obj.__class__.__name__ in requiredObject:
                try:
                    getattr(self, obj.__class__.__name__.lower()).append(obj)
                except:
                    pass
            
    def generate_goal(self):
        pass

    def add_external_method(self, action):
        if not action in self.external_actions: self.external_actions.append(action)

    def run(self, timeout=999000, sessionName=None, schedule=schedule, raise_=False):
        if not sessionName: sessionName = self.__class__.__name__
        self.problem()
        self.generate_goal()
        self_methods = [getattr(self,m) for m in dir(self) if callable(getattr(self,m)) and hasattr(getattr(self, m), "_planned")]
        model_methods = []
        methods_scanned = set()
        for obj in self.objectList:
            if not obj.__class__.__name__ in methods_scanned:
                methods_scanned.add(obj.__class__.__name__)
                for m in dir(obj):
                    if callable(getattr(obj, m)) and hasattr(getattr(obj, m), "_planned"):
                        model_methods.append(getattr(obj, m))
        try:
            self.plan = schedule(
                methods=self_methods + list(model_methods) + self.external_actions, 
                # methods=self_methods + list(model_methods), 
                space=list(self.__dict__.values())+self.objectList,
                goal=lambda:(self.goal()),
                timeout=timeout,
                sessionName=sessionName
                #exit=self.exit
            )
        except SchedulingError:
            if raise_:
                raise SchedulingError("Can't solve")
            else:
                pass
    
    def xrun(self, timeout=999000, sessionName=None):
        "Run and execute plan"
        self.run(timeout, sessionName, schedule=xschedule, raise_=True)

    def goal(self):
        pass

    