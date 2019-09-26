from poodle import Object

 
class Type(Object):
    pass

class Status(Object):
    pass

class StatusPod(Object):
    pass

class StatusNode(Object):
    pass

class StatusReq(Object):
    pass

class StatusSched(Object):
    pass
    
class StatusServ(Object):
    pass
class StatusDepl(Object):
    pass
    
class StatusLim(Object):
    pass

class Label(Object):
    def __str__(self):
        return str(self._get_value())

class TypePolicy(Object):
    pass

class TypeServ(Object):
    pass