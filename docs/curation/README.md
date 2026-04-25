# Curation Workflow

The curation step turns the pipeline-held-out `curation_pool.jsonl` into the
two evaluation files shipped in `data/splits/`:

- **`test.jsonl`** — evaluation set. The paper's headline metrics come from this set.
- **`sanity.jsonl`** — 20-example smoke-test set for development.

In TRACE v1 the whole curation pool is promoted as the test corpus (no hand
curation). The **review + compile** scripts are still part of the pipeline
because (a) regenerating the test and sanity splits is deterministic from the
pool, and (b) anyone adapting TRACE to a new clinical domain can reuse the
same workflow with their own taxonomy.

---

## Two scripts

| Script | What it does |
|---|---|
| `src/prepare_curation.py` | Renders `curation_pool.jsonl` as a browseable Markdown document in `docs/curation/review.md` — one candidate per section, grouped by task × category, with gold labels and provenance visible. |
| `src/compile_curation.py` | Splits the curation pool into `data/splits/test.jsonl` (the remainder) and `data/splits/sanity.jsonl` (20 examples, largest-remainder stratified by category). Deterministic under `--seed`. |

---

## Commands

```bash
# Regenerate the browseable review document.
uv run python src/prepare_curation.py

# Compile the test + sanity splits from the pool.
uv run python src/compile_curation.py

# Override the sanity size (default 20) or seed (default 42).
uv run python src/compile_curation.py --sanity-n 20 --seed 42
```

After `compile_curation.py` runs you'll have:
- `data/splits/test.jsonl` — the evaluation set
- `data/splits/sanity.jsonl` — the smoke-test set

---

## Reading `review.md`

`review.md` renders each candidate with:
- A heading showing the task type, category, and `example_id`.
- Gold labels inline (method, domain, level, learner profile, mastery state;
  or pattern class, behavior functions, escalation, confidence, crisis-plan flag).
- A short provenance line (for session interpretation: number of sessions,
  number of behaviors, whether IOA is included, whether ABC is included).
- The full user message (the teaching-program prompt or the session log).
- The full assistant message (the structured response).

Use `LEGEND.md` as a side-pane reference for the session-log notation in
Task 2 examples.

---

## Flagging issues for re-generation

If you spot a clinical inaccuracy while browsing `review.md`:

1. Note the candidate's `example_id` (shown in its heading).
2. Look up the candidate's `meta.provenance.taxonomy_cells` in the JSONL to
   identify which taxonomy dimension produced the issue.
3. Edit the relevant YAML under `configs/` (or the renderer in `src/generators/`
   if it's a rendering-logic issue) — *never* hand-edit individual JSONL
   entries, because the fix should propagate to every example that sampled
   the same cells.
4. Regenerate the corpus with `src/generate.py --all`, re-split with
   `src/split_data.py`, and re-compile with `src/compile_curation.py`.

Every clinical-review flag during v1 development landed as a single
targeted taxonomy edit plus a full regeneration — never a hand-edit of
the JSONL. This is the invariant the pipeline relies on: fixes must
propagate through the taxonomy to be systematic across the corpus.

---

## Adapting the workflow to a new clinical domain

The scripts are domain-agnostic. To port to a different dataset:

- `prepare_curation.py` just reads `data/splits/curation_pool.jsonl` and
  renders it. Works on any JSONL with the same envelope shape.
- `compile_curation.py` stratifies on `category_of(example)` — a small
  function near the top of the script. Change its logic to use whichever
  field best represents your category (the `method` field for TRACE's
  teaching programs; the `pattern_class` field for session interpretation).
- Everything else — largest-remainder allocation, deterministic splitting,
  provenance preservation — carries over unchanged.
