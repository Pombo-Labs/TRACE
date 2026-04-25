# TRACE Dataset Schema v1

**Purpose.** This document defines the **wire format** for TRACE training examples — the precise shape each JSONL line takes, the structure of user messages and assistant responses, and the metadata fields used for evaluation label extraction.

**Scope.** Two tasks, each with its own input/output conventions but sharing a common chat-format wrapper. Every taxonomy category from `taxonomy-v1.md` maps to a field or sampling decision here.

**Status.** Version 1, 2026-04-23. Breaking changes require a version bump.

**Companion documents.**
- `taxonomy-v1.md` — the controlled vocabulary (what categories exist)
- `schema-v1.md` — this document (how examples are shaped)
- `datasheet.md` (pending) — dataset card
- `src/prepare_data.py` (pending rewrite) — implements this schema

---

## 0. Overview

Two tasks:

| Task | Input | Output | MLX-LM role mapping |
|---|---|---|---|
| **1. Teaching Program Generation** | Learner profile + skill target + method + context | Structured teaching program with method-specific fields | user -> assistant |
| **2. Behavioral Session Interpretation** | Multi-session behavioral log (8–12 sessions typical) | Structured clinical interpretation (concerns + pattern + function + recommendations + escalation + confidence + rationale) | user -> assistant |

Each training example is one JSONL line with:
- `messages` — the chat-format messages the model trains on (system + user + assistant)
- `meta` — evaluation metadata (gold labels, provenance) that is *not* shown to the model during training but is used by `src/evaluate.py` for metric computation

---

## 1. Wire format

### 1.1 MLX-LM chat format

MLX-LM's `--data` expects JSONL files where each line has a `"messages"` array. Each message is `{"role": "system"|"user"|"assistant", "content": "..."}`. When `mask_prompt: true`, loss is computed only on assistant tokens.

### 1.2 TRACE extended format

```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "meta": {
    "task_type": "teaching_program" | "session_interpretation",
    "example_id": "<sha256-hex-prefix-16-chars>",
    "gold_labels": { ... task-specific ... },
    "provenance": {
      "layer": 1 | 2 | 3,
      "template_id": "<string>",
      "taxonomy_cells": { ... sampled values ... },
      "teacher_model": "<string or null>",
      "seed": <int>,
      "generated_at": "<ISO-8601>"
    }
  }
}
```

The `meta` field is ignored by MLX-LM during training but preserved for evaluation and provenance tracking. `example_id` is a deterministic hash of the user + assistant content so that duplicates can be detected across generations.

### 1.3 Splits

Train / valid / test splits live in `data/splits/`:
- `train.jsonl` — 85% (used for LoRA training)
- `valid.jsonl` — 10% (used by MLX-LM for periodic validation loss)
- `test.jsonl` — 5% (held out; only used for final evaluation)

Stratified by `meta.task_type` and by `meta.gold_labels.pattern_class` (task 2) so each split is balanced.

---

## 2. Common conventions

### 2.1 Synthetic identifiers

Every learner referenced in any example has a synthetic ID: `SYN-####` where `####` is a 4-digit number from a fixed range (1000–9999). Generator uses `random.Random(seed)` to draw these deterministically. **No real-world ID patterns, no initials, no names.**

### 2.2 Dates

Synthetic dates always fall in the range `2026-01-01` -> `2026-12-31` (stable, non-leaking). Format: `YYYY-MM-DD`. Session timestamps within a day are not included (unnecessary detail).

### 2.3 Measurement notation (within session logs)

| Measurement | Abbreviation / format |
|---|---|
| Accuracy (trial-based) | `X/N correct (PP%)` e.g., `6/10 correct (60%)` |
| Frequency (count) | `freq = N` |
| Rate | `rate N.NN/min` |
| Duration | `Nm` or `N m Ns` |
| Latency | `latency N.Ns` |
| Partial-interval | `PIR PP% of intervals` |
| Whole-interval | `WIR PP% of intervals` |
| Momentary time sampling | `MTS PP%` |
| Episode-based | `N episodes, mean duration Nm Ns` |
| IOA | `IOA PP%` (with "session marked IOA" header) |

