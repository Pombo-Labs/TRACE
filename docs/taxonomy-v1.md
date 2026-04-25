# TRACE Dataset Taxonomy v1

**Purpose.** This document is the **controlled vocabulary** for the TRACE synthetic dataset. Every category our data-generation pipeline can draw from is defined here, with an operational definition and a canonical citation. If a category is not in this document, the generator will not produce it — and if it is here, its clinical validity is defensible against a peer-reviewed source.

**Who this serves.**
- The data-generation pipeline (`src/prepare_data.py`) consumes this taxonomy as its source of truth.
- The dataset paper's composition table is a direct rendering of this document.
- Reviewers verifying "no invented clinical categories" can trace each entry -> citation -> CHH chapter / JABA paper / curriculum manual.

**Status.** Version 1, 2026-04-22. Breaking changes require a bumped version and a changelog entry.

**Citation conventions.** Throughout this document:
- **CHH** = Cooper, Heron, & Heward (2020). *Applied Behavior Analysis* (3rd ed.). Pearson.
- **JABA** = *Journal of Applied Behavior Analysis*
- **BAP** = *Behavior Analysis in Practice*
- DOIs link to the authoritative source wherever possible.

---

## 0.A Program orientation — Acceleration vs Deceleration

Every ABA goal falls into one of two program orientations, a distinction that runs through virtually all clinical data systems:

| Orientation | Purpose | Covers |
|---|---|---|
| **Acceleration** | Behaviors / skills to **increase** | Skill-acquisition programs (VB-MAPP, AFLS targets); adaptive behaviors (toileting, communication including AAC); FCT-trained replacement behaviors; independent coping with denied access |
| **Deceleration** | Behaviors to **decrease** | Target problem behaviors (section 5): SIB, aggression, elopement, tantrum, stereotypy, pica, etc. |

**Citation.** Standard ABA terminology; see CHH Ch. 22 ("Differential Reinforcement" — acceleration via reinforcement of desired behavior) and Ch. 24 ("Extinction") together with Ch. 25 ("Antecedent Interventions") for deceleration.

**Dataset usage.**
- section 1 teaching methods DTT, NET, Task Analysis, PRT, Incidental Teaching apply to **acceleration** programs.
- section 1.4 FCT is the acceleration method paired with deceleration — it teaches a replacement behavior while reducing a target behavior.
- section 1.5 BST is meta-level (trains staff on any program).
- Task 2 session logs sample across both orientations per session — several acceleration targets and zero or more deceleration behaviors. Exact counts are pipeline hyperparameters.

---

## 0.B How taxonomy dimensions combine

Each **teaching program generation** example is produced by sampling one value from each of these dimensions:

| Dimension | # values | Section |
|---|---|---|
| Teaching method | 6 (optionally 8 if video modeling + script fading approved) | section 1 |
| Skill domain | 16 (VB-MAPP) + 6 (AFLS) = 22 | section 2 |
| Developmental level | 5 (3 VB-MAPP + 2 AFLS) | section 2 |
| Skill target | ~250 | section 2 |
| Mastery state | 7 | section 3 |
| Prompt hierarchy | 6 | section 8 |
| Reinforcement schedule | 7 | section 9 |
| Error correction | 5 | section 10 |
| Mastery criteria | 7 | section 11 |

Each **behavioral session interpretation** example is produced by sampling:

| Dimension | # values | Section |
|---|---|---|
| Session pattern | 12 | section 7 |
| Primary skills observed | 3–8 per session | section 2 |
| Target behaviors observed (if any) | 0–3 per session | section 5 |
| Measurement types used | 2–5 per session | section 6 |
| Behavior function hypothesis | 4 + "not applicable" | section 4 |
| Escalation level | 4 | section 12 |
| Confidence level | 3 | section 13 |
| BIP component structure | 4 | section 11 |

---

## 1. Teaching methods

The first task (Teaching Program Generation) produces content modality-aware. A "mand" goal is not automatically a DTT program — real clinical practice picks the method that fits the skill and learner. The model must reason about method selection.

### 1.1 Discrete Trial Training (DTT)
- **Operational definition.** A structured teaching format consisting of clearly defined trial units: *discriminative stimulus (SD) -> learner response -> consequence (reinforcement or correction) -> inter-trial interval (ITI)*. Trials are massed in a contrived setting (usually table-based), with explicit prompt hierarchy and error-correction procedure.
- **When to use.** Acquisition of discrete, decontextualized skills (receptive labels, tacts, matching, early imitation) especially early in instruction when stimulus control must be established.
- **Canonical citation.** Lovaas, O. I. (1987). *JCCP, 55*(1), 3–9. https://doi.org/10.1037/0022-006X.55.1.3 — seminal EIBI trial establishing DTT-based programming. Modern definition: Smith, T. (2001). *Focus on Autism, 16*(2), 86–92.
- **Dataset usage.** Default teaching method for early-learner (VB-MAPP Level 1–2) discrete skills. Output includes explicit SD, prompt hierarchy, stimulus array, error-correction, mastery criteria.

### 1.2 Natural Environment Teaching (NET)
- **Operational definition.** Teaching that occurs within the learner's natural context, capitalizing on child-initiated motivation and ongoing activities. The teaching opportunity is embedded in the environment, not contrived.
- **When to use.** Generalization phase, functional communication, requesting (mand) skills, when motivation is the limiting factor, or when the skill's natural occasion is ecologically predictable (e.g., requesting food during snack time).
- **Canonical citation.** Hart, B. & Risley, T. R. (1975). *JABA, 8*(4), 411–420. https://doi.org/10.1901/jaba.1975.8-411 (origin of incidental teaching). Autism extension: McGee, G. G., Krantz, P. J., & McClannahan, L. E. (1985). *JABA, 18*(1), 17–31.
- **Dataset usage.** Default teaching method for mand targets and generalization-phase goals. Output emphasizes environmental setup / MO arrangement over contrived SD.

### 1.3 Task Analysis / Chaining
- **Operational definition.** Decomposition of a complex behavior into sequential component steps, followed by teaching each step and chaining them together. Three chain types:
  - **Forward chaining** — teach step 1 to mastery, then 1->2, then 1->2->3, etc.
  - **Backward chaining** — complete all steps except the last; teach last; move backward.
  - **Total-task presentation** — prompt through entire chain every trial; fade prompts across all steps.
