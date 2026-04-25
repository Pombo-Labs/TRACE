# Data Statement for TRACE (v1)

**TRACE** — **T**axonomy-**R**eferenced **A**BA **C**linical **E**xamples

Template: Bender, E. M., & Friedman, B. (2018). *Data Statements for Natural Language Processing: Toward Mitigating System Bias and Enabling Better Science.* Transactions of the Association for Computational Linguistics. https://aclanthology.org/Q18-1041/

---

## A. Curation Rationale

### Why this data, and why this composition?
Applied Behavior Analysis (ABA) is a clinical discipline with high documentation workload — BCBAs produce teaching programs and interpret multi-session behavioral logs continuously across their caseloads. Existing general-purpose language assistants are both unspecialized to ABA's structured conventions (operational definitions, VB-MAPP / AFLS curricula, functional-analysis frameworks) and unvetted against its clinical standards (BACB Ethics Code 2020; ABAI 2010 Position Statement on Restraint). This dataset was curated to support fine-tuning a small on-device language model (Gemma 4 E2B) specifically for **drafting** — i.e., producing first-pass teaching programs and session interpretations that a BCBA then reviews and revises — without any ingestion of real client data.

Two tasks are represented because they are the two highest-frequency authorial tasks in an ABA clinical team's week: (1) drafting teaching programs for new or evolving skill targets, and (2) interpreting session-by-session behavioral data to adjust programming. They share a taxonomy (learner profiles, mastery states, teaching methods, target behaviors) but diverge in structure (teaching-program responses are single-program documents; session-interpretation responses are diagnostic summaries).

### Why synthetic?
Real ABA session data contains 45 CFR 164 protected health information (PHI) under HIPAA and is additionally subject to BACB Ethics Code confidentiality rules (section 2.03, section 2.05). Any public dataset drawn from real client data would require individual consent, facility release, and de-identification that cannot reliably preserve the clinical detail required for training. Synthetic generation avoids these constraints by construction: the data never represented a real person in the first place. The trade-off — distributions may not match any one real caseload — is made explicit in the dataset card (section 6.5) and flagged to users.

---

## B. Language Variety

All text is in **English (en-US)**, written in standard American clinical register. The authorial style follows the conventions of:
- **Peer-reviewed ABA literature** — *Journal of Applied Behavior Analysis* (JABA), *Behavior Analysis in Practice* (BAP).
- **Reference textbook** — Cooper, Heron, & Heward (2020), *Applied Behavior Analysis* (3rd ed.).
- **Professional documentation** — BACB Ethics Code (2020), ABAI Position Statements.

Within that register, the dataset covers:
- **Teaching-program language** — imperative instructional prose (stimulus control description, prompt hierarchy specification, reinforcement-schedule specification, error-correction procedure, mastery criterion).
- **Session-log language** — telegraphic data-sheet notation (`accuracy 6/10 (60%); freq 2; duration 3m; IOA 88%`) mixed with ABC-entry prose.
- **Clinical-interpretation language** — structured prose matching the assistant template's headings (Clinical Concerns, Pattern Classification, Behavior Function Hypothesis, Programming Recommendations, Crisis Plan when applicable, Confidence).

There is no dialectal variation, no code-switching, no second-language speaker voice. Generalization to non-US clinical conventions (BCBA-D vs. international RBT frameworks, different curricula) is explicitly out of scope for v1.

---

## C. Speaker Demographic

**Not applicable.** The dataset has no speakers. All content is programmatically generated from taxonomy configs written by a single author with ABA domain fluency. The written conventions inherit from the sources listed in section B.

---

## D. Annotator Demographic

**Not applicable in the conventional sense.** No human annotators labeled instances after generation. Gold labels are emitted at generation time from the same taxonomy cells that produced the example — they are by-construction the ground truth of the sampling step.

**Quasi-annotator role: clinical-accuracy reviewer.** One individual (the dataset author) performed ad-hoc clinical-accuracy review of generated candidates during iteration. This reviewer:

- Has practitioner-adjacent exposure to ABA clinical settings (not a BCBA; not a BCaBA; not an RBT in active practice).
- Is a native English speaker, fluent in the English clinical-documentation register.
- Performed review by browsing full-text candidate renderings and flagging clinical implausibilities against published sources (CHH 2020; BACB Ethics Code 2020; JABA papers for operational definitions).

