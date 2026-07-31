from pathlib import Path
import importlib.util


EVAL_NAMES = [
    "PTV_eval",
    "PTV_eval56Gy",
    "PTV_eval (56Gy)",
    "PTV_eval (56 Gy)",
    "PTV eval 56Gy",
    "PTV56Gy_eval",
    "PTV 56 Gy eval",
    "PTV-56Gy-Eval",
]


def _load(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hn_scorecard_eval_variants():
    module = _load(Path(__file__).parents[1] / "hn_scorecard_engine.py", "hn_scorecard_engine_test")
    for name in EVAL_NAMES:
        assert module._is_eval_structure(name), name
    assert not module._is_eval_structure("PTV_evaluation_56Gy")


def test_primary_ptv_is_not_eval():
    module = _load(Path(__file__).parents[1] / "hn_scorecard_engine.py", "hn_scorecard_engine_test2")
    assert not module._is_eval_structure("PTV60")
