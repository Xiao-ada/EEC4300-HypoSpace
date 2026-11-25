"""Audit grammar-derived aliases of training classes without model generation.

This finite syntax audit is exploratory. It does not enumerate every possible
whitespace/parenthesis spelling and does not use test references or responses.
"""
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer.experiment import assess
from explorer.upstream import evaluator


def expressions(depth):
    if depth == 0:
        return {"x", "y"}
    previous = expressions(depth - 1)
    return previous | {f"NOT ({a})" for a in previous} | {
        f"({a} {op} {b})" for op in ["AND", "OR"] for a in previous for b in previous
    }


def main():
    target = ROOT / "results/diagnostics/v1_alias_audit.json"
    if target.exists():
        raise SystemExit("Retain the existing audit rather than overwrite it")
    training = json.loads((ROOT / "runs/final_v1/training_data.json").read_text())
    # Only rule metadata comes from the task cache; no cached task labels are read.
    metadata = json.loads((ROOT / ".cache/tasks.json").read_text())["metadata"]
    assert metadata["variables"] == ["x", "y"] and metadata["max_depth"] == 2
    keys = {g["key"] for g in training["groups"]} | {g["key"] for g in training["empty_groups"]}
    aliases = defaultdict(list)
    rejected = 0
    outside_training = 0
    ev = evaluator(metadata)
    candidates = sorted(expressions(2))
    for formula in candidates:
        outcome = assess(ev, metadata, {"id": "grammar-only", "observations": []}, "Expression: " + formula, [])
        if not outcome["in_space"]:
            rejected += 1
        elif outcome["key"] not in keys:
            outside_training += 1
        else:
            aliases[outcome["key"]].append(formula)
    counts = [len(aliases[key]) for key in sorted(keys)]
    result = {"status": "post-hoc train-class syntax audit, not a model performance experiment",
              "uses_test_references": False, "generation_calls": 0,
              "finite_candidate_strings": len(candidates), "rejected_by_shared_space_gate": rejected,
              "space_passes_outside_training_reference_keys": outside_training,
              "training_reference_classes": len(keys), "represented_classes": sum(c > 0 for c in counts),
              "positive_alias_count_min": min(c for c in counts if c), "alias_count_max": max(counts),
              "alias_count_histogram": dict(sorted(Counter(counts).items())),
              "aliases_by_training_key": {key: aliases[key] for key in sorted(keys)},
              "v1_target_alias_counts": dict(Counter(len(g["aliases"]) for g in training["groups"])),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "aliases_by_training_key"}, indent=2))


if __name__ == "__main__":
    main()
