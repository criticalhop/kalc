from collections import Mapping, Set, Sequence 
from guardctl.misc.object_factory import labelFactory, stringFactory
import string

import dpath.util
def dget(d, path, default):
    try:
        return dpath.util.get(d, path)
    except KeyError:
        return default

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
        return stringFactory.get(obj)
    else:
        raise ValueError("Value type not suported: %s" % repr(obj))


def cpuConvertToAbstractProblem(cpuParot):
    #log.debug("cpuParot", cpuParot)
    cpu = 0
    if cpuParot[len(cpuParot)-1] == 'm':
        cpu = int(cpuParot[:-1])
    else:
        cpu = int(cpuParot)*1000
    # log.debug("cpuParot ", cpuParot, " ret ", cpuAdd)
    cpu = cpu / 20
    if cpu == 0:
        cpu = 1
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
    ret = ret / 20
    if ret == 0:
        ret = 1
    return int(ret)