### 2.4 Prompt-level shorthand

Used inside session logs to describe trial-level prompting distribution:

- `FP` — full physical
- `PP` — partial physical
- `M` — model
- `G` — gestural
- `V` — verbal
- `Pos` — positional
- `Vis` — visual
- `I` — independent

Example: `prompts: FP×3, PP×2, G×1, I×4` means 3 full-physical, 2 partial-physical, 1 gestural, 4 independent trials.

### 2.5 Markdown conventions (assistant output)

All assistant outputs use GitHub-flavored markdown. Section headers use `##` for top-level fields and `###` for sub-fields. Structured labels (pattern class, escalation, confidence) appear under their own `##` headers and contain a single canonical value in the first paragraph for regex extraction.

---

## 3. Task 1 — Teaching Program Generation

### 3.1 System prompt (task 1)

```
You are an expert ABA (Applied Behavior Analysis) clinical assistant. You help
Board Certified Behavior Analysts and staff design teaching programs for
individuals with autism. Your responses are clinically accurate, individualized
to the learner profile, follow BACB ethical guidelines, and reference no real
client data. Select the appropriate teaching method (DTT, NET, Task Analysis,
FCT, BST, PRT) based on the skill target and learner profile.
```

### 3.2 User message format (task 1)

Seven required fields filled from the taxonomy. The generator samples valid combinations per section 14 of `taxonomy-v1.md`.

```
Generate a teaching program for the following target.

Skill Target: {skill_name}
Curriculum Reference: {vbmapp_domain or afls_module} — {level or none}
Learner Profile: {early | school-age | adolescent | adult}
Current Mastery: {emerging | developing | approaching | near | mastered | generalization | maintenance}
Teaching Method: {dtt | net | task_analysis | fct | bst | prt}
Program Context: {D | R | Both}

Provide the full program structure appropriate to the selected method.
```

Template variations (~5 paraphrases) are sampled per Self-Instruct convention to avoid canonical-form overfitting.

### 3.3 Assistant message format (method-agnostic sections)

Every task-1 output contains these top-level sections in order:

```markdown
## Program Overview
{1-2 sentence summary of what is being taught and to whom}

## {method-specific sections — see section 3.4}

## Mastery Criteria
{which of the 7 mastery conventions from taxonomy section 11.1}

## Data Collection
{what measurement types will be used; when IOA will be scheduled}

## Generalization & Maintenance Plan
{when to probe across therapists / settings / materials; maintenance schedule}
```

### 3.4 Method-specific output variants

The middle section of the output varies by method. Each has a fixed field structure.

#### 3.4.1 DTT

```markdown
## Discriminative Stimulus (SD)
Primary SD: "{sd_text}"
Variations: {list}
Presentation: {how stimulus is presented}

## Prompt Hierarchy
Strategy: {most-to-least | least-to-most | time-delay | graduated-guidance | stimulus-fading | stimulus-shaping}
Sequence: {ordered prompt-level levels}
Current prompt level: {based on mastery state}

## Stimulus Array
Array size: {field of N or no-array}
Target stimuli: {list}
Distractor stimuli: {list or N/A}
Rotation: {how position/order is varied}

## Error Correction Procedure
{one of the 5 procedures from taxonomy section 10}

## Reinforcement Schedule
{one of the 7 schedules from taxonomy section 9}
```

#### 3.4.2 NET

```markdown
## Motivating Operation (MO) Arrangement
{how the environment is set up to establish value for the target}

## Natural Opportunity
{when and where in the natural routine the teaching occurs}

## Prompt Strategy
Strategy: {prompt hierarchy}
Delivery: {how prompts are embedded naturally}

## Natural Reinforcer
{the functional reinforcer that follows the target behavior}

## Generalization Tactics
{multiple exemplar training; programming common stimuli}
```

#### 3.4.3 Task Analysis / Chaining

