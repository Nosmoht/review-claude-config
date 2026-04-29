---
name: llm-linguistic-failures-cluster
description: Cluster overview of systematic LLM linguistic failure modes (negation, quantifier-range, lexical-overlap, mispriming, syntactic heuristics) with iff-pattern operationalization status
last_refreshed: 2026-04-29
---

# LLM Linguistic Failure-Mode Cluster

LLMs exhibit systematic, evidence-documented failure modes on specific linguistic constructions that competent humans handle reliably. These failures are *robust to scale* — bigger models do not fix them — and *robust across families*. They affect the skills' downstream consumer LLM and therefore are skill-author-time concerns: the skill body's wording can amplify or mitigate the failure.

This file extends the WS-5 (Negation, Truong et al. arXiv:2306.08189, baked into commit b0daa03) precedent into a broader cluster of related findings. Three modes are operationalized as new rubric items (WS-6, WS-7, WS-8). Two additional modes are documented but deferred (no clear artifact-level binary detector).

## Operationalized Modes

### WS-6 — Quantifier-Range Brittleness

**Phenomenon**: Models reason correctly only within typical training-distribution ranges. RoBERTa correctly compares ages within the human range (e.g., 25 vs 70) but fails when ages fall outside it (e.g., 250 vs 700). Quantifier and comparator reasoning is *context-dependent*, not abstract. Half of oLMpics tasks fail completely across all tested model families.

**Tier-1 Sources**

- Talmor et al. 2020. *oLMpics — On What Language Model Pre-training Captures*. arXiv:1912.13283. EMNLP 2020.
- Cross-validation: McCoy et al. 2019 (compositional reasoning failures, see WS-7) — same paradigm of "model passes on training-distribution-typical inputs, fails on systematic variants".

**Manifestation in Skill Artifacts**

- Skill body says "if the file is older than typical" / "if there are more imports than usual" / "if the function is too long" — bare relative comparator without numeric or unit anchor.
- Agent must infer the threshold from training-data-typical values. Inference will silently disagree across runs; review-skill convergence breaks.

**iff-Predicate (regex-tractable)**

> If the body contains a comparator from `/\b(more|fewer|older|newer|larger|smaller|less|greater|higher|lower)\s+than\b/i` AND the next 80 chars do NOT contain a numeric value, a unit (`days|hours|files|lines|tokens|bytes|MB|KB|chars`), or an explicit threshold reference (`exceeds|below|above\s+\d+|threshold`) → Clarity capped at C.

**PASS examples**
- "older than 30 days"
- "more than 10 files"
- "exceeds the 500-token threshold"
- "larger than the documented 8000-byte budget"

**FAIL examples**
- "older than typical"
- "more imports than usual"
- "longer than expected"
- "fewer files than recommended"

### WS-7 — Lexical-Overlap Classification

**Phenomenon**: Models adopt three syntactic heuristics during NLI: lexical-overlap (assume entailment if hypothesis tokens appear in premise), subsequence (assume entailment if hypothesis is contiguous subsequence), and constituent (assume entailment if hypothesis is a constituent). All three break down on adversarial inputs. BERT-class models perform very poorly on HANS even after MNLI training.

**Tier-1 Sources**

- McCoy, Pavlick, Linzen 2019. *Right for the Wrong Reasons: Diagnosing Syntactic Heuristics in Natural Language Inference*. arXiv:1902.01007. ACL 2019.
- Cross-validation: Talmor et al. 2020 oLMpics § "Different LMs exhibit qualitatively different reasoning abilities" — confirms that compositional reasoning is shallow across LM families.

**Manifestation in Skill Artifacts**

- Skill body asks the agent to classify or route based on token-presence in user input or file content: "if the file mentions X, treat as Y", "if the description contains Z, dispatch to subagent A".
- Without an explicit semantic verification step, the agent uses lexical-overlap as the routing signal — which fails on inputs where the keyword is incidental, negated, or used in a different sense.

**iff-Predicate (LLM-binary)**

