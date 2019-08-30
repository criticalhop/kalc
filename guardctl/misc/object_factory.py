from guardctl.model.system.primitives import Label, String

class _LabelFactory:
    def __init__(self):
        self.labels = {}
    def get(self, name, value):
        lbl = f"{name}:{value}"
        if not lbl in self.labels:
            self.labels[lbl] = Label(lbl)
        return self.labels[lbl]

labelFactory = _LabelFactory()

class _StringFactory:
    def __init__(self):
        self.strings = {}
    def get(self, str_):
        if not str_ in self.strings:
            self.strings[str_] = String(str_)
        return self.strings[str_]

stringFactory = _StringFactory()