```markdown
## Task Analysis
Chain type: {forward | backward | total-task}
Steps:
1. {step description}
2. {step description}
...
N. {step description}

## Prompt Strategy Per Step
{prompt level used at each step, fading plan}

## Error Correction
{procedure for when a step is missed}

## Reinforcement
Per-step reinforcement: {yes/no, schedule}
Terminal reinforcement: {on chain completion}
```

#### 3.4.4 FCT

```markdown
## Target Behavior (to reduce)
{operational definition, hypothesized function}

## Replacement Response
Topography: {vocal phrase | sign | AAC icon | card exchange}
Training sequence: {how the replacement is taught}

## Extinction Plan
{how the problem behavior is placed on extinction}

## Reinforcement for Replacement
Schedule: {initially CRF; thinning plan}
Magnitude: {quality and duration matched to natural reinforcer for problem behavior}

## Crisis Plan
{if extinction burst or safety concern, what staff do}
```

#### 3.4.5 BST (staff-facing)

```markdown
## Training Target
{the program or skill the trainee will learn to implement}

## Training Components
1. Instruction: {what written/verbal instruction is given}
2. Modeling: {trainer demonstrates; video or live}
3. Rehearsal: {trainee practices with feedback}
4. Feedback: {specific, behavior-specific, immediate}

## Fidelity Checklist
{bulleted items that must be demonstrated, scored yes/no}

## Mastery Criterion (trainee)
{e.g., 100% fidelity across 2 consecutive role-plays with novel scenarios}
```

#### 3.4.6 PRT

```markdown
## Motivation Arrangement
{how child choice, preferred materials, and interspersal are set up}

## Teaching Opportunities
{when target is presented; how multiple cues are programmed}

## Reinforcement of Attempts
{what counts as an attempt; how attempts are reinforced differentially}

## Natural Reinforcer
{the functional reinforcer for the target response}

## Generalization
{multiple-exemplar plan; across people / settings}
```

### 3.5 Metadata fields (task 1)

```json
"meta": {
  "task_type": "teaching_program",
  "example_id": "<sha256 prefix>",
  "gold_labels": {
    "method": "dtt",
    "domain": "VB-MAPP.Tact",
    "level": "L2",
    "learner_profile": "early",
    "mastery_state": "developing",
    "context": "Both"
  },
  "provenance": {
    "layer": 1,
    "template_id": "tp-dtt-001",
    "taxonomy_cells": {
      "skill_target": "Tacts colors of objects",
      "prompt_hierarchy": "most-to-least",
      "reinforcement_schedule": "CRF",
      "error_correction": "transfer_trial"
    },
    "teacher_model": null,
    "seed": 20260423001,
    "generated_at": "2026-04-23T14:22:11Z"
  }
}
```

