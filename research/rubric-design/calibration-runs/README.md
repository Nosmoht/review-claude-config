---
last_refreshed: 2026-04-28
---

# Calibration Runs

Point-in-time calibration data snapshots for `scoring-rubric.md` boundary-validation. Each subdirectory or filename prefix `YYYY-MM-DD` is a snapshot, never edited after creation. Append-only — superseded runs stay for audit. This is distinct from `research/<domain>/<domain>.md` which is refresh-in-place per memory `feedback_domain_not_dated_filenames.md`.

## File shape per run

- `<date>-empirical-manifest.yaml` — per-artifact lookup of existing post-refresh report or "needs fresh run" sentinel
- `<date>-empirical-scores.yaml` — per-artifact per-dimension empirical grades (extracted or freshly generated)
- `<date>-ground-truth.yaml` — user-provided ground-truth grades (independent elicitation, no proposed letters shown)
- `<date>-divergence.md` — per-dim cell-disagreement rate, N_eff, directional bias, confusion matrices

## Provenance

Calibration runs reference the rubric at the run's `calibration_version` only. Cross-version comparisons are not supported by the divergence math; if rubric drifts between runs, prior calibrations are marked `[Superseded by <newer-version>]` in `rubric-calibration-evidence.md`.
