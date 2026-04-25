"""Render curation_pool.jsonl as a readable review document.

This used to drive a hand-curation workflow with decisions.csv; we now
use the whole curation pool as our test set (see compile_curation.py).
review.md is still produced as a human-readable browse of the test
corpus so clinical issues can be flagged ad hoc and fixed in the
generator configs.

Usage:
    uv run python src/prepare_curation.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POOL_PATH = REPO_ROOT / "data" / "splits" / "curation_pool.jsonl"
REVIEW_MD = REPO_ROOT / "docs" / "curation" / "review.md"


def category_of(example: dict) -> str:
    """Short category label for a candidate."""
    gl = example["meta"]["gold_labels"]
    if example["meta"]["task_type"] == "teaching_program":
        return gl.get("method", "?")
    return gl.get("pattern_class", "?")


def gold_labels_markdown(example: dict) -> str:
    """Render gold labels inline for the review markdown."""
    gl = example["meta"]["gold_labels"]
    bits = []
    for k, v in gl.items():
        if isinstance(v, dict):
            inner = ", ".join(f"{ik}->{iv}" for ik, iv in v.items())
            bits.append(f"**{k}:** {{{inner}}}")
        elif isinstance(v, bool):
            bits.append(f"**{k}:** {str(v).lower()}")
        else:
            bits.append(f"**{k}:** `{v}`")
    return " · ".join(bits)


def provenance_markdown(example: dict) -> str:
    """Render a short provenance line."""
    prov = example["meta"].get("provenance", {})
    bits = []
    if "n_sessions" in prov:
        bits.append(f"{prov['n_sessions']} sessions")
    if "n_behaviors" in prov:
        bits.append(f"{prov['n_behaviors']} behaviors")
    if "has_ioa_session" in prov:
        bits.append("IOA ✓" if prov["has_ioa_session"] else "no IOA")
    if "has_abc_data" in prov:
        bits.append("ABC ✓" if prov["has_abc_data"] else "no ABC")
    return " · ".join(bits) if bits else ""


def render_candidate(idx: int, example: dict) -> str:
    """Render one candidate as a markdown block."""
    task = example["meta"]["task_type"]
    cat = category_of(example)
    example_id = example["meta"]["example_id"]
    user_content = example["messages"][1]["content"]
    assistant_content = example["messages"][2]["content"]
    prov_str = provenance_markdown(example)
    prov_line = f"\n*{prov_str}*\n" if prov_str else "\n"

    return f"""
---

### Candidate {idx:03d} | `{task}` | `{cat}` | id `{example_id}`

**Gold labels:** {gold_labels_markdown(example)}
{prov_line}
<details>
<summary><strong>User message (click to expand)</strong></summary>

```
{user_content}
```

</details>

<details>
<summary><strong>Assistant response (click to expand)</strong></summary>

```
{assistant_content}
```

</details>
"""


def main() -> int:
    if not POOL_PATH.exists():
        print(f"Curation pool not found: {POOL_PATH}", file=sys.stderr)
        print("Run `uv run python src/split_data.py` first.", file=sys.stderr)
        return 1

    candidates: list[dict] = []
    with open(POOL_PATH) as f:
        for line in f:
            candidates.append(json.loads(line))

    # Group by category for diversity visibility.
    grouped_raw: dict[str, list[dict]] = {}
    for ex in candidates:
        key = f"{ex['meta']['task_type']} / {category_of(ex)}"
        grouped_raw.setdefault(key, []).append(ex)

    ordered: list[tuple[int, dict, str]] = []
    idx = 0
    for key in sorted(grouped_raw.keys()):
        for ex in grouped_raw[key]:
            idx += 1
            ordered.append((idx, ex, key))

    REVIEW_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_MD, "w") as f:
        f.write("# Corpus Review — TRACE test corpus\n\n")
        f.write(f"**{len(candidates)} examples** held out as the evaluation corpus.\n\n")
        f.write("## How to use this file\n")
        f.write("- Browse candidates below to spot clinical-accuracy issues "
                "(wrong topography, unrealistic scenario, inconsistent data, etc.).\n")
        f.write("- When you find one, note the candidate id (shown next to the candidate title). "
                "Fixes are applied by editing the generator configs in `configs/` and regenerating.\n")
        f.write("- The test + sanity splits are compiled from this pool by "
                "`uv run python src/compile_curation.py` (no per-example decisions required).\n\n")
        f.write("## Distribution\n\n")
        f.write("| Category | Count |\n|---|---|\n")
        for key in sorted(grouped_raw.keys()):
            f.write(f"| {key} | {len(grouped_raw[key])} |\n")
        f.write("\n---\n\n")
        f.write("## Candidates\n")
        current_group = None
        for idx, ex, key in ordered:
            if key != current_group:
                f.write(f"\n### Group: {key}\n")
                current_group = key
            f.write(render_candidate(idx, ex))

    print(f"Wrote: {REVIEW_MD}  ({len(candidates)} candidates)")
    print("Next: run `uv run python src/compile_curation.py` to produce test.jsonl + sanity.jsonl.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
