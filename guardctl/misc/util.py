from collections.abc import Mapping, Set, Sequence 
from guardctl.misc.object_factory import labelFactory 
import string

CPU_DIVISOR = 200
MEM_DIVISOR = 200

from poodle.arithmetic import logSparseIntegerFactory
for n in range(1,10000):
    try:
        i = logSparseIntegerFactory.numbers[n]
    except KeyError:
        break
POODLE_MAXLIN = n-1

try:
    from six import string_types, iteritems
except ImportError:
    string_types = (str, ) if str is bytes else (str, bytes)
    iteritems = lambda mapping: getattr(mapping, 'iteritems', mapping.items)()

def objwalk(obj, path=(), memo=None):
    if memo is None:
        memo = set()
    if isinstance(obj, Mapping):
        if id(obj) not in memo:
            memo.add(id(obj)) 
            for key, value in iteritems(obj):
                for child in objwalk(value, path + (key,), memo):
                    yield child
    elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
        if id(obj) not in memo:
            memo.add(id(obj))
            for index, value in enumerate(obj):
                for child in objwalk(value, path + (index,), memo):
                    yield child
    else:
        yield path, obj

def find_property(obj, p):
    path = p[0]
    val = p[1]
    if len(path) == 1:
        if hasattr(obj, path[0]):
            return path[0], val
    
    for i in range(len(path), 1, -1):
        try_path = path[:i]
        spath = "_".join([x if isinstance(x, str) else "" for x in try_path])
        # print("Trying ", spath)
        if hasattr(obj, spath) and i==len(path):
            # print("FOUND1")
            return spath, val
        elif hasattr(obj, spath) and i==len(path)-1:
            # print("FOUND2")
            return spath, {path[-1]: val}
    return None, None

def k8s_to_domain_object(obj):
    try_int = False
    try:
        int(obj)
        try_int = True
    except:
        pass
    if isinstance(obj, int):
        return obj
    elif isinstance(obj, dict) and len(obj) == 1:
        k,v=list(obj.items())[0]
        return labelFactory.get(k,v)
    elif isinstance(obj, str) and obj[0] in string.digits+"-" and not obj[-1] in string.digits:
        # pass on, probably someone will take care
        return obj
    elif isinstance(obj, str) and try_int:
        return int(obj)
    elif isinstance(obj, str) and not obj[0] in string.digits+"-":
        return obj
    else:
        return obj.__str__()
        # raise ValueError("Value type not suported: %s" % repr(obj))


def cpuConvertToAbstractProblem(cpuParot):
    #log.debug("cpuParot", cpuParot)
    cpu = 0
    if isinstance(cpuParot, int):
        cpu = cpuParot*1000
    else:
        if cpuParot[len(cpuParot)-1] == 'm':
            cpu = int(cpuParot[:-1])
        else:
            cpu = int(cpuParot)*1000
    # log.debug("cpuParot ", cpuParot, " ret ", cpuAdd)
    cpu = int(cpu / CPU_DIVISOR)
    if cpu == 0:
        cpu = 1
    assert cpu >= 0
    assert cpu <= POODLE_MAXLIN, "Number exceeds Poodle power"
    return int(cpu)

def memConvertToAbstractProblem(mem):
    ret = 0
    if mem[len(mem)-2:] == 'Gi':
        ret = int(mem[:-2])*1000
    elif mem[len(mem)-2:] == 'Mi':
        ret = int(mem[:-2])
    elif mem[len(mem)-2:] == 'Ki':
        ret = int(int(mem[:-2])/1000)
    else:
        ret = int(int(mem)/1000000)
    ret = int(ret / MEM_DIVISOR)
    if ret == 0:
        ret = 1
    assert ret >= 0
    assert ret <= POODLE_MAXLIN, "Number exceeds Poodle power"
    return int(ret)

#object deduplicator by metadata_name
def objDeduplicatorByName(objList):
    dedupList = []
    nameList = []
    counter = 0
    for obj in objList:
        if not(obj.metadata_name._get_value() in nameList):
            dedupList.append(obj)
            nameList.append(obj.metadata_name._get_value())
        counter +=1
    return dedupList

#solve bug in poodle by this
def objRemoveByName(objList, metadata_name):
    br = True
    while br:
        br = False
        for obj in objList:
            if obj.metadata_name._get_value() == metadata_name :
                objList.remove(obj)
                br = True
                break
