from typing import Set
from kalc.model.system.base import HasLabel
from kalc.model.system.primitives import Label

class Controller(HasLabel):
    "Kubernetes controller base class"
    spec_selector_matchLabels: Set[Label]