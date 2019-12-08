class KindPlaceholder:
    pass

class FilteredKind:
    def __init__(self, kind_name, state_objects):
        self.kind_name = kind_name
        self.state_objects = state_objects
        self.cache = []
    
    def gen_listing(self):
        raise NotImplementedError()

    def __dir__(self):
        # if not self.cache: self.cache = self.gen_listing()
        # return self.cache
        return self.gen_listing()
    
class KindFilterResult:
    def __init__(self, objects):
        self.objects = objects

class FilterByLabelValue(FilteredKind):
    def __init__(self, kind_name, state_objects, target_key):
        super().__init__(kind_name, state_objects)
        self.target_key = target_key

    def gen_listing(self):
        label_values = set()
        for obj in filter(lambda x: x.__class__.__name__ == self.kind_name, self.state_objects):
            for label in obj.metadata_labels:
                if label.key == self.target_key:
                    label_values.add(label.value)
        return list(label_values)
 
    def __getattr__(self, val):
        # if not self.cache: self.cache = self.gen_listing()
        self.cache = self.gen_listing()
        if val in self.cache:
            matched = []
            for ob in filter(lambda x: x.__class__.__name__ == self.kind_name):
                for l in ob.metadata_labels:
                    if l.key == self.target_key and l.value == val:
                        matched.append(ob)
            return KindFilterResult(matched)
        return super().__getattribute__(val)

class FilterByLabelKey(FilteredKind):
    def gen_listing(self):
        label_keys = set()
        for obj in filter(lambda x: x.__class__.__name__ == self.kind_name, self.state_objects):
            for label in obj.metadata_labels:
                label_keys.add(label.key)
        return list(label_keys)
    
    def __getattr__(self, val):
        # if not self.cache: self.cache = self.gen_listing()
        self.cache = self.gen_listing()
        if val in self.cache:
            return FilterByLabelValue(self.kind_name, self.state_objects, target_key=val)
        return super().__getattribute__(val)


class FilterByName(FilteredKind):
    def gen_listing(self):
        names = []
        for obj in filter(lambda x: x.__class__.__name__ == self.kind_name, self.state_objects):
            names.append(obj.metadata_name)
        return names
    
    def __getattribute__(self, val):
        if val in self.gen_listing():
            return Filter
        super().__getattribute__(val)

