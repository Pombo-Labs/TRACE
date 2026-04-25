# Session-Log Reading Guide

Reference for reading Task 2 (session-interpretation) examples. Keep this
open in a side pane while browsing `review.md`.

---

## Session header line

```
Session 3 — 2026-10-10 — 45 min — 1 observer
```

Or, for inter-observer agreement sessions:

```
Session 5 — 2026-10-14 — IOA SESSION — 2 observers
```

| Piece | Meaning |
|---|---|
| `Session N` | Nth observation session in this log |
| `2026-10-10` | Synthetic date (always in 2026 range) |
| `45 min` | Session duration |
| `1 observer` / `2 observers` | Single observer (primary) or IOA session |
| `IOA SESSION` | (If present) agreement check; behavior lines in this session show a trailing `IOA X% agreement` |

---

## Skill data line (acquisition programs)

```
ordering in a restaurant: 9/13 correct (67%); latency 3.1s; prompts 5
```

| Piece | Meaning |
|---|---|
| `9/13 correct` | Correct trials / total trials |
| `67%` | Accuracy |
| `latency 3.1s` | Mean response latency after SD presentation |
| `prompts 5` | Number of trials on which any prompt was delivered |

---

## Behavior data lines

Each target behavior gets its own measurement format matched to the
behavior's clinical shape. Generic `freq` lines apply to most behaviors;
behaviors with clinically distinctive shapes have behavior-specific
measurements.

### Generic frequency behaviors

```
Aggression: freq 3
Elopement: freq 2
SIB: freq 5
Property destruction: freq 1
Non-compliance: freq 4
Verbal aggression: freq 2
```

`freq N` = N occurrences this session.

### Tantrum (includes duration)

```
Tantrum: freq 2, duration 7m total
```

### Stereotypy and mouthing (include partial-interval recording)

```
Motor stereotypy: freq 8; PIR 18%
Vocal stereotypy: freq 5; PIR 12%
Mouthing: freq 6; PIR 15%
```

`PIR X%` = partial-interval recording: % of intervals in which the behavior
occurred at any point.

### Pica (attempts vs successful ingestion)

```
Pica: attempts 3 (2 unsuccessful — staff retrieved item before ingestion; 1 successful — item ingested)
```

Staff often intercept pica attempts; tracking attempts / successful
separately preserves the severity signal that a raw frequency loses.

### Fecal smearing / scatolia (attempts vs completed smearing)

```
Fecal smearing (scatolia): attempts 2 (1 intercepted — staff redirected before smearing; 1 completed — feces transferred to skin, clothing, or surface)
```

Same intercepted / completed split as pica — clinically critical because
staff responsiveness directly shapes outcome severity.

### Toileting (four-count voiding log)

```
Toileting accident (urine or bowel): urine: 3 in-toilet / 2 accidents; BM: 0 in-toilet / 1 accidents
```

Mirrors a standard clinical voiding log. The deceleration target is
**accidents** (urine + BM), but successful in-toilet voids are tracked
alongside for context:

- `urine: X in-toilet / Y accidents` — successful urinations vs. urine accidents
- `BM: P in-toilet / Q accidents` — successful bowel movements vs. BM accidents

### IOA annotation

On sessions marked `IOA SESSION`, each behavior line ends with `; IOA X% agreement`:

```
Aggression: freq 3; IOA 88% agreement
```

---

## ABC line

```
ABC (elopement): A = peer took toy; B = ran from room; C = staff retrieved learner
```

- `A` = Antecedent (what happened immediately before the behavior)
- `B` = Behavior (operational description)
- `C` = Consequence (what happened immediately after)

ABC evidence feeds the behavior-function hypothesis in the assistant's
response (escape / attention / tangible / automatic, per Iwata et al. 1994
and Hanley, Iwata, & McCord 2003).

---

## Function-hypothesis line (log header)

Near the top of a log you'll see one line per tracked behavior:

```
1. Fecal smearing (scatolia) — function hypothesized: automatic
2. Aggression — function hypothesized: escape
```

These are the sampled (gold) functions that the interpretation response
should corroborate with the evidence in the log.

---

## Program list

```
Programs tracked this session block:
1. ordering in a restaurant (AFLS Community) — task_analysis
2. mands for a break (VB-MAPP Mand L1) — net
3. tacts colors of objects (VB-MAPP Tact L2) — dtt
```

Each entry names the skill target, its curriculum location, and the
teaching method.

---

## Behavioral indicator block (across sessions)

```
BEHAVIORAL OBSERVATIONS (across sessions)
- Increased response latency (3–5× baseline)
- Pushing materials away from the work area
- Vocal refusal ("no", "I don't want to")
```

These are pattern-specific indicator clusters (frustration, engagement, or
disengagement) sampled from `the `behavioral_indicators` block in configs/session_interpretation/taxonomy.yaml`.
