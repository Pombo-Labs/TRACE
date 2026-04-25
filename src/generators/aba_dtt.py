"""DTT area generator.

Loads configs/dtt/ + configs/shared/ and produces JSONL examples with
clinically-consistent combinations sampled from the DTT taxonomy.
"""

import random
from pathlib import Path

from .base import (
    article,
    load_area,
    load_shared,
    render_prompt_sequence,
    sample_stimuli,
    strip_trailing_period,
    make_example_envelope,
)

# Area identifier + task type
AREA = "dtt"
TASK_TYPE = "teaching_program"


# SD (Discriminative Stimulus) generation — clinically nuanced


def generate_sd(skill_target: str, domain_id: str, rng: random.Random) -> dict:
    """Generate primary SD, variations, and presentation description.

    Sub-domain aware: Tact-of-colors gets "What color?", not "What is this?".
    """
    skill = skill_target.lower()

    if domain_id == "tact":
        if "color" in skill:
            return _sd("What color?", '"What color is this?"; "Tell me the color"',
                       "Present a single-color object and ask while pointing to it.")
        if "shape" in skill:
            return _sd("What shape?", '"What shape is this?"; "Tell me the shape"',
                       "Present a clearly-shaped object or shape card and ask while pointing to it.")
        if "action" in skill:
            return _sd("What is he doing?", '"What action?"; "What is she doing?"; "What is happening here?"',
                       "Present an action picture, video clip, or live demonstration.")
        if "emotion" in skill or "feeling" in skill:
            return _sd("How does he feel?", '"What emotion?"; "How is she feeling?"',
                       "Present a photograph or emoji card depicting the target emotion.")
        if "body part" in skill:
            return _sd("What is this?", '"Tell me"; "Name this body part"',
                       "Point to the target body part (on self, learner, or doll) and ask.")
        if "animal" in skill:
            return _sd("What animal is this?", '"What is this?"; "Name this animal"',
                       "Present an animal picture card and ask while pointing.")
        if "preposition" in skill:
            return _sd("Where is it?", '"Where is the {object}?"; "Tell me where"',
                       "Arrange two objects in a target spatial relation and ask about the position.")
        if "adjective" in skill:
            return _sd("What is it like?", '"Describe it"; "Is it big or little?"',
                       "Present two contrasting items and prompt a comparative description.")
        if "past" in skill or "event" in skill:
            return _sd("What happened?", '"What did she do?"; "Tell me what you did"',
                       "Reference a recently completed action or event familiar to the learner.")
        if "categor" in skill:
            return _sd("What category?", '"What group does this belong to?"; "What kind of thing?"',
                       "Present a clearly categorizable item and prompt the category label.")
        return _sd("What is this?", '"Tell me what you see"; "What\'s that?"; "Name this"',
                   "Present the target stimulus within visual field and ask while pointing to it.")

    if domain_id == "vp_mts":
        return _sd("Match", '"Find the same"; "Put with same"',
                   "Present the sample stimulus and an array of comparison stimuli simultaneously.")

    if domain_id in {"listener_responding", "lrffc"}:
        return _sd("Touch [target item]",
                   '"Point to [target item]"; "Give me [target item]"; "Show me [target item]"',
                   "Present an array of items on the table and deliver a clear verbal SD.")

    if domain_id == "reading":
        if "sight word" in skill or "word" in skill:
            return _sd("What word?", '"Read this word"; "What does it say?"',
                       "Present the sight-word card and deliver the SD.")
        if "letter" in skill:
            return _sd("What letter is this?", '"Read this letter"; "What does this say?"',
                       "Present the letter flashcard.")
        if "sentence" in skill or "passage" in skill:
            return _sd("Read this.", '"Read it aloud"; "What does this sentence say?"',
                       "Present the written sentence or passage at an appropriate reading level.")
        return _sd("What letter is this?", '"Read this letter"; "What does this say?"',
                   "Present the letter or word on a flashcard.")

    if domain_id == "writing":
        return _sd("Write the target.", '"Trace this"; "Copy this"; "Write {word}"',
                   "Provide pencil and paper; deliver a clear verbal instruction naming the target letter or word.")

    if domain_id == "math":
        if "numeral" in skill or "identif" in skill:
            return _sd("What number is this?", '"Which number?"; "Tell me the number"',
                       "Present the numeral card.")
        if "count" in skill:
            return _sd("How many?", '"Count these"; "How many are there?"',
                       "Present the set of objects to count.")
        if "add" in skill or "subtract" in skill:
            return _sd("Solve this.", '"What is the answer?"; "How much?"',
                       "Present a written or spoken arithmetic problem at target level.")
        return _sd("How many?", '"Count these"; "What number is this?"',
                   "Present the numeral card or a set of objects to count.")

    return _sd("Show me", '"Do this"; "Your turn"',
               "Present relevant stimuli and deliver a clear verbal SD.")


def _sd(primary: str, variations: str, presentation: str) -> dict:
    return {"primary_sd": primary, "sd_variations": variations, "sd_presentation": presentation}


def current_prompt_guidance(mastery_state_id: str) -> str:
    """Translate mastery state into current-prompt-level guidance."""
    if mastery_state_id in {"emerging", "developing"}:
        return "begin at higher prompt levels (full-physical or partial-physical) with systematic fading."
    if mastery_state_id == "approaching":
        return "deliver gestural or positional prompts; fade toward independence."
    if mastery_state_id in {"near", "mastered", "generalization"}:
        return "use minimal prompts (positional or verbal hint) only when needed; expect independent responding."
    return "prompt level calibrated to current performance."


# DTTGenerator class


