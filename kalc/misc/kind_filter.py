import pandas as pd

def label_string_to_python(label: str):
    return label.replace("_", "__").replace("-", "_")

def return_one_or_dataframe(matched: list):
    if len(matched) > 1: return KindFilterResult(matched)
    elif len(matched) == 1: return matched[0]
    else: return None

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
    
class KindFilterResultSeries(pd.Series):

    @property
    def _constructor(self):
        return KindFilterResultSeries 

    @property
    def _constructor_expanddim(self):
        return KindFilterResult 


class KindFilterResult(pd.DataFrame):

    @property
    def _constructor(self):
        return KindFilterResult 

    @property
    def _constructor_sliced(self):
        return KindFilterResultSeries 

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
            return return_one_or_dataframe(matched)
        return super().__getattribute__(val)


class FilterByALL(FilteredKind):
    def _gen_listing(self):
        objAttr = set()
        for obj in filter(lambda x: x.__class__.__name__ == self._kind_name, self._state_objects):
            if hasattr(obj, 'pretty_dir'):
                objAttr.update(obj.pretty_dir)
        return objAttr

    def gen_legend(self, data):
        column = []
        column.append(self._kind_name)
        max_len = 1
        for row in data:
            if max_len < len(row):
                max_len = len(row)

        if max_len == 1:
            return column
        
        kind = None
        for row in data:
            if len(row) > 1:
                kind = row[1].__class__.__name__
        if kind :
            for i in range(max_len-1):
                column.append("{0}{1}".format(kind, i+1))
        return column

    def _safe_getattr(self, val):
        self._gen_listing()
        ret = []
        for obj in self._state_objects:
            if obj.__class__.__name__ == self._kind_name:
                retIn = []
                attr = getattr(obj, val)
                retIn.append(obj)
                if callable(attr):
                    target = attr()
                    if isinstance(target, list):
                        retIn.extend(target)
                    else:
                        retIn.append(target)
                else:
                    target = attr
                    if isinstance(target, list):
                        retIn.extend(target)
                    else:
                        retIn.append(target)
                ret.append(retIn)
        return pd.DataFrame(ret, columns=self.gen_legend(data=ret))
    


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
            return self._gen_listing(return_object=val)
        super().__getattribute__(val)

