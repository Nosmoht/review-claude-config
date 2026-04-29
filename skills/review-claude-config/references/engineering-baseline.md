---
name: engineering-baseline
description: Evidence-based prompt, context, and tool design techniques for evaluating Claude Code skills and agents
last_refreshed: 2026-04-29
---

# Engineering Baseline

## Prompt Engineering Techniques

**Structured Output** `[Proven result]` — Define exact output structure when the task depends on reliable formatting. Check: is the expected output shape explicit?

**Role Priming** `[Engineering guidance]` — Use a functional role statement when domain context materially changes judgment. Use functional descriptions ("You are a dependency checker that…"), not demographic or expert personas — they improve generative tasks but damage factual accuracy on discriminative tasks. Task-irrelevant cues cause up to 26.2% degradation. Check: does the role add behavioral context, or is it decorative?

**Stepwise Decision Flow** `[Engineering guidance]` — Break fragile reasoning into explicit ordered steps for analysis, validation, or branching work. Check: are complex decisions sequenced instead of left implicit?

**Few-Shot Examples** `[Engineering guidance]` — Add 3-5 canonical examples when output or trigger logic is easy to misread; wrap in `<example>` tags. Optimal count is model-specific; more is not better. Check: are examples present where behavior would otherwise be ambiguous?

**Constraint Specification** `[Proven result]` — State prohibitions, boundaries, and success conditions explicitly.

**Quantifier-Range Anchoring** `[Proven result]` — Comparators (`more/fewer/older/newer/larger/smaller than`) carry a numeric value or unit within 80 chars. Talmor et al. arXiv:1912.13283 (oLMpics, EMNLP 2020): LLMs reason on quantifiers only within typical training-distribution ranges; abstract reasoning fails. McCoy et al. arXiv:1902.01007 cross-validates the context-dependence pattern. Anti-pattern: "older than typical", "more imports than usual". Pattern: "older than 30 days", "more than 10 imports". Check: every relative comparator has a numeric or unit anchor adjacent.

**Lexical-Overlap Verification** `[Engineering guidance]` — Token-presence-triggered classification or routing pairs with a semantic verification step (regex pattern, frontmatter schema check, structured-field extraction). McCoy et al. arXiv:1902.01007 (HANS, ACL 2019): NLI models adopt three syntactic heuristics (lexical-overlap, subsequence, constituent) that fail on adversarial inputs; corroborated by Talmor oLMpics paradigm. Anti-pattern: "If the file mentions hooks, treat it as a hook." Pattern: "If frontmatter `type:` field equals `agent`, dispatch." Check: classifications based on string-presence include a semantic disambiguator.

**Distractor Isolation** `[Engineering guidance]` — When a step loads ≥2 reference/context sources, name which is canonical and which is excluded. Kassner & Schütze arXiv:1911.03343 (ACL 2020): PLMs are easily distracted by misprimes — irrelevant adjacent tokens shift predictions even when off-topic. Ettinger 2020 arXiv:1907.13528 (TACL) cross-validates via psycholinguistic diagnostics. Anti-pattern: "Read A.md and B.md, then process the input." Pattern: "Read A.md AND B.md. For step 3, apply only A.md's rules; B.md is for the merge in step 5." Check: multi-source steps have explicit scope markers (`focus on X`, `ignore Y`).

**Positive Framing over Negative Verbots** `[Proven result]` — LLMs are systematically negation-insensitive (Truong et al. arXiv:2306.08189: cloze hit rate <0.15, NLI sub-baseline, SAR ~50% vs BERT-large 92.5%; inverse scaling — bigger models do not help). Worse, **contrasting prompts** ("don't do X — do Y") increase wrong-hit-rate as the model repeats prior-context tokens. Pattern to use: **iff-predicate** with positively enumerated checks; if a negative verbot is rhetorically necessary, pair it with an adjacent positive whitelist (operation class + allowed verbs/tools) within 200 chars. Anti-pattern: a long `NEVER use: X, Y, Z` list — replace with `ALLOWED: A, B, C` + operation class ("read-only commands only"). Check: does each prohibition carry an adjacent positive predicate the agent can verify against?

**Verification Criteria** `[Engineering guidance]` — Tell the agent how to confirm correctness using checks, validators, or expected outcomes. Check: can the agent verify the output without relying only on intuition?

**Feedback Loops** `[Engineering guidance]` — For quality-critical work, use a validate-fix-repeat pattern instead of a single-pass instruction. Check: does the workflow include a correction loop where failure is likely?

**Evidence-First Critique** `[Engineering guidance]` — In review tasks, ground findings in quotes, paths, or specific examples rather than generic quality language. Check: could another reviewer verify the claim from the artifact?