- **When to use.** Multi-step skills with a natural sequence: toileting, handwashing, dressing, cooking, social routines.
- **Canonical citation.** CHH Ch. 23 ("Chaining"). Empirical comparison: Slocum, S. K. & Tiger, J. H. (2011). *JABA, 44*(4), 793–805. https://doi.org/10.1901/jaba.2011.44-793
- **Dataset usage.** Default for self-care (AFLS Basic Living), domestic, community, and vocational domains. Output structure replaces "SD" with "task analysis steps" (numbered list) + chain type + prompt strategy per step.

### 1.4 Functional Communication Training (FCT)
- **Operational definition.** Procedure for teaching a communication response that serves the *same function* as a target problem behavior, paired with extinction of the problem behavior. Example: a child who tantrums to escape demands is taught to say/sign "break please," which is reinforced; the tantrum is placed on extinction.
- **When to use.** Any target behavior with a clear social function (escape, attention, tangible). First-line strategy before consequence-based interventions.
- **Canonical citation.** Carr, E. G. & Durand, V. M. (1985). *JABA, 18*(2), 111–126. https://doi.org/10.1901/jaba.1985.18-111 (seminal). Modern practical review: Tiger, J. H., Hanley, G. P., & Bruzek, J. (2008). *BAP, 1*(1), 16–23.
- **Dataset usage.** Default teaching method in behavior-intervention-adjacent recommendations (task 2 interpretation output when behavior data is present). Output ties communication response -> hypothesized function -> reinforcement schedule.

### 1.5 Behavior Skills Training (BST)
- **Operational definition.** Staff/caregiver training procedure with four components in sequence: **(1) Instruction**, **(2) Modeling**, **(3) Rehearsal**, **(4) Feedback**, iterated until the trainee meets mastery criteria on a performance checklist.
- **When to use.** Training RBTs on a new program, training caregivers on a home procedure, preparing staff for a BIP rollout.
- **Canonical citation.** Parsons, M. B., Rollyson, J. H., & Reid, D. H. (2012). *BAP, 5*(2), 2–11. https://doi.org/10.1007/BF03391819
- **Dataset usage.** Used in a minority of task 1 outputs when the target is a staff-facing training program (rather than a learner-facing teaching program). Output structure emphasizes trainer steps and fidelity checklist.

### 1.6 Pivotal Response Training (PRT)
- **Operational definition.** Naturalistic teaching targeting "pivotal" behaviors that produce widespread collateral gains: **motivation**, **self-initiation**, **responsivity to multiple cues**, **self-management**. Uses child choice, interspersal of mastered/acquisition targets, natural reinforcers, and reinforcement of attempts (not just correct responses).
- **When to use.** Language acquisition in autism, social initiation, generalization across contexts.
- **Canonical citation.** Koegel, R. L., O'Dell, M. C., & Koegel, L. K. (1987). *JADD, 17*(2), 187–200. https://doi.org/10.1007/BF01495055 (origin of NLP -> PRT). JABA-indexed: Laski, K. E., Charlop, M. H., & Schreibman, L. (1988). *JABA, 21*(4), 391–400.
- **Dataset usage.** Used for a minority of early-language targets in naturalistic conditions. Output emphasizes motivation arrangement, child-choice, attempt-reinforcement.

### Method-selection heuristics (encoded as prompt guidance, not hard rules)

| Skill context | Default method | Alternative |
|---|---|---|
| Early discrete skills (tacts, receptive labels, matching) | DTT | PRT (if motivation is limiting) |
| Mand / requesting | NET | FCT (if replacing problem behavior) |
| Multi-step routines (dressing, handwashing) | Task Analysis | — |
| Problem-behavior reduction | FCT | — |
| Generalization phase | NET | PRT |
| Staff-facing training | BST | — |
| Social-initiation skills | PRT | NET |

---

## 2. Skill curriculum (Acceleration targets)

All skill domains in this section are **acceleration** targets — goals we want the learner to perform MORE often / more independently. See section 0.A.

Two overlapping curricula are encoded: **VB-MAPP** (early learners, 0–48 months developmental age) and **AFLS** (adolescents / adults and functional living). Together they cover the full learner age span TRACE should handle.

### 2.1 VB-MAPP (Verbal Behavior Milestones Assessment and Placement Program)

**Primary citation.** Sundberg, M. L. (2008). *Verbal Behavior Milestones Assessment and Placement Program*. AVB Press. Validation study: Barnes, C. S., Mellor, J. R., & Rehfeldt, R. A. (2014). *Analysis of Verbal Behavior, 30*(1), 36–47. https://doi.org/10.1007/s40616-013-0004-5

**Developmental levels:**
- **Level 1** — 0–18 months typical developmental age
- **Level 2** — 18–30 months
- **Level 3** — 30–48 months

**16 skill domains**, each expanded to 5 representative targets per developmental level (Sundberg 2008):

**1. Mand** — requesting.
- L1: single-word mands for preferred items; mands for missing items needed to complete an activity; mands for actions; mands for help; mands using 2-word phrases.
- L2: mands for information using "what"; mands for information using "where"; mands using adjectives (big, little, more); mands for attention from peers; mands for others to stop an action.
- L3: mands for information using "why"; mands for information using "when"; mands using complete sentences with correct grammar; mands for future events or items not present; mands using polite social conventions.

**2. Tact** — labeling / naming.
- L1: common objects (ball, cup, shoe); familiar people by name; common actions (running, eating, sleeping); body parts (nose, eyes, mouth); common animals (dog, cat, bird).
- L2: colors of objects; shapes (circle, square, triangle); adjectives (big/little, hot/cold); prepositions (in, on, under); emotions in self and others.
- L3: community helpers and their roles; categories (fruits, vehicles, clothing); features of objects (color, shape, function); past-tense events; abstract concepts (same/different, first/last).

**3. Echoic** — vocal imitation.
- L1: single vowel sounds; single consonant-vowel combinations; 1–2 syllable words; animal sounds; familiar words on request.
- L2: 2-word phrases; 3-word phrases; blended consonants; novel words with correct articulation; short sentences.
- L3: multi-syllable words accurately; full sentences with correct prosody; unfamiliar words from context; phrases with correct intonation patterns; complex instructions verbatim.

**4. Listener Responding** — receptive language.
- L1: 1-step motor instructions (sit down, stand up); select correct item from an array of 2; point to named body parts; point to named common objects; follow instructions involving objects.
- L2: select correct item from an array of 4–6; follow 2-step instructions; select items by feature (find something red); select items by function (find something you eat with); select items by class (find an animal).
- L3: follow multi-step instructions with qualifiers; select items by multiple features simultaneously; follow conditional instructions (if X, then Y); respond to questions about stories read aloud; follow instructions involving temporal concepts (before, after).

