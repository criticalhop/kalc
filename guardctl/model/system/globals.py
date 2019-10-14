from poodle import Object
from guardctl.model.system.primitives import Type, Status
from guardctl.model.kinds.Node import Node


class GlobalVar(Object):
    is_deployment_disrupted: bool
    is_deployment_distuption_searchable: bool
    is_service_disrupted: bool
    is_service_disruption_searchable: bool
    is_node_disrupted: bool
    is_node_disruption_searchable: bool
    goal_achieved: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_service_disrupted = False
        self.goal_achieved = False
        self.is_deployment_distuption_searchable = True
        self.is_service_disruption_searchable:
        