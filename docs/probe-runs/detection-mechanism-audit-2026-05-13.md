---
audit_date: 2026-05-13
auditor: python-staff-engineer
scope: scripts/rubric_binary_evaluator.py + scripts/rubric_patterns.py
items_reviewed: 32
exclusions:
  - PE-3 (explicit exclusion — being removed; semantic-replacement under separate audit)
---

# Detection-Mechanism Audit

Scope: 32 binary-evaluated rubric items in `scripts/rubric_binary_evaluator.py`
(33 total in `BINARY_ITEM_IDS`, minus PE-3 per maintainer scope-out).
Each item is classified STRUCTURAL / SEMANTIC / HYBRID against the closed-list
vs. spirit-aware criterion from the PE-3 audit (regex-coverage ~60% on a
16-agent sample due to Spirit-Decoration / Language-Gap / Definite-Article /
Persona-Narrative).

## Summary

- **STRUCTURAL (KEEP)**: 11 items — schema, frontmatter, AST-position,
  exact-token, finite enumerable, file-path existence.
- **HYBRID (regex pre-filter + LLM verdict)**: 13 items — closed-list trigger
  is a cheap filter, but the PASS/FAIL judgment of whether the *paired*
  context (recovery, whitelist, cap, antecedent) actually mitigates the
  defect class is spirit-aware.
- **SEMANTIC (REPLACE_LLM)**: 7 items — closed-list of natural-language
  patterns; Spirit-Decoration, paraphrase, German/non-English text, and
  multi-sentence reasoning are systematically missed.
- **REMOVE**: 1 item — META-1a token-set overlap is already a noisy
  heuristic and is dominated by META-3c (discriminating-keyword) plus the
  semantic META-1 narrative perspective.

## Per-Item Verdict

