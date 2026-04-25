"""NET area generator.

Loads configs/net/ + configs/shared/ and produces naturalistic teaching
program examples. Mand / Social / Spontaneous Vocal / some Intraverbal skills.
"""

import random
from pathlib import Path

from .base import (
    load_area,
    load_shared,
    make_example_envelope,
)

AREA = "net"
TASK_TYPE = "teaching_program"


def pick_mo_category(skill_target: str, domain_id: str, compat: dict) -> str:
    """Match skill text against domain + keyword rules to pick an MO category.

    Domain is checked first to avoid false matches from shared keywords
    (e.g., 'preferred' in both mand skills and spontaneous-vocal skills).
    """
    s = skill_target.lower()

    if domain_id == "mand":
        if "bathroom" in s or "potty" in s or "toilet" in s or "restroom" in s:
            return "mand_bathroom"
        if "break" in s:
            return "mand_break"
        if "all done" in s or "completion" in s or "finished" in s:
            return "mand_completion"
        if "missing" in s:
            return "mand_missing"
        if "help" in s:
            return "mand_help"
        if '"what"' in s or "what" in s.split():
            return "mand_info_what"
        if '"where"' in s or "where" in s.split():
            return "mand_info_where"
        if "attention" in s or "peers" in s:
            return "mand_attention"
        if "action" in s:
            return "mand_action"
        return "mand_item"

    if domain_id == "social":
        if "initiate" in s or "initiates" in s:
            return "social_initiation"
        if "turn" in s:
            return "social_turn_taking"
        if "reciprocal" in s or "conversation" in s:
            return "intraverbal_multi_turn"
        return "social_initiation"

    if domain_id == "spontaneous_vocal":
        if "greet" in s:
            return "spontaneous_greeting"
        return "spontaneous_comment"

    if domain_id == "intraverbal":
        if "multi-turn" in s or "conversation" in s:
            return "intraverbal_multi_turn"
        if "routine" in s:
            return "intraverbal_routine"
        return "intraverbal_multi_turn"

    return compat["default_mo_category"]


def pick_mo_arrangement(mo_category: str, mo_arrangements: list, rng: random.Random) -> dict:
    """Find an MO arrangement matching the category, falling back to random."""
    matches = [m for m in mo_arrangements if mo_category in m["applies_to"]]
    if matches:
        return rng.choice(matches)
    return rng.choice(mo_arrangements)


def current_prompt_guidance(mastery_state_id: str) -> str:
    """Guidance for NET prompt level based on mastery state."""
    if mastery_state_id in {"emerging", "developing"}:
        return "begin with a model prompt delivered during the motivated moment; fade to expectant look across sessions."
    if mastery_state_id == "approaching":
        return "use time delay (0 s -> 2 s -> 4 s) before delivering any model prompt; reinforce independent responses differentially."
    if mastery_state_id in {"near", "mastered", "generalization"}:
        return "use expectant look only; avoid direct prompts. The MO itself should be sufficient to occasion the response."
    return "prompt level calibrated to current performance."


