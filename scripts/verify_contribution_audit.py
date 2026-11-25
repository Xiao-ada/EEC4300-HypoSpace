"""Reproduce the published audit into an automatically cleaned temporary folder."""
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    with tempfile.TemporaryDirectory(prefix="hypospace-contribution-check-") as temporary:
        root = Path(temporary)
        target = root / "results/contribution_audit"
        audit = load_script("audit_independent_contribution")
        audit.OUT = target
        with contextlib.redirect_stdout(io.StringIO()):
            audit.main()
        proof = load_script("prove_coverage_properties")
        proof.ROOT = root
        with contextlib.redirect_stdout(io.StringIO()):
            proof.main()
        for name in ["secondary_metrics.json", "formal_examples.json"]:
            expected = json.loads((ROOT / "results/contribution_audit" / name).read_text())
            actual = json.loads((target / name).read_text())
            assert actual == expected, "Reproduction differs: " + name
            print("PASS exact reproduction:", name)
    print("Temporary evidence removed. No model training, generation, GPU or credentials used.")


if __name__ == "__main__":
    main()
