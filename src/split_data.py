"""Dataset splitter — combines per-area JSONL files into stratified train / valid / curation pool.

Stratification ensures:
- task_type ratio preserved across splits (60/40 teaching vs interp by default)
- For task 1: each method represented proportionally
- For task 2: each pattern represented proportionally

Usage:
    uv run python src/split_data.py
    uv run python src/split_data.py --seed 42 --out-dir data/splits
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.generators.base import load_yaml

CONFIG_DIR = REPO_ROOT / "configs"


def load_all_area_files(input_dir: Path, areas: list[str]) -> list[dict]:
    """Load every per-area JSONL file; deduplicate by example_id (a content hash)."""
    seen: set[str] = set()
    combined: list[dict] = []
    n_raw = 0
    for area in areas:
        path = input_dir / f"{area}.jsonl"
        if not path.exists():
            print(f"  Skipping {area}: {path} not found", file=sys.stderr)
            continue
        with open(path) as f:
            for line in f:
                n_raw += 1
                ex = json.loads(line)
                eid = ex["meta"]["example_id"]
                if eid in seen:
                    continue
                seen.add(eid)
                combined.append(ex)
    dropped = n_raw - len(combined)
    if dropped:
        print(f"  Deduplication: dropped {dropped} exact-duplicate example(s) ({n_raw} -> {len(combined)}).")
    return combined


def stratify_key(example: dict) -> str:
    """Return a stratification bucket key for an example."""
    task = example["meta"]["task_type"]
    gl = example["meta"]["gold_labels"]
    if task == "teaching_program":
        return f"t1:{gl['method']}"
    return f"t2:{gl['pattern_class']}"


def stratified_split(
    examples: list[dict],
    train_ratio: float,
    valid_ratio: float,
    curation_ratio: float,
    rng: random.Random,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Stratified three-way split preserving per-bucket proportions."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for ex in examples:
        buckets[stratify_key(ex)].append(ex)

    train, valid, curation = [], [], []
    for key in sorted(buckets.keys()):
        items = buckets[key]
        rng.shuffle(items)
        n = len(items)
        n_train = int(round(n * train_ratio))
        n_valid = int(round(n * valid_ratio))
        n_curation = n - n_train - n_valid
        # Guarantee at least 1 per split if bucket is large enough
        if n >= 10:
            n_valid = max(1, n_valid)
            n_curation = max(1, n_curation)
            n_train = n - n_valid - n_curation
        train.extend(items[:n_train])
        valid.extend(items[n_train : n_train + n_valid])
        curation.extend(items[n_train + n_valid :])
    rng.shuffle(train)
    rng.shuffle(valid)
    rng.shuffle(curation)
    return train, valid, curation


def write_jsonl(examples: list[dict], path: Path) -> None:
    with open(path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out-dir", type=str, default=None)
    args = parser.parse_args()

    gen_config = load_yaml(CONFIG_DIR / "generation.yaml")
    seed = args.seed if args.seed is not None else gen_config["seed"]
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / gen_config["output_dir"]

    splits_cfg = gen_config["splits"]
    tr = splits_cfg["train"]
    va = splits_cfg["valid"]
    cu = splits_cfg["curation_pool"]
    if abs(tr + va + cu - 1.0) >= 1e-6:
        raise ValueError(f"Splits must sum to 1.0 (got {tr + va + cu})")

    # Collect enabled areas that have output files
    enabled_areas = [a for a, c in gen_config["areas"].items() if c.get("enabled")]
    examples = load_all_area_files(out_dir, enabled_areas)
    print(f"Loaded {len(examples)} total examples from {len(enabled_areas)} areas.\n")

    rng = random.Random(seed)
    train, valid, curation = stratified_split(examples, tr, va, cu, rng)

    write_jsonl(train, out_dir / "train.jsonl")
    write_jsonl(valid, out_dir / "valid.jsonl")
    write_jsonl(curation, out_dir / "curation_pool.jsonl")

    print("Splits written:")
    print(f"  train.jsonl          {len(train):5d} ({100*len(train)/len(examples):.1f}%)")
    print(f"  valid.jsonl          {len(valid):5d} ({100*len(valid)/len(examples):.1f}%)")
    print(f"  curation_pool.jsonl  {len(curation):5d} ({100*len(curation)/len(examples):.1f}%)")
    print()
    print("Curation pool is the source for the author-curated test (100) + sanity (20) splits.")

    # Sanity: report per-bucket balance in curation_pool
    bucket_counts = defaultdict(int)
    for ex in curation:
        bucket_counts[stratify_key(ex)] += 1
    print("\nCuration-pool stratification:")
    for key, c in sorted(bucket_counts.items()):
        print(f"  {key:45s} {c:3d}")


if __name__ == "__main__":
    main()
