from kalc.model.system.primitives import Label

class _LabelFactory:
    def __init__(self):
        self.labels = {}
    def get(self, name, value):
        lbl = f"{name}:{value}"
        if not lbl in self.labels:
            self.labels[lbl] = Label(lbl)
        return self.labels[lbl]

labelFactory = _LabelFactory()