**5. Visual Perceptual Skills & Matching-to-Sample (VP-MTS).**
- L1: match identical objects; match identical pictures; match colors (identical chips); match shapes (identical blocks); complete simple 3–4 piece puzzles.
- L2: match non-identical items by category; sort items into 2–3 categories; match quantities (1–5); match upper-case letters; complete 8–12 piece puzzles.
- L3: match associated items (sock-shoe, cup-plate); sort by multiple attributes simultaneously; match upper to lower case letters; sequence 3–4 step picture sequences; reproduce block designs from model.

**6. Motor Imitation.**
- L1: gross motor actions (clap hands, stomp feet); actions with objects (bang drum, push car); 2-step motor sequences; fine motor actions (pinch, point); facial movements (open mouth, stick out tongue).
- L2: 3-step motor sequences; novel motor actions on first attempt; actions in songs and finger plays; actions involving bilateral coordination; motor actions after a delay.
- L3: complex multi-step sequences; motor actions from video models; handwriting strokes and letter forms; craft and art activities; sports-related motor sequences.

**7. Independent Play.**
- L1: cause-and-effect toys independently; sensory toys for sustained periods; construction toys (blocks, Duplo); vehicles (pushing, rolling); electronic learning toys.
- L2: simple pretend play sequences; art materials (coloring, playdough); age-appropriate puzzles independently; books independently; simple board or card games.
- L3: elaborate pretend play with storylines; creative construction activities; rule-based games independently; independently select and transition between activities; hobby / special-interest activities productively.

**8. Social Behavior & Social Play.**
- L1: eye contact during interactions; responds to own name; social games (peek-a-boo, tickle); shows items to others spontaneously; tolerates proximity of peers during parallel play.
- L2: initiates social interactions with peers; takes turns during structured activities; shares materials when prompted; cooperative play with one peer; responds to peer initiations appropriately.
- L3: maintains reciprocal conversations with peers; demonstrates empathy and perspective-taking; negotiates and compromises during group activities; joins ongoing peer activities appropriately; maintains friendships over time.

**9. Intraverbal** — fill-ins, WH answers without visual prompt.
- L1: fills in words in songs and nursery rhymes; answers "what's your name"; fills in missing words in familiar phrases; answers simple what-questions about visible items; completes verbal routines (ready, set, ___).
- L2: answers WH-questions about familiar topics; describes function of common objects; names items in categories when given the category; answers social questions (How are you?); describes recent events in sequence.
- L3: answers why- and how-questions; provides definitions of words; answers hypothetical questions; engages in multi-turn conversations on a topic; makes inferences from given information.

**10. LRFFC** — Listener Responding by Feature, Function, Class.
- L1: select items by function (What do you drink from?); select items by feature (What is round?); select items by class (Find the animal); select by single function from array of 3; select by single visible feature from array of 3.
- L2: select items by function from array of 5–8; select items by feature from array of 5–8; select items by class from array of 5–8; select items by multiple features (round and red); select items by function when item not visible.
- L3: select items given 2+ features/functions simultaneously; select items by class with exclusion (animal but not a pet); select items by abstract features (something needed when cold); select items by comparison (which is heavier); select items by negative features (not round, not food).

**11. Reading.**
- L1: match letters to identical letters; identify own name in print; identify 5–10 upper-case letters; match words to identical words; track print left to right.
- L2: identify all upper-case letters; identify all lower-case letters; read 10–20 sight words; sound out CVC words (cat, dog, run); read simple 2–3 word phrases.
- L3: read sentences with comprehension; read short passages and answer questions; phonetic decoding for novel words; read and follow written instructions; read grade-level text with fluency.

**12. Writing.**
- L1: trace horizontal and vertical lines; trace basic shapes (circle, cross); copy basic shapes from model; trace letters of own name; write own name from model.
- L2: write own name independently; copy all upper-case letters from model; write upper-case letters from dictation; copy simple words from model; write numbers 1–10.
- L3: write words from dictation; write simple sentences with spacing; write answers to questions; write short compositions (3–5 sentences); use basic punctuation and capitalization.

**13. Math.**
- L1: rote count to 10; count objects 1–5 with 1:1 correspondence; identify numerals 1–5; match quantities to numerals 1–5; identify basic shapes in math context.
- L2: count objects 1–20 with 1:1 correspondence; identify numerals 1–20; compare quantities (more/less/same); solve single-digit addition with manipulatives; identify coins by name.
- L3: add single-digit numbers without manipulatives; subtract single-digit numbers; identify place value (ones, tens); tell time to the hour and half-hour; solve simple word problems.

**14. Group & Classroom Skills.**
- L1: sits in designated area for 2–3 minutes; attends to teacher during group instruction; follows group instructions (everyone stand up); transitions between activities with prompts; waits in line briefly.
- L2: sits in group for 10–15 minutes; raises hand to request or respond; follows classroom routines independently; works independently at desk for 5–10 minutes; transitions between activities independently.
- L3: participates in group discussions; follows multi-step classroom instructions; works independently for 15+ minutes; self-monitors behavior using checklist; completes and turns in assignments independently.

**15. Linguistic Structure** — grammar.
- L1: single words to communicate; combines 2 words (agent + action or action + object); basic noun-verb combinations; simple negation (no, not); basic pronouns (I, me, my).
- L2: 3–4 word sentences; regular plurals (-s); present progressive (-ing); prepositions in sentences; regular past tense (-ed).
- L3: complex sentences with conjunctions; irregular past tense correctly; pronouns with correct referents; questions with correct word order; passive voice and embedded clauses.

**16. Spontaneous Vocal Behavior.**
- L1: spontaneous vocalizations during preferred activities; spontaneous naming of items; spontaneous requests without prompts; spontaneous greetings to familiar people; spontaneous comments on events.
- L2: spontaneous descriptions of ongoing activities; spontaneous questions about the environment; spontaneous reporting of past events; spontaneous use of social phrases; spontaneous initiation of conversation with peers.
- L3: spontaneous storytelling / narratives; spontaneous relevant comments in conversations; spontaneous adjustment of language to different listeners; spontaneous use of humor appropriately; spontaneous provision of explanations and reasons.

### 2.2 AFLS (Assessment of Functional Living Skills)

**Primary citation.** Partington, J. W., & Mueller, M. M. (2012). *Assessment of Functional Living Skills*. Behavior Analysts, Inc. / Stimulus Publications.

**Developmental scope.** Late-childhood through adult; skills are functional rather than milestone-bound.

**6 skill modules** (we encode a representative subset of each):

