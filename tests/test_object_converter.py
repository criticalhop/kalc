from kalc.misc.util import k8s_to_domain_object, cpuConvertToAbstractProblem, memConvertToAbstractProblem, MEM_DIVISOR, CPU_DIVISOR
import kalc.misc.util as util
from kalc.model.system.primitives import Label

def test_convert_string():
    assert isinstance(k8s_to_domain_object("just_string"), str)

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

def test_convert_cpu_normal():
    x = cpuConvertToAbstractProblem("500m")
    assert x == int(500 / util.CPU_DIVISOR)

def test_convert_cpu_toosmall():
    try:
        x = cpuConvertToAbstractProblem("-1")
    except AssertionError:
        pass

def test_convert_cpu_toobig():
    try:
        x = cpuConvertToAbstractProblem("100000000000m")
    except AssertionError:
        pass


def test_convert_mem_normal():
    x = memConvertToAbstractProblem("500Mi")
    assert x == int(500 / MEM_DIVISOR)

def test_convert_mem_toosmall():
    try:
        x = memConvertToAbstractProblem("-1")
    except AssertionError:
        pass

def test_convert_mem_toobig():
    try:
        x = memConvertToAbstractProblem("100000000000Mi")
    except AssertionError:
        pass