**What this means for the dataset:**
- Clinical-accuracy review was grounded in published sources, not in one reviewer's clinical judgment alone. Where a reviewer uncertainty could not be resolved from a source, the item was retained with a flag rather than decided by individual preference.
- Full BCBA-level clinical validation (multi-reviewer, κ-scored) was not performed on v1.
- Bias from the reviewer's particular exposure (specific facility types, specific learner age ranges, specific behavioral topographies) is possible. The taxonomy's grounding in CHH and JABA is the mitigating control.

---

## E. Speech Situation

**Not applicable** (no speech). The imagined reader/user for the generated text:
- **Teaching programs** — a BCBA or behavior technician reading a first-pass program draft for clinical review, before it is finalized and implemented with a learner.
- **Session interpretations** — a BCBA or supervising analyst reading a summary of the most recent N sessions of a learner's data, as a decision-support document for programming adjustments.

The modality is written documentation, asynchronous, read in quiet clinical-office settings. The register is clinical-professional.

---

## F. Text Characteristics

### Genre
- Clinical documentation (teaching programs, behavioral session interpretations).
- Instructional prose interleaved with structured data-sheet notation.

### Structural Conventions
- Teaching programs follow a fixed section layout (Program Overview, Stimulus Control, Prompt Hierarchy, Reinforcement, Error Correction, Mastery Criteria, Generalization & Maintenance Plan). Variants exist for DTT, NET, and Task Analysis; Task Analysis has a distinct toleration-program layout.
- Session logs are rendered as pseudo-data-sheet blocks, one block per session, with per-program accuracy lines, per-behavior measurement lines, and optional ABC / IOA entries.
- Session interpretations follow a fixed layout (Clinical Concerns, Pattern Classification, Behavior Function Hypothesis, Programming Recommendations, Crisis Plan, Confidence).

### Domain-specific notation
- ABA abbreviations used freely: SD (discriminative stimulus), MO (motivating operation), ABC (antecedent-behavior-consequence), IOA (interobserver agreement), PIR (partial-interval recording), CRF (continuous reinforcement), FR-2, VR-3, etc.
- Measurement notation follows the schema in `schema-v1.md section 2.3`.

### Distribution characteristics
- Target behaviors: sampled per pattern (0–3 per log).
- Accuracy trajectories: driven by pattern-specific generators (ascending for mastery_progression, descending for regression, etc.).
- Behavior frequencies: pattern-trajectory-driven; bounded.
- Severity: per-behavior `typical_severity` flag (low/moderate/high) feeds escalation logic.

### What the dataset *does not* contain
- Personal names.
- Real identifiers.
- Dates outside 2026-01-01 to 2026-12-31.
- Non-English text.
- Informal register (chat-style, SMS, social media).
- Off-topic content.
- Adversarial or jailbreak examples.
- Real session notes or documentation.

---

## G. Recording Quality

**Not applicable** (no recording).

---

## H. Other

### Provenance guarantee
Every example carries full sampling provenance in `meta.provenance.taxonomy_cells`. This is the artifact that makes clinical auditing tractable: when a reviewer flags an implausible example, they can trace it to the exact cells that generated it and propose a taxonomy or compatibility-rule fix. This is a property of the dataset we consider essential and want future versions to preserve.

### Known biases
- **Caseload-distribution bias.** Pattern frequencies are uniform across the 12 session-interpretation patterns for learnability, whereas real caseloads skew toward mastery_progression. Users training epidemiological models should reweight.
- **Curriculum bias.** VB-MAPP and AFLS are the only curricula covered. Practitioners using ABLLS-R, Essential for Living, PEAK, or other curricula should adapt.
- **Register bias.** All text is US clinical-professional. Non-US or non-clinical register is not represented.
- **Reviewer-exposure bias.** Clinical review was performed by a single reviewer. See section D.
- **Synthetic-distribution bias.** Sampling weights reflect clinical frequency where known but are approximate.

### Transparency commitments
- Full generator code is public in the repository.
- Full taxonomy configs are public in the repository.
- Dataset regeneration from `(configs, seed)` is deterministic.
- Every version of the dataset is pinned to a specific repository commit hash.
- All citations used to ground taxonomy content are enumerated in `docs/research/citations-to-use.md`.
