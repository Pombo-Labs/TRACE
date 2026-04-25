"""Compile test.jsonl + sanity.jsonl from curation_pool.jsonl.

No hand-curation: the whole curation pool is promoted as the
evaluation corpus. A small stratified slice is carved out for
sanity.jsonl (training smoke-test); the remainder becomes test.jsonl.

Stratification is by category (method for teaching programs,
pattern_class for session interpretation) so both splits reflect the
pool's distribution.

Reads:
    data/splits/curation_pool.jsonl

Writes:
    data/splits/test.jsonl
    data/splits/sanity.jsonl

Usage:
    uv run python src/compile_curation.py
    uv run python src/compile_curation.py --sanity-n 20 --seed 42
"""

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POOL_PATH = REPO_ROOT / "data" / "splits" / "curation_pool.jsonl"
TEST_JSONL = REPO_ROOT / "data" / "splits" / "test.jsonl"
SANITY_JSONL = REPO_ROOT / "data" / "splits" / "sanity.jsonl"


def category_of(example: dict) -> str:
    gl = example["meta"]["gold_labels"]
    if example["meta"]["task_type"] == "teaching_program":
        return gl.get("method", "?")
    return gl.get("pattern_class", "?")


def stratified_sanity_sample(
    pool: list[dict], sanity_n: int, rng: random.Random
) -> tuple[list[dict], list[dict]]:
    """Carve sanity_n stratified examples out of the pool; return (test, sanity)."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for ex in pool:
        by_cat[category_of(ex)].append(ex)

    # Largest-remainder method: allocate sanity slots proportional to category size.
    total = len(pool)
    raw_quotas = {cat: sanity_n * len(exs) / total for cat, exs in by_cat.items()}
    floor_quotas = {cat: int(q) for cat, q in raw_quotas.items()}
    remainder = sanity_n - sum(floor_quotas.values())
    # Distribute remaining slots by largest fractional part.
    fractional = sorted(
        raw_quotas.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True
    )
    for cat, _ in fractional[:remainder]:
        floor_quotas[cat] += 1

    sanity: list[dict] = []
    for cat, quota in floor_quotas.items():
        if quota <= 0:
            continue
        picks = rng.sample(by_cat[cat], min(quota, len(by_cat[cat])))
        sanity.extend(picks)

    sanity_ids = {ex["meta"]["example_id"] for ex in sanity}
    test = [ex for ex in pool if ex["meta"]["example_id"] not in sanity_ids]
    return test, sanity


def tag_split(example: dict, split_name: str) -> dict:
    """Deep-copy and stamp the curation split label into meta."""
    out = json.loads(json.dumps(example))
    out["meta"]["curation"] = {"target_split": split_name}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanity-n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not POOL_PATH.exists():
        print(f"Curation pool missing: {POOL_PATH}", file=sys.stderr)
        print("Run `uv run python src/split_data.py` first.", file=sys.stderr)
        return 1

    pool: list[dict] = []
    with open(POOL_PATH) as f:
        for line in f:
            pool.append(json.loads(line))

    if args.sanity_n >= len(pool):
        print(
            f"sanity_n ({args.sanity_n}) must be smaller than pool size ({len(pool)}).",
            file=sys.stderr,
        )
        return 1

    rng = random.Random(args.seed)
    test, sanity = stratified_sanity_sample(pool, args.sanity_n, rng)

    TEST_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(TEST_JSONL, "w") as f:
        for ex in test:
            f.write(json.dumps(tag_split(ex, "test")) + "\n")
    with open(SANITY_JSONL, "w") as f:
        for ex in sanity:
            f.write(json.dumps(tag_split(ex, "sanity")) + "\n")

    def fmt_dist(rows: list[dict]) -> str:
        c = Counter(category_of(r) for r in rows)
        return ", ".join(f"{k}={v}" for k, v in sorted(c.items()))

    print(f"Wrote:")
    print(f"  {TEST_JSONL}   {len(test)} examples  ({fmt_dist(test)})")
    print(f"  {SANITY_JSONL} {len(sanity)} examples  ({fmt_dist(sanity)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