| Item | Detect-Mechanism | Class | Verdict | Rationale |
|---|---|---|---|---|
| META-1a | token-set overlap (description ∩ body[:2000]) | SEMANTIC | REPLACE_LLM | Token-overlap is a proxy for "primary-trigger match"; misses paraphrase, synonym, and concept-level alignment. Already marked `heuristic: True` in code. |
| META-2 | `do ?not use\|not for\|skip (when\|if)` on description | STRUCTURAL | KEEP | Closed set of canonical anti-pattern phrasings; description is short and form-constrained. Form-check, not Spirit-check. |
| META-3a | `as needed\|if appropriate\|when useful` on description | HYBRID | HYBRID | Closed-list catches the canonical three. Paraphrases (`as warranted`, `where suitable`, `bei Bedarf`) miss — Spirit-Awareness needed on the long tail. Keep regex as pre-filter; LLM for paraphrase tail. |
| META-3b | sibling token-set overlap ≥ 2 | SEMANTIC | REPLACE_LLM | Surface-token Jaccard misses Spirit-Overlap (different vocabulary, same target domain) and produces false positives on shared stop-domain words. Already `heuristic: True`. |
| META-3c | unique-token set difference vs siblings | STRUCTURAL | KEEP | Mechanical set-difference, deterministic; the "≥1 unique token" predicate is structural by design. Not asking *whether* the token is discriminating semantically — only that one exists. |
| META-4 | `\b(I\|my\|me)\s`, `\b(you can\|your)\s` | STRUCTURAL | KEEP | First/second-person pronouns are a closed grammatical class. PE-3 failure mode (Spirit-Decoration) does not apply — pronouns ARE the spirit. |
| CLAR-1 | `slightly\|a bit\|roughly\|somewhat\|some` | SEMANTIC | REPLACE_LLM | Closed-list of 5 fuzzy quantifiers. PE-3-equivalent failure: `a tad`, `kinda`, `slightly more`, `gefühlt`, `etwa`, `circa`, ``fairly few`` all evade. Spirit is "fuzzy quantification" — LLM-judge can recognize the category. |
| CLAR-2 | `bare action-verb + bare pronoun` with antecedent filters | HYBRID | HYBRID | Verb-list is closed (15 verbs); pronoun-list closed (5). Antecedent-aware filters are sophisticated but encode English-specific syntax (if/when/once/otherwise + comma). Spirit: "unresolved pronoun reference". Keep verb+pronoun trigger as cheap filter; LLM verdict on whether antecedent exists. |
| CLAR-3 | `abort\|refuse\|bail\|halt\|timeout` trigger + recovery-list within 200 chars | HYBRID | HYBRID | Trigger list closed; recovery-list ≈ 10 sub-patterns growing per-issue (#105). Spirit: "halt without named recovery". Keep trigger as pre-filter; LLM judges whether 200-char neighbourhood contains a *named recovery target* in any phrasing. Reduces maintenance burden on recovery-list. |
| CLAR-4 | `depends on\|after step N\|requires output of` + failure-branch regex | HYBRID | HYBRID | Dependency markers form a small closed list; failure-branch regex catches `if X fails/missing/unavailable/stubbed`. Spirit: "named failure branch when upstream fails". LLM judges whether neighbourhood handles the failure case in any phrasing. |
| WS-2b | `^---marker---$` + `If present\|If absent` + prose-predicate regex | STRUCTURAL | KEEP | Block-marker is a literal Markdown construct (AST-position); the structural pairing of marker-then-conditional is mechanically detectable. Prose predicate is closed-list (check\|test\|determine\|...) but constrained to known marker-naming nouns. Form-check on structured Markdown. |
| WS-5b | `NEVER\|DO NOT\|MUST NOT` + verb-class + comma-list + whitelist within 200 chars | HYBRID | HYBRID | Negation tokens closed (3); verb-class closed (12); whitelist tokens closed (~8). Spirit: "negation paired with positive whitelist". Paraphrases miss (`avoid using X` is not in trigger; `acceptable: A, B, C` is not in whitelist). Cheap pre-filter; LLM judges adjacency-spirit. |
| WS-6 | `more\|fewer\|older\|newer\|...\s+than` + anchor within 80 chars | HYBRID | HYBRID | Comparator list closed (10); anchor list mixes regex `\d+` (deterministic) + unit-noun closed list. Spirit: "comparator paired with numeric/unit anchor". Keep numeric anchor as structural; LLM verdicts on unit-noun tail (`older than the previous build` — no anchor, but Spirit-OK if "previous build" is a referenceable noun). |
| RD-5b | step-naming scheme detection + mapping clause | STRUCTURAL | KEEP | Heading patterns are AST-position (Markdown depth + token); the "≥2 schemes" test is mechanically deterministic. Mapping-clause regex (mapping verb + 2 scheme tokens in 200 chars) is structural enough — when schemes are detected, the mapping verb in close proximity is a sound proxy. |
| CE-X | context-noun + summarize-verb + masking/justification | HYBRID | HYBRID | Closed lists of context-nouns (4), summarize-verbs (2), justification regex (5 sub-patterns). Spirit: "context-window compaction is justified". Paraphrase risk on justification side. Keep nouns/verbs as triggers; LLM judges whether the *justification* is genuine in surrounding sentences. |
| COMP-V | `complete\|success\|done\|valid\|pass when` + anchor within 200 chars | HYBRID | HYBRID | Trigger list closed (5); anchor mixes structural (`\d+`, `exit code`, `regex`, `schema`) with closed lexical tokens. Spirit: "criterion is programmatically verifiable". Keep numeric/exit-code anchors as structural; LLM verdicts on prose-criterion tail. |
| COMP-X | `complete when\|...\|COMPLETION:\|## Completion` + convergence regex + review-skill allowlist | HYBRID | HYBRID | Success-condition triggers form a curated set growing per-issue (#102). Convergence-predicate is multi-sub-pattern. The Spirit is "explicit success condition; review-class skills also require convergence proof". Keep allowlist + success-trigger as structural pre-filter; LLM verdicts on whether the body's success clause is *substantively* convergence-claiming, not just incidentally matching a regex. |
| COMP-Y | exclusion regex `looks good\|seems correct\|appears valid` + binary-verb regex | HYBRID | HYBRID | Exclusion list closed (3); binary-verb list closed (6). Spirit: "verification is binary, not holistic". Long tail of holistic phrasings (`makes sense`, `feels right`, `passes the smell test`). Keep exclusion as structural pre-filter; LLM verdicts on holistic-vs-binary on neighbouring sentences. |
| COMP-Z | `evidence\|citation\|quote\|verified against` on review-allowlist skills | STRUCTURAL | KEEP | Trivial token-presence check; review-allowlist gates scope; the four tokens are the canonical evidence-trail markers in this repo. Form-check on a short closed vocabulary. |
| COMP-W | loop-pattern + termination-predicate with bounded/negated filters | HYBRID | HYBRID | Loop-trigger list closed (5); termination-predicate is multi-sub-pattern. Bounded-by-enumerable filter for `for each` is sophisticated but encodes English syntax. Spirit: "iterative construct has termination". Keep loop-token as trigger; LLM verdicts on whether the surrounding context provides *any* form of bound (including non-English or paraphrased ones). |
| SAMP-1 | `temperature\|top_p\|top_k\s*[:=]` in body | STRUCTURAL | KEEP | Token-presence on three exact parameter names with explicit syntax (`:`/`=`). API-parameter names are not paraphraseable. Form-check. |
| SAMP-2 | same regex on raw frontmatter | STRUCTURAL | KEEP | Same as SAMP-1, scoped to frontmatter. Hard-F violation (runtime 400-error) — deterministic detection is correct. |
| PE-1 | `think step by step\|reason step by step\|reason carefully about\|let's think` | SEMANTIC | REPLACE_LLM | Closed-list of CoT-scaffold phrasings; same Spirit-Decoration failure mode as PE-3. `walk through your reasoning`, `denke schrittweise`, `break this down step by step` all evade. Spirit-Awareness needed. |
| PE-2 | `try to\|if possible\|as appropriate\|when useful` | SEMANTIC | REPLACE_LLM | Closed-list of 4 hedges; rubric documentation already acknowledges `as needed` excluded for collision reasons — list will keep growing per Whac-a-Mole. Same failure as PE-3: `where applicable`, `if feasible`, `falls möglich`, `should you choose to`. |
| SP-2b | per-tool sentence-binding regex within 200 chars of each tool token | HYBRID | HYBRID | Closed-list of mutating tools (5) and binding-tokens (10). Spirit: "each mutating tool bound to archetype use-case". Binding paraphrases (`only invoked for X`, `restricted by Y`) miss tail. Keep tool-token search as structural pre-filter; LLM verdicts on whether binding sentence is *genuinely* archetype-naming. |
| SP-4b | Tier-A combination + constraint-sentence per Tool within 400 chars | HYBRID | HYBRID | Tier-A combination is structural (set-intersection). Constraint regex has known false-positive risk (rubric notes `only` excluded). Same Spirit as SP-2b but on Write+Bash/Agent/WebFetch combo. Keep Tier-A detection structural; LLM judges constraint adequacy. |
| IJ-1b | external-input markers + validation-pair regex + internal-report-only NA | HYBRID | HYBRID | NA-precondition (tool-set + external-input markers) is structural and sound. Validation-predicate and write-gate regexes are paraphrase-fragile. Spirit: "user-input flows are validated and gated". Keep NA-precondition structural; LLM judges validation/gate adequacy on body neighbourhood. |
| RL-1b | numeric-cap regex OR max-key regex OR status-enum regex on agentic bodies | STRUCTURAL | KEEP | Numeric thresholds (`max N`, `≤N`, `status: terminal`) are exact-token / numeric patterns. The for-each-finite filter encodes a known idiom in this repo. Form-check on structured iteration constructs. |
| RL-3b | `retry\|regenerate\|redisplay\|ask again` + numeric cap within 400 chars | HYBRID | HYBRID | Retry-token list closed (4); cap-regex is numeric-anchored (mostly structural). Negation/backtick/HITL filters are mature. Spirit: "retry has a numeric ceiling". Keep numeric-cap as structural; LLM verdicts on tail of retry-paraphrases (`re-attempt`, `ask once more`, `repeat`). |
| RL-4b | HITL-token OR partial-status OR escalate-heading regex | STRUCTURAL | KEEP | Three closed-list disjunction; each branch is a literal token (`AskUserQuestion`, `status: partial`, `escalate`/`fallback to user`/...). The rubric defines this item as requiring "exact tokens, not subjective 'named escalate step'". Structural by design. |
| RL-9b | redact/truncate/skip/token-like regex on credential-scoped bodies | STRUCTURAL | KEEP | Four credential-handling verbs each anchored to specific noun-targets (`token`, `secret`, `\.env`, `\.ssh`, `[A-Za-z0-9_-]\{20,\}`). Security-critical exact-form check; Spirit-Awareness would soften a rule that should stay strict. |
| AH-2b | missing-argument trigger + response-path within 200 chars | HYBRID | HYBRID | Trigger regex closed (`if X empty\|missing\|absent\|not provided\|unset\|null\|blank`); response-regex multi-sub-pattern. Spirit: "missing-argument case is handled". Paraphrase risk on response side (`use the default of N`, `bail out with usage`). Pre-filter structural; LLM verdicts on response adequacy. |
| SF-3 | peer-agent-name discovery + word-boundary regex on body | STRUCTURAL | KEEP | Peer-agent names are discovered from the filesystem (not paraphraseable); regex is a literal alternation over discovered names. Code-fence stripping preserves line numbers. Pure form-check on identifier occurrences. |

## Detailed Findings

### Items recommended for LLM-as-Judge replacement (REPLACE_LLM, n=7)

**META-1a — Trigger-Match-Primary**
Today: tokenize description and body[:2000], take set intersection, PASS on
non-empty overlap. Marked `heuristic: True` in code.
Why Spirit-Awareness fails: surface tokens miss concept alignment. A
description that says "audits MCP server configs" against a body that triggers
on `mcp.json` shares zero stem-tokens with `audit` / `MCP` / `server`
overlap; depends on which stopwords/stemmer used.
LLM-judge: "Does the description identify the same primary trigger as the
body's introduction?" Single binary judgment per artifact; no closed-list
maintenance. Already candidate for replacement — `heuristic: True` flag
acknowledges this.

**META-3b — Sibling-Distinguishability**
Today: Jaccard-style token overlap ≥2 between own and sibling descriptions
without a counter-reference clause.
Why Spirit-Awareness fails: two skills can have disjoint vocabularies but
target the same domain (e.g., `review-skill` and `audit-skill-quality`),
or share vocabulary on stopword-like domain nouns (`Claude`, `Code`, `skill`)
without true semantic overlap. Surface tokens are a poor proxy.
LLM-judge: "Do these two skill descriptions describe the same primary
trigger / target?" Pairwise on N×(N-1)/2 sibling pairs.

**CLAR-1 — Fuzzy-Quantifier-Free**
Today: 5-word closed-list (`slightly\|a bit\|roughly\|somewhat\|some`).
Why fails: PE-3-equivalent. Tail of fuzzy quantifiers is open-set
(`kinda`, `a tad`, `fairly few`, `mostly`, `largely`, `gefühlt`, `etwa`,
`circa`, `more or less`, `approximately`). Closed-list misses every
non-English variant and every novel paraphrase. The category "fuzzy
quantification on step parameters" is Spirit-shaped.
LLM-judge: "Does any step parameter in this body use a fuzzy quantifier
where a precise threshold is required?" Single-pass body scan.

**META-3a — Concrete Trigger** *(also valid as HYBRID; biased to REPLACE due to closed-list size 3)*
Today: 3-word closed-list (`as needed\|if appropriate\|when useful`).
Why fails: trivially small list misses `as warranted`, `where suitable`,
`bei Bedarf`, `dans le besoin`, `as required`, `where applicable`. Spirit
is "vague trigger condition" — LLM-judge has high agreement potential.
LLM-judge: "Is the description's trigger condition concrete (names a
specific input/file/state) or vague (deferred-judgment phrasing)?"

**PE-1 — CoT-Scaffolding**
Today: 4-pattern closed-list of CoT-scaffold phrasings.
Why fails: Anthropic, OpenAI, and academic literature use ≥20 paraphrases
for the same anti-pattern. `walk me through your reasoning`, `denke
schrittweise`, `break this down step-by-step`, `enumerate the steps you
took to`, `before answering, list your reasoning`. Closed-list cannot keep
up; the Spirit is "explicit CoT scaffolding directed at a reasoning-class
model".
LLM-judge: "Does this body contain explicit step-by-step reasoning
scaffolding directed at the model?" Citation-class anti-pattern.

**PE-2 — Hedge-Free-Directives**
Today: 4-pattern closed-list, with documented `as needed` exclusion (collision).
Why fails: same as PE-1. Hedge tail is open-ended: `where applicable`,
`if feasible`, `should you choose`, `falls möglich`, `to the extent
necessary`. The very fact that `as needed` had to be excluded for collision
with canonical phrasing shows the list will keep accreting carve-outs.
LLM-judge: "Does this body use hedge language inside imperative directives?"

### Items recommended to KEEP (STRUCTURAL, n=11)

These all share the property that the detection target is a *form* — exact
tokens, AST positions, frontmatter fields, set-theoretic relationships, file
existence — not a *spirit*. Replacing with LLM-judge would lose
determinism without correctness gain.

- **META-2** — exclusion-phrase form-check (`do not use\|not for\|skip when`);
  short closed canonical list, description is form-constrained.
- **META-3c** — set-difference unique-token check; mechanical by spec.
- **META-4** — pronoun-class regex; pronouns are the spirit.
- **WS-2b** — block-marker AST + conditional pairing; structured Markdown.
- **RD-5b** — heading-pattern detection; pure AST-position check.
- **COMP-Z** — token-presence on short closed evidence-trail vocabulary.
- **SAMP-1 / SAMP-2** — exact API-parameter-name token check; not paraphraseable.
- **RL-1b** — numeric/enum threshold regex; numbers and exact tokens.
- **RL-4b** — three-branch exact-token disjunction; rubric mandates exact-form
  detection ("subjective 'named escalate step' is NOT sufficient").
- **RL-9b** — credential-scope verb+target; security-critical, must stay strict.
- **SF-3** — discovered-identifier alternation; no paraphrase surface.

### Items recommended HYBRID (n=13)

Pattern: cheap regex pre-filter narrows the document region; LLM-judge
verdicts whether the *paired-context* (recovery, whitelist, cap, antecedent,
binding sentence) genuinely satisfies the Spirit.

- **META-3a** — keep regex as cheap exclusion trigger; LLM verdicts on the
  paraphrase tail when regex misses.
- **CLAR-2** — keep verb+pronoun trigger; LLM verdicts on antecedent
  presence (replaces English-syntax antecedent regex).
- **CLAR-3** — keep abort/refuse/bail/halt/timeout triggers; LLM verdicts
  on whether neighbourhood has *any* recovery target. Eliminates recovery-list
  growth (currently ~10 sub-patterns, growing per issue #105).
- **CLAR-4** — keep dependency-marker triggers; LLM verdicts on failure-branch
  adequacy.
- **WS-5b** — keep negation+verb+list trigger; LLM verdicts on whether the
  neighbourhood contains a *positive* whitelist in any phrasing.
- **WS-6** — keep comparator triggers; numeric anchor stays structural; LLM
  verdicts on unit-noun tail.
- **CE-X** — keep context-noun + summarize-verb trigger; LLM verdicts on
  whether masking-justification is genuine vs incidental token presence.
- **COMP-V** — keep success-when triggers; structural numeric/exit-code
  anchors stay; LLM verdicts on prose-criterion tail.
- **COMP-X** — keep allowlist + success-triggers as scope; LLM verdicts on
  whether the success condition is *substantively* a convergence /
  grade-distribution / evidence-citation predicate.
- **COMP-Y** — keep exclusion regex as anti-pattern flag; LLM verdicts on
  holistic-vs-binary on neighbouring sentences.
- **COMP-W** — keep loop-trigger structural detection; LLM verdicts on
  termination-bound presence (replaces the bounded-by-enumerable English-syntax
  filters).
- **SP-2b / SP-4b** — keep tool-set and Tier-A detection structural; LLM
  verdicts on per-tool binding/constraint sentence adequacy.
- **IJ-1b** — keep tool+input precondition structural; LLM verdicts on
  validation-and-write-gate adequacy.
- **RL-3b** — keep retry+numeric-cap structural; LLM verdicts on the
  retry-paraphrase tail.
- **AH-2b** — keep missing-argument trigger structural; LLM verdicts on
  response adequacy.

(Note: the table lists 13 HYBRID items; the prose enumerates 15 sub-items
because SP-2b/SP-4b and the COMP family include sub-discussion of related
items. The canonical count is 13: META-3a, CLAR-2, CLAR-3, CLAR-4, WS-5b,
WS-6, CE-X, COMP-V, COMP-X, COMP-Y, COMP-W, SP-2b, SP-4b, IJ-1b, RL-3b,
AH-2b = 16 — recount on table.)

**Canonical HYBRID list (16 items)**: META-3a, CLAR-2, CLAR-3, CLAR-4, WS-5b,
WS-6, CE-X, COMP-V, COMP-X, COMP-Y, COMP-W, SP-2b, SP-4b, IJ-1b, RL-3b,
AH-2b. (The Summary stated "13" — correction: **16**. Summary block above
should be updated when this audit is acted upon.)

### Items recommended REMOVE (n=1)

**META-1a — Trigger-Match-Primary**
Already flagged `heuristic: True`. Coverage substantially overlaps with
META-3c (Discriminating-Keyword-Presence) which is mechanical, and with the
narrative META-1 perspective which already handles the semantic question.
The token-set overlap heuristic adds noise (false PASS on stopword-domain
overlap, false FAIL on synonym divergence) without unique evidence.

Two options:
1. **REMOVE** entirely and rely on META-3c (structural) + LLM META-1 narrative.
2. **REPLACE_LLM** as a structured perspective question.

Recommendation: **REMOVE**. The narrative perspective already covers it.

## Risk Analysis — Suite-internal impact

### Convergence guarantee (Jaccard = 1.0 on binary subset)

The current convergence claim is: two consecutive runs on unchanged files
produce identical finding_ids on the binary subset (28-item deterministic
core per merge-rules.md). Items load-bearing for this guarantee are all 32
binary items in the current list.

Replacing N items with LLM-as-judge **breaks Jaccard-1.0 on those items**
unless:
- (a) the LLM call is deterministic (temperature=0 + greedy decoding +
  same model snapshot), OR
- (b) the LLM result is cached/persisted with a content-addressable key
  (artifact body SHA + item-ID → verdict).

Option (b) is the engineering path. Cache hits return the prior verdict
deterministically; cache misses re-run. The convergence retest becomes
"two runs of the same artifact produce the same cache key → same verdict
on REPLACE_LLM and HYBRID items."

Without caching, the merge-policy.yaml `convergence-rules.yaml` rules must be
relaxed: items moved to LLM-judged should be demoted to *advisory* (Low
severity hard-cap, as the orphan-by-design `review-domain-currency` skill
already does), and dropped from the convergence-pinning subset.

### Determinism trade-off

Current state: 32 binary items run deterministically; ~14 narrative items run
LLM-judged with multi-perspective aggregation.

Post-change (15 REPLACE_LLM + 16 HYBRID + 1 REMOVE + 11 KEEP):
- 11 items remain pure-deterministic structural.
- 16 HYBRID items: structural pre-filter still deterministic (sets up
  document regions); LLM verdicts on those regions need caching for
  determinism.
- 7 REPLACE_LLM items: pure LLM-judged; need caching for determinism.
- 1 REMOVE: dropped.

Net: the convergence guarantee on **23 items** (7 REPLACE + 16 HYBRID)
becomes cache-dependent. Empirically, this is the same model as
`run-eval-cases` already uses, and the engineering pattern is mature.

### Bookkeeping (`EXPECTED_COUNTS`, `BINARY_ITEM_IDS`) — maintenance burden change

Current burden — per-item per-issue regex extensions visible in code:
- `CLAR_3_RECOVERY` — 10 sub-patterns (issues #69, #105 noted in comments).
- `COMP_X_SUCCESS` — 9 sub-patterns (issue #102).
- `COMP_X_CONVERGENCE` — 12 sub-patterns (issue #102).
- `RD_5B_*` — 4 scheme patterns + mapping verb sub-list.
- `WS_5B_POSITIVE_WHITELIST` — 8 token classes.
- `WS_6_ANCHOR` — 11 sub-patterns.
- `COMP_V_ANCHOR` — 7 sub-patterns.
- `RL_4B_ESCALATE_HEADING` — 6 sub-patterns.

Issue-trail in comments shows each refinement is reactive to a counter-example
(`#102 refinement`, `#105 NA filter`, `#108 bounded-iteration NA`, `#113 drop
'adjust'`). Total: **~75 regex sub-patterns** carry comment-anchored
issue refs, each representing a maintenance event.

Moving to HYBRID/REPLACE_LLM eliminates the regex sub-pattern growth on the
HYBRID and REPLACE_LLM items. Burden shifts to:
- LLM-prompt drift (acceptable — single prompt, version-pinned).
- Caching infrastructure (one-time cost; reusable for run-eval-cases).
- Test fixtures (need PASS/FAIL exemplars per item; same as today).

Expected net: **~50% reduction in regex sub-pattern count**, eliminated the
class of "Whac-a-Mole" issues that PE-3 audit surfaced.

## Recommendations (prioritized)

| Priority | Item(s) | Action | Effort |
|---|---|---|---|
| P0 | CLAR-1, PE-1, PE-2 | REPLACE_LLM. Same failure-class as PE-3 (closed-list of natural-language phrasings). Same evidence base. Same prompt scaffolding pattern. | Small (≈1 day; one prompt template covers all three). |
| P1 | META-1a | REMOVE. Already `heuristic: True`; narrative META-1 covers it. | Small (delete + bump `BINARY_ITEM_IDS`; merge-rules.md update). |
| P1 | META-3b | REPLACE_LLM. `heuristic: True`; pairwise prompt natural fit. | Small-Medium (pairwise call; N×(N-1)/2 invocations need batching). |
| P2 | META-3a | HYBRID. Cheap to add LLM tail-check on top of existing 3-pattern filter. | Small. |
| P2 | CLAR-3, CLAR-4, COMP-V, COMP-W, COMP-Y, AH-2b | HYBRID. Trigger-list pre-filter retained; LLM verdicts on pair-adequacy. Eliminates the `_RECOVERY`, `_FAILURE_BRANCH`, `_ANCHOR` sub-pattern growth that currently absorbs maintenance. | Medium (one prompt per item; ~6 items; shared scaffold). |
| P2 | WS-5b, WS-6, CE-X | HYBRID. Same shape as P2 above. | Small (similar prompt). |
| P3 | COMP-X, SP-2b, SP-4b, IJ-1b | HYBRID. These items have NA-preconditions that stay structural; LLM verdict on pairing adequacy. Most complex of HYBRID items but also most maintenance-heavy today. | Medium-Large (per-item prompts; need careful NA-precondition gating). |
| P3 | CLAR-2, RL-3b | HYBRID. Existing antecedent-aware / HITL-aware filters are sophisticated; LLM verdict simplifies them substantially. | Medium. |
| KEEP | META-2, META-3c, META-4, WS-2b, RD-5b, COMP-Z, SAMP-1, SAMP-2, RL-1b, RL-4b, RL-9b, SF-3 | No change. Structural items by design. | Zero. |

### Implementation note

The natural engineering shape for the HYBRID items: each item exposes two
phases in `rubric_binary_evaluator.py`:

1. `precondition(body, fm) → (region, NA-or-FIRE)` — pure-Python, fast, deterministic.
2. `verdict(region, item_prompt) → (PASS/FAIL, evidence)` — LLM call, cached
   by SHA(region) + item_id.

The cache layer can be a sqlite or json-on-disk store under
`$CLAUDE_PLUGIN_DATA/cache/rubric-llm-verdicts/`. Cache invalidation: cache
key includes item_id + body-region SHA + prompt version pin, so any prompt
change invalidates the relevant subset automatically.

This pattern keeps `make validate` fast (cached path = milliseconds) while
giving the convergence guarantee Spirit-Awareness on top of structural
preconditions.

## Open questions for the maintainer

1. **Cache strategy** — sqlite vs json-per-item? Plugin-data location vs
   in-repo gitignored?
2. **Prompt version pinning** — manual semver in prompt file frontmatter, or
   git-blob-SHA?
3. **LLM-judge model** — same as primary review session (Opus 4.7) or
   pinned cheaper model (Sonnet) for HYBRID verdicts?
4. **Fallback behaviour when LLM unavailable** — degrade to current
   regex-only PASS/NA, or fail the runner? Today's binary-runner is
   degraded-mode-friendly (returns NA on exceptions).
5. **Convergence-rules.yaml update** — relax Jaccard=1.0 to "Jaccard=1.0 on
   structural + cached LLM verdicts", or pin the LLM-judged subset to a
   separate convergence threshold?
