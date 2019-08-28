from guardctl.model.full import FullModel

def test_full_model_creattion():
    fm = FullModel()
    assert hasattr(fm, "StartPod")