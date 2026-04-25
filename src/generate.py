"""TRACE synthetic data generator — orchestrator.

Routes to per-area generators. Each area is self-contained under configs/<area>/
with its own taxonomy, template, and compatibility rules.

Usage:
    # Generate one area (count from generation.yaml)
    uv run python src/generate.py --area dtt

    # Generate one area with explicit count
    uv run python src/generate.py --area dtt --n 50

    # Generate all enabled areas
    uv run python src/generate.py --all

    # Write to a specific file (single-area mode only)
    uv run python src/generate.py --area dtt --n 10 --out data/samples/dtt-10.jsonl
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

# Path setup so we can run as a script
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.generators.aba_dtt import DTTGenerator
from src.generators.aba_net import NETGenerator
from src.generators.aba_session_interp import SessionInterpretationGenerator
from src.generators.aba_task_analysis import TaskAnalysisGenerator
from src.generators.base import load_yaml

CONFIG_DIR = REPO_ROOT / "configs"

# Area registry — add new generators here as they come online.
GENERATORS = {
    "dtt": DTTGenerator,
    "net": NETGenerator,
    "task_analysis": TaskAnalysisGenerator,
    "session_interpretation": SessionInterpretationGenerator,
    # "fct": FCTGenerator,
    # "bst": BSTGenerator,
    # "prt": PRTGenerator,
}


def deterministic_area_offset(area: str) -> int:
    """Stable per-area seed offset.

    Using Python's built-in ``hash()`` here would be non-deterministic across
    processes (PYTHONHASHSEED randomization), which would make the dataset
    irreproducible run-to-run. SHA-256 is stable across processes and Python
    versions.
    """
    return int(hashlib.sha256(area.encode()).hexdigest(), 16) % 10000


def generate_area(area: str, n: int, seed: int, out_stream) -> int:
    """Generate `n` examples for `area`; write to `out_stream` as JSONL. Returns count written."""
    if area not in GENERATORS:
        raise ValueError(f"Generator for area '{area}' not registered. Available: {list(GENERATORS)}")
    GenCls = GENERATORS[area]
    generator = GenCls(CONFIG_DIR)
    rng = random.Random(seed)
    for _ in range(n):
        example = generator.render_example(rng)
        out_stream.write(json.dumps(example) + "\n")
    return n


def main():
    parser = argparse.ArgumentParser(description="TRACE per-area generator orchestrator.")
    parser.add_argument("--area", default=None, help="Generate only this area.")
    parser.add_argument("--all", action="store_true", help="Generate all enabled areas from generation.yaml.")
    parser.add_argument("--n", type=int, default=None, help="Override example count.")
    parser.add_argument("--seed", type=int, default=None, help="Override global seed.")
    parser.add_argument("--out", type=str, default=None, help="Output JSONL file (single-area mode).")
    args = parser.parse_args()

    gen_config = load_yaml(CONFIG_DIR / "generation.yaml")
    seed = args.seed if args.seed is not None else gen_config["seed"]

    if not args.area and not args.all:
        parser.error("Must specify --area <name> or --all.")

    if args.all:
        # Multi-area: write one file per area under output_dir
        output_dir = REPO_ROOT / gen_config["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        total = 0
        for area, area_cfg in gen_config["areas"].items():
            if not area_cfg.get("enabled"):
                print(f"  - {area}: disabled, skipping")
                continue
            if area not in GENERATORS:
                print(f"  - {area}: generator not yet built, skipping")
                continue
            n = area_cfg["n"]
            out_path = output_dir / f"{area}.jsonl"
            with open(out_path, "w") as f:
                generate_area(area, n, seed + deterministic_area_offset(area), f)
            print(f"  - {area}: {n} examples -> {out_path}")
            total += n
        print(f"\nTotal generated: {total} examples.")
    else:
        # Single-area mode
        area = args.area
        n = args.n if args.n is not None else gen_config["areas"][area]["n"]
        out_stream = open(args.out, "w") if args.out else sys.stdout
        try:
            generate_area(area, n, seed, out_stream)
        finally:
            if args.out:
                out_stream.close()
        if args.out:
            print(f"Wrote {n} examples to {args.out}")


if __name__ == "__main__":
    main()