class DTTGenerator:
    """Generates teaching-program examples for the DTT area.

    Loads its self-contained taxonomy + template + compatibility rules from
    configs/dtt/ and uses shared primitives from configs/shared/.
    """

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.shared = load_shared(self.config_dir)
        self.area = load_area(self.config_dir, AREA)
        self.template = self.area["template"]
        self.taxonomy = self.area["taxonomy"]
        self.compat = self.area["compatibility"]
        self.prompt_types = self.shared["prompt_types"]["prompt_types"]

    # sampling

    def sample_combination(self, rng: random.Random) -> dict:
        """Sample a clinically-valid DTT combo."""
        # Sample level with weights from compatibility config
        level_weights = self.compat["level_sampling_weights"]
        levels = list(level_weights.keys())
        weights = [level_weights[k] for k in levels]
        level_id = rng.choices(levels, weights=weights)[0]

        # Sample domain — filter to only those that define this level (some
        # domains like Writing don't have L3 in the DTT taxonomy because
        # long-form writing is Task Analysis territory).
        all_domains = self.taxonomy["skill_domains"]["vbmapp"]["domains"]
        domains_with_level = [d for d in all_domains if level_id in d]
        if not domains_with_level:
            # Fall back: pick from all domains and re-sample a level they support
            domain = rng.choice(all_domains)
            available_levels = [lv for lv in levels if lv in domain]
            level_id = rng.choice(available_levels)
        else:
            domain = rng.choice(domains_with_level)
        skill_target = rng.choice(domain[level_id])

        # Learner profile filtered by level
        profiles = self.shared["learner_profiles"]["profiles"]
        allowed_profile_ids = set(self.compat["level_to_learner_profiles"][level_id])
        profile = rng.choice([p for p in profiles if p["id"] in allowed_profile_ids])

        mastery_state = rng.choice(self.shared["mastery_states"]["states"])

        # Prompt hierarchy then error-correction (filtered for errorless compat)
        prompt_hierarchy = rng.choice(self.taxonomy["prompt_hierarchies"])
        all_ecs = self.taxonomy["error_corrections"]
        required_hierarchy = self.compat.get("errorless_requires_hierarchy")
        if prompt_hierarchy["id"] != required_hierarchy:
            valid_ecs = [ec for ec in all_ecs if ec["id"] != "errorless"]
        else:
            valid_ecs = all_ecs
        error_correction = rng.choice(valid_ecs)

        # Reinforcement schedule filtered by mastery state
        all_schedules = self.taxonomy["reinforcement_schedules"]
        allowed_schedule_ids = set(self.compat["mastery_to_reinforcement"][mastery_state["id"]])
        valid_schedules = [s for s in all_schedules if s["id"] in allowed_schedule_ids]
        if not valid_schedules:
            valid_schedules = [s for s in all_schedules if s["id"] == "crf"]
        reinforcement_schedule = rng.choice(valid_schedules)

        mastery_criterion = rng.choice(self.taxonomy["mastery_criteria"])

        return {
            "skill_target": skill_target,
            "domain_id": domain["id"],
            "domain_name": domain["name"],
            "level_id": level_id,
            "learner_profile": profile,
            "mastery_state": mastery_state,
            "prompt_hierarchy": prompt_hierarchy,
            "reinforcement_schedule": reinforcement_schedule,
            "error_correction": error_correction,
            "mastery_criterion": mastery_criterion,
        }

    # slot computation

    def compute_slots(self, combo: dict, rng: random.Random) -> dict:
        array_size_info = self.compat["array_size_by_level"][combo["level_id"]]
        array_size_n = array_size_info["n"]
        array_size_text = array_size_info["text"]

        sd = generate_sd(combo["skill_target"], combo["domain_id"], rng)
        stim = sample_stimuli(combo["skill_target"], array_size_n, rng)

        if stim["distractors"]:
            distractor_block = f"Distractor stimuli: {', '.join(stim['distractors'])}"
        else:
            distractor_block = "Distractor stimuli: N/A (no-array SD format)"

        mastery_state = combo["mastery_state"]

        return {
            "skill_target": combo["skill_target"],
            "curriculum_ref": f"{combo['domain_name']} {combo['level_id']}",
            "learner_profile_name": combo["learner_profile"]["name"],
            "learner_profile_article": article(combo["learner_profile"]["name"]),
            "mastery_state_name": mastery_state["name"],
            "mastery_state_short": mastery_state.get("short", mastery_state["name"].lower()),
            "primary_sd": sd["primary_sd"],
            "sd_variations": sd["sd_variations"],
            "sd_presentation": sd["sd_presentation"],
            "prompt_hierarchy_name": combo["prompt_hierarchy"]["name"],
            "prompt_sequence": render_prompt_sequence(
                combo["prompt_hierarchy"]["sequence"], self.prompt_types
            ),
            "current_prompt_guidance": current_prompt_guidance(mastery_state["id"]),
            "array_size": array_size_text,
            "target_stimuli": ", ".join(stim["targets"]),
            "distractor_block": distractor_block,
            "error_correction_steps": combo["error_correction"]["steps"].strip(),
            "reinforcement_schedule_name": combo["reinforcement_schedule"]["name"],
            "reinforcement_description": strip_trailing_period(combo["reinforcement_schedule"]["description"]),
            "mastery_criterion_text": combo["mastery_criterion"]["text"],
            "ioa_frequency": rng.choice([3, 4, 5]),
            "n_generalization_therapists": rng.choice([2, 3]),
            "n_generalization_settings": rng.choice([2, 3]),
        }

    # rendering

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
                "prompt_hierarchy": combo["prompt_hierarchy"]["id"],
                "reinforcement_schedule": combo["reinforcement_schedule"]["id"],
                "error_correction": combo["error_correction"]["id"],
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
