"""Implementing full model from all effects"""
from poodle import Object
import guardctl.model.kinds
import pkgutil, inspect
import guardctl.misc.problem

kinds_collection = []

for importer, modname, ispkg in pkgutil.iter_modules(
        path=guardctl.model.kinds.__path__,
        prefix=guardctl.model.kinds.__name__+'.'):
    module = __import__(modname, fromlist="dummy")
    for n in dir(module):
        c = getattr(module, n)
        if inspect.isclass(c) and issubclass(c, Object) and not c is Object:
            kinds_collection.append(c)


    