1. **Basic Living Skills** — toileting, eating, dressing, hygiene, bathing (chaining-intensive).
2. **Home Skills** — meal preparation, cleaning, laundry, bed-making.
3. **Community Participation Skills** — safety signs, money handling, transportation, shopping, restaurants.
4. **School Skills** — classroom routines, assignments, social-academic interaction.
5. **Vocational Skills** — task completion, workplace etiquette, punctuality.
6. **Independent Living Skills** — budgeting, appointments, medication, self-advocacy.

**Dataset usage.** AFLS targets appear in task 1 examples for older learners (labeled "Adolescent" or "Adult" learner profile) and in task 2 session logs for those learner profiles. Teaching method defaults to **Task Analysis / Chaining**.

### 2.3 Learner-profile age bands

| Profile label | Age band | Curricula |
|---|---|---|
| Early Learner | developmental age 0–48 mo | VB-MAPP |
| School-Age Learner | 6–12 yr chronological, varying developmental | VB-MAPP L2–3 + AFLS School |
| Adolescent Learner | 13–17 yr chronological, moderate-severe support needs | AFLS + VB-MAPP L3 for residual gaps |
| Adult Learner | 18+ yr in residential / day program | AFLS + Community + Vocational |

**Dataset usage.** Learner-profile label is a sampling dimension.

**On distribution.** No research source prescribes an ABA-population age-band distribution. The pipeline config sets a balanced default across the four profiles (rather than skewing toward any band) so the model trains on the full lifespan. Real-world caseload distributions vary by facility type (early-intervention centers skew Early; residential programs skew Adult). The exact ratio is a *pipeline hyperparameter*, not a clinical truth.

### 2.4 Gaps explicitly not covered in v1

- **Essential for Living** (McGreevy, Fry, & Cornwall 2014) — skills for adults with severe support needs. Partially covered by AFLS; full EFL integration is not included in v1.
- **ABLLS-R** (Partington 2010) — heavily overlaps VB-MAPP for early learners; not separately encoded.
- **PEAK** (Dixon 2014+) — relational frame / advanced cognition; out of scope for baseline dataset.

---

## 3. Mastery states

Seven-state taxonomy describing where a skill is in its learning trajectory. Values are slot values in task 1 user prompts and targets in task 2 interpretation.

| State | Operational criterion | Clinical meaning |
|---|---|---|
| **Emerging** | < 30% accuracy across recent sessions | Skill not yet acquired; high prompt levels needed |
| **Developing** | 30–50% accuracy, inconsistent | Responding established; stimulus control unstable |
| **Approaching mastery** | 50–70% accuracy, prompt fading in progress | Moving toward independence |
| **Near mastery** | 70–85% accuracy, occasional errors | Stimulus control solid, complex stimuli still variable |
| **Mastered (current level)** | ≥ 85% accuracy across 3 consecutive sessions | Meets mastery criterion for current step |
| **Generalization phase** | Mastered in training but not in novel settings / with novel materials / across therapists | Ready for NET-style generalization probes |
| **Maintenance** | Previously mastered; periodic probes to check retention | Maintenance schedule (weekly->monthly) |

**Citation.** Mastery-criterion conventions follow CHH Ch. 26 ("Generalization and Maintenance of Behavior Change") and the programmatic mastery-criteria convention in CHH Ch. 28.

**Dataset usage.** Mastery state is a primary slot in every task 1 prompt. In task 2, the narrative "a previously mastered skill has regressed" vs "a developing skill has plateaued" is the basis for pattern detection (section 7).

---

## 4. Behavior functions

The **four-function taxonomy** of problem behavior is the spine of all behavior reasoning in ABA. Iwata's original functional analysis identified three (attention, escape, sensory); Hanley, Iwata & McCord formalized the fourth (tangible) as standard.

| Function | Reinforcer | Example context | Hypothesis test |
|---|---|---|---|
| **Escape** (negative reinforcement) | Termination / avoidance of an aversive stimulus (demand, task, interaction) | Child hits when presented with math worksheet -> demand is removed | Elevated rate in demand condition vs control |
| **Attention** (positive reinforcement, social) | Attention from others (adult or peer) | Child yells when parent on phone -> parent attends | Elevated rate in attention condition vs control |
| **Tangible** (positive reinforcement, material) | Access to an item or activity | Child tantrums when iPad is taken away -> iPad is returned | Elevated rate when preferred item is restricted |
| **Automatic** (non-social / sensory) | Self-produced reinforcement (proprioceptive, auditory, visual, gustatory) | Repetitive hand-flapping persists during alone condition | Elevated rate in alone condition; persists across conditions |

**Canonical citations.**
- Iwata, B. A., Dorsey, M. F., Slifer, K. J., Bauman, K. E., & Richman, G. S. (1982/1994). *JABA, 27*(2), 197–209. https://doi.org/10.1901/jaba.1994.27-197 — THE foundational functional-analysis paper.
- Hanley, G. P., Iwata, B. A., & McCord, B. E. (2003). *JABA, 36*(2), 147–185. https://doi.org/10.1901/jaba.2003.36-147 — definitive review; formalizes four-function taxonomy including tangible.
- Pre-FA conceptual roots: Carr, E. G. (1977). *Psychological Bulletin, 84*(4), 800–816.
- CHH Ch. 27 ("Functional Behavior Assessment").

**Clinical principle.** Same topography can serve different functions across individuals. A "tantrum" in one client may be escape-maintained; in another, attention-maintained. **Interventions must match function**, not topography.

**Dataset usage.**
- Task 2 interpretation output includes **Function Hypothesis** field when behavior data is present — one of the four functions or "Not Applicable" (skill-only sessions).
- When present, the hypothesis cites the evidence in the session log (e.g., "elevated rate during demand presentation -> escape-maintained").

---

## 5. Target behaviors — Deceleration targets (with operational definitions)

All behaviors in this section are **deceleration** targets — behaviors we want to reduce. See section 0.A.

Eighteen challenging behaviors with JABA-grounded operational definitions suitable for staff scoring. Behaviors without a canonical operational definition in the literature (e.g., disrobing, grabbing/snatching) are deliberately excluded from v1 rather than invented.