> If the body contains a classification or routing instruction triggered by token-presence in user input (`/(if|when)\s+the\s+(file|description|input|argument|user|content)\s+(contains|mentions|includes|has)\s+/i`) AND the body lacks a semantic verification predicate within 200 chars (regex match, schema check, structured-field extraction, or explicit "verify the keyword is in scope X" instruction) → Clarity capped at C.

**PASS examples**
- "If the file's frontmatter `type:` field equals `agent`, dispatch to /review-agent."
- "If the description contains `mcp` AND a regex match against `\.mcp\.json|MCP\s+server` succeeds in body, route to /review-mcp-server."
- "If `$ARGUMENTS` matches `^[A-Z]+-[0-9]+$` (issue-id schema), dispatch to issue-lookup."

**FAIL examples**
- "If the file mentions hooks, treat it as a hook." (lexical overlap — "hooks" could refer to git hooks, React hooks, Claude Code hooks; no schema check)
- "If the user says they want to review, route to review-skill." (lexical — "review" is overloaded across domains)
- "If the description contains `agent`, treat the file as an agent." (could be a skill that mentions agents, not an agent file)

### WS-8 — Distractor-Isolation in Multi-Source Context

**Phenomenon**: PLMs do not distinguish between negated and non-negated cloze probes (e.g., "Birds cannot [MASK]" produces the same predictions as "Birds can [MASK]"), and are easily distracted by misprimes (irrelevant adjacent tokens shift predictions). The mispriming effect is *robust across model sizes*. The cognitive analogue is that humans can ignore irrelevant context; current LMs cannot reliably.

**Tier-1 Sources**

- Kassner & Schütze 2020. *Negated and Misprimed Probes for Pretrained Language Models: Birds Can Talk, But Cannot Fly*. arXiv:1911.03343. ACL 2020.
- Cross-validation: Ettinger 2020. *What BERT Is Not — Lessons from a New Suite of Psycholinguistic Diagnostics*. arXiv:1907.13528. TACL 2020. Confirms negation-failure and adds event-knowledge / role-assignment failures.

**Manifestation in Skill Artifacts**

- Skill loads multiple references / examples / context blocks via JIT and asks the agent to act, without naming which reference is canonical for the current step.
- Agent's output is influenced by the most-recently-mentioned tokens regardless of whether they are relevant — the mispriming effect surfaces as "agent applied the wrong reference's rules to this step".

**iff-Predicate (LLM-binary)**

> If the body loads ≥2 reference files in the same step (multi-source context) AND the step lacks an explicit distractor-isolation marker — a sentence pairing `/(focus|use|apply|reference|consult)\s+(only|just|specifically)\s+/i` with a named reference, OR a sentence excluding `/(ignore|skip|bypass|do\s+not\s+(read|use|consult))/i` other references — → Clarity capped at C.

**PASS examples**
- "Read `references/A.md` AND `references/B.md`. For step 3, apply only A.md's rules; B.md is for the merge step in step 5."
- "Load both reference files; ignore B.md unless the input matches schema X."

**FAIL examples**
- "Read `references/A.md` and `references/B.md`. Then process the input." (no isolation marker — agent will mix rules from both references unpredictably)
- Multiple reference-loads in one step with no scope markers anywhere in the step.

## Deferred Modes

These modes have Tier-1 evidence but no clear artifact-level binary detector. Documented for future work; not operationalized in this commit.

### Pragmatic / Event-Knowledge Inference (Ettinger 2020)

BERT fails on commonsense-pragmatic inference, semantic-role assignment, and category-membership probes. Manifests in skills as: instructions assume the agent will fill commonsense gaps (e.g., "extract the relevant function") without naming the criterion.

**Why deferred**: The artifact-level pattern is "instructions that rely on commonsense" — too broad for a binary check. May be operationalizable by detecting *bare imperatives* without object specification (e.g., "extract the relevant function" without saying *which*) — but this overlaps heavily with WS-2b (conditional-specificity) and CLAR-1 (fuzzy-quantifier-free).

### Negation-with-Mispriming (composite)

