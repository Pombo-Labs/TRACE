# Datasheet for TRACE (v1)

**TRACE** — **T**axonomy-**R**eferenced **A**BA **C**linical **E**xamples

Template: Gebru, T., Morgenstern, J., Vecchione, B., Wortman Vaughan, J., Wallach, H., Daumé III, H., & Crawford, K. (2021). *Datasheets for Datasets.* Communications of the ACM. https://arxiv.org/abs/1803.09010

---

## Motivation

### Why was the dataset created?
To provide the first public, open-access synthetic instruction-tuning dataset for two tasks in Applied Behavior Analysis (ABA): (1) teaching program generation and (2) multi-session behavioral interpretation. Board Certified Behavior Analysts (BCBAs) draft large numbers of these documents weekly; current LLM assistants are both unspecialized to ABA and unvetted against its clinical standards. The dataset supports fine-tuning a small, on-device language model (Gemma 4 E2B at 2B parameters) for drafting support, preserving clinical oversight at the point of deployment.

### Who funded the creation of the dataset?
No external funding. Authored by Festus Kahunla (Drexel University) and released publicly under the **Pombo Labs** organization (https://github.com/Pombo-Labs).

### Any other comments?
The dataset's primary novelty is its **taxonomy-driven construction with complete provenance**: every example can be traced back to a specific set of taxonomy cells that produced it. This is a deliberate choice to make clinical validity auditable.

---

## Composition

### What do the instances represent?
Two instance types:

1. **Teaching-program instances** (1,800 total) — a user message describes a learner profile and a skill target; an assistant message produces a structured teaching program. Covers three methods: Discrete Trial Training (DTT, 800), Natural Environment Teaching (NET, 500), Task Analysis / chaining (500).

2. **Session-interpretation instances** (1,200 total) — a user message contains a multi-session behavioral log (5–12 sessions, with per-session accuracies, target behaviors with measurements, and optional ABC and IOA data); an assistant message produces clinical concerns, a pattern classification, a function hypothesis, recommendations, and when applicable a crisis plan.

### How many instances are there in total?
2,999.

### Does the dataset contain all possible instances or is it a sample?
The dataset is a **programmatic sample** from a combinatorial space defined by the taxonomy. The space is formally enumerable (domains × levels × learner profiles × mastery states × prompt hierarchies × reinforcement schedules × error corrections × mastery criteria) but is far larger than 2,999 examples. Sampling weights reflect approximate clinical frequency where known (e.g., VB-MAPP Level 1 is sampled more heavily than Level 3 for DTT because early learners dominate the data space in practice).

### What data does each instance consist of?
See `schema-v1.md` and `dataset-card.md section 3`. Each instance is one JSONL line with two top-level keys:
- `messages` — a three-message chat triple (system, user, assistant) that the fine-tuner trains on.
- `meta` — task type, example ID, gold labels, and full sampling provenance (ignored during training).

### Is there a label or target associated with each instance?
Yes, stored in `meta.gold_labels`. For teaching programs: method, domain, level, learner profile, mastery state. For session interpretation: pattern class, behavior functions, escalation level, confidence, crisis-plan requirement.

### Is any information missing from individual instances?
Some instances have optional data by design:
- **Task Analysis / toleration programs** have `shaping_steps` instead of `steps` and no `chain_type` (not applicable).
- **Session logs** carry ABC data on approximately 30% of sessions when behaviors are present; IOA data on approximately 25% of logs; behavioral-indicator clusters per pattern. Absence of these is intentional, not missingness.

### Are relationships between individual instances made explicit?
Instances are independent by construction. No implicit links between examples.

### Are there recommended data splits?
Yes. The dataset ships with four split files:

| Split | Count | Fraction | Purpose |
|---|---:|---:|---|
| `train.jsonl` | 2,549 | 85% | LoRA fine-tuning |
| `valid.jsonl` | 149 | 5% | Validation during training |
| `test.jsonl` | 281 | 9.4% | Held-out evaluation |
| `sanity.jsonl` | 20 | 0.7% | Training smoke-test |

All splits are stratified by area × category to preserve the corpus distribution.

### Are there errors, sources of noise, or redundancies?
- **Template repetition.** Assistant responses follow a structured template; lexical patterns recur by design. This is an intentional trade-off for learnability.
- **Sampling drift.** Because the generator samples independently per example, some combinations of cells can land improbable but not impossible (e.g., a "mastered" skill still running an error-correction procedure). Compatibility rules reduce this; ad-hoc practitioner review catches the rest.
- **Clinical accuracy.** Every example passed at least a syntactic quality check. A subset underwent ad-hoc practitioner review during iteration; not every example has been individually inspected.

### Does the dataset contain data that might be considered confidential?
No. All data is synthetic. No real client information. No real session notes. No real names, dates, or IDs. Synthetic IDs use the `SYN-####` pattern from a fixed range; synthetic dates fall in 2026-01-01 to 2026-12-31.

### Does the dataset contain data that might be offensive, insulting, threatening, or otherwise cause anxiety?
The session logs describe challenging behavior (aggression, self-injury, property destruction, pica, elopement, fecal smearing, toileting accidents, tantrum). These descriptions are clinical in register and grounded in the operational definitions used in the peer-reviewed JABA literature. They may be distressing to readers unfamiliar with ABA. Target behaviors appear only in the context of a session log being interpreted — they are never endorsed, glorified, or represented outside clinical framing.

### Does the dataset relate to people?
Indirectly. Instances describe synthetic learners in clinical scenarios. No real people are identifiable. No real demographic distributions are encoded.

### Does the dataset identify any sub-populations?
Learner profiles are:
- **Early Learner** (≈3–5 years; VB-MAPP L1 or L2 depending on skill)
- **School-Age** (≈6–10 years; VB-MAPP L2–L3, AFLS basic_living and home)
- **Adolescent** (≈11–17 years; AFLS community, vocational)
- **Adult** (≈18+ years; AFLS independent_living primary)

These are developmentally anchored; they do not encode race, ethnicity, socioeconomic status, or gender identity. No sub-populations are characterized on those axes.

### Is it possible to identify individuals from the dataset?
No. The dataset is synthetic.

### Does the dataset contain data that might be considered sensitive?
The subject matter is sensitive — autism-related clinical challenges, problem behavior, restraint-related crisis planning. The data itself is not sensitive because it is synthetic. Care was taken in the crisis-plan content to cite authoritative sources (BACB Ethics Code 2020 section 3.05; ABAI 2010 Position Statement) and to avoid prescribing restraint procedures directly.

---

## Collection Process

### How was the data associated with each instance acquired?
Programmatic generation. The pipeline is a deterministic function of (a) the YAML taxonomy configs and (b) a random seed. Inputs to the generator come from published curricula (VB-MAPP; AFLS) and textbook / JABA / BACB Ethics Code content that was manually encoded into the taxonomy YAMLs by the authors. **No web scraping. No ingestion of patient records. No use of real session notes.**

### What mechanisms or procedures were used?
Python scripts under `src/generators/` with taxonomy YAMLs under `configs/`. See `dataset-card.md section 4`.

### If sampled, what was the sampling strategy?
Weighted random sampling on each taxonomy dimension, with compatibility rules applied afterward to reject clinically inconsistent combinations. Weights are human-specified (in `compatibility.yaml` files) to approximate clinical frequency.

### Who was involved in the data collection process?
Festus Kahunla (Drexel; Pombo Labs) wrote the generator and the taxonomy, conducted clinical-accuracy review, and authored the dataset docs.

### Over what timeframe was the data collected?
January 2026 to April 2026. The early months covered taxonomy research, literature grounding, and pipeline design; the corpus itself was generated and iterated in April 2026.

### Were any ethical review processes conducted?
No IRB required — the dataset is entirely synthetic. The generator architecture is explicitly designed so no real client data can enter the pipeline. Clinical scope (what counts as a reasonable teaching program, what crisis procedures are appropriate) was grounded in published sources (BACB Ethics Code 2020; ABAI 2010 Position Statement; Cooper, Heron, & Heward 2020) rather than personal clinical experience.

### Does the dataset relate to people? If so, did you collect data from them directly or from a third-party?
The dataset does not relate to any real person. No data was collected from any person.

### Were the individuals in question notified about data collection?
Not applicable (no real individuals).

### Did the individuals in question consent to data collection?
Not applicable (no real individuals).

### If consent was obtained, were they given a mechanism to revoke consent?
Not applicable.

### Has an analysis of the potential impact of the dataset and its use on data subjects been conducted?
The dataset has no data subjects. The intended model users (BCBAs and ABA technicians) are discussed in section 6.2 of the dataset card (clinical-risk framing) and section 6.3 (crisis-plan sensitivity).

---

## Preprocessing / Cleaning / Labeling

### Was any preprocessing / cleaning / labeling of the data done?
- **Labeling.** Gold labels are emitted at generation time from the same taxonomy cells that produced the example. No post-hoc annotation. Labels are therefore by-construction correct for the taxonomy; they are only as valid as the taxonomy is (see section 4.3 of the dataset card for grounding).
- **Deduplication.** Example IDs are deterministic hashes of the message content; duplicates (same user + assistant content) would be detected across generations, but in practice duplicates do not occur because every render draws fresh random values for the slots.
- **Filtering.** Compatibility rules reject clinically inconsistent samples before rendering. No post-rendering filter is applied.

### Was the "raw" data saved in addition to the preprocessed data?
The generator is a deterministic function of (configs, seed) and produces the same data on every run. There is no separate "raw" stage — every artifact is reproducible from source.

### Is the software used to preprocess / clean / label the data available?
Yes, in the repository: `src/generators/`, `src/prepare_data.py`, `src/split_data.py`, `src/prepare_curation.py`, `src/compile_curation.py`.

---

## Uses

### Has the dataset been used for any tasks already?
At time of v1 release, the dataset has been used for the associated research paper and for Pombo Labs's on-device small-LM fine-tuning experiments. Downstream fine-tuning + evaluation results will be referenced from this dataset card as they are published.

### Is there a repository that links to any or all papers or systems that use the dataset?
Repository: https://github.com/Pombo-Labs/TRACE (v1 pinned to the initial release commit). Downstream artifacts — training logs, evaluation results, and any derived models — will be released separately and referenced from this dataset card as they become available.

### What other tasks could the dataset be used for?
- Evaluation baselines for future ABA-specific LLM work.
- Research on taxonomy-driven synthetic data generation (the pipeline is domain-agnostic; only the configs are ABA-specific).
- Research on provenance-traceable data and auditable clinical AI.

### Is there anything about the composition of the dataset or the way it was collected and preprocessed / cleaned / labeled that might impact future uses?
- **Pattern frequencies are uniform for learnability.** Real clinical caseloads are skewed toward mastery-progression; users who care about epidemiological plausibility should reweight.
- **The dataset is English-only and US-clinical-context-only.** Users in other jurisdictions or languages will need to adapt.
- **Target-behavior presence in logs is bounded** (0–3 per log by pattern); real logs may have more or fewer.
- **Crisis plans are deliberately vague on physical-intervention procedures** because those procedures are training- and jurisdiction-specific. Users building systems that need to recommend specific restraint procedures will need additional data curated to their jurisdiction.

### Are there tasks for which the dataset should not be used?
TRACE is a research artifact and is not a clinical tool. Any clinical use is at the user's own risk. See dataset card section 5.3 for the full framing. Summarized:

- Not for autonomous clinical decisions.
- Not for final BIP writing without BCBA review.
- Not to be combined with real client data during training or inference.
- Not for medical diagnosis, legal documentation, or insurance reimbursement.

---

## Distribution

### Will the dataset be distributed to third parties outside of the entity on behalf of which it was created?
Yes — intended for open release under a research license (CC BY-NC 4.0 recommended, pending finalization).

### How will the dataset be distributed?
Public GitHub repository and Hugging Face Hub.

### When will the dataset be distributed?
2026-04-25 for the v1 release.

### Will the dataset be distributed under a copyright or intellectual property license?
Data: CC BY-NC 4.0. Code: MIT. TRACE is a research artifact; it has not been clinically validated and is not a clinical tool. Any use in a clinical setting is at the sole responsibility of the user and their facility.

### Have any third parties imposed IP-based or other restrictions?
No third-party IP is embedded. Curriculum references are to published frameworks (VB-MAPP, AFLS); no proprietary items are reproduced. Citation-based references to the Cooper/Heron/Heward textbook and JABA papers are just that — citations, not text reproductions.

### Do any export controls or other regulatory restrictions apply?
No.

---

## Maintenance

### Who will be supporting / hosting / maintaining the dataset?
**Pombo Labs** (https://github.com/Pombo-Labs) is the release maintainer. Festus Kahunla is the primary author and active maintainer of the dataset.

### How can the owner / curator / manager of the dataset be contacted?
Via the GitHub repository issue tracker.

### Is there an erratum?
A CHANGELOG will be maintained in the repository for each dataset version.

### Will the dataset be updated?
Yes, as ongoing research warrants. Future versions will be released as new git tags (semantic versioning) with full CHANGELOG entries. No public roadmap is committed to at v1.

### If the dataset relates to people, are there applicable limits on retention?
Not applicable (no real people).

### Will older versions continue to be supported?
Yes. Each dataset version is pinned to a specific commit hash; old versions remain reproducible from the corresponding configs and generator code.

### If others want to extend / augment / build on / contribute to the dataset, is there a mechanism for them to do so?
Yes. The taxonomy YAMLs are the intended extension surface. Adding a new skill target, a new target behavior, a new mastery criterion, or a new teaching method follows a documented pattern (see `configs/` for structure). Pull requests to the repository are the intended contribution mechanism.