| # | Behavior | Operational definition | Citation |
|---|---|---|---|
| 1 | **Self-injurious behavior (SIB)** | Any response that produces tissue damage or has the potential to produce it, including head-hitting, self-biting, face-slapping, head-banging against objects, skin-picking, self-pinching, hair-pulling directed at self. | Iwata et al. 1982/1994 |
| 2 | **Head-directed SIB** (subtype) | Contact between the individual's hand and head, OR between the head and a stationary object, with audible impact. | Iwata et al. 1982/1994 |
| 3 | **Aggression** | Attempted or completed forceful contact directed toward another person: hitting, kicking, biting, hair-pulling, scratching, pinching, or throwing objects AT another person. | Marcus, B. A. et al. (2001). *Behavior Modification, 25*(2), 189–213. https://doi.org/10.1177/0145445501252002 |
| 4 | **Property destruction** | Hitting or kicking furniture/walls; throwing objects not intended to be thrown; tearing clothing, books, or materials; swiping items off surfaces; overturning furniture. | Piazza, C. C., Bowman, L. G., Contrucci, S. A., et al. (1999). *JABA, 32*(4), 437–449. https://doi.org/10.1901/jaba.1999.32-437 |
| 5 | **Elopement** | Full body (or pre-specified anatomical threshold) crossing a designated boundary (e.g., classroom door, yard fence) without adult approval. | Kodak, T., Grow, L., & Northup, J. (2004). *JABA, 37*(2), 229–232. https://doi.org/10.1901/jaba.2004.37-229; Lang, R. et al. (2010). *JABA, 43*(1), 113–118. |
| 6 | **Pica** | Placement of any inedible (non-food) item past the plane of the lips, including mouthing and ingestion of objects (paper, dirt, cigarette butts, fabric, small toys, hair). | Piazza, C. C., Fisher, W. W., Hanley, G. P., et al. (1998). *JABA, 31*(2), 165–189. https://doi.org/10.1901/jaba.1998.31-165 |
| 7 | **Motor stereotypy** | Repetitive, non-functional motor movements (hand-flapping, body-rocking, finger-flicking, spinning) occurring independent of social context and serving no apparent instrumental purpose. | Rapp, J. T. & Vollmer, T. R. (2005). *RIDD, 26*(6), 527–547. https://doi.org/10.1016/j.ridd.2004.11.005 |
| 8 | **Vocal stereotypy** | Non-contextual, non-communicative vocalization: repetitive sounds, words, phrases, humming, or echolalia outside appropriate conversational context. | Ahearn, W. H., Clark, K. M., MacDonald, R. P. F., & Chung, B. I. (2007). *JABA, 40*(2), 263–275. https://doi.org/10.1901/jaba.2007.30-06 |
| 9 | **Tantrum** | Co-occurring cluster of two or more of: crying/screaming, dropping to floor, kicking, hitting, throwing objects, lasting ≥ 3 s. Scored from onset of first component topography to 5 s without any component behavior. | Kurtz, P. F. et al. (2003). *JABA, 36*(2), 205–219. https://doi.org/10.1901/jaba.2003.36-205; topography adapted from Carr & Durand 1985. |
| 10 | **Non-compliance** | Failure to initiate a requested response within 5 s of an instructional prompt (vocal, model, or physical), OR active refusal (verbal "no," walking away). | Wilder, D. A. et al. (2012). *JABA, 45*(1), 121–126. https://doi.org/10.1901/jaba.2012.45-121 |
| 11 | **Mouthing (non-pica)** | Placement of the hand, fingers, saliva, or non-food object into the mouth past the lip plane, excluding eating/drinking during scheduled meals. | Piazza, C. C., Hanley, G. P., & Fisher, W. W. (1996). *JABA, 29*(4), 437–449. https://doi.org/10.1901/jaba.1996.29-437 |
| 12 | **Throwing** | Propelling an object through the air with force (excluding task-relevant throwing such as during a game). | Property destruction literature, specifically Piazza et al. 1999 — throwing is often coded as a subtype. |
| 13 | **Food refusal / selectivity** | Rejection of presented food by turning the head, closing the mouth, batting the utensil away, or expelling food once placed in the mouth. | Piazza, C. C. et al. (2003). *JABA, 36*(2), 187–204 — feeding-disorder literature. |
| 14 | **Rumination / regurgitation** | Voluntary regurgitation of previously ingested food into the mouth, followed by re-chewing, re-swallowing, or expulsion. Scored per regurgitation episode. | Lyons, E. A., Rue, H. C., Luiselli, J. K., & DiGennaro, F. D. (2007). *JABA, 40*(4), 743–747. https://doi.org/10.1901/jaba.2007.743-747. See also Kahng et al. 2003. |
| 15 | **Sleep resistance / disruption** | Non-compliance with bedtime routine (refusing to go to bed, leaving bed, repeated requests) OR night waking ≥ 5 min at a time. Scored as instances or total disrupted minutes per night. | Friman, P. C., Hoff, K. E., Schnoes, C., Freeman, K. A., Woods, D. W., & Blum, N. (1999). *JABA, 32*(4), 505–508. https://doi.org/10.1901/jaba.1999.32-505 |
| 16 | **Verbal aggression / threats** | Yelling, cursing, name-calling, or making verbal threats directed toward another person (e.g., "I'll hit you," "I hate you"). | Kelley, M. E., Lerman, D. C., & Van Camp, C. M. (2002). *JABA, 35*(1), 59–63. See also Hagopian & Boelter 2005. |
| 17 | **Food stealing** | Taking food items not offered to the individual — from another person's plate, a storage area, or during restricted-access periods — and/or placing such items in the mouth outside designated meal/snack times. | Maglieri, K. A., DeLeon, I. G., Rodriguez-Catter, V., & Sevin, B. M. (2000). Adjunctive delivery of noncontingent reinforcement to treat food stealing during sessions of DRO. *JABA, 33*(4), 615–618. https://doi.org/10.1901/jaba.2000.33-615 |
| 18 | **Inappropriate sexual behavior (ISB)** | Engagement in sexual self-stimulation (genital contact, rhythmic self-stimulatory movements) in public or semi-public contexts where such behavior is socially or institutionally inappropriate. Scored per episode with onset/offset criteria specified in the program. | Davis, T. N., Machalicek, W., Scalzo, R., Kobylecky, A., Campbell, V., Pinkelman, S., Chan, J., & Sigafoos, J. (2016). A review and treatment selection model for individuals with developmental disabilities who engage in inappropriate sexual behavior. *BAP, 9*(4), 389–402. https://doi.org/10.1007/s40617-016-0149-5. See also Fyffe, C. E., Kahng, S., Fittro, E., & Russell, D. (2004). *JABA, 37*(3), 401–404. |

**Dataset usage.**
- Task 2 session logs include 0–3 target behaviors per log. Sampling weight biased toward the common behaviors (tantrum, non-compliance, aggression, stereotypy, elopement).
- Each target behavior in a log has an associated function hypothesis (section 4) that drives the interpretation output.

---

## 6. Measurement types

Real session logs mix measurement types; task 2 inputs must reflect this heterogeneity.