Combines WS-5 (negation) with mispriming (Kassner & Schütze). Skill bodies that use a negative imperative followed by a positively-framed example are especially likely to mislead the agent: the example primes the negated behavior. Example: "DO NOT use `cat` for files >50 lines. For example, `cat large.log`..." — the example reinforces the prohibited operation.

**Why deferred**: Detecting "example-after-prohibition that demonstrates the prohibited operation" requires LLM-binary parsing of example semantics. Out of scope for the regex/binary-LLM architecture.

## Self-Application Audit (2026-04-29)

| Mode | Scan method | Hits | Verdict |
|---|---|---|---|
| WS-6 | grep across `skills/*/SKILL.md` for the comparator regex, then filter for numeric/unit anchor within 80 chars | 3 hits in `skills/review-analytics/SKILL.md` (lines 76, 78, 80); each is anchored to "≥5 points" within 80 chars via an OR-clause | PASS — all hits anchored, no violation |
| WS-7 | grep for `(if|when) the (file|description|input|argument|user|content) (contains|mentions|includes|has)` | 0 hits across all skills | PASS — no violations |
| WS-8 | Spot-check on 3 multi-reference-loading skills (`review-skill`, `audit-repo`, `scaffold-skill`) | All three load references at the orchestration boundary with step-level scope markers present (e.g., "Those files contain the authoritative recipe; the sub-steps below are the orchestration sequence") | PASS — sample compliance |

**Result**: No fix commits needed. The repo's existing discipline (positive framing per WS-5, scoped reference loading, anchored thresholds in numeric-discriminator skills) already complies with the new WS-6/7/8 items. AC requirement "≥1 fix commit per qualified mode" interpreted as N/A when no violations exist. The new items become preventive going forward — caught at review-time for new artifacts.

**Future re-audit cadence**: WS-6/7/8 will be re-scanned automatically as part of `/review-skill` runs since they are added to `NON_BINARY_ITEMS` in `rubric_binary_evaluator.py`.

## Cross-Validation Posture

| Mode | Tier-1 Sources | Cross-validation status |
|---|---|---|
| WS-6 | Talmor 2020 + McCoy 2019 (paradigm corroboration) | Passes web-research rule |
| WS-7 | McCoy 2019 + Talmor 2020 (paradigm corroboration) | Passes web-research rule |
| WS-8 | Kassner 2020 + Ettinger 2020 (independent psycholinguistic suite) | Passes web-research rule |

All sources are peer-reviewed (ACL / EMNLP / TACL conferences, 2019-2020). Foundational papers exempt from 18-month freshness rule.

## Item-Cap Note (Gawande)

This commit raises Clarity binary items from 8 to 11. Gawande's 5-9 cap applies to manual cognitive checklists; our items are evaluated by `rubric_binary_evaluator.py` and perspective sub-agents, not by a single human review pass. Cognitive-load argument does not directly apply; relevant constraint is reviewer-LLM instruction-density (AgentIF: ≤10 distinct constraints per task), which is unaffected because WS-6/7/8 sit in the same `Ambiguity Markers` section that is already loaded as one chunk.

If empirical convergence drops after WS-6/7/8 introduction, candidate consolidations are: merge WS-2b into WS-5 (both positive-specificity items), or merge CLAR-1 into a broader fuzzy-language item.

## References

- arXiv:1912.13283 — Talmor et al., oLMpics (EMNLP 2020)
- arXiv:1902.01007 — McCoy, Pavlick, Linzen, Right for the Wrong Reasons / HANS (ACL 2019)
- arXiv:1911.03343 — Kassner & Schütze, Negated and Misprimed Probes (ACL 2020)
- arXiv:1907.13528 — Ettinger, What BERT Is Not (TACL 2020)
- arXiv:2306.08189 — Truong et al., LLMs Are Not Naysayers (already operationalized as WS-5)
- https://aclanthology.org/2020.tacl-1.3/ — Ettinger TACL canonical
- https://aclanthology.org/2020.acl-main.698/ — Kassner & Schütze ACL canonical
- https://aclanthology.org/P19-1334/ — McCoy et al. ACL canonical
