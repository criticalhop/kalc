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
    try:
        int(obj)
        try_int = True
    else:
        try_int = False
    if isinstance(obj, dict) and len(obj) == 1:
        k,v=obj.items[0]
        return labelFactory.get(k,v)
    elif isinstance(obj, str) and obj[0] in string.digits and not obj[-1] in string.digits:
        # pass on, probably someone will take care
        return obj
    elif isinstance(obj, str) and try_int:
        return int(obj)
    elif isinstance(obj, str) and not obj[0] in string.digits:
        return stringFactory.get(obj)
    else:
        raise ValueError("Value type not suported: %s" % repr(obj))