| Type | Operational definition | Use case | Citation |
|---|---|---|---|
| **Frequency** (event recording) | Raw count of occurrences of a discrete, quickly-completing behavior during a session. "12 requests this session." | Discrete, countable behaviors with clear onset/offset. | CHH Ch. 4 |
| **Rate** | Frequency normalized to time: count ÷ session duration. "0.4 requests per minute." | Compare sessions of different durations. | CHH Ch. 4 |
| **Duration** | Total elapsed time a behavior lasts (sum across instances). "Tantrum total duration: 8 min." | Behaviors with meaningful length (tantrums, on-task engagement, stereotypy). | CHH Ch. 4 |
| **Latency** | Time from SD to initiation of response. "Mean latency: 3.2 s." | Responsivity / prompt dependency. | CHH Ch. 4 |
| **Partial-interval recording (PIR)** | Divide session into intervals (e.g., 10 s); mark each interval if behavior occurred *at any point*. Overestimates prevalence. | Hard-to-count behaviors (stereotypy). | Powell, Martindale & Kulp 1975; Harrop & Daniels 1986 |
| **Whole-interval recording** | Mark interval only if behavior occurred for the *entire* interval. Underestimates. | Behaviors to increase (on-task engagement). | Cooper et al. Ch. 4 |
| **Momentary time sampling (MTS)** | Check once at the end of each interval whether behavior is occurring. Efficient for groups. Approximates duration. | Multi-client settings; duration estimation. | Powell et al. 1975 |

**Inter-Observer Agreement (IOA).** Two observers independently record the same session; agreement expressed as percent or κ. **Minimum acceptable: ≥ 80%** across 33% of sessions for scientific validity.
- Citation: CHH Ch. 5 ("Improving and Assessing the Quality of Behavioral Measurement"); Kazdin, A. E. (1977). *JABA, 10*(1), 141–150. https://doi.org/10.1901/jaba.1977.10-141

**Dataset usage.**
- Every task 2 session log includes at least one **Primary Measurement Type** per target skill or behavior.
- ~25% of logs include an **IOA subset** (percentage agreement reported) to test the model's ability to interpret reliability.
- Accuracy % (trial-based correct/total) is the dominant measurement for skill-acquisition programs — this stays.

### 6.1 Antecedent-Behavior-Consequence (ABC) data

ABC recording supplements behavior frequency counts with the immediate environmental context around each occurrence. A subset of task 2 session logs (~30%) include ABC entries for target behaviors, enabling function-hypothesis reasoning beyond what frequency data alone supports.

- **Antecedent** — what was happening immediately before (≤ 10 s) the behavior occurred.
- **Behavior** — the target behavior as operationally defined (section 5).
- **Consequence** — what happened immediately after (≤ 10 s), including any staff response.

**Citation.** Bijou, S. W., Peterson, R. F., & Ault, M. H. (1968). A method to integrate descriptive and experimental field studies at the level of data and empirical concepts. *JABA, 1*(2), 175–191. https://doi.org/10.1901/jaba.1968.1-175. See also CHH Ch. 27 ("Functional Behavior Assessment").

The remaining ~70% of logs include frequency-only behavior data, giving the model exposure to both enriched and minimal log formats.

### 6.2 Program execution context

Each acceleration and deceleration program is associated with one or more settings in which it runs:

| Context tag | Setting |
|---|---|
| D | Day (school or day habilitation) |
| R | Residential (home, group home, dormitory) |
| Both | Runs across settings |

**Dataset usage.** Each synthetic task 1 program and task 2 session log carries a context tag. Default sampling ~40% D, ~30% R, ~30% Both. No research source prescribes exact proportions; this is a pipeline hyperparameter.

---

## 7. Session patterns (for Task 2)

Behavioral session interpretation requires recognizing **patterns across sessions**. Fourteen clinically meaningful patterns are encoded.

| # | Pattern | Signature | Concern level | Extends prepare_data.py? |
|---|---|---|---|---|
| 1 | **Mastery progression** | Ascending accuracy, mastery criterion within reach | None | Yes |
| 2 | **Regression** | Previously mastered skill shows declining accuracy | High | Yes |
| 3 | **Plateau** | Flat accuracy below mastery for ≥ 5 sessions | Moderate | Yes |
| 4 | **Frustration pattern** | Declining accuracy + escape-function behavioral indicators | High | Yes |
| 5 | **Variable performance** | High session-to-session SD, no clear trend | Moderate | Yes |
| 6 | **Prompt dependency** | High prompted accuracy, low independent accuracy, prolonged | Moderate | Yes |
| 7 | **Rapid acquisition** | Accelerated mastery beyond expected timeline | None (good) | Yes |
| 8 | **Generalization failure** | Mastered in training, low accuracy in novel settings/stimuli | Moderate | Yes |
| 9 | **Extinction burst** | Temporary spike in problem behavior during reduction procedure | Expected | Yes |
| 10 | **Skill loss after break** | Performance drop after absence, recovering | Moderate | Yes |
| 11 | **Motivating operation shift** | Responding drops when MO changes (e.g., satiation of reinforcer); recovers when MO restored | Moderate | No — new in v1, grounded in Michael 1993 / CHH Ch.16 |
| 12 | **Setting event trigger** | Accuracy or behavior changes correlated with an external setting event (illness, sleep disruption, schedule change) | Moderate | No — new in v1, grounded in Smith & Iwata 1997 / Bijou & Baer 1961 |

**Citations.**
- Patterns 1–10 draw from standard single-case-design interpretation literature (CHH Ch. 6, 7). Specific ones:
  - Regression / skill loss: CHH Ch. 26 (maintenance).
  - Extinction burst: CHH Ch. 24.
  - Prompt dependency: Time-delay literature (Touchette, Touchette 1971; CHH Ch. 21 prompting).
  - Generalization failure: Stokes & Baer 1977 "An implicit technology of generalization" *JABA, 10*(2); CHH Ch. 26.
- Patterns 11–12 are TRACE additions with specific literature grounding:
  - MO shift: CHH Ch. 16 ("Motivating Operations"); Michael, J. (1993). *Journal of the Experimental Analysis of Behavior, 59*(3), 533–552.
  - Setting event: Bijou & Baer 1961; Smith, R. G. & Iwata, B. A. (1997). *JABA, 30*(2), 343–375.

**Honest framing.** This 12-pattern taxonomy is our *operationalization* for the dataset — no single paper proposes these as a canonical pattern set. Each underlying concept is well-grounded (citations above); the clustering into 12 discrete labels is a design choice that makes session interpretation a tractable classification task.

