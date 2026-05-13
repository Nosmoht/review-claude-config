---
name: role-statement-form-spec
description: Anchor material for future LLM-Judge implementation of WHO-axis form-check. Salvaged from withdrawn PR #274 (closed-list binary PE-3 approach). Not loaded at runtime by review skills.
last_refreshed: 2026-05-14
consumed_by: future LLM-Judge skill (D1b infrastructure — issue #273)
---

# Role-Statement Form Specification

This document is anchor material for a future LLM-Judge implementation
of the WHO-axis form-check (per EHJ framework). It is **out-of-tree** —
no runtime consumer in the current review skills. Substance was salvaged
from withdrawn PR #274 (issue #273 re-scoped 2026-05-13) after empirical
audit showed the closed-list/regex approach was structurally inadequate.

## Functional vs Non-Functional Role Statements

Functional form: `You are a <noun-phrase> that <verb-phrase>` where the
noun-phrase names the role's *function* (not demographic credentials) and
the verb-phrase names the role's *behavior* (not character traits).

### PASS exemplars (functional)

- `You are a dependency checker that validates SemVer ranges in pyproject.toml.`
- `You are an evaluator that verifies acceptance criteria against the implementation diff.`
- `You are a security analyst that audits Terraform IAM policies for least-privilege violations.`

### FAIL High exemplars (demographic prefix)

- `You are an expert evaluator that verifies ACs.` — demographic `expert`
- `You are a senior staff engineer that designs Python services.` — demographic `senior`
- `You are a Python expert that explains type-system edge cases.` — demographic `expert` (compound-noun position)

### FAIL Medium exemplars (decorative prefix)

- `You are a meticulous reviewer that audits skill quality.` — decoration `meticulous`
- `You are a strict but fair evaluator that scores rubrics.` — decoration `strict`

## Severity Policy

| Class | Tokens (illustrative) | Severity |
|---|---|---|
| Demographic | `expert`, `senior`, `experienced`, `principal`, `world-class`, `world`, `class`, `veteran`, `seasoned`, `professional` | **High** |
| Decoration | `meticulous`, `rigorous`, `disciplined`, `strict`, `careful`, `thorough`, `thoughtful`, `pragmatic`, `helpful`, `friendly`, `brilliant`, `talented`, `exceptional`, `extraordinary`, `outstanding` | **Medium** |

**Source for severity asymmetry**: demographic personas have larger
length-controlled MMLU degradation than decoration alone per Sclar et al.
arXiv:2603.18507 (long expert persona −5.3pp vs minimum −3.6pp on MMLU).

## Compound-Noun Detection

The detection target spans the full noun-phrase, not just position 1.
Plan-Review R1 (PR #274) surfaced the compound-noun gaming vector:
`You are a Python expert that explains type-system edge cases` — `expert`
is in token position 2, scanned by a single-token check would miss it.

LLM-Judge implementations should scan the entire noun-phrase between
`You are an?` and the next clause boundary (`that|who|which|,|.`).

## Tokens Are Anchors, Not the Full Surface

The closed-list approach in withdrawn PR #274 had ~60% coverage on a
16-agent realsample. Key misses:

1. **Spirit-Decoration beyond the list**: `cooperative`, `specialist`,
   `senior-level`, etc. — the list cannot be enumerated exhaustively.
2. **Language gap**: `Du bist ein spezialisierter ...` (German openers)
   not matched by English `You are an?` regex.
3. **Definite article**: `You are the strict X` / `Du bist der ... Agent`
   not matched by `an?` regex.
4. **Persona-narrative**: multi-line role descriptions (`You are a
   senior X. You review with the rigor of a 2am on-call engineer ...`)
   where the *narrative length* is the actual violation, not any single
   token. Sclar et al. demonstrate length-graded degradation —
   minimum persona −3.6pp, long persona −5.3pp on MMLU.

Future LLM-Judge implementations should classify into categorical
verdicts (not binary match): `functional` / `decorative-tag` /
`narrative` / `mixed` / `none`.

## Source Citations (Tier 1)

- **arXiv:2603.18507** (Sclar et al., PRISM) — length-controlled MMLU
  evidence: minimum persona −3.6pp, long expert persona −5.3pp; MT-Bench
  alignment-leaning subtasks show reversed direction; safety personas
  +17.7pp refusal rate; PRISM routes 97.6–99.4% of reasoning queries to
  no-persona base model.
- **arXiv:2311.10054v3** (Zheng et al., EMNLP 2024 Findings) — 162
  personas across 9 OSS models (FLAN-T5-XXL, Llama-3, Mistral-7B,
  Qwen2.5 3B–72B). MMLU subset only. No persona consistently improves
  accuracy; gendered and out-of-domain roles underperform.
- **arXiv:2512.05858** (Basil/Mollick et al.) — expert personas don't
  improve factual accuracy on GPQA Diamond + MMLU-Pro across 6 models.
- **Anthropic, "Keep Claude in character"** — official guidance: "one
  sentence naming expertise + context"; multi-sentence character
  backstories explicitly discouraged. <https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/keep-claude-in-character>

## Note on Withdrawn arXiv:2602.12285

Earlier versions of this spec (and the repo's engineering baseline)
cited `arXiv:2602.12285 (AAAI 2026 TrustAgent Workshop)` with a "26.2%
degradation" magnitude. Deep research on 2026-05-13 verified that:
- The arXiv ID `2602.12285` does not resolve
- The "26.2%" magnitude does not appear in either Sclar (2603.18507)
  or Zheng (2311.10054v3) paper body

Both citations have been corrected throughout the repo. See
`docs/probe-runs/deep-research-open-questions-2026-05-13.md` for the
verification trail.

## Future LLM-Judge Implementation Notes

Per deep-research findings (arXiv:2412.05579 survey + ICLR 2025
"Trust or Escalate" + arXiv:2510.09738 "Judge's Verdict"):

- Separate sub-judges per axis outperform combined judges → WHO/HOW/WHAT
  should be three independent calls or three rubric items scored
  independently before combining.
- Required structure: rubric-based + per-axis few-shot anchors (this
  document provides them) + Cohen's κ ≥ 0.6 calibration gate against a
  maintainer-labeled gold set (≥30 artifacts).
- Pairwise comparison more reliable than absolute scoring for subtle
  distinctions.
- Token budget per judge call < 2000 tokens (per arXiv:2402.14848:
  reasoning degradation starts at ~3000 tokens).

## Cross-References

- Withdrawn PR: <https://github.com/Nosmoht/review-claude-config/pull/274>
- Re-scoped issue: <https://github.com/Nosmoht/review-claude-config/issues/273>
- EHJ framework: `research/agent-skills/agent-composition-framework.md`
- Detection-form-agnostic rewrite recipe: `skills/apply-skill-review-findings/references/skill-fix-guide.md §Decorative-to-Functional Role-Statement Rewrite`