class NETGenerator:
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.shared = load_shared(self.config_dir)
        self.area = load_area(self.config_dir, AREA)
        self.template = self.area["template"]
        self.taxonomy = self.area["taxonomy"]
        self.compat = self.area["compatibility"]

    def sample_combination(self, rng: random.Random) -> dict:
        # Level with weights
        level_weights = self.compat["level_sampling_weights"]
        levels = list(level_weights.keys())
        weights = [level_weights[k] for k in levels]
        level_id = rng.choices(levels, weights=weights)[0]

        # Sample domain with a level match
        all_domains = self.taxonomy["skill_domains"]["vbmapp"]["domains"]
        domains_with_level = [d for d in all_domains if level_id in d]
        if not domains_with_level:
            domain = rng.choice(all_domains)
            available_levels = [lv for lv in levels if lv in domain]
            level_id = rng.choice(available_levels)
        else:
            domain = rng.choice(domains_with_level)
        skill_target = rng.choice(domain[level_id])

        # Learner profile
        profiles = self.shared["learner_profiles"]["profiles"]
        allowed = set(self.compat["level_to_learner_profiles"][level_id])
        profile = rng.choice([p for p in profiles if p["id"] in allowed])

        mastery_state = rng.choice(self.shared["mastery_states"]["states"])

        mo_category = pick_mo_category(skill_target, domain["id"], self.compat)
        mo_arrangement = pick_mo_arrangement(mo_category, self.taxonomy["mo_arrangements"], rng)
        natural_context = rng.choice(
            mo_arrangement.get("context_examples") or self.taxonomy["natural_contexts"]
        )
        prompt_strategy = rng.choice(self.taxonomy["prompt_strategies"])
        mastery_criterion = rng.choice(self.taxonomy["mastery_criteria"])

        return {
            "skill_target": skill_target,
            "domain_id": domain["id"],
            "domain_name": domain["name"],
            "level_id": level_id,
            "learner_profile": profile,
            "mastery_state": mastery_state,
            "mo_category": mo_category,
            "mo_arrangement": mo_arrangement,
            "natural_context": natural_context,
            "prompt_strategy": prompt_strategy,
            "mastery_criterion": mastery_criterion,
        }

    def compute_slots(self, combo: dict, rng: random.Random) -> dict:
        mastery_state = combo["mastery_state"]
        reinforcer_map = self.taxonomy["natural_reinforcer_examples"]
        natural_reinforcer = reinforcer_map.get(combo["mo_category"], reinforcer_map["default"])

        # Build a natural-opportunity description from the MO arrangement + natural context
        opportunity_text = (
            f"Embed the teaching opportunity within the learner's {combo['natural_context']} routine. "
            f"Deliver the opportunity when the MO is evident (learner oriented to the relevant stimulus, approaching the materials, or demonstrating interest)."
        )

        return {
            "skill_target": combo["skill_target"],
            "curriculum_ref": f"{combo['domain_name']} {combo['level_id']}",
            "learner_profile_name": combo["learner_profile"]["name"],
            "mastery_state_name": mastery_state["name"],
            "mastery_state_short": mastery_state.get("short", mastery_state["name"].lower()),
            "mo_arrangement_text": combo["mo_arrangement"]["text"],
            "primary_natural_context": combo["natural_context"],
            "natural_opportunity_text": opportunity_text,
            "prompt_strategy_name": combo["prompt_strategy"]["name"],
            "prompt_strategy_description": combo["prompt_strategy"]["description"],
            "current_prompt_guidance": current_prompt_guidance(mastery_state["id"]),
            "natural_reinforcer_text": f"Natural reinforcer: {natural_reinforcer}",
            "n_exemplars": rng.choice([3, 4, 5]),
            "n_settings": rng.choice([2, 3]),
            "n_therapists": rng.choice([2, 3]),
            "mastery_criterion_text": combo["mastery_criterion"]["text"],
            "ioa_frequency": rng.choice([3, 4, 5]),
        }

    def render_example(self, rng: random.Random) -> dict:
        combo = self.sample_combination(rng)
        slots = self.compute_slots(combo, rng)

        user_variant = rng.choice(self.template["user_variants"])
        user_content = user_variant.format(**slots)
        assistant_content = self.template["assistant_template"].format(**slots)

        gold_labels = {
            "method": AREA,
            "domain": f"VB-MAPP.{combo['domain_id']}",
            "level": combo["level_id"],
            "learner_profile": combo["learner_profile"]["id"],
            "mastery_state": combo["mastery_state"]["id"],
        }
        provenance = {
            "layer": 1,
            "area": AREA,
            "template_id": self.template["template_id"],
            "taxonomy_cells": {
                "skill_target": combo["skill_target"],
                "mo_category": combo["mo_category"],
                "mo_arrangement": combo["mo_arrangement"]["id"],
                "prompt_strategy": combo["prompt_strategy"]["id"],
                "mastery_criterion": combo["mastery_criterion"]["id"],
            },
            "teacher_model": None,
            "seed_tag": str(rng.getstate()[1][0] % 100000),
        }

        return make_example_envelope(
            system_content=self.template["system_prompt"],
            user_content=user_content,
            assistant_content=assistant_content,
            task_type=TASK_TYPE,
            gold_labels=gold_labels,
            provenance=provenance,
        )
