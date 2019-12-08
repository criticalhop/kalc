from poodle import Object

 
class Type(Object):
    def __str__(self): return str(self._get_value())

class Status(Object):
    def __str__(self): return str(self._get_value())

class StatusPod(Object):
    def __str__(self): return str(self._get_value())

class StatusNode(Object):
    def __str__(self): return str(self._get_value())

class StatusReq(Object):
    def __str__(self): return str(self._get_value())

class StatusSched(Object):
    def __str__(self): return str(self._get_value())
    
class StatusServ(Object):
    def __str__(self): return str(self._get_value())

class StatusDeployment(Object):
    def __str__(self): return str(self._get_value())

class StatusDaemonSet(Object):
    def __str__(self): return str(self._get_value())

class StatusLim(Object):
    pass

class Label(Object):
    def __str__(self):
        return str(self._get_value())

class TypePolicy(Object):
    pass

class TypeServ(Object):
    pass