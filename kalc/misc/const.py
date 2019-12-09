from poodle import Object
from kalc.model.system.primitives import StatusServ, StatusNode, StatusPod, StatusLim, StatusSched, StatusReq, TypePolicy, TypeServ, StatusDeployment, StatusDaemonSet


STATUS_POD = {
    "Running" : StatusPod("Running"),
    "Pending" : StatusPod("Pending"),
    "Killing" : StatusPod("Killing"),
    "Failed" : StatusPod("Failed"),
    "Succeeded" : StatusPod("Succeeded"),
    "Outaged" : StatusPod("Outaged")
}

STATUS_LIM = {
    "Limit Met" : StatusLim("Limit is met"),
    "Limit Exceeded" : StatusLim("Limit is exceded")
}

STATUS_NODE = {
    "Active" : StatusNode("Active"),
    "Inactive" : StatusNode("Inactive"),
    "Killing" : StatusNode("Killing"),
    "New" : StatusNode("New")
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
STATUS_DEPLOYMENT = {
    "Interrupted" : StatusDeployment("Interrupted"),
    "Pending" : StatusDeployment("Pending"),
    "Started" : StatusDeployment("Started")
}

STATUS_DAEMONSET_STARTED = StatusDaemonSet("Started")
STATUS_DAEMONSET_PENDING = StatusDaemonSet("Pending")
STATUS_DAEMONSET_INTERRUPTED = StatusDaemonSet("Interrupted")
