---
name: reasoning-techniques-cluster
description: Chain-of-Verification / Self-Consistency / Step-Back evaluated for static-artifact-author-time applicability; accept/reject decisions
last_refreshed: 2026-04-29
---

# Reasoning-Step Techniques: Static-Artifact Applicability

Three Tier-1 reasoning-step techniques evaluated for inclusion in the engineering baseline. The decisive question is **static-artifact applicability** — does writing the technique into a skill body actually help, or is it a runtime-orchestration concern?

| Technique | Tier-1 Source | Static-Artifact Applicable? | Decision |
|---|---|---|---|
| Chain-of-Verification (CoVe) | arXiv:2309.11495 (Dhuliawala et al. ACL 2024 Findings) | **Yes** — verification instructions live in the skill body | **ADOPT** as baseline technique |
| Self-Consistency | arXiv:2203.11171 (Wang et al. ICLR 2023) | **No** — requires runtime sampling of k completions + aggregation | **REJECT** for static baseline |
| Step-Back Prompting | arXiv:2310.06117 (Zheng et al. ICLR 2024, DeepMind) | **Yes — but conflicts with PE-1 + Claude adaptive thinking** | **REJECT** for static baseline |

## Tier-1 Evidence

### Chain-of-Verification (CoVe)

- **Source**: Dhuliawala, Komeili, Xu, Raileanu, Li, Celikyilmaz, Weston. *Chain-of-Verification Reduces Hallucination in Large Language Models*. arXiv:2309.11495. ACL 2024 Findings.
- **Method**: 4 steps — (i) draft initial response; (ii) plan verification questions to fact-check the draft; (iii) answer those questions *independently* (no access to original); (iv) generate final verified response.
- **Headline finding**: *Factored, decoupled verification* mitigates error propagation. Each verification is computed independently, preventing the model from anchoring on the original wrong answer.
- **Empirical**: hallucination decreases on Wikidata list-questions, MultiSpanQA, longform generation.

### Self-Consistency

- **Source**: Wang, Wei, Schuurmans, Le, Chi, Narang, Chowdhery, Zhou. *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. arXiv:2203.11171. ICLR 2023.
- **Method**: Sample k diverse reasoning paths via temperature sampling → majority/plurality vote on the final answer.
- **Headline metrics**: GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2%, StrategyQA +6.4%, ARC-challenge +3.9%.

### Step-Back Prompting

- **Source**: Zheng, Mishra, Chen, Cheng, Chi, Le, Zhou. *Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models*. arXiv:2310.06117. ICLR 2024 (Google DeepMind).
- **Method**: First derive a high-level concept or first principle from the question; then use that abstraction to guide concrete reasoning.
- **Headline metrics** (PaLM-2L): MMLU Physics +7%, MMLU Chemistry +11%, TimeQA +27%, MuSiQue +7%.

## Per-Technique Applicability Analysis

### CoVe → ADOPT

**Why static-artifact applicable**: The 4-step structure can be written into the skill body as a workflow: "After producing the initial response, list 3-5 fact-check questions about the response. Answer each independently before incorporating into the final output." Skills already do this informally (e.g., `review-skill`'s convergence-predicate, `audit-repo`'s metric-validation gate).

**Why compatible with existing rubric**: PE-1 forbids generic CoT scaffolding (`think step by step`, `let's think`). CoVe's verification language ("verify the initial response by fact-checking key claims") does NOT match the PE-1 regex. CoVe is a *verification* pattern, not a *reasoning* pattern.

**Repo overlap**:
- Existing baseline §"Verification Criteria" (`engineering-baseline.md:23`) already covers verification informally
- Existing baseline §"Feedback Loops" covers validate-fix-repeat
- COMP-Y / COMP-Z rubric items require programmatic check + evidence trail
- **CoVe's specific contribution** beyond this: the *decoupled* / *independent* nature of the verification questions. The agent should not see its draft answer when answering verification questions, otherwise error-propagation occurs.

**Operationalization** (baseline addition, not a new rubric item — too narrow for a binary check):
> **Decoupled Verification** `[Engineering guidance]` — When a skill produces an answer that has independently-verifiable claims (facts, paths, identifiers), structure the workflow so the verification step generates fact-check questions *before* re-reading the draft, then answers them with fresh tool calls (Read, Glob, Bash) rather than self-attestation. Dhuliawala et al. arXiv:2309.11495 (CoVe, ACL 2024 Findings): factored decoupled verification reduces hallucination across list-questions, MultiSpanQA, and longform generation. Anti-pattern: "after writing the report, re-read it and confirm it's correct" (self-attestation, anchored to draft). Pattern: "after writing the report, list 3-5 specific claims it makes; for each, run a fresh Read/Glob to verify the underlying file content matches before finalizing." Check: do verification steps re-touch the source-of-truth, or just re-read the draft?

### Self-Consistency → REJECT (static-artifact)