**Dataset usage.** Each task 2 example is generated from one of these 12 patterns as its hidden label. The interpretation output includes the pattern classification as a structured field (section 12).

---

## 8. Prompt hierarchies

Six prompt-fading strategies used in DTT and related methods.

| # | Strategy | Sequence | When to use |
|---|---|---|---|
| 1 | **Most-to-Least (errorless)** | Full physical -> partial physical -> gestural -> positional -> independent | Acquisition, early learner, safety-critical skills |
| 2 | **Least-to-Most** | Independent -> gestural -> positional -> partial physical -> full physical | Learner already has partial repertoire; promotes independence |
| 3 | **Graduated Guidance** | Hand-over-hand with fading pressure -> shadow -> independent | Motor skills, self-care chaining |
| 4 | **Time Delay** (progressive) | 0 s delay -> 2 s -> 4 s -> 6 s -> learner responds independently | Prompt-dependency prevention; ideal for fading |
| 5 | **Stimulus Fading** | Exaggerated stimulus -> gradually reduce salience -> natural stimulus | Receptive discrimination, early reading |
| 6 | **Stimulus Shaping** | Modified stimulus -> gradually reshape to target -> natural stimulus | Complex visual discriminations |

**Citations.** CHH Ch. 21 ("Imitation, Shaping, and Prompting") and Ch. 17 ("Stimulus Control"). Time delay: Touchette & Howard 1984 *JABA*.

**Dataset usage.** One of the six sampled per task 1 DTT / Task-Analysis example. Output describes the sequence and current prompt level based on mastery state (section 3).

---

## 9. Reinforcement schedules

Seven reinforcement arrangements — intentional kept to the commonly-used set for cleanliness.

| # | Schedule | Description | Typical use |
|---|---|---|---|
| 1 | **CRF** (continuous reinforcement) | Every correct response reinforced | Acquisition phase |
| 2 | **FR-2** (fixed ratio 2) | Every 2nd correct response reinforced | Thinning as accuracy stabilizes |
| 3 | **VR-3** (variable ratio 3) | Average of every 3rd correct response | Maintenance, resistance to extinction |
| 4 | **DRO** (differential reinforcement of other behavior) | Reinforce any behavior *other than* the problem behavior during an interval | Behavior reduction |
| 5 | **DRA** (differential reinforcement of alternative) | Reinforce a specific alternative behavior, extinguish problem behavior | FCT pairing |
| 6 | **DRI** (differential reinforcement of incompatible) | Reinforce a behavior physically incompatible with the problem behavior | Stereotypy reduction |
| 7 | **Token economy** | Tokens delivered per correct response, exchanged later for a back-up reinforcer | Group / classroom settings |

**Citations.** CHH Ch. 13 ("Schedules of Reinforcement"), Ch. 22 ("Differential Reinforcement").

**Dataset usage.** One schedule sampled per task 1 example. Task 2 recommendations may suggest schedule changes (e.g., "thin from CRF to FR-2 as accuracy exceeds 85%").

---

## 10. Error correction procedures

Five error-correction procedures used in DTT and related formats.

| # | Procedure | Steps |
|---|---|---|
| 1 | **Transfer trial** | Represent SD -> prompt at effective level -> reinforce prompted response -> distractor trial -> re-present SD independently |
| 2 | **4-step** | Model -> lead (do together) -> test (independent) -> distractor -> retest |
| 3 | **Backstep** | Return to previous prompt level that produced success -> successful response -> re-attempt at target prompt level |
| 4 | **Simple correction** | "No, watch me" -> model -> re-present SD -> differential reinforcement |
| 5 | **Error-free** | Prevent errors by using high prompts from start; fade gradually (paired with most-to-least) |

**Citations.** CHH Ch. 21. Specific: Heward, W. L. (1994) error-correction comparison.

**Dataset usage.** One procedure sampled per task 1 DTT example.

---

## 11. Mastery criteria options + BIP components

### 11.1 Mastery criteria

Seven mastery criteria conventions common in ABA practice.

1. 80% accuracy across 2 consecutive sessions with ≥ 10 trials each.
2. 90% accuracy across 3 consecutive sessions.
3. 80% accuracy with 2 different therapists and 2 different settings (generalization-inclusive).
4. 80% accuracy at independent prompt level across 3 sessions.
5. 90% first-trial-correct across 5 consecutive sessions.
6. Fluency criterion: correct responses within 3-second latency at 90% accuracy.
7. Demonstrated use in natural environment × 3 independent instances.

**Citation.** CHH Ch. 28 ("Developing Behavior-Change Programs").

### 11.2 BIP components (for task 2 recommendations)

When a target behavior is present in a session log, the task 2 recommendation field is structured along four BIP dimensions.

| Component | Purpose | Example content |
|---|---|---|
| **Antecedent strategies** | Prevent the behavior before it occurs by modifying the environment | Shorten tasks; offer choice; pre-teach coping; non-contingent attention; reduce demand difficulty; provide warnings before transitions |
| **Replacement behavior (teach)** | A skill that produces the same function more appropriately; pair with FCT | Teach "break please" for escape-function tantrums; teach "look at me" for attention-function disruption |
| **Consequence strategies** | Staff response after the behavior | Do not reinforce (extinction); redirection; blocking; DRA/DRI; differential reinforcement of replacement behavior |
| **Crisis plan** | Safety procedure if behavior escalates | Staff call-tree; environmental safety (clear hazards); agreed restraint/escape procedures per facility policy; post-incident debrief |

**Citations.**
- Antecedent strategies: CHH Ch. 25 ("Antecedent Interventions"); Smith, R. G. & Iwata, B. A. (1997). *JABA, 30*(2), 343–375.
- Replacement behaviors: Carr & Durand 1985 (FCT).
- Consequence strategies: CHH Ch. 22 (differential reinforcement), Ch. 24 (extinction).
- Crisis plan: no canonical JABA paper — cite BACB 5th ed. Task List G-15 / H-8 and the BACB *Ethics Code for Behavior Analysts* (2020). Flagged in section 15.

---

## 12. Escalation level (structured output for Task 2)

Every task 2 interpretation emits an **escalation level** as a classification label. This is the safety-critical head.

| Level | Meaning | Trigger examples |
|---|---|---|
| **1. Continue monitoring** | Current programming is effective; no changes | Mastery progression; rapid acquisition |
| **2. Adjust next session** | Implement a specific programming change at next session | Plateau -> change prompt strategy; prompt dependency -> introduce time delay |
| **3. Supervisor review** | Elevate to supervising BCBA within 24–48 hr | Regression; new emergence of problem behavior; unclear function |
| **4. Safety — immediate** | Stop program; contact supervisor and/or family immediately; consider crisis-plan activation | SIB escalation; aggression resulting in injury; high-rate elopement; extinction burst exceeding safety threshold |

