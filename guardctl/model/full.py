"""Implementing full model from all effects"""
import guardctl.model.effects
import pkgutil
from guardctl.model.effects.abstract import Effect
import inspect
import guardctl.misc.problem

all_effects = set([guardctl.misc.problem.ProblemTemplate])

for importer, modname, ispkg in pkgutil.iter_modules(
        path=guardctl.model.effects.__path__,
        prefix=guardctl.model.effects.__name__+'.'):
    module = __import__(modname, fromlist="dummy")
    for n in dir(module):
        c = getattr(module, n)
        if inspect.isclass(c) and issubclass(c, Effect) and not c is Effect:
            all_effects.add(c)

class FullModel(*list(all_effects)):
    pass


    
    