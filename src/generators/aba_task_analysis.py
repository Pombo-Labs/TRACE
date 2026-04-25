"""Task Analysis / Chaining area generator.

Loads configs/task_analysis/ + configs/shared/ and produces chaining
teaching program examples for AFLS modules (Basic Living, Home, Community,
Vocational, Independent Living).
"""

import random
from pathlib import Path

from .base import (
    load_area,
    load_shared,
    load_yaml,
    make_example_envelope,
)

AREA = "task_analysis"
TASK_TYPE = "teaching_program"


# Mastery state -> which shaping step the learner is currently at (as index range
# within the shaping_steps list). 0-indexed, end-exclusive.
TOLERATION_MASTERY_STEP_RANGES = {
    "emerging": (0, 2),
    "developing": (1, 3),
    "approaching": (2, 4),
    "near": (3, 5),
    "mastered": (4, 6),
    "generalization": (5, 7),
}


def current_shaping_step_guidance(mastery_state_id: str, shaping_steps: list) -> str:
    """Describe where the learner is currently sitting in the shaping progression."""
    n = len(shaping_steps)
    lo, hi = TOLERATION_MASTERY_STEP_RANGES.get(mastery_state_id, (0, 2))
    lo = max(0, min(lo, n - 1))
    hi = max(lo + 1, min(hi, n))
    idx = min(lo, n - 1)
    return (
        f"begin at shaping step {idx + 1} (\"{shaping_steps[idx]}\") and advance through "
        f"step {hi} across sessions as tolerance stabilizes."
    )


def render_shaping_steps(shaping_steps: list) -> str:
    """Render numbered shaping progression."""
    return "\n".join(f"{i}. {step}" for i, step in enumerate(shaping_steps, 1))


def current_prompt_guidance(mastery_state_id: str, prompt_strategy_id: str) -> str:
    """Guidance for chaining prompt level at the current mastery state."""
    if mastery_state_id in {"emerging", "developing"}:
        if prompt_strategy_id == "graduated_guidance":
            return "provide hand-over-hand guidance at each step; reduce physical pressure across sessions."
        return "use full-physical or partial-physical prompts at each step; fade systematically."
    if mastery_state_id == "approaching":
        return "use partial-physical or gestural prompts only at steps where errors occur; allow independence elsewhere."
    if mastery_state_id in {"near", "mastered", "generalization"}:
        return "deliver the least intrusive prompt that prevents an error; expect independence on previously-mastered steps."
    return "prompt level calibrated to current performance."


def render_steps(step_list: list, chain_type_id: str) -> str:
    """Render numbered step list, with callout of the learner-taught step for backward chaining."""
    lines = []
    for i, step in enumerate(step_list, 1):
        if chain_type_id == "backward" and i == len(step_list):
            lines.append(f"{i}. {step}  <- Learner-taught step (backward chaining starts here)")
        elif chain_type_id == "forward" and i == 1:
            lines.append(f"{i}. {step}  <- Learner-taught step (forward chaining starts here)")
        else:
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def render_criterion_text(criterion: dict, rng: random.Random) -> str:
    """Fill any slots in the mastery-criterion text (e.g., fluency seconds)."""
    text = criterion["text"]
    if "{fluency_seconds}" in text:
        text = text.replace("{fluency_seconds}", str(rng.choice([60, 90, 120, 180])))
    return text


