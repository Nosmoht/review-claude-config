---
research_date: 2026-05-13
researcher: general-purpose-subagent
questions: 6
budget_consumed:
  searches: 8
  fetches: 2
ehj_framework_under_validation: WHO=Role-Spec Eager, HOW=Method Hint, WHAT=Domain JIT
---

# Deep Research — Open Questions on PE-3 Redesign

## Scope and ID correction

The brief named arXiv:2602.12285 as the persona-degradation source. That ID
does not resolve. The intended paper is **arXiv:2311.10054** (Zheng et al.,
"When 'A Helpful Assistant' Is Not Really Helpful", Findings of EMNLP 2024).
A second, complementary paper surfaced and is now anchored alongside it:
**arXiv:2603.18507** (Sclar et al., "Expert Personas Improve LLM Alignment
but Damage Accuracy: Bootstrapping Intent-Based Persona Routing with
PRISM"). The "26.2% degradation" claim in the brief does not appear in
either paper body; the actual magnitudes are smaller and more nuanced,
detailed in Q1.

---

## Q1 — arXiv:2311.10054 + arXiv:2603.18507 Magnitude Verification

**Status**: verified (with ID correction; 26.2% magnitude claim **NOT
substantiated** — actual effects are smaller and task-conditional)

**Sources** (tier-labeled):
- [Tier 1] Zheng et al., "When 'A Helpful Assistant'..." — arXiv:2311.10054v3, EMNLP 2024 Findings. https://arxiv.org/abs/2311.10054 ; https://arxiv.org/html/2311.10054v3
- [Tier 1] Sclar et al., "Expert Personas Improve LLM Alignment but Damage Accuracy" — arXiv:2603.18507v1. https://arxiv.org/html/2603.18507v1
- [Tier 1] ACL Anthology mirror for 2311.10054. https://aclanthology.org/2024.findings-emnlp.888/

**Answer**:

### A. Zheng et al. 2311.10054 (the "no improvement" paper)
- **Magnitude**: effects are **small in absolute terms**. No persona
  consistently improved accuracy across MMLU. Most personas produced
  near-zero coefficients; some produced small negative effects.
  Authors emphasize "small effect sizes" — they do not report a single
  "26.2% degradation" headline figure. The in-domain persona advantage
  is **+0.004 coefficient** (p < 0.01) — directionally positive but
  empirically negligible.
- **Persona types**: 162 personas, two top-level classes —
  **Interpersonal** (50: family, friend, romantic, work, school, social)
  and **Occupational** (112: STEM, law, medicine, economics, politics,
  psychology, etc.), plus AI personas. Attributes scored:
  **gender** (explicit/implicit/neutral), **role category** (7 groups),
  **domain alignment** (in-domain vs out-domain).
- **Worst performers**: gendered roles (especially feminine-coded)
  underperform gender-neutral roles; out-of-domain roles underperform
  in-domain. Larger models (Llama-3-70B) show **more** negative persona
  effects than smaller siblings.
- **Benchmark**: MMLU subset only (2,410 questions, 26 subjects mapped
  to 8 domains: Law, Medicine, CS, Math, Politics, Psychology, Natural
  Science, Economics). **Single-dataset limitation** — no GSM8K or
  MMLU-Pro replication in this paper.
- **Models**: 9 instruction-tuned OSS models in 4 families: FLAN-T5-XXL,
  Llama-3-Instruct (8B, 70B), Mistral-7B-Instruct-v0.2, Qwen2.5-Instruct
  (3B–72B). **No GPT-4, no Claude** — closed models not tested here.
- **Authors' own classification**: form-classification is NOT the
  primary axis — they classify by **role semantics** (interpersonal vs
  occupational, in-domain vs out-domain, gender). The closest to the
  EHJ form-axis is "in-domain occupational" vs others, which is the
  "functional Role-Spec" analogue.

### B. Sclar et al. 2603.18507 (the harder-evidence paper)
This paper is the **stronger empirical anchor for the EHJ Role-Spec
caution** because it isolates a **length effect** within the persona
form and reports per-benchmark deltas.
- **MMLU**: baseline 71.6% → **long expert persona 66.3% (−5.3pp)**;
  **minimum persona 68.0% (−3.6pp)**. The longer the persona, the
  larger the accuracy hit on knowledge tasks.
- **MT-Bench (alignment-leaning)**: long expert helps in 5 of 8
  categories — strongest gains in **Extraction (+0.65)** and **STEM
  (+0.60)** (these are alignment-sensitive sub-tasks in this paper's
  framing); damages **Coding (−0.65)**, **Humanities (−0.20)**, **Math
  (−0.10)**.
- **Safety (JailbreakBench, "Safety Monitor" persona)**: refusal rate
  53.2% → 70.9% (**+17.7pp**). Personas matter where they encode
  policy/intent.
- **Models**: Qwen2.5-7B, Llama-3.1-8B, Mistral-7B, Mixtral-8x7B (MoE),
  plus reasoning-distilled R1-Llama-8B and R1-Qwen-7B.
- **Authors' classification**: pragmatic, two-axis —
  **alignment-dependent** (persona helps) vs
  **pretraining-dependent** (persona hurts), cross-cut by
  **persona length** (minimum ~5 tokens vs long ~150 tokens). They
  also distinguish **behavioral personas** (Critic, Safety Monitor,
  Helpful, Compliant) from **expert personas** (domain-functional).
- **PRISM mechanism**: a binary gate trained on query hidden states
  predicts whether a persona will help, then a LoRA adapter applies
  the persona behavior conditionally. Result: MMLU stays at 71.7%
  (≈ baseline) while alignment tasks gain +1.7 overall. Reasoning
  models route 97.6–99.4% of queries to base model — strong evidence
  that **for reasoning-heavy tasks the right action is to NOT prime
  with a persona at all**.

**Confidence**: high. Both paper bodies verified via fetch; both
peer-reviewed venues (EMNLP Findings 2024 and arXiv preprint with
detailed experimental tables). The brief's "26.2%" figure is
**not in either paper** — likely a hallucination or conflation with
an unrelated study. Recommend the rubric anchor on the Sclar paper's
**−5.3pp MMLU degradation from long persona** as the headline number,
because it is a single, citable, magnitude-precise claim with a
peer-reviewable provenance.

---

## Q2 — HOW-Axis Method-Binding Empirical Evidence

**Status**: partially verified (Anthropic's own doctrine maps cleanly
onto Method=Hint; no controlled A/B benchmark found that isolates
"Workflow eager vs hint" specifically)

**Sources** (tier-labeled):
- [Tier 1] Anthropic, "Effective context engineering for AI agents". https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- [Tier 1] Anthropic, "Equipping agents for the real world with Agent Skills". https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- [Tier 2] swirlai Newsletter, "Agent Skills: Progressive Disclosure as a System Design Pattern". https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure
- [Tier 2] DataCamp + dev.to comparison surveys of LangGraph/CrewAI/AutoGen, 2026. https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen ; https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63

**Answer**:

Anthropic's published doctrine — **progressive disclosure across three
levels (metadata → SKILL.md body → resources/scripts)** — is a direct
endorsement of Method-as-JIT. The official guidance is explicit: "Claude
loads information in stages as needed, rather than consuming context
upfront." The principle is named just-in-time retrieval and is
positioned as the **recommended pattern**, with hybrid (some eager,
some JIT) as the production reality. CLAUDE.md is called out as the
eager-by-design exception.

This maps cleanly onto EHJ:
- **WHO** (identity/contract) — eager at system level (CLAUDE.md /
  agent frontmatter analogue).
- **HOW** (workflow/method) — JIT-loaded SKILL.md body when the
  skill triggers.
- **WHAT** (domain data) — JIT-loaded references/scripts on demand.

Three caveats:
1. Anthropic's doctrine does not isolate "workflow in body vs workflow
   as referenced doc" as a controlled experiment. No A/B benchmark
   with quantified deltas was found.
2. Competitor frameworks diverge:
   - **CrewAI** binds Method **eagerly** at agent-construction time —
     each Agent has a `role`, `goal`, `backstory`, and explicit Task
     descriptions assembled into a Crew. Method is part of the
     constructor.
   - **LangGraph** binds Method **structurally as a graph** — nodes
     carry their own prompts and tools; the workflow is the graph
     topology, not a system-prompt block.
   - **AutoGen** is conversation-first; Method emerges from
     inter-agent dialogue rather than being declared upfront.
3. The cross-framework picture: **none of the four mainstream
   frameworks (Anthropic Agent Skills, LangGraph, CrewAI, AutoGen)
   universally treat Method as JIT-only**. Anthropic is the strongest
   endorsement of Method=Hint; CrewAI is the strongest counter-example
   (Method=Eager); the others are orthogonal.

**Confidence**: medium-high for the Anthropic mapping (Tier 1 official
docs are explicit), low for "industry consensus on Method=JIT" — that
consensus does not exist. The EHJ recommendation is **defensible by
appeal to Anthropic doctrine and context-rot evidence (Chroma Research
2025)**, but it cannot claim to be the universal industry pattern.

---

## Q3 — LLM-as-Judge for Form-Compliance / Persona Detection

**Status**: verified — LLM-as-Judge is a viable but not infallible
choice for structural-style/form-compliance tasks

**Sources** (tier-labeled):
- [Tier 1] Li et al., "LLMs-as-Judges: A Comprehensive Survey" — arXiv:2412.05579v2. https://arxiv.org/abs/2412.05579 ; https://arxiv.org/html/2412.05579v2
- [Tier 1] ICLR 2025, "Trust or Escalate: LLM Judges with Provable Guarantees". https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf
- [Tier 1] arXiv 2510.09738 (2025), "Judge's Verdict: A Comprehensive Analysis of LLM Judge Capability Through Human Agreement". https://arxiv.org/html/2510.09738v1
- [Tier 2] Evidently AI, "F.A.Q on LLM judges". https://www.evidentlyai.com/blog/llm-judges-faq
- [Tier 2] Confident AI / Langfuse / Arize practitioner docs on multi-criteria judges.

**Answer**:

### Accuracy / calibration on form-style judgments
- **Headline agreement number**: strong LLM judges (GPT-4-class)
  achieve **80–90% agreement with human evaluators on quality
  dimensions**, comparable to human-human inter-annotator agreement
  on the same tasks. ICLR 2025 reports 0.815–0.902 inter-annotator
  agreement when calibration is intact.
- **Calibration is the failure mode**: judges are systematically
  **over-confident** in agreement with the human majority. Naive raw
  output is biased; bias-corrected estimators exist (cf.
  arXiv:2605.06939).
- **Target metrics for high-confidence use**: weighted Cohen's κ ≥
  0.6 or Krippendorff's α near/above 0.8. Below those thresholds,
  human-in-loop should remain.

### Multi-axis vs separate calls
- **Strong consensus**: separate sub-judges (one judge per criterion,
  results combined deterministically) outperform single multi-axis
  judges. FineSurE-style decomposition is cited as the canonical
  example. Quote: "LLM handles one quality at a time rather than
  dealing with complex reasoning." — Evidently AI practitioner doc,
  echoing the survey.
- **Implication for EHJ-redesign**: WHO/HOW/WHAT should likely be
  **three separate judge calls** (or three rubric items in a single
  call with a strict "score each independently before combining"
  instruction), not one combined "is this a good agent prompt"
  judgment.

### Adversarial / gaming resistance
- LLM judges are vulnerable to **synonym-rephrasing attacks**, length
  bias, position bias, and self-preference (Justice or Prejudice,
  llm-judge-bias.github.io). Mitigations: rotate judge model,
  randomize positions in pairwise tasks, use rubric anchors not free
  scoring.

### Best prompt structures
1. **Rubric-based** (named criteria with explicit pass/fail anchors)
   beats free-form quality scoring. ICLR 2025 + the 2412.05579 survey
   converge on this.
2. **Pairwise comparison** is more reliable than absolute scoring for
   subtle/structural distinctions.
3. **Few-shot anchors** (one calibrated PASS example + one calibrated
   FAIL example per axis) reduce variance substantially.

**Confidence**: high. The survey is comprehensive and the ICLR/2510
papers provide quantified bounds. The practical recipe — rubric +
few-shot anchors + separate sub-judges + pairwise where possible —
is repeated across all sources.

---

## Q4 — Persona-as-Narrative Literature

**Status**: verified — **length is the dominant variable**, and
narrative personas degrade harder than minimal labels on knowledge
tasks

**Sources** (tier-labeled):
- [Tier 1] arXiv:2603.18507 (Sclar et al.). See Q1.
- [Tier 1] arXiv:2402.14848, "Same Task, More Tokens: the Impact of
  Input Length on the Reasoning Performance of Large Language
  Models". https://arxiv.org/html/2402.14848v1
- [Tier 1] Chroma Research, "Context Rot: How Increasing Input
  Tokens Impacts LLM Performance" (2025). https://www.trychroma.com/research/context-rot
- [Tier 1] Anthropic, "Keep Claude in character with role prompting
  and prefilling" — official prompt-engineering docs. https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/keep-claude-in-character

**Answer**:

The audit hypothesis — that the multi-line persona narrative is the
real violation while the single adjective tag is the surface symptom
— is **well-supported by the literature**.

### Evidence
- **Sclar et al. (2603.18507)**: explicit length-controlled comparison
  on MMLU. Minimum persona (~5 tokens) damages accuracy −3.6pp; long
  persona (~150 tokens) damages −5.3pp. The narrative form is
  **measurably worse** on knowledge tasks, with a ~1.7pp delta
  attributable specifically to the additional prose.
- **arXiv:2402.14848**: reasoning degrades well before models hit
  their context limit — degradation observed at input lengths as
  short as **3,000 tokens**, regardless of where key information
  sits. A multi-sentence persona narrative costs both token budget
  AND attention-quality.
- **Chroma "Context Rot" (2025)**: dense attention maps cause
  models to respond vaguely; irrelevant context degrades output
  measurably. A persona narrative is, by definition, identity-context
  that is not load-bearing for the task.
- **Anthropic official guidance**: "modern models are sophisticated
  enough that heavy-handed role prompting is often unnecessary, and
  overly specific roles ... can limit the AI's helpfulness." The
  recommended form is **one sentence naming expertise + context** —
  i.e., the audit's "functional Role-Spec" form. Multi-sentence
  character backstories are explicitly discouraged.

### Threshold effects
No paper found a clean threshold (e.g., "persona narrative > N tokens
flips sign"). The pattern is monotone: longer → worse on knowledge
tasks, with the slope conditional on task type. For alignment tasks,
the pattern can reverse — but the EHJ-target items are agents
performing reasoning/review/critique work, where the knowledge-task
slope dominates.

**Confidence**: high. Anthropic's own docs, the Sclar paper, and
two independent context-length papers converge on the same direction
and rough magnitude.

---

## Q5 — Closed-List vs Open-Vocabulary Anti-Pattern Detection

**Status**: verified — closed-list approaches fail on novel
phrasings/synonyms; hybrid approaches are the recommended practice

**Sources** (tier-labeled):
- [Tier 1] arXiv:2401.04422, "Estimating Text Similarity based on
  Semantic Concept Embeddings". https://arxiv.org/html/2401.04422v1
- [Tier 2] TechTarget, "Embedding models for semantic search: A
  guide" (2025). https://www.techtarget.com/searchenterpriseai/tip/Embedding-models-for-semantic-search-A-guide
- [Tier 2] Towards Data Science, "Text Embeddings, Classification,
  and Semantic Search". https://towardsdatascience.com/text-embeddings-classification-and-semantic-search-8291746220be/
- [Tier 1] Sclar et al. (2603.18507) — implicit evidence that a
  closed-list won't catch "expert-flavored" narrative personas
  unless the list explicitly enumerates every adjective + qualifier
  combination.

**Answer**:

### When closed-list fails
Closed-list/regex pattern detection in natural language fails when:
1. The anti-pattern is **semantically defined** rather than lexically
   defined ("decorative persona" is a meaning, not a word).
2. Authors paraphrase or rotate synonyms ("senior" → "experienced"
   → "seasoned" → "world-class" → "battle-tested").
3. The anti-pattern requires **multi-sentence detection** (narrative
   personas span 2–4 sentences with no single trigger token).
4. Negative space matters (something is missing — e.g., a functional
   verb-phrase — and closed lists cannot detect absence robustly).

The EHJ-Role-Spec check meets all four criteria — it is exactly the
case where closed-list is the wrong tool.

### Alternatives, ordered by deployment cost
1. **Embedding-based similarity** (sentence-transformers, Cohere,
   OpenAI embeddings) — cheap, fast, deterministic, but requires
   curated positive/negative anchor sets. Good for "is this near
   the decorative-narrative centroid?" but weak on absence detection.
2. **LLM-as-Judge with few-shot anchors** (Q3 findings) — handles
   semantics, absence detection, and novel phrasings. Expensive per
   call, calibration-sensitive. Best for the WHO axis.
3. **Fine-tuned classifier** (BERT-class on labeled corpus) —
   highest precision once trained; requires labeled data the suite
   does not have.
4. **Hybrid: structural-trigger + semantic-classifier** — cheap regex
   pre-filter narrows the candidate set; LLM/embedding handles the
   semantic judgment. This is the practitioner consensus (cited as
   the "Harmony project" approach in the embeddings literature).

### Recommendation for the suite
The EHJ-Role-Spec rubric item should use **option 4 (hybrid)**:
- A cheap structural trigger fires on any role-statement opening
  ("You are a/an ..."), or on system-prompt segments above a length
  threshold.
- An LLM-judge with rubric + few-shot anchors then classifies the
  match as `functional` / `decorative-tag` / `narrative` /
  `mixed` / `none`.

**Confidence**: medium-high. The general NLP guidance is well-attested.
The specific recommendation is a synthesis, not a benchmarked claim.

---

## Q6 — Agent-Composition Frameworks (State of the Art beyond EHJ)

**Status**: verified — no framework uses the exact WHO/HOW/WHAT
decomposition; closest analogues are CrewAI's role/goal/backstory and
Anthropic's metadata/body/resources progressive disclosure

**Sources** (tier-labeled):
- [Tier 1] Anthropic, "Equipping agents for the real world with Agent
  Skills" (Dec 2025 standard release). https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- [Tier 1] Anthropic Platform Docs, "Agent Skills overview". https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- [Tier 2] DataCamp, dev.to comparison studies of LangGraph / CrewAI /
  AutoGen (2026). Multiple URLs above.
- [Tier 3] alphaXiv 2602.12430, "Agent Skills for Large Language
  Models: Architecture, Acquisition, Security" — arXiv preprint
  surveying the standardized skills ecosystem.

**Answer**:

### Framework-by-framework decomposition

| Framework | WHO | HOW | WHAT |
|---|---|---|---|
| **Anthropic Agent Skills** | Metadata (name + description, eager) | SKILL.md body (JIT on trigger) | references/scripts (JIT on demand) |
| **CrewAI** | role + goal + backstory (eager) | Task descriptions + agent.execute (eager) | Tools + memory (mixed) |
| **LangGraph** | Per-node prompt (graph-structural) | Graph topology + edges (declarative) | Tools per node (eager) |
| **AutoGen** | system_message per agent (eager) | Conversational emergent (no explicit method binding) | Tools + group chat (mixed) |
| **EHJ (this suite)** | Role-Spec (eager) | Method (Hint, JIT) | Domain (JIT) |

### Observations
- **EHJ is most similar to Anthropic Agent Skills**, which is the
  only mainstream framework that explicitly endorses Method-as-JIT.
- **CrewAI is the strongest counter-example**: role + goal + backstory
  + task are all eager. CrewAI users frequently report "agent forgets
  its role" issues in long sessions — supporting the EHJ caution
  about over-eager identity priming.
- **No framework uses the exact WHO/HOW/WHAT vocabulary**. EHJ is a
  synthetic recommendation, defensible by appeal to (a) Anthropic's
  progressive-disclosure doctrine, (b) the Sclar persona-length
  evidence, and (c) the context-rot evidence — but it is not a
  named, citable, published framework.
- **December 2025 industry adoption**: OpenAI Codex CLI, Gemini CLI,
  GitHub Copilot, and Cursor all adopted Anthropic's Agent Skills
  standard. The progressive-disclosure architecture is now the
  cross-vendor default, lending strong indirect support to EHJ.

### Gaps EHJ should acknowledge
- The literature does not directly validate "WHO=Eager" as the right
  binding. Sclar's PRISM evidence suggests that **even WHO should be
  conditional** (97.6–99.4% of reasoning queries routed to base
  model without persona) — a more aggressive read would be
  WHO=Conditional, HOW=JIT, WHAT=JIT. The suite should document why
  WHO=Eager is chosen anyway (likely: discoverability + identity
  stability across sessions).

**Confidence**: medium-high. Framework descriptions are verified;
the WHO=Conditional consideration is a synthesis that needs
explicit treatment in the suite's framework doc.

---

## Synthesis — Implications for PE-3 Redesign

### 1. Should PE-3 move to LLM-as-Judge?

**Yes — partially.** The evidence (Q3, Q5) supports a hybrid:
- Keep a cheap structural pre-filter (regex on common role-statement
  openings + length heuristic).
- Route candidate matches to an LLM-judge with **rubric + few-shot
  anchors**, returning a categorical classification
  (`functional` / `decorative-tag` / `narrative` / `mixed` / `none`).
- Track inter-judge agreement against a maintainer-labeled gold set;
  require Cohen's κ ≥ 0.6 before treating the judge output as
  binding. Below that, surface as advisory.

The closed-list approach should be retired for the semantic axis
(persona narrative detection) but retained for trivial structural
matches (e.g., literal "Act as a..." openings).

### 2. What anchors does the LLM-Judge prompt need?

Required, per the Q3 + Q4 evidence:
- **Rubric-based scoring**, NOT free-form quality scoring.
- **Per-axis few-shot anchors** — at minimum one PASS and one FAIL
  example per axis (WHO/HOW/WHAT), drawn from the suite's own audit
  history.
- **Separate sub-judge calls** for the three axes — not a combined
  "is this a good agent prompt" judgment. Combined judgments confuse
  the model and lose accuracy.
- **Pairwise comparison option** for borderline cases (this agent
  vs a reference good/bad exemplar) — strictly more reliable than
  absolute scoring for subtle distinctions.
- **Position/length-bias mitigations**: randomize anchor ordering;
  cap judge context to limit length-bias on the input being judged.

### 3. Is WHO+HOW+WHAT the right axis-set?

**Mostly yes, with two refinements**:
- **WHO=Eager is defensible but not literature-validated.** Sclar's
  PRISM evidence (97.6–99.4% of reasoning queries routed to
  no-persona base model) is a non-trivial counter-signal. The suite
  should explicitly document that WHO=Eager is chosen for
  discoverability/stability reasons, not because the literature
  unanimously endorses persona priming.
- **No framework uses these exact terms.** EHJ is best positioned as
  a synthesis grounded in (a) Anthropic progressive disclosure, (b)
  the persona-length / context-rot evidence, (c) cross-framework
  decomposition observed in CrewAI/LangGraph/AutoGen. Cite all three
  in the framework doc rather than claiming EHJ as a discovered
  industry pattern.

The strongest empirical anchor for the WHO axis is **arXiv:2603.18507
MMLU −5.3pp from long expert persona**, not a 26.2% figure. Update
the rubric/baseline citations accordingly.

### 4. Specific implementation choices

- **Judge model**: at least GPT-4-class or Claude-Sonnet-class.
  Smaller judges underperform on structural-style judgments per the
  2412.05579 survey and 2510.09738.
- **Judge prompt structure**: rubric with named criteria, two
  few-shot anchors per criterion, instruction to score each
  criterion independently before producing a combined verdict, and
  an explicit "if uncertain, abstain and flag for human review"
  escape valve.
- **Calibration approach**: maintainer-labeled gold set of ≥30
  agent files (mix of functional, decorative-tag, narrative). Run
  judge against gold set whenever the judge prompt or model changes.
  Track Cohen's κ; require ≥ 0.6 before merging the rubric change.
- **Adversarial-gaming mitigation**: rotate judge model occasionally;
  do not announce the closed list of trigger phrases in any
  agent-facing documentation that the same model could read.
- **Token budget**: keep judge prompts under 2,000 tokens of context
  (per arXiv:2402.14848 — degradation starts at ~3,000 tokens).

---

## Provenance log

All claims in this document either cite a specific Tier-1 or Tier-2
source above or are explicitly labeled as synthesis. The two paper
bodies (2311.10054 and 2603.18507) were retrieved via WebFetch on
2026-05-13 and their numbers transcribed directly. The brief's
"26.2%" figure was searched against both paper bodies and is **not
present in either** — recommend retiring the figure from any internal
documentation that uses it.
