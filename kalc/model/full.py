"""Implementing full model from all effects"""
from poodle import Object
import kalc.model.kinds
import pkgutil, inspect
import kalc.misc.problem

kinds_collection = {}

for importer, modname, ispkg in pkgutil.iter_modules(
        path=kalc.model.kinds.__path__,
        prefix=kalc.model.kinds.__name__+'.'):
    module = __import__(modname, fromlist="dummy")
    globals()[modname.split(".")[-1]] = module
    for n in dir(module):
        c = getattr(module, n)
        if inspect.isclass(c) and issubclass(c, Object) and not c is Object:
            kinds_collection[c.__name__] = c

Node.Node.NODE_NULL = Node.Node("NULL")
Node.Node.NODE_NULL.isNull = True
Node.Node.NODE_NULL.metadata_name = "Null-Node"
Node.Node.NODE_NULL.searchable = False

Pod.Pod.POD_NULL = Pod.Pod("NULL")
Pod.Pod.POD_NULL.isNull = True

    