---
pretty_name: "TRACE — Taxonomy-Referenced ABA Clinical Examples"
license: cc-by-nc-4.0
language:
  - en
size_categories:
  - 1K<n<10K
task_categories:
  - text-generation
tags:
  - clinical
  - applied-behavior-analysis
  - autism
  - small-language-model
  - synthetic
  - instruction-tuning
  - taxonomy
  - provenance
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/splits/train.jsonl
      - split: validation
        path: data/splits/valid.jsonl
      - split: test
        path: data/splits/test.jsonl
      - split: sanity
        path: data/splits/sanity.jsonl
---

# TRACE Dataset Card (v1)

**Name:** **TRACE** — **T**axonomy-**R**eferenced **A**BA **C**linical **E**xamples
**Version:** v1.0.0
**Date:** 2026-04-25
**Primary language:** English
**License (data):** CC BY-NC 4.0 · **License (code):** MIT
**Total examples:** 2,999
**Tasks:** 2 — (1) ABA teaching program generation, (2) behavioral session interpretation.
**Author:** Festus Kahunla (Drexel University).
**Publisher / maintained by:** [Pombo Labs](https://github.com/Pombo-Labs).
**Repository:** https://github.com/Pombo-Labs/TRACE

---

## 1. TL;DR

TRACE is a **synthetic instruction-tuning dataset** for two clinical tasks in Applied Behavior Analysis (ABA):

1. **Teaching program generation** — given a learner profile and a skill target, produce a structured teaching program (DTT, NET, or Task Analysis/chaining) covering stimulus control, prompt hierarchy, reinforcement schedule, error correction, mastery criterion, and generalization plan.
2. **Behavioral session interpretation** — given a multi-session behavioral log (accuracies, target behaviors with measurements, optional ABC and IOA data), produce clinical concerns, a pattern classification, a function hypothesis, programming recommendations, and (when applicable) a crisis plan.

The dataset was produced by a **taxonomy-driven generator** whose controlled vocabulary is grounded in the canonical ABA literature (Cooper, Heron, & Heward 2020; VB-MAPP; AFLS; key JABA papers). Every example carries full **provenance metadata** — the exact taxonomy cells that were sampled to produce it. Clinical accuracy was iterated via practitioner-in-the-loop ad-hoc review.

**Intended use.** Research. TRACE is designed for fine-tuning small language models (e.g., 4-bit Gemma 4 E2B with QLoRA) on ABA-flavored instruction-following, as a substrate for research into clinical-NLP data pipelines, taxonomy-driven synthetic generation, and small-LM evaluation.

**Not for:** autonomous clinical decisions; training on or combining with real client data; medical diagnosis; legal or insurance documentation. TRACE has not been clinically validated and is not a clinical tool. See section 6 for the responsibility disclaimer.

---

## 2. Dataset Composition

### 2.1 Splits

| Split | Examples | Fraction | Purpose |
|---|---:|---:|---|
| `train.jsonl` | 2,549 | 85.0% | LoRA fine-tuning |
| `valid.jsonl` | 149 | 4.97% | Periodic validation loss during training |
| `test.jsonl` | 281 | 9.37% | Held-out evaluation (headline metrics) |
| `sanity.jsonl` | 20 | 0.67% | Training smoke-test (tiny stratified subset) |
| **Total** | **2,999** | 100% | |

Splits are **stratified by task × category** (method for teaching programs; pattern_class for session interpretation) so each split mirrors the corpus distribution. The test set is the full curation pool minus a 20-example stratified sanity carveout.

### 2.2 Per-area breakdown

| Area | Count | Task type | Primary source |
|---|---:|---|---|
| DTT | 800 | teaching_program | VB-MAPP (array-based discrete-response domains) |
| NET | 500 | teaching_program | VB-MAPP (mand, social, spontaneous vocal, intraverbal) |
| Task Analysis | 500 | teaching_program | AFLS (basic_living, home, community, vocational, independent_living) |
| Session Interpretation | 1,200 | session_interpretation | 12 clinical trajectory patterns |

### 2.3 DTT skill-domain distribution (800 total)

| VB-MAPP domain | Count |
|---|---:|
| Reading | 131 |
| LRFFC (Listener Responding by Feature/Function/Class) | 126 |
| Math | 120 |
| Visual Perceptual / Matching-to-Sample | 115 |
| Listener Responding | 111 |
| Tact | 106 |
| Writing | 91 |

Sampled across VB-MAPP Levels 1 (≈45%), 2 (≈40%), and 3 (≈15%).

### 2.4 NET skill-domain distribution (500 total)

| VB-MAPP domain | Count |
|---|---:|
| Spontaneous Vocal | 143 |
| Mand (including bathroom, break, all-done) | 141 |
| Social Behavior & Play | 131 |
| Intraverbal | 85 |

Each NET program carries a Motivating Operation arrangement matched to the skill (deprivation, missing-item, break opportunity, completion opportunity, bathroom opportunity, peer presence, reciprocal conversation, routine lead-in) and is embedded in a natural context (snack, free play, transition, arrival, etc.).

### 2.5 Task Analysis distribution (500 total)

| AFLS module | Count | | Program type | Count |
|---|---:|---|---|---:|
| Basic Living | 172 | | Independence | 413 |
| Home | 96 | | Toleration (systematic desensitization) | 87 |
| Community | 94 | | | |
| Vocational | 76 | | | |
| Independent Living | 62 | | | |

**Toleration programs** are a distinct program type for learners whose clinical goal is to *allow* a caregiver-delivered routine (tooth brushing, hair washing, nail clipping, haircuts, showering, medical exam) rather than to perform it independently. They use a shaping progression with duration targets rather than a step chain.

### 2.6 Session Interpretation distribution (1,200 total)

Twelve trajectory patterns, roughly uniform (84–113 each):

| Pattern | Count |
|---|---:|
| regression | 113 |
| prompt_dependency | 109 |
| setting_event_trigger | 107 |
| rapid_acquisition | 106 |
| motivating_operation_shift | 104 |
| generalization_failure | 103 |
| mastery_progression | 100 |
| skill_loss_after_break | 100 |
| plateau | 96 |
| frustration_pattern | 91 |
| variable_performance | 87 |
| extinction_burst | 84 |

**Target behaviors** sampled into logs (presence per log; a log carries 0–3 behaviors):

| Behavior | Logs | Measurement shape |
|---|---:|---|
| Aggression | 95 | freq |
| Toileting (urine + BM, in-toilet + accidents) | 89 | `urine: X in-toilet / Y accidents; BM: P in-toilet / Q accidents` |
| Pica | 81 | `attempts N (X unsuccessful; Y successful)` |
| Self-Injurious Behavior (SIB) | 79 | freq |
| Verbal Aggression | 79 | freq |
| Fecal Smearing (scatolia) | 78 | `attempts N (X intercepted; Y completed)` |
| Property Destruction | 75 | freq |
| Elopement | 75 | freq |
| Non-compliance | 70 | freq |
| Tantrum | 66 | `freq N, duration Mm total` |
| Mouthing | 56 | `freq N; PIR P%` |
| Motor Stereotypy | 50 | `freq N; PIR P%` |
| Vocal Stereotypy | 48 | `freq N; PIR P%` |

---

## 3. Data Format

### 3.1 Wire format

Each example is one JSONL line:

```json
{
  "messages": [
    {"role": "system",    "content": "<ABA clinical-assistant system prompt>"},
    {"role": "user",      "content": "<task-specific prompt>"},
    {"role": "assistant", "content": "<structured clinical response>"}
  ],
  "meta": {
    "task_type":    "teaching_program" | "session_interpretation",
    "example_id":   "<deterministic hash, 16-hex>",
    "gold_labels":  { ... task-specific labels ... },
    "provenance":   {
      "layer": 1,
      "area":  "dtt" | "net" | "task_analysis" | "session_interpretation",
      "template_id": "...",
      "taxonomy_cells": { ... exact sampled values ... },
      "teacher_model": null,
      "seed_tag": "...",
      "generated_at": "..."
    }
  }
}
```

Only `messages` is used for training (mask_prompt: true). `meta` is preserved for evaluation and provenance tracking.

### 3.2 Gold labels per task

**Teaching program:**
```
{
  "method":          "dtt" | "net" | "task_analysis",
  "domain":          "VB-MAPP.<domain>" | "AFLS.<module>",
  "level":           "L1" | "L2" | "L3" | ...,     # VB-MAPP only
  "learner_profile": "early" | "school_age" | "adolescent" | "adult",
  "mastery_state":   "emerging" | "developing" | "approaching" | "near" | "mastered" | "generalization",
  "program_type":    "independence" | "toleration",  # Task Analysis only
  "chain_type":      "forward" | "backward" | "total_task"  # Task Analysis only
}
```

**Session interpretation:**
```
{
  "pattern_class":        "<one of 12 patterns>",
  "behavior_functions":   { "<behavior_name>": "escape"|"attention"|"tangible"|"automatic"|"unknown" },
  "escalation_level":     1 | 2 | 3 | 4,
  "confidence":           "high" | "moderate" | "low",
  "crisis_plan_required": true | false
}
```

### 3.3 Provenance

Every sampled choice is recorded in `meta.provenance.taxonomy_cells`. For teaching programs this includes the skill target, prompt hierarchy, reinforcement schedule, error correction, and mastery criterion. For session interpretation it includes the pattern, number of sessions, behaviors sampled, functions inferred, and whether IOA and ABC data are present. This enables:

- **Traceability:** any clinical issue in a generated example can be traced back to the exact taxonomy cell that produced it.
- **Reproducibility:** the dataset can be regenerated deterministically from the configs and seed.
- **Stratification:** splits can be regenerated with different stratification keys without regenerating the corpus.
- **Ablation:** subsets can be constructed by filtering on provenance cells.

---

## 4. How It Was Built

### 4.1 Architecture

```
configs/
├── shared/                          # cross-area primitives (learner profiles, mastery states, prompt types)
├── dtt/                             # DTT area: taxonomy + template + compatibility
├── net/                             # NET area
├── task_analysis/                   # Chaining area (independence + toleration templates)
└── session_interpretation/          # Session interp area:
                                     #   taxonomy + compatibility + trajectory_rules
                                     #   + recommendations (per-pattern bullets) + template
src/generators/
├── aba_dtt.py                       # per-area generator
├── aba_net.py
├── aba_task_analysis.py
└── aba_session_interp.py
src/generate.py                      # orchestrator
```

### 4.2 Generation loop

For each example:
1. Sample a clinical configuration from the taxonomy, weighted by realistic clinical frequency (level weights, module weights, pattern weights).
2. Apply compatibility rules (e.g., DTT errorless error correction pairs only with most-to-least prompting; certain patterns have bias toward certain behavior functions).
3. Compute template slots — current-prompt-level guidance from mastery state; MO arrangement from skill keywords; mastery criterion; reinforcement schedule.
4. Render `user_content` from a random user-variant.
5. Render `assistant_content` by filling `{slots}` in the assistant template.
6. Stamp `meta.gold_labels` and `meta.provenance`.
7. Write as one JSONL line.

### 4.3 Grounding

- **Skill curricula** — VB-MAPP milestones (Sundberg 2008) for verbal-behavior domains; AFLS (Partington & Mueller) for adaptive-living domains.
- **Teaching methods** — DTT (Lovaas 1987; Smith 2001); NET (Hart & Risley 1975 in CHH Ch. 18); Task Analysis / chaining (CHH Ch. 20).
- **Operational definitions of target behaviors** — Cooper/Heron/Heward Ch. 3, 27; key JABA papers (Iwata et al. 1994 for SIB and functional analysis; Carr & Durand 1985 for FCT; Hanley, Iwata, & McCord 2003 for FBA).
- **Session patterns** — derived from CHH Ch. 6–7 (analyzing behavior change) and Stokes & Baer 1977 (generalization).
- **Crisis plans** — BACB Ethics Code (2020) section 3.05; ABAI Position Statement on Restraint and Seclusion (2010). Physical-intervention procedures are left vague on purpose because they vary by training program (Safety-Care, CPI, PMT, TCI) and jurisdiction; the dataset emphasizes verbal de-escalation, environmental safety, BIP authorization, and contraindications.

### 4.4 Clinical-accuracy pipeline

Initial generation produced the structural skeleton. The corpus was then iterated via **practitioner-in-the-loop review** — a full-text render of the held-out candidate pool was browsed by a reviewer with ABA practitioner exposure, and each flagged clinical inaccuracy was traced to the responsible taxonomy cell and fixed with a single targeted edit plus a full regeneration. Because every example records its sampling provenance, a single cell-level edit propagates to every example that sampled the affected cells — so flagging one example systematically corrects a class of examples.

---

## 5. Intended Uses

### 5.1 Direct use
- Instruction-tuning a small language model (recommended: Gemma 4 E2B 4-bit with QLoRA) to draft ABA teaching programs and interpret session logs.
- Evaluation of task-specific competencies using the held-out `test.jsonl` (281 examples).
- Research on taxonomy-driven synthetic data generation for clinical decision support.

### 5.2 Downstream use
- Research on small-LM drafting assistants in structured clinical-documentation domains.
- Comparison baselines for future ABA-specific LLM work (Kumar et al. 2024 "Personalized-ABA" is the closest direct predecessor; the present dataset extends to structured program generation and session-log interpretation).

### 5.3 Out-of-scope (do NOT use for)
- Autonomous clinical decisions.
- Writing final Behavior Intervention Plans without BCBA review.
- Training models on or combined with real client records (the pipeline and schema are explicitly designed to avoid this).
- Legal or insurance documentation.
- Medical diagnosis.

---

## 6. Ethics & Risks

### 6.1 Provenance
Every example is synthetic. No real client data, no real session notes, no real identifiers were used at any step. Learner references use synthetic IDs (`SYN-####`); dates fall in the range 2026-01-01 to 2026-12-31.

### 6.2 Clinical-risk framing
The dataset is designed around a **draft-and-review** authoring pattern. Assistant responses are structured so that a reviewer can quickly see the method, the stimulus arrangement, the prompt hierarchy, the reinforcement plan, the error-correction procedure, the mastery criterion, and the generalization plan — each as a distinct, scannable section. Session-interpretation responses surface a confidence level (high / moderate / low) and an escalation level (1–4) as structured fields. These are design choices that support auditability; they are not clinical advice, and TRACE's responsibility disclaimer applies.

### 6.3 Crisis-plan sensitivity
Crisis plans were written against the ABAI 2010 Position Statement on Restraint and Seclusion and BACB Ethics Code 2020 section 3.05. The dataset references facility crisis-prevention frameworks (Safety-Care, CPI, PMT, TCI) only as examples and **deliberately avoids specifying restraint procedures** because those procedures are (a) jurisdiction-dependent, (b) training-certification-gated, and (c) learner-specific (many learners have contraindications). The dataset embeds explicit text in every crisis-plan bullet that physical intervention is used only when specifically authorized in the learner's BIP and only by staff currently certified in the facility's training program.

### 6.4 Population representation
Learner profiles are intentionally abstract (early / school-age / adolescent / adult). The dataset does not encode demographic categories (race, socioeconomic status, gender identity) and does not attempt to characterize clinical presentations by such categories. This is a deliberate choice for a first release; future versions may add representation if grounded in published demographic work.

### 6.5 Known limitations
- **English only.** Teaching method terminology, curriculum targets, and session-log conventions are rendered in English.
- **Synthetic distributions.** Pattern frequencies are approximately uniform for learnability; real clinical practice has different frequencies (mastery-progression is far more common than frustration-pattern in a healthy caseload). The dataset is explicitly a teaching set, not an epidemiological sample.
- **VB-MAPP + AFLS only.** Other curricula (ABLLS-R, Essential for Living, PEAK) are not covered. Practitioners using those curricula should adapt.
- **No longitudinal data.** Sessions within a log are temporally ordered but the pipeline does not model real continuity over months or years.
- **Toleration covers hygiene only.** Other toleration programs (e.g., wearing glasses, riding in a car seat) are not represented.
- **Toilet-training acquisition is out of scope.** Accidents are tracked in session logs and bathroom-requesting is taught as a NET mand, but the full Azrin & Foxx 1971 rapid toilet-training acquisition protocol is not included as a task-analysis program.

### 6.6 License
**Data:** CC BY-NC 4.0 — research and non-commercial use with attribution. **Code:** MIT.

**Responsibility.** TRACE is a research artifact. It is not a clinical tool, has not been clinically validated, and carries no clinical endorsement. Anyone who chooses to deploy TRACE — or any model derived from it — in a clinical setting does so entirely at their own responsibility and under their facility's own oversight. The authors and Pombo Labs make no representation of clinical suitability and accept no liability for clinical outcomes.

---

## 7. Reproducibility

The corpus is regenerated deterministically from:
- `configs/` (all YAMLs)
- `configs/generation.yaml` (seed and per-area counts)
- `src/generators/*.py` (generator code)

```bash
uv run python src/generate.py --all                  # regenerate 3000 examples
uv run python src/split_data.py                      # stratified split
uv run python src/prepare_curation.py                # browseable review.md
uv run python src/compile_curation.py                # test.jsonl + sanity.jsonl
```

The dataset version is `v1.0.0`; the matching git tag pins the exact configs and generator code that produced the published JSONL splits.

---

## 8. Citation

Please cite as:

> Kahunla, F. (2026). *TRACE: Taxonomy-Grounded Synthetic Data for Teaching Program Generation and Session Interpretation in Applied Behavior Analysis.* Pombo Labs. https://github.com/Pombo-Labs/TRACE

Machine-readable metadata: `CITATION.cff`.

---

## 9. Appendices

- **Datasheet** (Gebru et al. 2021 format): `datasheet.md`
- **Data statement** (Bender & Friedman 2018 format): `data-statement.md`
- **Taxonomy reference** (operational definitions + citations): `taxonomy-v1.md`
- **Schema reference** (wire format + slot specifications): `schema-v1.md`
