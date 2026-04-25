"""Shared base utilities for per-area generators.

This module is domain-agnostic. Area-specific logic lives in
`aba_<area>.py` modules.
"""

import random
import re
from pathlib import Path

import yaml

# ============================================================
# YAML loading
# ============================================================


def load_yaml(path: Path) -> dict:
    """Load a single YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_shared(config_dir: Path) -> dict:
    """Load the shared primitives used across all areas.

    Returns a dict keyed by primitive name:
        learner_profiles, mastery_states, prompt_types
    """
    shared_dir = Path(config_dir) / "shared"
    return {
        "learner_profiles": load_yaml(shared_dir / "learner_profiles.yaml"),
        "mastery_states": load_yaml(shared_dir / "mastery_states.yaml"),
        "prompt_types": load_yaml(shared_dir / "prompt_types.yaml"),
    }


def load_area(config_dir: Path, area: str) -> dict:
    """Load an area's self-contained config: taxonomy + template + compatibility."""
    area_dir = Path(config_dir) / area
    if not area_dir.is_dir():
        raise FileNotFoundError(f"Area config directory not found: {area_dir}")
    return {
        "taxonomy": load_yaml(area_dir / "taxonomy.yaml"),
        "template": load_yaml(area_dir / "template.yaml"),
        "compatibility": load_yaml(area_dir / "compatibility.yaml"),
    }


# ============================================================
# Text / rendering utilities
# ============================================================


def article(word: str) -> str:
    """Return 'a' or 'an' appropriate for the following word."""
    if not word:
        return "a"
    return "an" if word[0].lower() in "aeiou" else "a"


def strip_trailing_period(text: str) -> str:
    """Remove a single trailing period — for safe mid-sentence embedding."""
    return text.rstrip().rstrip(".")


def render_prompt_sequence(hierarchy_sequence: list, prompt_types: list) -> str:
    """Render a prompt-hierarchy sequence as a human-readable arrow chain.

    Looks up each item in the canonical prompt_types list; falls back to
    underscore-to-space conversion for composite IDs like '0s_delay'.
    """
    id_to_name = {pt["id"]: pt["name"] for pt in prompt_types}
    rendered = []
    for seq_id in hierarchy_sequence:
        if seq_id in id_to_name:
            rendered.append(id_to_name[seq_id].lower())
        else:
            rendered.append(seq_id.replace("_", " "))
    return " -> ".join(rendered)


def parse_skill_numeric_range(skill_text: str):
    """Extract (min, max) numeric range from skill text.

    Handles patterns like '1-5', '1–5' (en-dash), 'to 10', '1-20'.
    Returns None if no range is present.
    """
    s = skill_text.lower()
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (min(lo, hi), max(lo, hi))
    m = re.search(r"to\s+(\d+)", s)
    if m:
        return (1, int(m.group(1)))
    return None


# ============================================================
# Shared stimulus pools (used by DTT-like array-based generators)
# ============================================================

STIMULUS_POOLS = {
    "objects": [
        "ball", "cup", "shoe", "spoon", "book", "car", "block", "brush", "key",
        "phone", "hat", "sock", "apple", "crayon", "scissors", "glue", "pencil",
        "napkin", "plate", "towel", "jacket", "backpack", "bottle", "blanket",
        "toothbrush",
    ],
    "colors": ["red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "black", "white"],
    "shapes": ["circle", "square", "triangle", "rectangle", "star", "diamond", "oval", "heart"],
    "animals": [
        "dog", "cat", "bird", "fish", "horse", "cow", "pig", "sheep", "rabbit",
        "frog", "bear", "lion", "elephant", "monkey", "duck", "chicken",
    ],
    "actions": [
        "running", "jumping", "eating", "sleeping", "reading", "writing",
        "drawing", "singing", "clapping", "washing", "brushing", "pouring",
    ],
    "letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "numbers": [str(n) for n in range(1, 21)],
}

SKILL_TO_POOL = [
    ("color", "colors"),
    ("shape", "shapes"),
    ("animal", "animals"),
    ("letter", "letters"),
    ("number", "numbers"),
    ("numeral", "numbers"),
    ("count", "numbers"),
    ("action", "actions"),
]


def choose_stimulus_pool(skill_target: str) -> str:
    """Pick the stimulus pool whose keyword appears in the skill name; default 'objects'."""
    s = skill_target.lower()
    for keyword, pool in SKILL_TO_POOL:
        if keyword in s:
            return pool
    return "objects"


def sample_stimuli(
    skill_target: str, array_size_n: int, rng: random.Random
) -> dict:
    """Pick target + distractor stimuli, respecting any numeric range in the skill text."""
    pool_name = choose_stimulus_pool(skill_target)
    pool = list(STIMULUS_POOLS[pool_name])

    rng_tuple = parse_skill_numeric_range(skill_target)
    if rng_tuple is not None:
        lo, hi = rng_tuple
        if pool_name == "numbers":
            pool = [str(n) for n in range(lo, hi + 1)]
        elif pool_name == "letters":
            pool = pool[: max(hi, 3)]

    n_targets = min(3, len(pool))
    targets = rng.sample(pool, n_targets)
    remaining = [x for x in pool if x not in targets]
    n_distractors = min(max(array_size_n - 1, 0), len(remaining))
    distractors = rng.sample(remaining, n_distractors) if n_distractors > 0 else []
    return {"targets": targets, "distractors": distractors}


# ============================================================
# Example envelope helpers
# ============================================================


import hashlib


def make_example_envelope(
    *,
    system_content: str,
    user_content: str,
    assistant_content: str,
    task_type: str,
    gold_labels: dict,
    provenance: dict,
) -> dict:
    """Assemble the final JSONL example dict with id + meta envelope.

    Envelope is a deterministic function of its inputs: identical inputs produce
    an identical envelope, including the example_id. The example_id is
    ``sha256(user_content + assistant_content)[:16]`` computed on the *published*
    (stripped) message content, so any consumer can verify it directly from the
    JSONL row. Per-run wall-clock timestamps are deliberately NOT included so
    that running the generator twice with the same seed produces byte-identical
    output.
    """
    system_content = system_content.strip()
    user_content = user_content.strip()
    assistant_content = assistant_content.strip()
    example_hash = hashlib.sha256(
        (user_content + assistant_content).encode()
    ).hexdigest()[:16]
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ],
        "meta": {
            "task_type": task_type,
            "example_id": example_hash,
            "gold_labels": gold_labels,
            "provenance": provenance,
        },
    }
