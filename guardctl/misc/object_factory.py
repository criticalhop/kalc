from guardctl.model.object.k8s_classes import Label

class _LabelFactory:
    def __init__(self):
        self.labels = {}
    def get(self, name, value):
        lbl = f"{name}:{value}"
        if not lbl in self.labels:
            self.labels[lbl] = Label(lbl)
        return self.labels[lbl]

labelFactory = _LabelFactory()