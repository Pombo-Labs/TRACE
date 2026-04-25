# CHANGELOG

All notable changes to TRACE are recorded here, starting with v1.0.0.
Future releases will follow semantic versioning:

- **Patch** (v1.0.x) — typo fixes, metadata tweaks, no change to the JSONL splits.
- **Minor** (v1.x.0) — additions to the taxonomy or new teaching methods; existing examples preserved; new examples appended to splits.
- **Major** (v2.0.0) — schema changes or re-generations that invalidate prior splits; prior versions remain accessible via git tags.

---

## v1.0.0 — 2026-04-25

Initial public release. 2,999 examples split across train (2,549) / valid (149) / test (281) / sanity (20). Paired with the dataset card, datasheet (Gebru et al. 2021), and data statement (Bender & Friedman 2018).

### What's covered

- **Teaching programs** across three methods — DTT (800), NET (500), Task Analysis (500, including toleration programs).
- **Session interpretations** — 1,200 multi-session behavioral logs across 12 trajectory patterns with 13 target behaviors.
- **Provenance** — every example carries full `meta.provenance.taxonomy_cells` for auditable traceback.
- **Reproducibility** — the corpus regenerates byte-identically from `(configs, seed)` on any platform; every `example_id` is verifiable as `sha256(user_content + assistant_content)[:16]` directly from the published JSONL row.

### Known limitations

See the dataset card section 6 and the data statement section H for the full list. Most notable:

- English-only, US clinical register.
- Pattern frequencies are uniform for learnability rather than epidemiologically weighted.
- VB-MAPP + AFLS only.
- Single-reviewer clinical validation.