**Constraint Load** `[Engineering guidance]` — When a step carries many simultaneous constraints, split it. Performance collapses beyond ~100 instances; instance count matters more than token count. For agent definitions, dense per-section packing risks the same at smaller scale `[Repo default]`.

**Deterministic Conditionals** `[Proven result]` — Write branch conditions as observable tests, not vague phrases like "if needed" or "as appropriate". Check: would two models take the same branch from the same input?

**Instruction Calibration** `[Engineering guidance]` — Smarter models need less aggressive prompting. Claude 4.6+ overtriggers on MUST/CRITICAL/ALWAYS — use natural phrasing. Prefilled responses deprecated; use `thinking: {type: "adaptive"}` over prescriptive step chains.

**Subagent Guardrails** `[Engineering guidance]` — Claude 4.6+ natively delegates but may overuse subagents. Skills should steer when subagents are/are not warranted and include "keep solutions minimal" constraints.

## Context Engineering Techniques

**Context Budget** `[Proven result]` — Focused, relevant context usually beats large but noisy context. Check: is each piece of context earning its token cost?

**Just-in-Time Retrieval** `[Engineering guidance]` — Keep references lightweight and load deeper material only when the task actually needs it. Check: does the item retrieve context progressively instead of front-loading everything?

**Subagent Isolation** `[Engineering guidance]` — Use subagents or isolated workers for bounded subtasks so each sees only the context it needs. Subagents do NOT inherit parent permissions — tool grants must be declared explicitly per subagent. Check: are large tasks decomposed into focused units, and do subagent tool grants reflect least-privilege rather than assuming inheritance?

**Reference File Separation** `[Engineering guidance]` — Move stable knowledge into `references/` files and keep the main instruction surface concise. Check: is reusable background knowledge separated from the workflow?

**Tool Set Curation** `[Engineering guidance]` — Give agents the smallest tool set that completes the task. Least-privilege reduces agent attack success rates by orders of magnitude with only 1-6% latency overhead. Match tools to archetype per `tool-grant-decision-tree.md`; Tier A combinations (Bash+network, Bash+Write, Write+WebFetch) require documented justification.

**Activation Precision** `[Engineering guidance]` — Describe clearly when a skill or agent should trigger and when it should not. The description is the sole activation signal for auto-dispatch — trigger logic that appears only in the body is invisible to the dispatcher. Check: would unrelated requests accidentally match this wording? Does the body contradict what the description says about when to activate?

**Error Preservation** `[Engineering guidance]` — Preserve failed attempts or error traces when they help the system avoid repeating the same mistake. Check: does the workflow retain useful failure context for correction?

**KV-Cache Friendliness** `[Engineering guidance]` — Keep shared prefixes and repeated orchestration blocks stable when dispatching similar work. Check: are repeated agent prompts and tool sets stable enough to benefit from reuse?

**Confirmation Gates** `[Engineering guidance]` — Require explicit user confirmation before destructive or irreversible actions. Check: can the item modify or delete important data without approval?

**Stop Conditions** `[Engineering guidance]` — Define clear termination criteria for retries, loops, recursive work. For multi-step skills, define testable "done" criteria before execution — prevents marking work complete without verification.

**Retry Ceilings** `[Repo default]` — When a task includes retries, keep the retry budget small and explicit so failures escalate instead of looping invisibly. Check: is there a concrete retry limit?

**Idempotency Design** `[Engineering guidance]` — Make tool operations produce the same result when executed multiple times. LLM agents retry 15-30% of tool calls due to timeouts or validation errors. Check: can every create/modify/delete tool call be safely retried?

**Circuit Breaker Pattern** `[Engineering guidance]` — Track failures in a sliding window and temporarily halt requests when thresholds are exceeded to prevent cascade failures. Check: does the workflow stop calling a failing service after repeated failures?

**Progressive Fallback** `[Engineering guidance]` — When operations fail, degrade through self-correction, fallback strategies, and escalation rather than immediate failure. Check: does the workflow have multiple recovery paths instead of binary success/failure?

**Knowledge Gap Detection** `[Engineering guidance]` — Teach the system to escalate, retrieve more context, or admit uncertainty when required knowledge is missing. Check: does the workflow prevent confident guessing when information is insufficient?

**Dynamic Tool Loadout** `[Low-evidence area]` — Pre-filter available tools when a large shared catalog creates selection ambiguity, but treat exact numeric cutoffs as heuristic unless benchmarked for the target environment. Check: does the agent see only the tools relevant to the current task?

**Context Compression** `[Engineering guidance]` — For long-running work, compress older context while preserving key decisions and failures. Guided compression: ACON 26-54% token reduction at >95% accuracy; Focus 22.7% autonomous compaction at identical SWE-bench accuracy; Context-Folding 10× smaller active context. Check: does the skill have a compaction strategy for workflows exceeding ~10 tool-call turns?

