from poodle import Object
from guardctl.model.system.primitives import StatusServ, StatusNode, StatusPod, StatusLim, StatusSched, StatusReq, Type
from guardctl.misc.object_factory import stringFactory

STATUS_LIM_MET = stringFactory.get("Limit is met")
STATUS_LIM_EXCEEDED = stringFactory.get("LImits is exceded")
STATUS_POD_FAILED =  stringFactory.get("Inactive")
STATUS_POD_KILLING = stringFactory.get("Killing")
STATUS_POD_PENDING = stringFactory.get("Pending") 
STATUS_POD_RUNNING = stringFactory.get("Running")
STATUS_NODE_ACTIVE = stringFactory.get("Active")
STATUS_NODE_INACTIVE = stringFactory.get("Inactive")
# STATUS_REQ_ATKUBEPROXY = StatusReq()
# STATUS_REQ_ATLOADBALANCER = StatusReq()
# STATUS_REQ_ATPODINPUT = StatusReq()
# STATUS_REQ_ATSTART = StatusReq()
# STATUS_REQ_CPURESOURCECONSUMED = StatusReq()
# STATUS_REQ_CPURESOURCERELEASED = StatusReq()
# STATUS_REQ_DIRECTEDTONODE = StatusReq()
# STATUS_REQ_DIRECTEDTOPOD = StatusReq()
# STATUS_REQ_MEMRESOURCECONSUMED = StatusReq()
# STATUS_REQ_MEMRESOURCERELEASED = StatusReq()
# STATUS_REQ_NODECAPACITYOVERWHELMED = StatusReq()
# STATUS_REQ_REQUESTFINISHED = StatusReq()
# STATUS_REQ_REQUESTPIDTOBEENDED = StatusReq()
# STATUS_REQ_REQUESTTERMINATED = StatusReq()
# STATUS_REQ_RESOURCESCONSUMED = StatusReq()
# STATUS_REQ_RESOURCESRELEASED = StatusReq()
# STATUS_REQ_RUNNING = StatusReq()
STATUS_SCHED_CHANGED =  stringFactory.get("Changed")
STATUS_SCHED_CLEAN   =  stringFactory.get("Clean")
STATUS_SERV_INTERRUPTED = stringFactory.get("Interrupted")
STATUS_SERV_PENDING = stringFactory.get("Pending")
STATUS_SERV_STARTED = stringFactory.get("Started")



TYPE_POLICY_PreemptLowerPriority = stringFactory.get("PreemptLowerPriority")
TYPE_POLICY_NEVER = stringFactory.get("Never")
