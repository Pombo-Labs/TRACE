"""Session Interpretation generator (Task 2).

Generates multi-session behavioral logs and matching structured interpretations.
The log is produced deterministically from a sampled hidden pattern so the
interpretation's gold labels are known by construction.
"""

import random
from datetime import date, timedelta
from pathlib import Path

from .base import (
    load_area,
    load_shared,
    load_yaml,
    strip_trailing_period,
    make_example_envelope,
)

AREA = "session_interpretation"
TASK_TYPE = "session_interpretation"


# Trajectory math — generate per-session accuracy values following a pattern rule


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def generate_accuracy_trajectory(pattern_id: str, rule: dict, n_sessions: int, rng: random.Random) -> list:
    """Return a list of accuracy values for n_sessions based on pattern rule."""
    acc = rule["accuracy"]

    if pattern_id == "generalization_failure":
        alt = acc["alternating"]
        tr_lo, tr_hi = alt["training_range"]
        nov_lo, nov_hi = alt["novel_range"]
        noise = alt["noise"]
        vals = []
        training = rng.uniform(tr_lo, tr_hi)
        novel = rng.uniform(nov_lo, nov_hi)
        for i in range(n_sessions):
            base = training if i % 2 == 0 else novel
            vals.append(_clip(base + rng.uniform(-noise, noise)))
        return vals

    if pattern_id == "skill_loss_after_break":
        base = rng.uniform(*acc["base_range"])
        drop = rng.uniform(*acc["initial_drop"])
        rec = rng.uniform(*acc["recovery_per_session_range"])
        noise = acc["noise"]
        vals = [_clip(base - drop + rng.uniform(-noise, noise))]
        for _ in range(1, n_sessions):
            vals.append(_clip(vals[-1] + rec + rng.uniform(-noise, noise), 0.1, base))
        return vals

    if pattern_id == "motivating_operation_shift":
        base = rng.uniform(*acc["base_range"])
        dip_len = rng.randint(*acc["mo_dip_sessions"])
        dip_mag = rng.uniform(*acc["mo_dip_magnitude"])
        rec = rng.uniform(*acc["recovery_per_session_range"])
        noise = acc["noise"]
        dip_start = max(2, n_sessions // 3)
        vals = []
        for i in range(n_sessions):
            in_dip = dip_start <= i < dip_start + dip_len
            if in_dip:
                v = base - dip_mag + rng.uniform(-noise, noise)
            elif i >= dip_start + dip_len:
                prev = vals[-1]
                v = min(base, prev + rec + rng.uniform(-noise, noise))
            else:
                v = base + rng.uniform(-noise, noise)
            vals.append(_clip(v, 0.1, 0.98))
        return vals

    if pattern_id == "setting_event_trigger":
        base = rng.uniform(*acc["base_range"])
        se_idx = max(1, int(acc["setting_event_session_fraction"] * n_sessions))
        mag = rng.uniform(*acc["setting_event_magnitude"])
        rec = rng.uniform(*acc["recovery_per_session_range"])
        noise = acc["noise"]
        vals = []
        for i in range(n_sessions):
            if i < se_idx:
                v = base + rng.uniform(-noise, noise)
            elif i == se_idx:
                v = base - mag + rng.uniform(-noise, noise)
            else:
                prev = vals[-1]
                v = min(base, prev + rec + rng.uniform(-noise, noise))
            vals.append(_clip(v, 0.1, 0.98))
        return vals

    if pattern_id == "extinction_burst":
        base = rng.uniform(*acc["base_range"])
        delta = rng.uniform(*acc["delta_per_session_range"])
        noise = acc["noise"]
        vals = [_clip(base + i * delta + rng.uniform(-noise, noise)) for i in range(n_sessions)]
        return vals

    # Default: linear delta from base
    base = rng.uniform(*acc["base_range"])
    delta = rng.uniform(*acc["delta_per_session_range"])
    noise = acc["noise"]
    cap = acc.get("cap", 0.98)
    floor_v = acc.get("floor", 0.05)
    return [_clip(base + i * delta + rng.uniform(-noise, noise), floor_v, cap) for i in range(n_sessions)]


def generate_behavior_frequencies(
    traj_name: str, library: dict, n_sessions: int, rule: dict, rng: random.Random
) -> list:
    """Return a list of integer behavior frequencies per session."""
    cfg = library[traj_name]
    if traj_name == "temporary_spike":
        base_lo, base_hi = cfg["base_freq_range"]
        mult_range = cfg["spike_multiplier_range"]
        noise = cfg["noise"]
        burst_start = max(2, int(rule.get("burst_start_fraction", 0.33) * n_sessions))
        burst_len = rule.get("burst_duration_sessions", 2)
        base = rng.uniform(base_lo, base_hi)
        mult = rng.uniform(*mult_range)
        vals = []
        for i in range(n_sessions):
            if burst_start <= i < burst_start + burst_len:
                v = base * mult + rng.uniform(-noise, noise)
            else:
                v = base + rng.uniform(-noise, noise)
            vals.append(max(0, round(v)))
        return vals
    if traj_name == "coincident_spike":
        # Spike coincides with setting event index
        base_lo, base_hi = cfg["base_freq_range"]
        mult_range = cfg["spike_multiplier_range"]
        noise = cfg["noise"]
        se_idx = max(1, int(rule["accuracy"]["setting_event_session_fraction"] * n_sessions))
        base = rng.uniform(base_lo, base_hi)
        mult = rng.uniform(*mult_range)
        vals = []
        for i in range(n_sessions):
            if i in {se_idx, se_idx + 1}:
                v = base * mult + rng.uniform(-noise, noise)
            else:
                v = base + rng.uniform(-noise, noise)
            vals.append(max(0, round(v)))
        return vals
    # default: base_freq_range + cumulative delta + noise
    base_lo, base_hi = cfg["base_freq_range"]
    delta = cfg.get("delta_per_session", 0.0)
    noise = cfg.get("noise", 1.0)
    base = rng.uniform(base_lo, base_hi)
    return [max(0, round(base + i * delta + rng.uniform(-noise, noise))) for i in range(n_sessions)]


# Stimulus / profile sampling helpers


SKILL_POOL_BY_CATEGORY = {
    "early_language": [
        ("Mand", "single-word mands for preferred items (e.g., \"cookie\", \"iPad\")", "NET"),
        ("Mand", "mands for missing items needed to complete an activity", "NET"),
        ("Mand", "2-word mand phrases (e.g., \"more cracker\", \"open please\")", "NET"),
        ("Mand", "requesting a break ('break please' or AAC 'I need a break')", "NET"),
        ("Mand", "indicating completion ('all done', 'finished')", "NET"),
        ("Tact", "tacts common objects", "DTT"),
        ("Tact", "tacts colors of objects", "DTT"),
        ("Listener Responding", "follows 1-step motor instructions", "DTT"),
        ("Listener Responding", "selects items by feature", "DTT"),
        ("Echoic", "echoes 2-word phrases", "DTT variant"),
        ("Motor Imitation", "imitates 3-step motor sequences", "DTT variant"),
        ("Intraverbal", "answers WH-questions about familiar topics", "NET"),
        ("Tolerating Denied Access", "wait calmly when access to preferred item is denied", "FCT"),
    ],
    "school_age": [
        ("Reading", "reads 10–20 sight words", "DTT"),
        ("Reading", "sounds out CVC words", "DTT"),
        ("Writing", "copies simple words from model", "DTT"),
        ("Math", "identifies numerals 1–20", "DTT"),
        ("Math", "counts objects 1–20", "DTT"),
        ("Mand", "requesting preferred items using AAC device (e.g., \"I want cookie please\")", "NET"),
        ("Mand", "single-word requests for preferred items", "NET"),
        ("Mand", "requesting preferred items using a full sentence", "NET"),
        ("Mand", "requesting a break during non-preferred tasks", "NET"),
        ("Mand", "indicating 'all done' when an activity is complete", "NET"),
        ("Tolerating Denied Access", "wait calmly when access to preferred item is denied", "FCT"),
        ("Social Behavior", "takes turns during structured activities", "PRT"),
    ],
    "adolescent": [
        ("Self-Care", "washing hands independently", "Task Analysis"),
        ("Self-Care", "dressing (pants, shirt)", "Task Analysis"),
        ("Self-Care", "brushing teeth independently", "Task Analysis"),
        ("Self-Care", "tolerating tooth brushing by caregiver", "Task Analysis"),
        ("Self-Care", "tolerating haircut", "Task Analysis"),
        ("Home Skills", "making the bed", "Task Analysis"),
        ("Home Skills", "meal cleanup after eating", "Task Analysis"),
        ("Community", "identifying community safety signs", "DTT"),
        ("Community", "ordering in a restaurant", "Task Analysis"),
        ("Mand", "requesting preferred items using AAC device", "NET"),
        ("Mand", "requesting help when a task is difficult", "NET"),
        ("Mand", "requesting a break during non-preferred activities", "NET"),
        ("Mand", "indicating 'all done' with a step or activity", "NET"),
        ("Tolerating Denied Access", "wait calmly when access to preferred item is denied", "FCT"),
    ],
    "adult": [
        ("Independent Living", "scheduling medical appointments", "Task Analysis"),
        ("Independent Living", "managing a budget", "Task Analysis"),
        ("Independent Living", "self-advocacy statements", "BST"),
        ("Vocational", "clocking in at start of shift", "Task Analysis"),
        ("Vocational", "completing assigned tasks in order", "Task Analysis"),
        ("Home Skills", "doing laundry", "Task Analysis"),
        ("Home Skills", "simple meal preparation", "Task Analysis"),
        ("Community", "using public transportation", "Task Analysis"),
        ("Mand", "requesting assistance using AAC device", "NET"),
        ("Mand", "requesting a break during extended tasks", "NET"),
        ("Mand", "indicating 'all done' at task completion", "NET"),
        ("Tolerating Denied Access", "wait calmly when a preferred activity is denied", "FCT"),
    ],
}


def sample_programs(learner_profile_id: str, n: int, rng: random.Random) -> list:
    """Sample a realistic set of n acceleration programs for the learner profile."""
    category_map = {
        "early": "early_language",
        "school_age": "school_age",
        "adolescent": "adolescent",
        "adult": "adult",
    }
    primary = category_map.get(learner_profile_id, "school_age")
    pool = list(SKILL_POOL_BY_CATEGORY[primary])
    # Mix in one program from an adjacent category for realism
    adjacent = {"early": "school_age", "school_age": "early_language", "adolescent": "school_age", "adult": "adolescent"}
    pool += SKILL_POOL_BY_CATEGORY[adjacent.get(learner_profile_id, "school_age")][:3]
    rng.shuffle(pool)
    return pool[:n]


# Session log rendering


def _render_measurements_for_program(
    skill_domain: str, accuracy: float, rng: random.Random
) -> str:
    """Return a one-line measurement string for one program in one session."""
    trials = rng.randint(8, 15)
    correct = round(accuracy * trials)
    fp = rng.randint(0, max(0, trials // 3))
    pp = rng.randint(0, max(0, trials // 3))
    g = rng.randint(0, max(0, trials // 3))
    indep = max(0, trials - fp - pp - g)
    prompts = f"FP×{fp}, PP×{pp}, G×{g}, I×{indep}"
    latency = 1.5 + (1.0 - accuracy) * 4.5 + rng.uniform(-0.3, 0.3)
    return f"{correct}/{trials} correct ({round(accuracy*100)}%); latency {latency:.1f}s; prompts {prompts}"


def _render_behavior_measurement(behavior_id: str, freq: int, rng: random.Random) -> str:
    """Return a measurement string for one target behavior in one session."""
    if behavior_id in {"tantrum"}:
        if freq == 0:
            return f"freq 0"
        duration_total = freq * rng.randint(2, 5)
        return f"freq {freq}, duration {duration_total}m total"
    if behavior_id in {"motor_stereotypy", "vocal_stereotypy", "mouthing"}:
        pir_pct = min(60, freq * rng.randint(3, 5) + rng.randint(0, 10))
        return f"freq {freq}; PIR {pir_pct}%"
    if behavior_id == "pica":
        # Pica is measured as attempts (total) and successful ingestions (subset).
        # Most pica events are caught by staff before ingestion — successful ≤ attempts.
        if freq == 0:
            return "attempts 0"
        attempts = freq
        # Successful ingestion is stochastic but bounded; most are intercepted.
        successful = 0
        for _ in range(attempts):
            if rng.random() < 0.25:
                successful += 1
        unsuccessful = attempts - successful
        return (
            f"attempts {attempts} ({unsuccessful} unsuccessful — staff retrieved item before ingestion; "
            f"{successful} successful — item ingested)"
        )
    if behavior_id == "fecal_smearing":
        # Scatolia is measured as attempts (reaching for feces) and completed smearing (subset).
        # Staff often intercept before smearing completes — completed ≤ attempts.
        if freq == 0:
            return "attempts 0"
        attempts = freq
        completed = 0
        for _ in range(attempts):
            if rng.random() < 0.35:
                completed += 1
        intercepted = attempts - completed
        return (
            f"attempts {attempts} ({intercepted} intercepted — staff redirected before smearing; "
            f"{completed} completed — feces transferred to skin, clothing, or surface)"
        )
    if behavior_id == "toileting_accident":
        # Toileting data tracks both successful voids (in toilet) and accidents.
        # BM accidents scale with overall accident load but stay physiologically
        # bounded — typical session window is 0–1 BMs; some learners with GI
        # clustering (IBS, diet, medication-related) can reach 2.
        if freq == 0:
            bm_accidents = 0
        elif freq == 1:
            bm_accidents = 1 if rng.random() < 0.25 else 0
        elif freq <= 4:
            bm_accidents = rng.choices([0, 1], weights=[0.65, 0.35])[0]
        else:
            bm_accidents = rng.choices([0, 1, 2], weights=[0.50, 0.35, 0.15])[0]
        urine_accidents = max(0, freq - bm_accidents)

        # Successful voids scale inversely with accident load — a session full
        # of accidents represents missed toileting opportunities.
        if freq == 0:
            urine_success = rng.randint(3, 6)
        elif freq <= 2:
            urine_success = rng.randint(2, 5)
        elif freq <= 4:
            urine_success = rng.randint(1, 3)
        else:
            urine_success = rng.randint(0, 2)

        # BM successes: typically 0 per session window, sometimes 1. Learners
        # with BM accidents can still have an earlier successful BM in the toilet
        # (e.g., scheduled morning sit worked, later opportunities missed).
        if bm_accidents > 0:
            bm_success = 1 if rng.random() < 0.15 else 0
        else:
            bm_success = rng.choices([0, 1], weights=[0.75, 0.25])[0]

        return (
            f"urine: {urine_success} in-toilet / {urine_accidents} accidents; "
            f"BM: {bm_success} in-toilet / {bm_accidents} accidents"
        )
    if behavior_id in {"elopement"}:
        return f"freq {freq}"
    return f"freq {freq}"


ABC_TEMPLATES = {
    "escape": [
        ("worksheet task presented", "refused + pushed materials away", "task removed for 2 min"),
        ("demand to complete math problem", "threw materials and vocalized 'no'", "staff removed demand, redirected"),
        ("transition to non-preferred activity", "dropped to floor, cried", "transition delayed, preferred item offered"),
        ("asked to finish dressing task", "kicked at materials", "task paused for 3 min"),
    ],
    "attention": [
        ("adult attention diverted to another learner", "vocalized loudly + approached staff", "staff turned to address behavior"),
        ("staff engaged in paperwork nearby", "yelled name + tapped staff", "staff attended and redirected"),
    ],
    "tangible": [
        ("preferred iPad removed at end of break", "screamed + reached for device", "staff redirected to alternative"),
        ("peer took preferred toy", "grabbed toy back + cried", "staff mediated and returned item"),
    ],
    "automatic": [
        ("quiet unstructured moment between trials", "engaged in hand-flapping", "no social consequence; self-terminated after 30s"),
        ("waiting in line transition", "mouthed own hand", "staff redirected to task materials"),
    ],
}


# Behavior-specific ABC overrides — used in preference to the function-keyed
# templates above when the behavior has distinctive antecedents / topography.
BEHAVIOR_ABC_TEMPLATES = {
    "fecal_smearing": [
        ("quiet moment in bathroom after bowel movement", "reached into diaper, retrieved feces", "staff redirected hands and initiated clean-up"),
        ("unstructured downtime, staff out of direct line of sight", "reached behind waistband of pants", "staff intercepted and guided to bathroom"),
        ("post-toileting, before hygiene steps completed", "transferred feces to arm and wall surface", "staff blocked further smearing, cleaned skin and surface"),
        ("lying down for rest period", "reached into pull-up, brought hand to face", "staff intercepted before oral contact; hygiene routine initiated"),
    ],
    "toileting_accident": [
        ("during demand sequence at the work table", "voided (urine) without signaling need", "staff paused programming, changed clothing, resumed after 10 min"),
        ("transition from preferred activity to non-preferred task", "voided (urine) en route to the work area", "staff redirected to bathroom, changed clothing"),
        ("end of 90-minute block without scheduled toileting", "soiled (bowel) at the work table", "staff initiated clean-up and hygiene routine; program paused"),
        ("during group activity without requesting bathroom", "voided (urine) in seat", "staff removed learner from group, changed clothing, re-entered after clean-up"),
    ],
}


def _render_abc_entry(behavior_id: str, behavior_name: str, function: str, rng: random.Random) -> str:
    templates = BEHAVIOR_ABC_TEMPLATES.get(behavior_id) or ABC_TEMPLATES.get(function) or ABC_TEMPLATES["escape"]
    a, b, c = rng.choice(templates)
    return f"ABC ({behavior_name.lower()}): A = {a}; B = {b}; C = {c}"


def render_session_log(
    *,
    synthetic_id: int,
    learner_profile: dict,
    curricula_line: str,
    programs: list,
    accuracies_per_program: list,
    behaviors: list,
    behavior_frequencies_per_behavior: list,
    behavior_functions: list,
    n_sessions: int,
    start_date: date,
    duration_per_session: int,
    ioa_session_idx: int | None,
    ioa_agreement: float | None,
    include_abc: bool,
    abc_sessions: list,
    behavioral_indicators_cluster: list,
    rng: random.Random,
) -> str:
    """Render the full multi-session log as text."""
    lines = []
    lines.append("LEARNER PROFILE")
    lines.append(f"Synthetic ID: SYN-{synthetic_id}")
    profile_text = f"{learner_profile['name']}"
    if "chronological_age" in learner_profile:
        profile_text += f" ({learner_profile['chronological_age']})"
    elif "developmental_age" in learner_profile:
        profile_text += f" (dev age {learner_profile['developmental_age']})"
    lines.append(f"Profile: {profile_text}")
    lines.append(f"Curricula: {curricula_line}")
    end_date = start_date + timedelta(days=n_sessions * 2)
    lines.append(f"Date range: Sessions 1–{n_sessions} across {(end_date - start_date).days} days ({start_date.isoformat()} to {end_date.isoformat()})")
    lines.append("")

    lines.append("ACCELERATION PROGRAMS")
    for i, (domain, skill, method) in enumerate(programs, 1):
        lines.append(f"{i}. {skill} ({domain})")
        lines.append(f"   Method: {method}")
    lines.append("")

    if behaviors:
        lines.append("DECELERATION TARGETS")
        for i, (beh, fn) in enumerate(zip(behaviors, behavior_functions), 1):
            lines.append(f"{i}. {beh['name']} — function hypothesized: {fn}")
        lines.append("")

    lines.append("SESSION DATA")
    for s_idx in range(n_sessions):
        session_num = s_idx + 1
        d = (start_date + timedelta(days=s_idx * 2)).isoformat()
        if ioa_session_idx == s_idx:
            lines.append(f"")
            lines.append(f"Session {session_num} — {d} — IOA SESSION — 2 observers")
            for i, (domain, skill, method) in enumerate(programs):
                acc = accuracies_per_program[i][s_idx]
                lines.append(f"  {skill}: {round(acc*100)}% (primary); IOA {round(ioa_agreement*100)}% agreement")
            for i, beh in enumerate(behaviors):
                freq = behavior_frequencies_per_behavior[i][s_idx]
                ms = _render_behavior_measurement(beh["id"], freq, rng)
                lines.append(f"  {beh['name']}: {ms}; IOA {round(ioa_agreement*100)}% agreement")
        else:
            lines.append(f"")
            lines.append(f"Session {session_num} — {d} — {duration_per_session} min — 1 observer")
            for i, (domain, skill, method) in enumerate(programs):
                acc = accuracies_per_program[i][s_idx]
                ms = _render_measurements_for_program(domain, acc, rng)
                lines.append(f"  {skill}: {ms}")
            for i, beh in enumerate(behaviors):
                freq = behavior_frequencies_per_behavior[i][s_idx]
                ms = _render_behavior_measurement(beh["id"], freq, rng)
                lines.append(f"  {beh['name']}: {ms}")
            # ABC entry for this session?
            if include_abc and s_idx in abc_sessions and behaviors:
                beh_idx = rng.randrange(len(behaviors))
                fn = behavior_functions[beh_idx]
                if behavior_frequencies_per_behavior[beh_idx][s_idx] > 0:
                    beh = behaviors[beh_idx]
                    lines.append(f"  {_render_abc_entry(beh['id'], beh['name'], fn, rng)}")

    if behavioral_indicators_cluster:
        lines.append("")
        lines.append("BEHAVIORAL OBSERVATIONS (across sessions)")
        for ind in behavioral_indicators_cluster:
            lines.append(f"- {ind}")

    return "\n".join(lines)


# Interpretation section assembly


def assemble_clinical_concerns(
    pattern_id: str,
    pattern: dict,
    accuracies_first_last: tuple,
    behaviors: list,
    behavior_frequencies_per_behavior: list,
    n_sessions: int,
) -> str:
    """Produce the clinical-concerns bullets."""
    first, last = accuracies_first_last
    bullets = []
    if pattern_id == "mastery_progression":
        bullets.append(f"- Steady improvement: accuracy rose from {round(first*100)}% to {round(last*100)}% across {n_sessions} sessions.")
        bullets.append("- No clinical concerns at this time; mastery criteria should be reachable within a few additional sessions.")
    elif pattern_id == "regression":
        bullets.append(f"- **Regression identified**: accuracy has declined from {round(first*100)}% to {round(last*100)}% across {n_sessions} sessions.")
        if behaviors:
            bullets.append("- Accompanying behavior data suggests the decline may be function-related.")
    elif pattern_id == "plateau":
        bullets.append(f"- **Plateau**: accuracy has remained near {round(((first+last)/2)*100)}% for {n_sessions} sessions without meaningful improvement.")
        bullets.append("- Performance is below mastery criteria; current teaching procedure may not be effective for this learner.")
    elif pattern_id == "frustration_pattern":
        bullets.append(f"- **Frustration pattern**: declining accuracy ({round(first*100)}% -> {round(last*100)}%) with escape-indicator behaviors.")
        bullets.append("- Risk of learned helplessness and escape-maintained behavior if not addressed.")
    elif pattern_id == "variable_performance":
        avg = (first + last) / 2
        bullets.append(f"- **Variable performance**: accuracy fluctuating around {round(avg*100)}% with no clear trend.")
        bullets.append("- Inconsistency may indicate stimulus-control issues or motivational variability across sessions.")
    elif pattern_id == "prompt_dependency":
        bullets.append(f"- **Prompt dependency**: high accuracy maintained ({round(first*100)}%–{round(last*100)}%) but primarily at prompted levels.")
        bullets.append("- Independent responding remains low despite extended training.")
    elif pattern_id == "rapid_acquisition":
        bullets.append(f"- **Rapid acquisition**: accelerated mastery from {round(first*100)}% to {round(last*100)}% across {n_sessions} sessions.")
        bullets.append("- Acquisition has exceeded expected timeline.")
    elif pattern_id == "generalization_failure":
        bullets.append("- **Generalization failure**: strong performance in training context but failure to generalize to novel conditions.")
        bullets.append("- Skill may be under restricted stimulus control.")
    elif pattern_id == "extinction_burst":
        bullets.append("- **Extinction burst** observed: temporary increase in problem behavior consistent with an extinction procedure.")
        bullets.append("- This is an expected phase of behavior change and typically indicates the intervention is working.")
    elif pattern_id == "skill_loss_after_break":
        bullets.append(f"- **Skill loss following break**: performance dropped to {round(first*100)}% at return, recovering to {round(last*100)}%.")
        bullets.append("- Maintenance schedule should be reviewed and strengthened.")
    elif pattern_id == "motivating_operation_shift":
        bullets.append("- **Motivating-operation shift**: mid-log dip in responding followed by recovery suggests reinforcer-value change.")
        bullets.append("- Possible satiation with current reinforcer; preference reassessment indicated.")
    elif pattern_id == "setting_event_trigger":
        bullets.append("- **Setting event pattern**: observable change in performance correlated with an external event (illness, sleep, schedule).")
        bullets.append("- Correlation between setting event and performance should be tracked explicitly.")
    return "\n".join(bullets)


def assemble_function_hypothesis_section(
    behaviors: list, behavior_functions: list, abc_events_summary: str
) -> str:
    """Produce the function hypothesis section, or empty string if no behaviors."""
    if not behaviors:
        return ""
    lines = ["", "## Behavior Function Hypothesis"]
    for beh, fn in zip(behaviors, behavior_functions):
        lines.append(f"{beh['name']}: {fn}")
        if fn != "unknown":
            ev_bits = []
            if abc_events_summary:
                ev_bits.append(f"ABC events in the log support the {fn} function")
            # Function-specific evidence without showing the operational definition
            func_evidence = {
                "escape": "behavior occurs in the context of demand presentation and terminates contingent on task removal",
                "attention": "behavior occurs during low-attention periods and results in social attention contingently",
                "tangible": "behavior occurs when preferred items are restricted and is followed by access to the item",
                "automatic": "behavior persists across contexts without clear social mediation",
            }
            if fn in func_evidence:
                ev_bits.append(func_evidence[fn])
            lines.append(f"  Evidence: " + "; ".join(ev_bits) + ".")
        else:
            lines.append("  Evidence: insufficient data to disambiguate functions; recommend FBA / preference assessment before programming changes.")
    lines.append("")
    return "\n".join(lines)


def assemble_replacement_section(behaviors: list, behavior_functions: list, recs_pool: list) -> str:
    """Produce the replacement behavior (FCT) section — only if behaviors present."""
    if not behaviors or not recs_pool:
        return ""
    lines = ["", "### Replacement behavior (FCT)"]
    for r in recs_pool[:3]:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def assemble_crisis_section(recs_pool: list, escalation_level: int) -> str:
    """Produce the crisis plan section — only if escalation >= 3 and pool has items."""
    if escalation_level < 3 or not recs_pool:
        return ""
    lines = ["", "### Crisis plan"]
    for r in recs_pool[:3]:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def assemble_rationale(
    accuracies_first_last: tuple,
    mean_accuracy: float,
    n_sessions: int,
    behaviors: list,
    behavior_frequencies_per_behavior: list,
    ioa_present: bool,
    ioa_agreement: float | None,
) -> str:
    """Produce the data-supported rationale bullets."""
    first, last = accuracies_first_last
    bullets = []
    bullets.append(f"- Mean accuracy across {n_sessions} sessions: {round(mean_accuracy*100, 1)}%.")
    direction = "upward" if last > first else "downward" if last < first else "flat"
    bullets.append(f"- Trend direction: {direction} (first session: {round(first*100)}%, last session: {round(last*100)}%).")
    if behaviors:
        for beh, freqs in zip(behaviors, behavior_frequencies_per_behavior):
            mean_f = sum(freqs) / len(freqs)
            first_third = sum(freqs[:max(1, len(freqs)//3)]) / max(1, len(freqs)//3)
            last_third = sum(freqs[-max(1, len(freqs)//3):]) / max(1, len(freqs)//3)
            bullets.append(f"- {beh['name']}: mean {mean_f:.1f}/session (early-window mean {first_third:.1f} -> late-window mean {last_third:.1f}).")
    if ioa_present and ioa_agreement is not None:
        bullets.append(f"- IOA data: {round(ioa_agreement*100)}% agreement on IOA session — {'adequate' if ioa_agreement >= 0.80 else 'below threshold'}.")
    else:
        bullets.append("- No IOA session in this log; reliability of measurements cannot be independently verified.")
    return "\n".join(bullets)


# Escalation + confidence inference


def infer_escalation(
    pattern: dict,
    behaviors: list,
    behavior_frequencies_per_behavior: list,
    rules: dict,
) -> int:
    """Compute escalation level from pattern + behavior severity."""
    level = int(pattern["default_escalation"])
    severe_ids = set(rules.get("severe_behavior_ids", []))
    if any(b["id"] in severe_ids for b in behaviors):
        level = min(4, level + rules.get("severe_behavior_escalation_bump", 1))
    # Safety-immediate threshold
    safety_threshold_ids = set(rules.get("safety_immediate_threshold_behaviors", []))
    threshold_rate = rules.get("safety_immediate_sib_rate_per_session", 8)
    for beh, freqs in zip(behaviors, behavior_frequencies_per_behavior):
        if beh["id"] in safety_threshold_ids:
            if len(freqs) >= 2 and all(f >= threshold_rate for f in freqs[-2:]):
                level = 4
    return level


def infer_confidence(
    n_sessions: int,
    ioa_present: bool,
    accuracies: list,
    rules: dict,
) -> str:
    """Compute confidence level from data-quality features.

    Rules:
      - low: very short log, OR short log with no IOA and non-trivial variance
      - moderate: default when criteria for high are not met
      - high: long log with IOA evidence and low variance
    """
    mean = sum(accuracies) / len(accuracies)
    sd = (sum((a - mean) ** 2 for a in accuracies) / len(accuracies)) ** 0.5

    # Explicit low triggers
    if n_sessions < rules["min_sessions_for_moderate"]:
        return "low"
    if n_sessions < 7 and not ioa_present and sd > 0.15:
        return "low"
    if sd > 0.35:
        return "low"

    # High requires long log + IOA + modest variance
    if (
        n_sessions >= rules["min_sessions_for_high"]
        and (not rules["ioa_required_for_high"] or ioa_present)
        and sd <= rules["variance_threshold_low"]
    ):
        return "high"

    return "moderate"


# Main generator class


class SessionInterpretationGenerator:
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.shared = load_shared(self.config_dir)
        self.area = load_area(self.config_dir, AREA)
        self.template = self.area["template"]
        self.taxonomy = self.area["taxonomy"]
        self.compat = self.area["compatibility"]
        self.trajectory_rules = load_yaml(self.config_dir / AREA / "trajectory_rules.yaml")
        self.recommendations = load_yaml(self.config_dir / AREA / "recommendations.yaml")

    def _pattern_by_id(self, pid: str) -> dict:
        return next(p for p in self.taxonomy["patterns"] if p["id"] == pid)

    def _behavior_by_id(self, bid: str) -> dict:
        return next(b for b in self.taxonomy["target_behaviors"] if b["id"] == bid)

    def _escalation_label(self, level: int) -> str:
        return next(e["label"] for e in self.taxonomy["escalation_levels"] if e["id"] == level)

    def render_example(self, rng: random.Random) -> dict:
        # Sample hidden pattern
        pattern = rng.choice(self.taxonomy["patterns"])
        pattern_id = pattern["id"]

        # Log length
        lo, hi = self.compat["log_length_by_pattern"][pattern_id]
        n_sessions = rng.randint(lo, hi)

        # Learner profile (any — patterns are profile-agnostic)
        profile = rng.choice(self.shared["learner_profiles"]["profiles"])

        # Acceleration programs
        n_programs = rng.randint(*self.compat["programs_per_log_range"])
        programs = sample_programs(profile["id"], n_programs, rng)
        curricula_names = sorted(set(p[0] for p in programs))
        curricula_line = " + ".join(curricula_names)

        # Trajectory per program (all programs follow the pattern's trajectory loosely)
        rule = self.trajectory_rules["rules"][pattern_id]
        accuracies_per_program = [
            generate_accuracy_trajectory(pattern_id, rule, n_sessions, rng)
            for _ in programs
        ]

        # Target behaviors (if any)
        n_beh_lo, n_beh_hi = self.compat["pattern_behavior_count_ranges"][pattern_id]
        n_behaviors = rng.randint(n_beh_lo, n_beh_hi)
        behaviors = []
        behavior_functions = []
        if n_behaviors > 0:
            function_bias = self.compat["pattern_function_bias"].get(pattern_id, [])
            candidate_behs = [
                b for b in self.taxonomy["target_behaviors"]
                if any(f in b["plausible_functions"] for f in function_bias) or not function_bias
            ]
            behaviors = rng.sample(candidate_behs, min(n_behaviors, len(candidate_behs)))
            for beh in behaviors:
                if function_bias:
                    valid = [f for f in function_bias if f in beh["plausible_functions"]]
                    behavior_functions.append(rng.choice(valid) if valid else rng.choice(beh["plausible_functions"]))
                else:
                    behavior_functions.append(rng.choice(beh["plausible_functions"]))

        # Behavior frequencies per session
        behavior_freqs = []
        if behaviors:
            traj_name = self.trajectory_rules["rules"][pattern_id]["behavior_trajectory"]
            for _ in behaviors:
                freqs = generate_behavior_frequencies(
                    traj_name, self.trajectory_rules["behavior_trajectory_library"],
                    n_sessions, rule, rng,
                )
                behavior_freqs.append(freqs)

        # IOA decision
        include_ioa = rng.random() < self.compat["ioa_inclusion_probability"]
        ioa_session_idx = None
        ioa_agreement = None
        if include_ioa and n_sessions >= 4:
            ioa_session_idx = rng.randint(n_sessions // 3, 2 * n_sessions // 3)
            if rng.random() < self.compat["ioa_low_probability"]:
                ioa_agreement = rng.uniform(*self.compat["ioa_low_range"])
            else:
                ioa_agreement = rng.uniform(*self.compat["ioa_agreement_range"])

        # ABC decision
        include_abc = bool(behaviors) and rng.random() < self.compat["abc_inclusion_probability"]
        abc_sessions = []
        if include_abc:
            candidate_sessions = [i for i in range(n_sessions) if any(bf[i] > 0 for bf in behavior_freqs)]
            n_abc = min(rng.randint(1, 3), len(candidate_sessions))
            abc_sessions = rng.sample(candidate_sessions, n_abc) if candidate_sessions else []

        # Behavioral indicators
        cluster = self.compat["pattern_behavioral_indicator_cluster"].get(pattern_id)
        indicators = []
        if cluster:
            pool = self.taxonomy["behavioral_indicators"][cluster]
            indicators = rng.sample(pool, min(rng.randint(2, 4), len(pool)))

        # Log dates
        start_date = date(2026, rng.randint(1, 10), rng.randint(1, 28))
        duration_per_session = rng.randint(*self.compat["session_duration_minutes_range"])

        # Synthetic ID
        synthetic_id = rng.randint(1000, 9999)

        # Render the user's session log
        session_log = render_session_log(
            synthetic_id=synthetic_id,
            learner_profile=profile,
            curricula_line=curricula_line,
            programs=programs,
            accuracies_per_program=accuracies_per_program,
            behaviors=behaviors,
            behavior_frequencies_per_behavior=behavior_freqs,
            behavior_functions=behavior_functions,
            n_sessions=n_sessions,
            start_date=start_date,
            duration_per_session=duration_per_session,
            ioa_session_idx=ioa_session_idx,
            ioa_agreement=ioa_agreement,
            include_abc=include_abc,
            abc_sessions=abc_sessions,
            behavioral_indicators_cluster=indicators,
            rng=rng,
        )

        # Compute gold labels
        escalation_level = infer_escalation(
            pattern, behaviors, behavior_freqs, self.compat["escalation_rules"]
        )
        # Flatten accuracies across all programs for variance check
        flat_accs = [v for traj in accuracies_per_program for v in traj]
        confidence_level = infer_confidence(
            n_sessions, ioa_session_idx is not None, flat_accs, self.compat["confidence_rules"]
        )

        # Primary-program accuracies for concerns/rationale (take first program)
        primary_accs = accuracies_per_program[0]
        mean_primary = sum(primary_accs) / len(primary_accs)

        # Assemble the assistant message sections
        clinical_concerns_bullets = assemble_clinical_concerns(
            pattern_id, pattern, (primary_accs[0], primary_accs[-1]),
            behaviors, behavior_freqs, n_sessions,
        )

        pattern_explanations = {
            "mastery_progression": "Accuracy is ascending cleanly across sessions with no interfering behaviors, consistent with a mastery-progression trajectory.",
            "regression": "Previously-established responding has declined across recent sessions, warranting review of environmental and reinforcement variables.",
            "plateau": "Responding has stabilized below mastery criterion without meaningful movement, indicating the current procedure is limiting further acquisition.",
            "frustration_pattern": "Declining accuracy co-occurs with escape-indicator behaviors, consistent with frustration and escape-maintained responding to demand.",
            "variable_performance": "High session-to-session variability with no clear trend suggests environmental or motivational inconsistency rather than a single programmatic issue.",
            "prompt_dependency": "Accuracy stays high only at prompted levels; independent responding remains low despite extended training.",
            "rapid_acquisition": "Accuracy ascended steeply beyond expected timeline for this learner's profile.",
            "generalization_failure": "Alternation between strong training performance and poor novel-condition performance indicates restricted stimulus control.",
            "extinction_burst": "Mid-log spike in problem-behavior frequency followed by recovery is consistent with a planned extinction procedure.",
            "skill_loss_after_break": "Sharp drop at the start of the log followed by gradual recovery indicates skill loss following an absence.",
            "motivating_operation_shift": "A mid-log dip followed by recovery maps onto a motivating-operation change rather than a skill issue.",
            "setting_event_trigger": "A discontinuous performance change at a specific session correlates with an external setting event.",
        }

        function_section = assemble_function_hypothesis_section(
            behaviors, behavior_functions,
            "ABC events present" if include_abc and abc_sessions else ""
        )

        pattern_recs = self.recommendations["patterns"][pattern_id]
        antecedent_pool = pattern_recs["antecedent"] or ["Continue monitoring; reassess in 2 weeks."]
        consequence_pool = pattern_recs["consequence"] or ["Maintain current consequences."]
        ant_bullets = "\n".join(f"- {r}" for r in antecedent_pool[:4])
        con_bullets = "\n".join(f"- {r}" for r in consequence_pool[:3])

        rep_section = assemble_replacement_section(
            behaviors, behavior_functions, pattern_recs.get("replacement", [])
        )
        crisis_section = assemble_crisis_section(
            pattern_recs.get("crisis", []), escalation_level
        )

        escalation_justifications = {
            1: "Current programming is effective; no change needed.",
            2: "Programming adjustments indicated at next session; no immediate safety concern.",
            3: "Combination of performance decline and/or behavior data warrants supervising BCBA review within 24–48 hours.",
            4: "Safety-critical signals require immediate cessation of current program and direct BCBA contact; consider crisis-plan activation.",
        }

        confidence_justifications = {
            "high": f"Pattern is well-supported: {n_sessions} sessions of data, low variance, and IOA evidence confirm reliability.",
            "moderate": f"Pattern is supported but alternatives cannot be fully excluded: {n_sessions} sessions of data" + (" with IOA evidence." if ioa_session_idx is not None else "; no IOA session included."),
            "low": f"Insufficient data: only {n_sessions} sessions, high variance, and/or no IOA evidence. Recommend additional data collection before programming changes.",
        }

        rationale_bullets = assemble_rationale(
            (primary_accs[0], primary_accs[-1]),
            mean_primary,
            n_sessions,
            behaviors,
            behavior_freqs,
            ioa_session_idx is not None,
            ioa_agreement,
        )

        # Fill template
        user_variant = rng.choice(self.template["user_variants"])
        user_content = user_variant.format(session_log=session_log)

        assistant_content = self.template["assistant_template"].format(
            clinical_concerns_bullets=clinical_concerns_bullets,
            pattern_class=pattern_id,
            pattern_explanation=pattern_explanations[pattern_id],
            function_hypothesis_section=function_section,
            antecedent_bullets=ant_bullets,
            replacement_section=rep_section,
            consequence_bullets=con_bullets,
            crisis_section=crisis_section,
            escalation_level=escalation_level,
            escalation_label=self._escalation_label(escalation_level),
            escalation_justification=escalation_justifications[escalation_level],
            confidence_level=confidence_level,
            confidence_justification=confidence_justifications[confidence_level],
            rationale_bullets=rationale_bullets,
        )

        # Metadata
        gold_labels = {
            "pattern_class": pattern_id,
            "behavior_functions": {b["name"]: f for b, f in zip(behaviors, behavior_functions)},
            "escalation_level": escalation_level,
            "confidence": confidence_level,
            "crisis_plan_required": escalation_level >= 3,
        }
        provenance = {
            "layer": 1,
            "area": AREA,
            "template_id": self.template["template_id"],
            "taxonomy_cells": {
                "hidden_pattern_id": pattern_id,
                "learner_profile": profile["id"],
                "n_sessions": n_sessions,
                "n_programs": len(programs),
                "n_behaviors": len(behaviors),
                "behavior_ids": [b["id"] for b in behaviors],
                "behavior_functions": list(behavior_functions),
                "has_abc_data": include_abc and bool(abc_sessions),
                "has_ioa_session": ioa_session_idx is not None,
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
