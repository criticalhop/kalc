from poodle import Object


class String(Object):
    pass
    
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
    
class StatusLim(Object):
    pass

class Label(Object):
    def __str__(self):
        return self.poodle_internal__value