class TaskAnalysisGenerator:
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.shared = load_shared(self.config_dir)
        self.area = load_area(self.config_dir, AREA)
        self.template = self.area["template"]                        # chain-based (independence)
        self.template_toleration = load_yaml(
            self.config_dir / AREA / "template_toleration.yaml"
        )
        self.taxonomy = self.area["taxonomy"]
        self.compat = self.area["compatibility"]

    def sample_combination(self, rng: random.Random) -> dict:
        # Weighted module selection
        module_weights = self.compat["module_sampling_weights"]
        modules = self.taxonomy["afls"]["modules"]
        module_ids = [m["id"] for m in modules]
        weights = [module_weights[mid] for mid in module_ids]
        module = rng.choices(modules, weights=weights)[0]

        # Sample a skill from the module
        skill_entry = rng.choice(module["skills"])
        skill_target = skill_entry["name"]
        is_toleration = skill_entry.get("program_type") == "toleration"

        # Learner profile — intersect module's allowed with the (shared) learner list
        profiles = self.shared["learner_profiles"]["profiles"]
        module_allowed = set(module["learner_profiles"])
        profile = rng.choice([p for p in profiles if p["id"] in module_allowed])

        mastery_state = rng.choice(self.shared["mastery_states"]["states"])

        # Filter mastery criteria by program type (independence vs toleration)
        program_type = "toleration" if is_toleration else "independence"
        eligible_criteria = [
            c for c in self.taxonomy["mastery_criteria"]
            if c.get("applies_to", "independence") == program_type
        ]
        if not eligible_criteria:
            eligible_criteria = self.taxonomy["mastery_criteria"]
        mastery_criterion = rng.choice(eligible_criteria)

        if is_toleration:
            # Toleration programs: duration-based shaping, no chain / prompt / EC fields needed.
            return {
                "skill_target": skill_target,
                "program_type": "toleration",
                "shaping_steps": skill_entry["shaping_steps"],
                "target_activity": skill_entry["target_activity"],
                "end_goal_description": skill_entry["end_goal_description"],
                "module_id": module["id"],
                "module_name": module["name"],
                "learner_profile": profile,
                "mastery_state": mastery_state,
                "mastery_criterion": mastery_criterion,
            }

        # Independence (chain-based) program — existing path
        steps = skill_entry["steps"]
        preferred_chain = skill_entry.get("chain_type_preferred", "total_task")

        if rng.random() < self.compat["use_preferred_chain_type_probability"]:
            chain_type = next(c for c in self.taxonomy["chain_types"] if c["id"] == preferred_chain)
        else:
            chain_type = rng.choice(self.taxonomy["chain_types"])

        allowed_strategy_ids = set(self.compat["mastery_to_prompt_strategies"][mastery_state["id"]])
        valid_strategies = [s for s in self.taxonomy["prompt_hierarchies"] if s["id"] in allowed_strategy_ids]
        if not valid_strategies:
            valid_strategies = self.taxonomy["prompt_hierarchies"]
        prompt_strategy = rng.choice(valid_strategies)

        allowed_schedule_ids = set(self.compat["mastery_to_reinforcement"][mastery_state["id"]])
        valid_schedules = [s for s in self.taxonomy["reinforcement_schedules"] if s["id"] in allowed_schedule_ids]
        if not valid_schedules:
            valid_schedules = [s for s in self.taxonomy["reinforcement_schedules"] if s["id"] == "crf_per_step"]
        reinforcement_schedule = rng.choice(valid_schedules)

        error_correction = rng.choice(self.taxonomy["error_corrections"])

        return {
            "skill_target": skill_target,
            "program_type": "independence",
            "steps": steps,
            "module_id": module["id"],
            "module_name": module["name"],
            "chain_type": chain_type,
            "learner_profile": profile,
            "mastery_state": mastery_state,
            "prompt_strategy": prompt_strategy,
            "reinforcement_schedule": reinforcement_schedule,
            "error_correction": error_correction,
            "mastery_criterion": mastery_criterion,
        }

    def compute_slots(self, combo: dict, rng: random.Random) -> dict:
        mastery_state = combo["mastery_state"]
        common = {
            "skill_target": combo["skill_target"],
            "curriculum_ref": f"AFLS {combo['module_name']}",
            "learner_profile_name": combo["learner_profile"]["name"],
            "mastery_state_name": mastery_state["name"],
            "mastery_state_short": mastery_state.get("short", mastery_state["name"].lower()),
            "mastery_criterion_text": render_criterion_text(combo["mastery_criterion"], rng),
            "ioa_frequency": rng.choice([3, 4, 5]),
            "n_generalization_settings": rng.choice([2, 3]),
            "n_generalization_therapists": rng.choice([2, 3]),
        }

        if combo["program_type"] == "toleration":
            return {
                **common,
                "target_activity": combo["target_activity"],
                "end_goal_description": combo["end_goal_description"],
                "shaping_step_list": render_shaping_steps(combo["shaping_steps"]),
                "current_step_guidance": current_shaping_step_guidance(
                    mastery_state["id"], combo["shaping_steps"]
                ),
            }

        # Independence (chain-based)
        ec_steps_clean = combo["error_correction"]["steps"].strip()
        return {
            **common,
            "chain_type_name": combo["chain_type"]["name"],
            "chain_type_description": combo["chain_type"]["description"],
            "step_list": render_steps(combo["steps"], combo["chain_type"]["id"]),
            "prompt_strategy_name": combo["prompt_strategy"]["name"],
            "prompt_strategy_description": combo["prompt_strategy"]["description"],
            "current_prompt_guidance": current_prompt_guidance(mastery_state["id"], combo["prompt_strategy"]["id"]),
            "error_correction_name": combo["error_correction"]["name"],
            "error_correction_steps": ec_steps_clean.rstrip("."),
            "reinforcement_schedule_name": combo["reinforcement_schedule"]["name"],
            "reinforcement_description": combo["reinforcement_schedule"]["description"].rstrip("."),
        }

    def render_example(self, rng: random.Random) -> dict:
        combo = self.sample_combination(rng)
        slots = self.compute_slots(combo, rng)

        template = (
            self.template_toleration
            if combo["program_type"] == "toleration"
            else self.template
        )
        user_variant = rng.choice(template["user_variants"])
        user_content = user_variant.format(**slots)
        assistant_content = template["assistant_template"].format(**slots)

        gold_labels = {
            "method": AREA,
            "domain": f"AFLS.{combo['module_id']}",
            "skill": combo["skill_target"],
            "program_type": combo["program_type"],
            "learner_profile": combo["learner_profile"]["id"],
            "mastery_state": combo["mastery_state"]["id"],
        }
        if combo["program_type"] == "independence":
            gold_labels["chain_type"] = combo["chain_type"]["id"]

        taxonomy_cells = {
            "skill_target": combo["skill_target"],
            "module": combo["module_id"],
            "mastery_criterion": combo["mastery_criterion"]["id"],
        }
        if combo["program_type"] == "independence":
            taxonomy_cells.update({
                "chain_type": combo["chain_type"]["id"],
                "prompt_strategy": combo["prompt_strategy"]["id"],
                "reinforcement_schedule": combo["reinforcement_schedule"]["id"],
                "error_correction": combo["error_correction"]["id"],
            })
        else:
            taxonomy_cells["shaping_n_steps"] = len(combo["shaping_steps"])

        provenance = {
            "layer": 1,
            "area": AREA,
            "template_id": template["template_id"],
            "taxonomy_cells": taxonomy_cells,
            "teacher_model": None,
            "seed_tag": str(rng.getstate()[1][0] % 100000),
        }

        return make_example_envelope(
            system_content=template["system_prompt"],
            user_content=user_content,
            assistant_content=assistant_content,
            task_type=TASK_TYPE,
            gold_labels=gold_labels,
            provenance=provenance,
        )
