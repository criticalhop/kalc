from poodle import Object
from guardctl.model.system.primitives import StatusServ, StatusNode, StatusPod, StatusLim, StatusSched, StatusReq, TypePolicy


STATUS_POD = {
    "Running" : StatusPod("Running"),
    "Pending" : StatusPod("Pending"),
    "Killing" : StatusPod("Killing"),
    "Failed" : StatusPod("Failed"),
    "Succeeded" : StatusPod("Succeeded")
}

STATUS_LIM = {
    "Limit Met" : StatusLim("Limit is met"),
    "Limit Exceeded" : StatusLim("Limit is exceded")
}

STATUS_NODE = {
    "Active" : StatusNode("Active"),
    "Inactive" : StatusNode("Inactive")
}

STATUS_SCHED = {
    "Changed" : StatusSched("Changed"),
    "Clean" :  StatusSched("Clean")
}

STATUS_SERV = {
    "Interrupted" : StatusServ("Interrupted"),
    "Pending" : StatusServ("Pending"),
    "Started" : StatusServ("Started")
}
POLICY = {
    "PreemptLowerPriority" : TypePolicy("PreemptLowerPriority"),
    "Never" : TypePolicy("Never")
}