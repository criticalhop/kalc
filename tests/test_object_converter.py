from guardctl.misc.util import k8s_to_domain_object
from guardctl.model.system.primitives import String, Label

def test_convert_string():
    assert isinstance(k8s_to_domain_object("just_string"), String)

def test_convert_int():
    assert k8s_to_domain_object("123") == 123
def test_convert_int_neg():
    assert k8s_to_domain_object("-123") == -123
def test_convert_unit():
    assert k8s_to_domain_object("123Mi") == "123Mi"
def test_convert_unit_minus():
    assert k8s_to_domain_object("-123Mi") == "-123Mi"
def test_convert_labeldict():
    assert isinstance(k8s_to_domain_object({"test":"test2"}), Label)
