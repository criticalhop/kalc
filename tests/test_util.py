from guardctl.misc.util import dget
import yaml

def test_dget_ok():
    d=yaml.load(open("./tests/kube-config/deployments.yaml"))
    assert dget(d["items"][0], "metadata/name", "NONE") == "redis-master"

def test_dget_default():
    d=yaml.load(open("./tests/kube-config/deployments.yaml"))
    assert dget(d["items"][0], "name", "NONE") == "NONE"