### 3.6 Complete task-1 example (abridged)

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert ABA clinical assistant..."
    },
    {
      "role": "user",
      "content": "Generate a teaching program for the following target.\n\nSkill Target: Tacts colors of objects\nCurriculum Reference: VB-MAPP Tact L2\nLearner Profile: early\nCurrent Mastery: developing\nTeaching Method: dtt\nProgram Context: Both\n\nProvide the full program structure appropriate to the selected method."
    },
    {
      "role": "assistant",
      "content": "## Program Overview\nThis program teaches {learner} to tact (label) the color of presented objects...\n\n## Discriminative Stimulus (SD)\nPrimary SD: \"What color?\"\nVariations: \"Tell me the color\", \"What color is this?\"\nPresentation: ...\n\n## Prompt Hierarchy\nStrategy: most-to-least\nSequence: full physical (hand guidance to point) -> partial physical (touch elbow) -> gestural (point to color) -> positional (color nearest learner) -> independent.\nCurrent prompt level: given current 40% accuracy, begin at partial-physical and fade to gestural across sessions.\n\n## Stimulus Array\nArray size: field of 3 (target + 2 distractors)\nTarget stimuli: red, blue, yellow\nDistractor stimuli: 2 non-target colors per trial\nRotation: randomize position of target across trials.\n\n## Error Correction Procedure\nTransfer trial: re-present SD -> provide effective-level prompt -> reinforce prompted response -> distractor trial -> re-present SD independently.\n\n## Reinforcement Schedule\nCRF (continuous reinforcement) during acquisition; fade to FR-2 once accuracy exceeds 80%.\n\n## Mastery Criteria\n80% accuracy across 2 consecutive sessions with at least 10 trials each.\n\n## Data Collection\nTrial-by-trial data recording prompt level and response accuracy. IOA scheduled every 4th session at minimum.\n\n## Generalization & Maintenance Plan\nPost-mastery: probe with novel color stimuli, across 2 additional therapists, and in at least 2 natural contexts. Maintenance probes weekly for 4 weeks, then monthly."
    }
  ],
  "meta": {
    "task_type": "teaching_program",
    "example_id": "a3f2b8d14e9c7a0f",
    "gold_labels": {
      "method": "dtt",
      "domain": "VB-MAPP.Tact",
      "level": "L2",
      "learner_profile": "early",
      "mastery_state": "developing",
      "context": "Both"
    },
    "provenance": {
      "layer": 1,
      "template_id": "tp-dtt-001",
      "taxonomy_cells": {
        "skill_target": "Tacts colors of objects",
        "prompt_hierarchy": "most-to-least",
        "reinforcement_schedule": "CRF",
        "error_correction": "transfer_trial"
      },
      "teacher_model": null,
      "seed": 20260423001,
      "generated_at": "2026-04-23T14:22:11Z"
    }
  }
}
```

---

## 4. Task 2 — Behavioral Session Interpretation

### 4.1 System prompt (task 2)

```
You are an expert ABA clinical assistant. You analyze multi-session behavioral
session logs for individuals with autism and produce structured clinical
interpretations that identify patterns, hypothesize behavior functions when
applicable, and recommend programming adjustments structured along BIP lines
(antecedent strategies, replacement behaviors, consequence strategies, crisis
plan). Your interpretation also includes an escalation level and a confidence
expression. Every recommendation is grounded in the data provided. Follow BACB
ethical guidelines and reference no real client data.
```

### 4.2 User message format — the session log

The session log is a plain-text block with a fixed top-level structure. The generator produces it deterministically from sampled taxonomy values + a hidden pattern label.

#### 4.2.1 Learner profile block

```
LEARNER PROFILE
Synthetic ID: SYN-####
Profile: {Early Learner | School-Age Learner | Adolescent Learner | Adult Learner} ({chronological age} yr)
Curricula: {VB-MAPP L# | AFLS {module(s)} | combination}
Primary context: {D | R | Both}
Date range: Sessions 1–N across M days ({start date} to {end date})
```

#### 4.2.2 Acceleration programs block

```
ACCELERATION PROGRAMS
1. {Skill Target} ({Curriculum Reference})
   Method: {method}, {method-specific brief, e.g., "backward chaining, 8 steps"}
   Context: {D | R | Both}
2. ...
```

Typically 3–6 acceleration programs per log.

#### 4.2.3 Deceleration targets block

```
DECELERATION TARGETS
1. {Target behavior} — function hypothesized: {escape | attention | tangible | automatic | unknown}
2. ...
```

Zero to three deceleration targets per log. When present, each has a hypothesized function used by the gold-label generator; the hypothesis may or may not be the correct answer in the interpretation (some examples deliberately encode ambiguity).

#### 4.2.4 Per-session data format

One block per session.

```
Session {N} — {YYYY-MM-DD} ({context-tag}) — {duration} min — {# observers}
  {Skill 1 name}: {measurement 1}; {measurement 2}; prompts {prompt distribution}
  {Skill 2 name}: {measurement}
  ...
  {Behavior 1 name}: {measurement}
  {Behavior 2 name}: {measurement}
  {optional: ABC(behavior): A = {antecedent}; B = {behavior description}; C = {consequence}}
```

ABC entries appear in ~30% of logs (taxonomy section 6.1), at a rate of approximately 1 ABC event per session that includes behavior occurrence.

#### 4.2.5 IOA session format

Approximately 25% of logs include one IOA session (sampled uniformly from the middle third of sessions in the log).

```
Session {N} — IOA SESSION — 2 observers
  {Skill 1} IOA: {percentage}% agreement
  {Behavior 1} IOA: {percentage}% agreement
  ...
```

Agreements below 80% in generated IOA data are intentional in a minority of examples to test the model's ability to flag reliability concerns.

#### 4.2.6 Cross-session observations block

```
BEHAVIORAL OBSERVATIONS (across sessions)
- {narrative observation 1}
- {narrative observation 2}
- ...
```

3–6 bullet observations that summarize trends visible in the session data. Generated deterministically from the hidden pattern label + the behavioral indicator pool from taxonomy section 7.

### 4.3 Assistant message format — structured interpretation

Eight top-level sections in fixed order. Sections marked **required** always appear; sections marked **conditional** appear only when behavior data is present in the log.

```markdown
## Clinical Concerns          (required — free-form prose)

## Pattern Classification     (required — structured label + 1–2 sentence evidence)

## Behavior Function Hypothesis (conditional — only if deceleration targets observed)

## Programming Recommendations  (required — 4 BIP-structured subsections)
### Antecedent strategies
### Replacement behavior       (conditional on behavior presence)
### Consequence strategies
### Crisis plan                (conditional — escalation level ≥ 3)

## Escalation Level           (required — structured label + brief justification)

## Confidence                 (required — structured label + brief justification)

## Data-Supported Rationale   (required — numeric grounding)
```

#### 4.3.1 Clinical Concerns

Free-form prose, 2–5 bullets or short paragraphs. Each concern references specific data from the log (accuracy values, frequencies, trends).

#### 4.3.2 Pattern Classification

First paragraph contains exactly one canonical label (or two labels joined by `+` if co-occurring):

```markdown
## Pattern Classification
{pattern_label}

{1–2 sentence explanation of why this pattern was identified}
```

Pattern labels drawn from taxonomy section 7 (12 patterns):
`mastery_progression | regression | plateau | frustration_pattern | variable_performance | prompt_dependency | rapid_acquisition | generalization_failure | extinction_burst | skill_loss_after_break | motivating_operation_shift | setting_event_trigger`

Co-occurring example: `regression + frustration_pattern`.

#### 4.3.3 Behavior Function Hypothesis (conditional)

Present only if deceleration targets appear in the log. One sub-entry per target behavior.

```markdown
## Behavior Function Hypothesis
{behavior name}: {escape | attention | tangible | automatic | unknown}
  Evidence: {1–3 sentences grounded in log data, referencing ABC events if present}

{behavior name}: ...
```

If the log lacks evidence to distinguish functions, the hypothesis is `unknown` and the interpretation notes what data would disambiguate.

#### 4.3.4 Programming Recommendations (BIP-structured)

Four subsections. `### Antecedent strategies` and `### Consequence strategies` are always present; `### Replacement behavior` appears when deceleration targets are present; `### Crisis plan` appears when escalation level ≥ 3.

```markdown
## Programming Recommendations

### Antecedent strategies
- {specific, testable recommendation}
- ...

### Replacement behavior (FCT)
- {teaching target, function-matched}
- {reinforcement plan for replacement}

### Consequence strategies
- {how staff respond to target behavior}
- {what is reinforced; what is placed on extinction}

### Crisis plan
- {safety procedures for escalation}
```

#### 4.3.5 Escalation Level

```markdown
## Escalation Level
{1 | 2 | 3 | 4} — {short label}

{1–2 sentence justification}
```

Labels: `1 — Continue monitoring`, `2 — Adjust next session`, `3 — Supervisor review`, `4 — Safety immediate`.

#### 4.3.6 Confidence

```markdown
## Confidence
{high | moderate | low}

{1 sentence explaining the data-quality basis for the confidence level}
```

#### 4.3.7 Data-Supported Rationale

Numeric grounding for all claims made above. Bulleted list of specific accuracy / frequency / duration / trend statistics drawn from the session log.

### 4.4 Metadata fields (task 2)

```json
"meta": {
  "task_type": "session_interpretation",
  "example_id": "<sha256 prefix>",
  "gold_labels": {
    "pattern_class": "regression+frustration_pattern",
    "behavior_functions": {
      "Tantrum": "escape",
      "Mouthing": "automatic"
    },
    "escalation_level": 3,
    "confidence": "moderate",
    "crisis_plan_required": true
  },
  "log_properties": {
    "n_sessions": 10,
    "n_acceleration_programs": 4,
    "n_deceleration_targets": 2,
    "has_abc_data": true,
    "has_ioa_session": true,
    "learner_profile": "adolescent",
    "context_distribution": {"D": 0.3, "R": 0.7, "Both": 0.0}
  },
  "provenance": {
    "layer": 1,
    "template_id": "sess-regress-v1",
    "pattern_seed": 20260423007,
    "seed": 20260423007,
    "generated_at": "2026-04-23T14:30:00Z"
  }
}
```

### 4.5 Complete task-2 example (abridged user content, full assistant output)

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert ABA clinical assistant. You analyze multi-session behavioral session logs..."
    },
    {
      "role": "user",
      "content": "Interpret the following behavioral session log. Provide clinical concerns, pattern classification, behavior function hypothesis (if applicable), programming recommendations (antecedent / replacement / consequence / crisis), escalation level, confidence, and data-supported rationale.\n\nLEARNER PROFILE\nSynthetic ID: SYN-4721\nProfile: Adolescent Learner (16 yr)\nCurricula: AFLS Basic Living + AFLS Home Skills + VB-MAPP L3 (residual)\nPrimary context: Residential (R), partial Day (D)\nDate range: Sessions 1–10 across 14 days (2026-03-01 to 2026-03-14)\n\nACCELERATION PROGRAMS\n1. Self-Care: Washing Hands (AFLS Basic Living)\n   Method: Task Analysis, backward chaining, 8 steps\n   Context: Both\n2. Requesting with AAC (VB-MAPP Mand L3 adapted)\n   Method: NET\n   Context: Both\n3. Community Safety Signs (AFLS Community)\n   Method: DTT\n   Context: D\n4. Tolerating Denied Access (FCT replacement)\n   Method: FCT, replacement response = \"wait please\"\n   Context: Both\n\nDECELERATION TARGETS\n1. Tantrum — function hypothesized: escape\n2. Mouthing (non-pica) — function hypothesized: automatic\n\nSession 1 — 2026-03-01 (R) — 45 min — 1 observer\n  Washing Hands: 3/8 steps independent (38%); prompts FP×3, PP×2, G×1\n  AAC Requests: freq = 4 (rate 0.09/min); 2 independent, 2 prompted\n  Safety Signs: 6/10 correct (60%); latency 4.2s\n  Tolerating Denied Access: 2/3 trials successful\n  Tantrum: freq 1, duration 4m\n  Mouthing: freq 8; PIR 20%\n  ABC (tantrum): A = iPad removed at 2:15pm; B = screaming + drop-to-floor; C = staff redirected to preferred activity after 4 min\n\nSession 2 — 2026-03-02 (R) — 50 min — 1 observer\n  Washing Hands: 3/8 (38%); prompts FP×3, PP×2, G×1\n  Safety Signs: 5/10 (50%); latency 4.8s\n  Tantrum: freq 2, duration 7m\n  Mouthing: freq 12; PIR 28%\n\n[... Sessions 3–9 ...]\n\nSession 7 — IOA SESSION — 2 observers\n  Washing Hands IOA: 87% agreement\n  Tantrum IOA: 91% agreement\n  AAC Requests IOA: 95% agreement\n\nSession 10 — 2026-03-14 (R) — 45 min — 1 observer\n  Washing Hands: 2/8 (25%); prompts FP×5, PP×2, G×1\n  Safety Signs: 4/10 (40%); latency 6.1s\n  Tolerating: 0/3 success\n  Tantrum: freq 4, duration 12m\n  Mouthing: freq 15; PIR 35%\n  ABC (tantrum, occurrence 2): A = asked to finish worksheet; B = hit table + scream; C = task removed for 5 min, staff attention\n\nBEHAVIORAL OBSERVATIONS\n- Increasing response latency in Safety Signs\n- Increasing tantrum duration\n- Mouthing rate climbing\n- Worksheet and non-preferred tasks consistently precede tantrums"
    },
    {
      "role": "assistant",
      "content": "## Clinical Concerns\n- Regression pattern in Safety Signs and Washing Hands: accuracy has declined from 60->40% and 38->25% respectively across 10 sessions.\n- Tantrum frequency and duration are increasing, clustered around demand presentation.\n- Mouthing rate is increasing, consistent with automatic function but also temporally correlated with tantrum increases.\n\n## Pattern Classification\nregression + frustration_pattern\n\nConcurrent regression in previously-approaching skills alongside a frustration pattern characterized by escape-indicator behaviors (declining accuracy + increased tantrum duration + demand-triggered occurrences).\n\n## Behavior Function Hypothesis\nTantrum: escape\n  Evidence: both documented ABC events show demand antecedent (iPad removal, worksheet task) followed by task/demand removal or redirection. Tantrum duration increases concurrent with demand difficulty.\nMouthing: automatic\n  Evidence: persists across contexts, no clear social consequence, occurs during low-demand periods and throughout sessions.\n\n## Programming Recommendations\n\n### Antecedent strategies\n- Reduce worksheet task duration by 50% for next 3 sessions; introduce choice between two acceptable non-preferred tasks before any demand.\n- Pre-teach \"wait please\" response before predictable iPad-removal windows.\n- Schedule preferred activity access immediately before (not after) known demand windows to leverage MO.\n\n### Replacement behavior (FCT)\n- Strengthen FCT training for Tolerating Denied Access — current 2->1->0/3 rate across sessions suggests teaching is not yet effective. Consider 0-second time delay prompting and increased reinforcement magnitude for independent \"wait please.\"\n- Pair \"wait please\" with a brief, predictable delay (10–15s) followed by reinforcement access.\n\n### Consequence strategies\n- Do NOT remove demand contingent on tantrum (currently reinforcing escape function).\n- Provide brief (20s) break contingent on independent \"wait please\" or equivalent communication.\n- Place tantrum on escape extinction: continue presenting the task while ensuring learner and staff safety.\n\n### Crisis plan\n- If tantrum exceeds 10 minutes or escalates to property destruction or aggression, follow facility crisis protocol, document the incident, and notify supervising BCBA within 24 hours.\n\n## Escalation Level\n3 — Supervisor review\n\nRegression co-occurring with increasing problem behavior warrants BCBA review within 24–48 hours before implementing proposed FCT and extinction changes.\n\n## Confidence\nmoderate\n\nFunction hypothesis is well-supported by 2/2 documented ABC events, but single-observer sessions limit IOA coverage to one session out of 10. Recommend one additional IOA session before finalizing the intervention plan.\n\n## Data-Supported Rationale\n- Mean Safety Signs accuracy sessions 1–3: 58%; sessions 8–10: 42% (16 percentage point decrement, 27% relative decline).\n- Mean tantrum frequency sessions 1–3: 1.3/session; sessions 8–10: 3.3/session (2.5× increase). Mean duration 4 min -> 12 min.\n- 2/2 documented ABC events show demand antecedent -> tantrum behavior -> task removal consequence, consistent with escape-maintained hypothesis.\n- Mouthing PIR 20% -> 35% across the same period (75% relative increase).\n- IOA data (session 7) — 87–95% agreement — supports data reliability for tantrum and AAC measures; no IOA for Safety Signs or Mouthing."
    }
  ],
  "meta": {
    "task_type": "session_interpretation",
    "example_id": "b5c9e2a14f8d7310",
    "gold_labels": {
      "pattern_class": "regression+frustration_pattern",
      "behavior_functions": {
        "Tantrum": "escape",
        "Mouthing": "automatic"
      },
      "escalation_level": 3,
      "confidence": "moderate",
      "crisis_plan_required": true
    },
    "log_properties": {
      "n_sessions": 10,
      "n_acceleration_programs": 4,
      "n_deceleration_targets": 2,
      "has_abc_data": true,
      "has_ioa_session": true,
      "learner_profile": "adolescent",
      "context_distribution": {"D": 0.2, "R": 0.8, "Both": 0.0}
    },
    "provenance": {
      "layer": 1,
      "template_id": "sess-regress-frust-v1",
      "pattern_seed": 20260423007,
      "seed": 20260423007,
      "generated_at": "2026-04-23T14:30:00Z"
    }
  }
}
```

---

## 5. Validation and parsing

### 5.1 Required fields

For every example (both tasks):
- `messages` present with exactly 3 entries: system, user, assistant (in that order)
- `meta.task_type` in `{teaching_program, session_interpretation}`
- `meta.example_id` present and non-empty
- `meta.gold_labels` present with task-specific required keys
- `meta.provenance.seed` present

### 5.2 Label extraction regex (for evaluator)

After model generation, labels are extracted from the assistant response using deterministic regex. If extraction fails, the example is scored as a parse failure (counts against the model).

**Pattern classification (task 2):**
```python
r"##\s*Pattern\s*Classification\s*\n\s*([a-z_+]+)\s*\n"
```

**Escalation level (task 2):**
```python
r"##\s*Escalation\s*Level\s*\n\s*([1-4])\s*—"
```

**Confidence (task 2):**
```python
r"##\s*Confidence\s*\n\s*(high|moderate|low)\s*\n"
```

**Behavior function (task 2, per behavior):**
```python
r"^([A-Z][A-Za-z\s\-\(\)]+):\s*(escape|attention|tangible|automatic|unknown)\s*$"
```

**Method (task 1, validated against user input):**
```python
# No regex needed — method is sampled and stored in gold_labels; evaluator checks
# whether the assistant output contains the method-specific sections (section 3.4)
# corresponding to the expected method.
```

### 5.3 Schema validity checks (pre-training)

`src/prepare_data.py` applies these before writing to splits:

1. All 3 messages present with correct roles
2. System prompt matches canonical form for the task
3. Assistant response contains all required section headers for its task
4. Structured-label sections are regex-extractable
5. No placeholder strings (`{...}`, `TODO`, empty `Provide:` blocks) in assistant content
6. User message contains no real-world identifying patterns (regex scan for name-like tokens)
7. Total length under `max_seq_length` (4096 tokens for training)
8. No duplicate `example_id` across the full dataset (SimHash + exact-match dedup)

Examples failing any check are written to `data/processed/rejected.jsonl` with a `reason` field.

---

## 6. Extensibility

### 6.1 Adding new session patterns

1. Add entry to `taxonomy-v1.md` section 7 with citation.
2. Add generator template in `src/prepare_data.py` with trajectory rules.
3. Add label to regex enum in section 5.2.
4. Add stratification target in split generator.
5. Bump schema version.

### 6.2 Adding new teaching methods

1. Add entry to `taxonomy-v1.md` section 1.
2. Add method-specific output variant to `schema-v1.md` section 3.4.
3. Add generator template in `src/prepare_data.py`.
4. Bump schema version.

### 6.3 Versioning

Schema versions follow `major.minor`:
- **Minor** — additive changes (new pattern, new method, new optional field). Old data remains valid.
- **Major** — breaking changes (renamed fields, removed sections, changed required structure). Old data requires migration or a new dataset version.

Each generated example records the schema version it was generated under in `meta.provenance.schema_version`.

---

## 7. Changelog

- **v1.0 (2026-04-23)** — initial schema. Two tasks defined. Task 1 covers 6 teaching methods (DTT, NET, Task Analysis, FCT, BST, PRT); Task 2 covers 12 session patterns with structured labels for pattern class, behavior function, escalation level, and confidence.
