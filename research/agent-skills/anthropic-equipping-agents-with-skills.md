---
last_refreshed: 2026-04-04
---

# Equipping Agents for the Real World with Agent Skills

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Single source - Claude Blog, "Equipping agents for the real world with agent skills"
- Last reviewed: 2026-04-03

**Source:** [Claude Blog](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
**Fetched:** 2026-03-24

## What Makes a Good Skill

A skill requires a `SKILL.md` file with YAML frontmatter containing `name` and `description` metadata. The description is critical — Claude uses it to decide whether to activate the skill. "Claude will use these when deciding whether to trigger the skill in response to its current task," making clear, accurate naming essential for proper skill discovery.

Example: The PDF skill bundles a core `SKILL.md` with related files (`reference.md`, `forms.md`) that Claude accesses only when needed.

## Best Practices

### Evaluation-First Approach
"Identify specific gaps in your agents' capabilities by running them on representative tasks and observing where they struggle or require additional context."

### Progressive Layering
Start with lean core documentation, then split into separate files when content becomes unwieldy. "If certain contexts are mutually exclusive or rarely used together, keeping the paths separate will reduce the token usage."

### Iterative Refinement
"Ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill." This collaborative development reveals what agents actually need versus anticipated requirements.

### Perspective-Taking
Monitor real usage patterns rather than assuming optimal structure upfront.

## Progressive Disclosure (Context Engineering)

Skills implement a hierarchical information architecture mirroring "a well-organized manual that starts with a table of contents, then specific chapters, and finally a detailed appendix."

This design ensures "agents don't need to read the entirety of a skill into their context window when working on a particular task," making "the amount of context that can be bundled into a skill effectively unbounded."

### How It Works
1. Pre-load skill metadata (names/descriptions) into system prompt
2. Load full `SKILL.md` when Claude deems the skill relevant
3. Access supplementary files on-demand via code execution

## Quality Criteria

### Security
"Install skills only from trusted sources" and thoroughly audit code dependencies and external network connections before deployment.

### Structural Patterns
- Use code for deterministic operations (form extraction, sorting) rather than token generation
- Bundle executable scripts alongside documentation
- Keep instructions and code clear about when Claude should execute versus read-as-reference

### Documentation Quality
The `name` and `description` serve as discovery mechanisms — they must accurately convey skill scope without loading full context unnecessarily.

---

## 2026-04-04 Update

Sources: 12 Tier 1 sources (Anthropic platform docs current 2026, Anthropic Engineering blog March 2026, arXiv papers AAAI 2026 / ICLR 2026 / ICSE 2026 venues). Delta basis: existing file fetched 2026-03-24.

---

### Finding 1: Agent Skills Specification Extended

**Status:** EXTENDS
**Source:** [Anthropic Platform Docs — Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) (Tier 1, fetched 2026-04-04)
**Key finding:** The official specification has expanded significantly since the blog post. Skills now operate across four surfaces — Claude.ai, Claude API, Claude Code, and Claude Agent SDK — each with different constraints: the API surface has no network access and no runtime package install; Claude Code has full network access. Custom Skills can be uploaded via `/v1/skills` endpoints for workspace-wide API sharing (requires beta headers `code-execution-2025-08-25`, `skills-2025-10-02`, `files-api-2025-04-14`). Frontmatter constraints are now formalized: `name` max 64 chars, lowercase+hyphens+numbers only, cannot contain "anthropic" or "claude"; `description` max 1024 chars, non-empty, no XML tags. The three-level progressive disclosure token budgets are now explicit targets: Level 1 metadata ~100 tokens (always loaded), Level 2 instructions <5k tokens (loaded on trigger), Level 3+ resources effectively unlimited (loaded via bash on demand). [Engineering guidance]
**Relevance to skill writing:** The 100-token metadata budget and <5k instruction budget are now concrete targets for Level 1/2 content. Skills should degrade gracefully when network access is unavailable, since API and some Claude.ai surfaces restrict it.

---

### Finding 2: Planner-Generator-Evaluator Harness Architecture

**Status:** NEW
**Source:** [Anthropic Engineering — Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) (Tier 1, March 2026)
**Key finding:** A three-agent GAN-inspired architecture addresses a core self-evaluation failure: agents "confidently praise their own work even when quality is obviously mediocre." The Planner converts briefs to specifications; the Generator implements iteratively; the Evaluator tests against objective criteria using Playwright or equivalent. Before each sprint, Generator and Evaluator negotiate testable "done" criteria (e.g., 27 explicit criteria for a level editor sprint), preventing the failure mode of marking features complete without verification. A key simplification principle: "Every component in a harness encodes an assumption about what the model can't do on its own" — as models improve, remove components. Cost/quality tradeoff is real: solo agent runs in 20 min/$9 but produces broken output; full harness takes 6 hrs/$200 but is functional. [Engineering guidance]
**Relevance to skill writing:** Skills that orchestrate multi-step workflows can apply the generator-evaluator separation. Output format specifications in skill instructions benefit from explicit, testable acceptance criteria rather than qualitative descriptions.

---

### Finding 3: Agent SDK Hooks — 19-Event System

**Status:** NEW
**Source:** [Anthropic Platform Docs — Agent SDK Hooks](https://platform.claude.com/docs/en/agent-sdk/hooks) (Tier 1, fetched 2026-04-04)
**Key finding:** The Agent SDK hooks system has 19 events, substantially beyond the 6 previously documented for Claude Code: PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStart, SubagentStop, PreCompact, PermissionRequest, SessionStart, SessionEnd, Notification, Setup, TeammateIdle, TaskCompleted, ConfigChange, WorktreeCreate, WorktreeRemove. PreToolUse hooks return `permissionDecision: "allow" | "deny" | "ask"` — deny takes priority over ask, which takes priority over allow when multiple hooks conflict. Hooks can rewrite tool inputs via `updatedInput` (e.g., redirect file writes to sandbox paths). Subagents do NOT inherit parent permissions. Side-effect hooks (logging, webhooks) use `{ async: true }` to avoid blocking. Multiple hooks execute in array order, enabling layered security (rate limiter → authorization → sanitizer → logger). [Engineering guidance]
**Relevance to skill writing:** The `allowed-tools` frontmatter field maps to the PreToolUse permission model. Subagent permission isolation is critical for skills that spawn subagents; do not assume parent-granted permissions propagate.

---

### Finding 4: Role Assignment Causes Performance Degradation

**Status:** NEW (revised 2026-05-13 after paper-body verification)
**Sources:**
- [arXiv 2603.18507](https://arxiv.org/abs/2603.18507) — "Expert Personas Improve LLM Alignment but Damage Accuracy: PRISM" (Tier 1, 2026)
- [arXiv 2311.10054v3](https://arxiv.org/abs/2311.10054) — Zheng et al., "When 'A Helpful Assistant' Is Not Really Helpful" (Tier 1, EMNLP 2024 Findings)

**Key finding:** Length-controlled MMLU evidence from Sclar et al. (2603.18507): minimum persona (~5 tokens) damages baseline 71.6% → 68.0% (−3.6pp); long expert persona (~150 tokens) damages 71.6% → 66.3% (−5.3pp). Effect monotone with persona length. MT-Bench (alignment-leaning) shows reversed direction: long expert helps Extraction +0.65, STEM +0.60, but damages Coding −0.65 / Humanities −0.20 / Math −0.10. Safety Monitor persona increases refusal rate +17.7pp. The PRISM mechanism routes 97.6–99.4% of reasoning queries to no-persona base model — strong evidence that reasoning-heavy tasks should NOT prime with persona. Cross-validated by Zheng et al. (2311.10054v3) across 162 personas, 9 OSS models — directionally consistent (gendered roles and out-of-domain roles underperform), absolute effects small. [Proven result]

**Note on earlier "26.2% degradation" claim:** earlier versions of this finding cited arXiv:2602.12285 with a 26.2% magnitude. That arXiv ID does not resolve and the 26.2% figure is not present in either Sclar or Zheng paper bodies. The defensible headline number is Sclar's MMLU −5.3pp; corrected 2026-05-13.
**Relevance to skill writing:** Skill system prompts and agent descriptions should use functional role definitions (e.g., "code reviewer focused on security vulnerabilities") rather than demographic or broad expert personas. If a skill performs both generative and discriminative tasks, consider task-type-conditional role framing.

---

### Finding 5: Skill Composition at Ecosystem Scale

**Status:** NEW
**Sources:**
- [arXiv 2603.02176](https://arxiv.org/abs/2603.02176) — "Organizing, Orchestrating, and Benchmarking Agent Skills at Ecosystem Scale" (Tier 1, 2026)
- [arXiv 2602.12430](https://arxiv.org/abs/2602.12430) — "Agent Skills for LLMs: Architecture, Acquisition, Security, Path Forward" (Tier 1, 2026)
- [arXiv 2604.01608](https://arxiv.org/abs/2604.01608) — "From Multi-Agent to Single-Agent: When Is Skill Distillation Beneficial?" (Tier 1, April 2026)

**Key finding:** DAG-based skill orchestration substantially outperforms flat invocation with identical skill sets; tree-based retrieval effectively approximates oracle skill selection at ecosystem scale (200 to 200K skills). 26.1% of community-contributed skills contain vulnerabilities, motivating four-tier provenance-based governance with gate-based permission models. A phase transition exists in large libraries: beyond a critical size, skill selection accuracy degrades sharply, requiring hierarchical organization. Multi-agent systems can be distilled into single-agent skill libraries with up to 8x cost reduction and 15x latency improvement; distillation success depends on metric topology (rigid vs. free metrics), not task type — skill lift ranges from +28% to -2%. [Proven result]
**Relevance to skill writing:** Design skills for DAG-based composition, not only standalone invocation. Audit community skills for security. Libraries beyond ~200 skills need hierarchical categorization to avoid selection degradation.

---

### Finding 6: Least-Privilege Tool Grants Are Practical

**Status:** NEW
**Sources:**
- [arXiv 2512.11147](https://arxiv.org/abs/2512.11147) — "MiniScope: Least Privilege Framework for Tool-Calling Agents" (Tier 1, Dec 2025)
- [arXiv 2601.08012](https://arxiv.org/abs/2601.08012) — "Towards Verifiably Safe Tool Use for LLM Agents" (Tier 1, ICSE NIER 2026)

**Key finding:** MiniScope reconstructs permission hierarchies from tool call relationships using a mobile-style permission model, incurring only 1-6% latency overhead versus standard tool-calling agents while significantly outperforming LLM-based permission baselines. A complementary approach applies STPA (System-Theoretic Process Analysis) to derive safety requirements as enforceable specifications on data flows and tool sequences, proposing capability-enhanced MCP with explicit confidentiality classifications and trust levels. Both approaches reframe agent autonomy as a deliberate design choice with formal guarantees rather than an emergent property. [Proven result]
**Relevance to skill writing:** The `allowed-tools` frontmatter field is a manual least-privilege mechanism consistent with MiniScope's model. The 1-6% overhead result validates that automatic least-privilege enforcement is practical. Skills accessing sensitive data should declare the minimum tool set required.

---

### Finding 7: Reliability — ICLR 2026 Confirmation

**Status:** CONFIRMS
**Source:** [arXiv 2510.22620](https://arxiv.org/abs/2510.22620) — "Breaking Agent Backbones" (Tier 1, ICLR 2026)
**Key finding:** Published at ICLR 2026, this paper confirms brittleness findings from existing ReliabilityBench research at a top venue. No contradictions with existing reliability guidance were found. Previously documented patterns remain valid: circuit breaker three-state pattern, exponential backoff with jitter (60-80% retry storm reduction), progressive fallback (self-correct → fallback → degrade → escalate), idempotency keys for all writes. [Proven result]
**Relevance to skill writing:** Existing reliability recommendations in this file are confirmed. No changes required to error handling guidance.

---

### Delta Summary

| Area | Status | Key delta |
|------|--------|-----------|
| Skills specification | EXTENDS | Cross-surface availability, API upload endpoint, token budgets formalized (100 / <5k / unlimited) |
| Agent harness | NEW | Planner-generator-evaluator, sprint contracts, simplification principle, cost/quality data |
| SDK hooks | NEW | 19 events (vs. 6 previously), permission priority model, subagent isolation, async hooks |
| Role assignment | NEW | MMLU −5.3pp from long expert persona (Sclar 2603.18507, length-controlled); reasoning queries route 97.6–99.4% to no-persona base; effects task-type-dependent |
| Skill composition | NEW | DAG outperforms flat; 26.1% community skills vulnerable; phase transition in large libraries; 8x/15x distillation gains |
| Least privilege | NEW | MiniScope 1-6% overhead; STPA formal safety; capability-enhanced MCP |
| Reliability | CONFIRMS | ICLR 2026 publication; no contradictions with existing guidance |
