from typing import Set
from guardctl.model.system.base import HasLabel
from guardctl.model.system.primitives import Label

class Controller(HasLabel):
    "Kubernetes controller base class"
    spec_selector_matchLabels: Set[Label]