**Observation Masking** `[Engineering guidance]` — Prefer masking (drop entries by age/index) over LLM summarisation when output is non-decision-relevant. ACE pattern (arXiv:2508.21433): 52% cost reduction at parity on SWE-bench Verified. CE-X decision table:
- (a) Output <1K tokens AND turn-history ≤5 → neither required.
- (b) Output ≥1K tokens AND non-decision-relevant → masking preferred (rotating window, drop entries older than N tool-calls).
- (c) Output ≥1K tokens AND semantic condensation needed → summarisation, with body-justification of why masking would lose dependency-graph signal.
Check: if workflow keeps history ≥10 turns AND uses summarisation, is the choice justified?

**Context Placement** `[Proven result]` — Place critical instructions at START and END, never only in the middle. LiM effect peaks at <50% context utilization; at >50%, weight toward END. Reduced in larger models. Check: are key instructions anchored at both ends?

## Goal Alignment Techniques

**Premise Verification** `[Proven result]` — When a skill acts on a user-supplied premise (path, command, classification, file content, claim) AND the premise is mechanically verifiable, include a verification predicate within 200 chars of the action. Sharma et al. arXiv:2310.13548 (Anthropic ICLR 2024): RLHF-trained models systematically prefer user agreement over factual correctness across 4 free-form generation tasks; SycEval arXiv:2502.08177 cross-validates persistence across model families. Anti-pattern: "use the path the user provides" without existence/format check. Pattern: "validate `$ARGUMENTS` matches `^[A-Za-z0-9_/.-]+$` AND file exists; surface discrepancy and stop on fail." Check: does each user-supplied input have an adjacent verification step before action? See `research/goal-alignment/sycophancy.md`.

**Function-Level Success Criteria** `[Engineering guidance]` — Define success in terms of *function* (does the artifact achieve the intent?), not *form* (was it produced?). Langosco et al. arXiv:2105.14111 (ICML 2022) + Shah et al. arXiv:2210.01790 (DeepMind): agents retain capabilities OOD but pursue proxy goals correlated with training objectives, including in LLM-without-RL settings. Anti-pattern: success = "report.md exists" / "5 files modified" / "every checklist item has a verdict". Pattern: success = "report contains ≥N findings each with Current/Recommended/Validation blocks AND each finding cites a path or quote" / "modified files pass `make validate` AND originally-failing test now passes". Check: can the skill's success criteria be satisfied by trivially-correct-but-functionally-empty output? See `research/goal-alignment/goal-misgeneralization.md`.

**Gaming-Resistant Criteria** `[Engineering guidance]` — In review-class skills (verbs ∈ {review, audit, classify, evaluate, score, certify}), pair every regex-checkable surface criterion with an evidence-grounding requirement (path:line citation, verbatim quote, tool-output reference). Bondarenko et al. arXiv:2502.13295 + arXiv:2505.07846: frontier models employ a hierarchy of exploitation strategies under criteria-pressure, escalating from state manipulation to logic subversion. Reasoning models are MORE prone, not less. Anti-pattern: "passes if regex `\bredact\b` appears in body" — gameable by inserting the keyword. Pattern: "passes if `redact` appears WITHIN 200 chars of a token-shape pattern (`[A-Za-z0-9_-]{20,}`)" — gaming requires actually scoping the redaction. Check: does each rubric item couple surface match with intent verification? See `research/goal-alignment/specification-gaming.md`.

## Tool Design Techniques

**Descriptions as Onboarding** `[Engineering guidance]` — Write tool descriptions as if explaining usage to a new teammate. Check: would an unfamiliar engineer understand when and why to use the tool?

**High-Signal Returns** `[Engineering guidance]` — Return only the information needed for the next decision, using filtering or truncation where appropriate. Check: could the tool overwhelm the context with irrelevant output?

**Meaningful Identifiers** `[Engineering guidance]` — Prefer semantic names and explicit parameters over cryptic IDs or overloaded free text. Check: are identifiers self-describing at the call site?

**Actionable Errors** `[Engineering guidance]` — Make tool errors suggest the next fix instead of returning opaque failure states. Check: would the error help the agent recover?

**Avoid Time-Sensitive Guidance** `[Engineering guidance]` — Keep stable prompt assets free of time-bound wording unless the task is explicitly time-sensitive.

**Poka-Yoke Tool Design** `[Engineering guidance]` — Remove common failure modes structurally, for example by requiring absolute paths or constrained parameters. Check: can the most common misuse be made impossible instead of merely warned about?

**Typed Schemas** `[Engineering guidance]` — Use explicit types and validation at tool boundaries so invalid inputs fail early. Check: do the tool parameters have an enforceable schema?
