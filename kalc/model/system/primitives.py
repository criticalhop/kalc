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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "key" in kwargs and "value" in kwargs:
            self.key = kwargs["key"]
            self.value = kwargs["value"]
        elif len(args) and isinstance(args[0], str) and ":" in args[0]:
            self.key, self.value = args[0].split(":")
        else:
            self.key="<UNDEFINED>"
            self.value="<UNDEFINED>"
    def __str__(self):
        return str(self._get_value())

class TypePolicy(Object):
    pass

class TypeServ(Object):
    pass