**Why not static-artifact applicable**: Self-Consistency requires the *harness* to invoke the model k times with different sampling seeds and aggregate via majority vote. A skill body cannot make Claude sample itself k times during one invocation — it would have to delegate to k separate subagents, which is expensive and orthogonal to the skill's purpose.

**Where the technique already lives in the repo**: `/review-skill`'s multi-perspective dispatch (3 perspectives → merge in `merge_findings.py`) is an *analog* of Self-Consistency at the orchestration layer — different perspectives give diverse reasoning paths; merging is an aggregation. This is the right place for the technique. No baseline addition needed.

**Documentation**: Self-Consistency stays in this research file as a runtime-orchestration reference, cited from `research/finding-identity/finding-identity-and-lifecycle.md` if the multi-perspective merge logic ever needs Tier-1 backing.

### Step-Back Prompting → REJECT (static-artifact)

**Why not static-artifact applicable**:

1. **Conflicts with PE-1 anti-pattern**: PE-1 forbids step-by-step reasoning scaffolding for reasoning-class models. Step-Back is a *structured* CoT variant ("first derive abstraction, then reason concretely") — the regex doesn't match Step-Back literally, but the *intent* of PE-1 is to avoid prescriptive reasoning chains in skills targeting Claude 4.6+/4.7 reasoning models.

2. **Conflicts with Claude 4.6+ adaptive thinking**: The existing baseline §"Instruction Calibration" notes that "Claude 4.6+ overtriggers on MUST/CRITICAL/ALWAYS — use natural phrasing. Prefilled responses deprecated; use `thinking: {type: 'adaptive'}` over prescriptive step chains." Step-Back's prescriptive abstraction-first chain falls into the "prescriptive step chain" category that should be left to adaptive thinking.

3. **Empirical setup is on PaLM-2L, not Claude 4.x**: Headline metrics (+7% to +27%) were measured on PaLM-2L, GPT-4, Llama2-70B. None of those models has Claude's adaptive-thinking primitive. The technique may still help on weaker models without adaptive thinking, but adopting it as a baseline would target the wrong model class.

**Documentation**: Step-Back stays in this research file as a "considered, deprecated for Claude 4.6+ targets" reference. If a skill is explicitly written for non-reasoning models (rare in this repo), a maintainer can cite this file for justification.

## Self-Application Audit (CoVe only)

Spot-check on 3 skills that produce structured output with verifiable claims:

| Skill | Has decoupled-verification pattern? | Verdict |
|---|---|---|
| `skills/review-skill/SKILL.md` | YES — convergence-predicate (re-run produces identical finding-IDs); `--compare-with` does fresh comparison against a separate file, not self-attestation | PASS |
| `skills/audit-repo/SKILL.md` | YES (after #100 fix) — completion criteria require concrete numeric values per metric or explicit "N/A with cause"; metrics computed from fresh `Bash` invocations, not re-reading the draft | PASS |
| `skills/audit-policy-compliance/SKILL.md` | PARTIAL — verifies tool authorizations against a separate policy file (`policy.json`), but does not have explicit "list claims, verify each independently" step. Could improve if maintainer chooses; current behavior is sufficient. | PASS (acceptable) |

**Result**: Repo's existing patterns are CoVe-compliant in spirit. New baseline technique is preventive guidance for future skills; no fix commits needed.

## Cross-Validation Posture

- CoVe (ACL 2024 Findings) — primary
- Self-Consistency (ICLR 2023) — corroborates the broader pattern that verification-via-multiplicity reduces error
- Step-Back (ICLR 2024 DeepMind) — corroborates that structured-reasoning helps on weaker models; informs the *reject* decision

All Tier-1 (peer-reviewed at ICLR / ACL conferences, well-cited). Passes web-research rule for the operationalized item (CoVe primary + Self-Consistency corroborating).

## References

- arXiv:2309.11495 — Dhuliawala et al., Chain-of-Verification (ACL 2024 Findings)
- arXiv:2203.11171 — Wang et al., Self-Consistency (ICLR 2023)
- arXiv:2310.06117 — Zheng et al., Step-Back Prompting (ICLR 2024 DeepMind)
- https://aclanthology.org/2024.findings-acl.212/ — CoVe canonical
- https://deepmind.google/research/publications/step-back-prompting-enables-reasoning-via-abstraction-in-large-language-models/ — DeepMind page

## Repo Cross-References

- `skills/review-claude-config/references/engineering-baseline.md` §"Verification Criteria" — adjacent technique; CoVe extends it
- `skills/review-claude-config/references/scoring-rubric.md` §"Reasoning-Model Anti-Patterns" — PE-1 rationale informs Step-Back rejection
- `skills/review-skill/references/merge-rules.md` — multi-perspective dispatch is the orchestration-layer analog of Self-Consistency
- `research/finding-identity/finding-identity-and-lifecycle.md` — multi-source merge rules