**Clinical principle.** Escalation level is **ordinal** — mistaking level 4 for level 1 is catastrophically worse than mistaking level 2 for level 1. Evaluation uses quadratic-weighted κ (section 13) to penalize distant mistakes accordingly.

**Dataset usage.** Every task 2 example has a gold-standard escalation level derived deterministically from the pattern (section 7), the target behaviors (section 5), and severity markers.

**On distribution.** No research source prescribes a specific class balance for escalation labels. The pipeline config (not this taxonomy) sets a default that keeps the minority class (level 4 "safety-immediate") present for training representation while reflecting that most sessions do not require immediate safety action. The exact ratio is a *pipeline hyperparameter*, not a clinical truth; see `configs/data-generation.yaml` once implemented.

**Framing as our contribution.** No canonical source specifies this 4-level escalation ordinal. It is TRACE's operationalization, designed to (a) make safety a first-class output and (b) support quadratic-weighted κ evaluation. We cite it as a project design choice, not a clinical taxonomy.

---

## 13. Confidence level (structured output for Task 2)

Three-level confidence expression acknowledging uncertainty.

| Level | Meaning | Example justifications |
|---|---|---|
| **High** | Pattern and recommendation well-supported by the data in this log | Multiple sessions of clear data; IOA present and ≥ 80%; single clear pattern |
| **Moderate** | Data supports the hypothesis but alternatives cannot be fully ruled out | No IOA; few sessions; multiple partially-matching patterns |
| **Low** | Insufficient data to rule in a specific pattern; recommend data collection before programming changes | < 3 sessions; no IOA; high variability; contradictory signals |

**Citations.** Calibrated uncertainty expression follows general clinical-LM principles (Med-PaLM 2, Singhal et al. 2025). No single ABA-specific source; flagged as project innovation.

**Dataset usage.** Confidence is sampled based on objective data-quality features of the log (number of sessions, IOA presence, variance). Evaluation computes calibration metrics (ECE, Brier — section 13 of `literature-foundation.md`).

---

## 14. Coverage matrix (dimension interactions)

Not every combination is valid. The pipeline enforces these constraints:

| Teaching method | Compatible skill domains | Compatible learner profiles |
|---|---|---|
| DTT | All discrete VB-MAPP domains (Mand, Tact, Listener Responding, Echoic, Motor Imitation, VP/MTS, LRFFC, Intraverbal, Math, Reading early) | Early, School-Age |
| NET | Mand, Tact, Social Behavior, Spontaneous Vocal Behavior, Independent Play | All |
| Task Analysis | AFLS modules, Writing (multi-step), complex Math, domestic/vocational | School-Age, Adolescent, Adult |
| FCT | Triggered by target behavior in session log, not by skill domain | All |
| BST | N/A — staff-facing | Training-program variant |
| PRT | Mand, Tact, Social Behavior, Spontaneous Vocal Behavior | Early, School-Age |

| Target behavior | Plausible functions | Typical severity / escalation |
|---|---|---|
| SIB | All four; most often automatic or escape | L3 – L4 |
| Aggression | Most often escape or tangible | L3 – L4 |
| Elopement | Escape, tangible, or automatic | L2 – L4 (depends on environmental risk) |
| Tantrum | Most often escape or tangible | L2 – L3 |
| Non-compliance | Primarily escape | L1 – L2 |
| Stereotypy | Primarily automatic | L1 – L2 (unless interfering with learning) |
| Pica | Automatic (oral) | L3 – L4 (safety) |

**Dataset usage.** Generators sample valid combinations only. Invalid combinations (e.g., DTT for a multi-step handwashing skill) are not produced, or are produced deliberately as negative-training examples (rare; labeled).

---

## 15. Gaps (explicitly acknowledged)

The following areas in the taxonomy have weaker citation grounding. We cite what exists, note the limitation in the dataset card, and flag them as future-work extensions.

1. **Crisis plan components** — no canonical JABA paper. Cited: BACB 5th ed. Task List G-15 / H-8 and the 2020 Ethics Code. Acceptable because BIP crisis planning is a BACB-regulated practice area.
2. **Patterns 11–12** (MO shift, setting event) — session-level operationalization is TRACE's contribution; underlying concepts grounded in Michael 1993, Smith & Iwata 1997, Bijou & Baer 1961.
3. **Disrobing, grabbing/snatching, cascading drift, comorbid skill-behavior** — considered for v1 but excluded because no canonical operational definition exists. We do not invent what the literature has not defined.
4. **Essential for Living / PEAK / ABLLS-R** — not encoded in v1. VB-MAPP + AFLS provide sufficient coverage for baseline dataset.
5. **Severity index within target behaviors** — no encoded numeric severity scale. v1 treats severity as implicit in the behavior type + escalation level.
6. **Multi-function (mixed-function) behaviors** — v1 assigns a single function hypothesis; real clinical reality includes mixed functions. Flagged as a known limitation.
7. **Cultural / linguistic variation** — v1 is English-only, US/North-American ABA convention. Flagged in dataset card limitations.
8. **Escalation ordinal (4 levels) and confidence ordinal (3 levels)** — TRACE design choices, not citation-grounded taxonomies. Framed as project contributions; their clinical validity will be evaluated empirically (quadratic-weighted κ vs BCBA raters).
9. **Class distributions** (escalation levels, learner profiles, pattern frequencies) — no research source prescribes exact proportions. These are pipeline hyperparameters tuned for training balance, not clinical truths.

---

## 16. Changelog

- **v1.0 (2026-04-22)** — initial taxonomy, drawn from VB-MAPP (Sundberg 2008), AFLS (Partington & Mueller 2012), Cooper/Heron/Heward (2020), Iwata (1982/1994), Hanley/Iwata/McCord (2003), Carr & Durand (1985), and supporting JABA operational-definition literature.

---

## 17. How this taxonomy is consumed by the pipeline

- `src/prepare_data.py` imports taxonomy as Python constants generated from this document.
- Each training example is produced by (a) sampling a valid combination of taxonomy values, (b) running the relevant generation template, (c) applying quality + safety filters.
- A provenance record is written per example: taxonomy slot values, template ID, teacher model, seed, filter thresholds, timestamp.
- If this taxonomy changes, the pipeline version and dataset version both bump; old data is preserved as a previous version on HuggingFace.

See `schema-v1.md` (next) for the precise JSON structure of training examples.
