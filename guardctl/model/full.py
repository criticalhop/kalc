"""Implementing full model from all effects"""
import guardctl.model.effects
import pkgutil
from guardctl.model.effects.abstract import Effect
import inspect
import guardctl.misc.problem

all_effects = {}

for importer, modname, ispkg in pkgutil.iter_modules(
        path=guardctl.model.effects.__path__,
        refix=guardctl.model.effects.__name__+'.'):
    module = __import__(modname, fromlist="dummy")
    for n in dir(module):
        c = getattr(module, n)
        if inspect.isclass(c) and issubclass(c, Effect):
            all_effects.append(c)

all_effects = [guardctl.misc.problem.ProblemTemplate] + list(all_effects)

class FullModel(**all_effects):
    pass


    
    