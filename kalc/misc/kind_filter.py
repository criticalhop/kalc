import pandas

def label_string_to_python(label: str):
    return label.replace("_", "__").replace("-", "_")

class KindPlaceholder:
    pass

class FilteredKind:
    def __init__(self, kind_name, state_objects):
        self._kind_name = kind_name
        self._state_objects = state_objects
        self._cache = []
    
    def _gen_listing(self):
        raise NotImplementedError()

    def _safe_getattr(self, value):
        return super().__getattribute__(value)

    def __dir__(self):
        # if not self.cache: self.cache = self.gen_listing()
        # return self.cache
        return [str(x) for x in self._gen_listing()]
    
    def __getattr__(self, value):
        if value.startswith("_"): return super().__getattribute__(value)
        return self._safe_getattr(value)
    
class KindFilterResult:
    def __init__(self, objects):
        self._objects = objects
    def __list__(self):
        return self._objects
    def __iter__(self):
        return iter(self._objects)
    def __repr__(self):
        return repr(pandas.DataFrame(list(self)))


class FilterByLabelValue(FilteredKind):
    def __init__(self, kind_name, state_objects, target_key):
        super().__init__(kind_name, state_objects)
        self._target_key = target_key

    def _gen_listing(self):
        label_values = set()
        for obj in filter(lambda x: x.__class__.__name__ == self._kind_name, self._state_objects):
            for label in obj.metadata_labels:
                if label.key == self._target_key:
                    label_values.add(label_string_to_python(label.value))
        return list(label_values)
 
    def _safe_getattr(self, val):
        # if not self._cache: self._cache = self.gen_listing()
        self._cache = self._gen_listing()
        if val in self._cache:
            matched = []
            for ob in filter(lambda x: x.__class__.__name__ == self._kind_name, self._state_objects):
                for l in ob.metadata_labels:
                    if label_string_to_python(l.key) == self._target_key and \
                                    label_string_to_python(l.value) == val:
                        matched.append(ob)
            return KindFilterResult(matched)
        return super().__getattribute__(val)

class FilterByLabelKey(FilteredKind):
    def _gen_listing(self):
        label_keys = set()
        for obj in filter(lambda x: x.__class__.__name__ == self._kind_name, self._state_objects):
            for label in obj.metadata_labels:
                label_keys.add(label_string_to_python(label.key))
                # because of ipython __dir__ completion bug,
                # we will be setting actual attrs here
                setattr(self, label_string_to_python(label.key), \
                    FilterByLabelValue(self._kind_name, self._state_objects, \
                            target_key=label_string_to_python(label.key)))
        return list(label_keys)
    
    def _safe_getattr(self, val):
        self._gen_listing()
        return super().__getattribute__(val)

    # because of bug in __dir__ ipython support, this does not work. TODO: file bug 
    # def _safe_getattr(self, val):
    #     if not self._cache: self._cache = self._gen_listing()
    #     # self._cache = self._gen_listing()
    #     if val in self._cache:
    #         return FilterByLabelValue(self._kind_name, self._state_objects, target_key=val)
    #     return super().__getattribute__(val)


class FilterByName(FilteredKind):
    def _gen_listing(self, return_object=None):
        names = []
        for obj in filter(lambda x: x.__class__.__name__ == self._kind_name, self._state_objects):
            names.append(label_string_to_python(str(obj.metadata_name)))
            if return_object == label_string_to_python(str(obj.metadata_name)): 
                return obj
        return names
    
    def _safe_getattr(self, val):
        if val in self._gen_listing():
            return KindFilterResult([self._gen_listing(return_object=val)])
        super().__getattribute__(val)

