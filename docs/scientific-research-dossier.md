# Scientific Research Dossier for `review-claude-config`

Evidence-first research baseline for the repository itself. `review-claude-config` is a meta-skill system for Claude Code managed repositories, so its design claims need stronger provenance and clearer certainty labels than a normal prompt-only repo.

## Method

- Scope: research themes already present in [`research/`](../research), plus the runtime and guidance surfaces that operationalize those themes in `skills/`, `hooks/`, `README.md`, `CLAUDE.md`, `docs/skills/`, and `docs/evidence-maintenance.md`.
- Source policy:
  - Tier 1: official Anthropic / Claude Code docs, official vendor docs, RFCs / specs, peer-reviewed papers, benchmark papers, and primary arXiv papers when no reviewed version is available.
  - Tier 2: engineering blogs or case studies with concrete technical detail and methodology.
  - Tier 3: supplementary community material only when needed for terminology or examples.
- Classification: use only the canonical classes defined in [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md).
- Contradiction handling: when local summaries and fresher primary sources diverge, the stronger source wins and the contradiction must be recorded explicitly.

## Freshness and Maintenance

- This dossier is a supporting interpretation artifact, not a canonical contract file.
- Follow the evidence-layer maintenance process defined in [`evidence-maintenance.md`](evidence-maintenance.md).
- Local `research/*` notes provide provenance metadata only. Repo-level claim interpretation remains in this dossier and in [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md).

## Contradiction Status

- No unresolved contradictions are currently recorded at the dossier layer.

## Repo Surface Covered

- Runtime review/apply layer: `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, `apply-review-findings`, `apply-skill-review-findings`, `apply-agent-review-findings`, `apply-rule-review-findings`
- Maintenance and diagnostics: `check-repo-health`, `review-analytics`, `refresh-engineering-baseline`, `sync-research-index`
- Discovery and generation: `audit-repo`, `suggest-skills`, `scaffold-skill`
- Hooks and top-level guidance: `hooks/skill_quality_gate.py`, `hooks/session_check.py`, `README.md`, `CLAUDE.md`, `docs/skills/*`, `docs/evidence-maintenance.md`
- Canonical contracts and references: `evidence-contract.md`, `review-report-contract.md`, `source-quality-criteria.md`, `engineering-baseline.md`

## Theme Matrix

| Theme | Why It Matters Here | Tier 1 Sources | Findings | Confidence | Classification | Repo Implication |
|---|---|---|---|---|---|---|
| Context engineering principles | Core design basis for retrieval, batching, and context discipline | Anthropic, "Effective context engineering for AI agents"; Claude Code docs; arXiv:2507.13334 | Focused context, JIT retrieval, and disciplined context management are first-order design concerns for agent quality. | High | Proven result | Keep prompt/context-first architecture as a core repo assumption. |
| Prompt engineering | Review rubric explicitly scores prompt quality | "The Prompt Report" (arXiv:2406.06608); Anthropic docs and engineering guidance | Structured outputs, role clarity, examples, and explicit constraints remain useful, but they are not the whole system. | High | Proven result | Keep prompt evaluation, but subordinate it to context and workflow design. |
| Agent skills / progressive disclosure | The repo is built around skills and references as reusable capability units | Claude blog, "Building agents with skills"; Anthropic agent-skills docs | Skills package reusable expertise and progressive disclosure via references is an endorsed pattern. | High | Engineering guidance | Keep the `SKILL.md` plus `references/` split. |
| Tool design and least privilege | Tool lists, hook behavior, and write gates are central review dimensions | Anthropic, "Writing tools for agents"; Claude Code hooks and best-practices docs | Tool descriptions, minimal loadout, and explicit boundaries materially affect agent reliability and safety. | High | Engineering guidance | Continue to enforce least privilege and explicit write confirmation. |
| Domain knowledge augmentation | The repo performs domain-specific research during review | arXiv:2601.15153; arXiv:2511.07568 | Codified procedural or domain knowledge can materially improve agent performance, especially for specialized workflows. | High | Proven result | Domain-aware review is justified, but strong domain evidence should stay distinct from heuristics. |
| Instruction following under constraints | Many review and apply prompts rely on strict output contracts | AGENTIF (arXiv:2505.16944); Claude Code docs on structured operation | Agentic systems degrade when constraints and tool contracts become ambiguous or overloaded. | Medium-High | Proven result | Output schemas and conditionals should stay explicit. |
| Claude Code project instructions and hooks | The repo is a Claude Code plugin and depends on Claude Code behaviors | Claude Code docs: best practices, hooks, slash commands, settings | `CLAUDE.md`, hooks, settings, and slash-command ergonomics are first-class Claude Code primitives. | High | Engineering guidance | Keep repo guidance aligned with current Claude Code behavior. |
| Knowledge caching / domain cache | `review-claude-config` uses a committed domain cache | Local research plus context-engineering literature; no strong direct benchmark found for this exact pattern | Reusable retrieved knowledge is plausible and often useful, but exact cache policy tradeoffs remain under-documented. | Medium | Engineering guidance | Keep cache support, but avoid overstating precise cache policies as settled science. |
| Token-efficiency principles | The repo defines token budgets and health checks | Anthropic context-engineering guidance; context-rot literature; Claude Code docs | Large, unfocused context hurts quality and latency. | Medium-High | Proven result | Retain token discipline and freshness checks. |
| Token budgets and thresholds | The repo uses concrete budget numbers and refresh thresholds | Same operational sources, but no direct benchmark for this repo’s exact constants | Exact numeric limits remain mostly local workflow choices rather than benchmark-backed law. | Medium | Repo default | Keep thresholds, but describe them as repo policy. |
| Source quality / web research credibility | The repo performs web research and persists summaries | Source-quality literature, credibility frameworks, Anthropic guidance for grounded work | Research quality depends on source filtering, recency, and cross-validation. | High | Engineering guidance | Keep `source-quality-criteria.md` central to research-consuming workflows. |
| Documentation design | This repo is heavily documentation-driven | Documentation best-practice literature; Anthropic documentation style | Discoverability, explicit rationale, and stable references improve maintainability, but duplicated prose increases drift risk. | Medium | Engineering guidance | Documentation should explain contracts, not duplicate prompt logic. |
| Repo audit signal extraction | `audit-repo` derives signals from repository characteristics | Repo-readiness and static-analysis literature | Static repository signals can guide assistant setup. | Medium | Engineering guidance | Keep repo-audit signal extraction, but scope claims carefully. |
| Architecture detection from repo structure | Used by `audit-repo` to infer architecture patterns | Architecture-detection and software-architecture mining papers | Pattern detection from source structure is a real field, but repo-specific precision varies. | Medium | Engineering guidance | Use architecture inference conservatively and mark uncertainty explicitly. |
| Analytics / path-first identity | `review-analytics` tracks changes across reports | Claude Code repo semantics + analytics design reasoning; no strong direct paper for this exact identity strategy | Path-first identity is operationally sound for repo artifacts, but it is primarily a local design choice. | Medium | Repo default | Keep path-first tracking, but document it as analytics policy rather than scientific necessity. |
| Command naming | `scaffold-skill` and slash command ergonomics rely on naming guidance | Limited empirical CLI usability literature; Claude Code slash-command docs | Direct science for Claude-style command naming remains thin. | Low-Medium | Low-evidence area | Keep naming rules lightweight and explicitly heuristic. |
| Skill gap detection | `suggest-skills` identifies missing capabilities | Little direct literature for this exact task | Opportunity detection for agent skills is useful, but direct evidence for a canonical framework is limited. | Low | Low-evidence area | Treat `suggest-skills` as heuristic discovery. |
| Primitive derivation | Mapping repo problems to CLAUDE primitives is central to `audit-repo` and `apply-audit-findings` | Limited direct literature; adjacent work in workflow and repo analysis | The exact mapping from observed repo issues to Claude-specific primitives remains a novel design layer rather than settled science. | Low | Low-evidence area | Primitive-decision matrices should be treated as evidence-informed local policy. |
| Agent definition quality benchmarks | The repo reviews agent definitions but no academic benchmark exists for this task | KDD 2025 survey (arXiv:2507.21504); ICLR 2026 Workshop (arXiv:2604.00594); arXiv:2602.16666 | No design-time benchmark exists. IRT decomposition, prompt robustness, and instruction density provide proxy evaluation dimensions. Requirements engineering quality frameworks exist as adjacent untested prior art. | Medium | Engineering guidance | New checklist items (TC-3, DA-5, AP-4) fill the gap with research-backed proxies. Composite system is Low-evidence area until validated. |
| Web scraping / WebFetch augmentation | Some research steps rely on fetching full articles beyond search snippets | Tooling docs and retrieval literature | Full-content retrieval is often needed because snippets are insufficient for evaluation-quality synthesis. | Medium | Engineering guidance | Retain WebFetch/WebSearch separation with strict filtering and attribution. |
| Hooks as quality gates | The plugin injects quality guidance and freshness warnings automatically | Claude Code hooks docs | Hooks are a supported mechanism for project and plugin lifecycle checks. | High | Engineering guidance | Keep hook guidance high-signal and lightweight. |
| Autonomous-agent reliability | The plugin runs agentic review/audit workflows whose failures are otherwise silent | MAST taxonomy (arXiv:2503.13657, kappa=0.88 inter-annotator, 94 % LLM-judge accuracy); arXiv:2602.16666 "Science of AI Agent Reliability" (12-metric decomposition); AgentIF (arXiv:2505.16944) showing <30 % perfect adherence | 14 named MAST failure modes, four architectural patterns (circuit-breaker / idempotency / progressive fallback / bounded execution), and a 10-criterion R1–R10 rubric section codified in `research/autonomous-agent-reliability/autonomous-agent-reliability.md`. Reliability is independent of raw accuracy. | High | Proven result | Safety and Context-Engineering rubric items reference MAST IDs (FM-1.2 / FM-2.3 / FM-2.6 / FM-3.1 / FM-3.2). New R10 (observability hooks) is filed against PostToolUse/SubagentStart trace surfaces. |
| Change discipline / multi-perspective review | The plugin enforces plan → review → implement → commit and dispatches 2–3 perspective agents per plan | Augment Code review-scale study (PRs <400 LOC capture 66–75 % defects); Kim/Yegge *Three Developer Loops* (IT Revolution); arXiv:2502.17086 *Mind the Blind Spots* (F1=0.126 LLM self-review weakness on novelty); Salesforce Prizm engineering blog | LLMs underweight non-technical dimensions during self-review; cross-model + cross-perspective dispatch materially mitigates. Six named agentic failure modes each map to a specific constraint mechanism (shortcuts, premature completion, review fatigue, decision delegation, knowledge loss, quality residue). | Medium-High | Engineering guidance | Justifies the "No plan without multi-perspective review" hard rule, the `reviewer.md` + `team-red.md` dispatch chain on auth/migration paths, and the SIMPLE/COMPLEX ceremony scaling in `docs/change-discipline-rule.md`. |

## Cross-Theme Findings

### Strongly Supported

- Prompt quality alone is insufficient; context management and workflow design matter materially.
- Structured outputs, explicit branching, and tool clarity improve agent reliability.
- Domain or procedural knowledge can improve specialized agent performance.
- Claude Code primitives such as `CLAUDE.md`, hooks, slash commands, and permissions are first-class surfaces and should be treated as such in this repo.

### Repo Defaults That Must Stay Explicit

- Exact token budgets, retry ceilings, and refresh thresholds are operational repo choices unless directly benchmark-backed.
- Analytics identity policy is operationally sound, but local.
- Some workflow and maintenance thresholds remain product decisions rather than scientific constants.

### Low-Evidence Zones That Must Stay Labeled

- Skill-gap detection as a formal method
- Primitive derivation from repository signals into Claude Code primitives
- Command naming rules beyond lightweight usability guidance
- Exact domain-cache policy tradeoffs

### Current Repo-State Implication

- This dossier and the gap analysis are supporting evidence narrative, not canonical contract files.
- The canonical evidence vocabulary now lives in `evidence-contract.md`.
- The canonical review/report runtime contract now lives in `review-report-contract.md`.
- Runtime hardening and heuristic-honesty work have been implemented, and bounded release validation has completed for the review, analytics, and integrity gates. The audit path has been validated through `audit-repo` plus a partially applied `apply-audit-findings` run, while the remaining release risk is the host-dependent write-approval path for mutation flows under `claude -p`.
- The remaining evidence-layer work is maintenance discipline: keep provenance fresh, record contradictions centrally, and reduce duplicated explanatory prose in later documentation cleanup.

## Source Register

### Tier 1

- Anthropic, "Effective context engineering for AI agents"  
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, "Writing tools for agents"  
  https://www.anthropic.com/engineering/writing-tools-for-agents
- Claude blog, "Building agents with skills: Equipping agents for specialized work"  
  https://claude.com/blog/building-agents-with-skills-equipping-agents-for-specialized-work
- Claude Code docs, "Best practices"  
  https://code.claude.com/docs/en/best-practices
- Claude Code docs, "Hooks" and "Hooks guide"  
  https://code.claude.com/docs/en/hooks  
  https://code.claude.com/docs/en/hooks-guide
- Claude Code docs, "Slash commands"  
  https://code.claude.com/docs/en/slash-commands
- Claude / Anthropic docs, "Choosing the right model"  
  https://docs.anthropic.com/en/docs/about-claude/models/choosing-a-model
- Schulhoff et al., "The Prompt Report" (arXiv:2406.06608)  
  https://arxiv.org/abs/2406.06608
- Mei et al., "A Survey of Context Engineering for Large Language Models" (arXiv:2507.13334)  
  https://arxiv.org/abs/2507.13334
- Qi et al., "AGENTIF: Benchmarking Instruction Following of Large Language Models in Agentic Scenarios" (arXiv:2505.16944)  
  https://arxiv.org/abs/2505.16944
- Wu et al., "Multi-Agent System Failure Taxonomy (MAST)" (arXiv:2503.13657) — 14 failure modes, kappa=0.88 inter-annotator agreement, 94 % LLM-judge accuracy  
  https://arxiv.org/abs/2503.13657
- "Towards a Science of AI Agent Reliability" (arXiv:2602.16666) — 12-metric decomposition across consistency / robustness / predictability / safety  
  https://arxiv.org/abs/2602.16666
- "Mind the Blind Spots: A Focus-Level Evaluation Framework for LLM Reviews" (arXiv:2502.17086) — F1=0.126 LLM self-review weakness on non-technical dimensions  
  https://arxiv.org/abs/2502.17086
- "How to Build AI Agents by Augmenting LLMs with Codified Human Expert Domain Knowledge?" (arXiv:2601.15153)  
  https://arxiv.org/html/2601.15153
- "Procedural Knowledge Improves Agentic LLM Workflows" (arXiv:2511.07568)  
  https://arxiv.org/abs/2511.07568

### Tier 2

- Martin Fowler, "Context Engineering for Coding Agents"  
  https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html
- Chroma Research, "Context Rot"  
  https://research.trychroma.com/context-rot
- Repository and documentation literature already summarized in local `research/*` files where no stronger primary source was found for the repo-specific design question

### Tier 1 Sources Backing Local Research Summaries

Each local `research/*` mirror file in this repo summarizes one or more canonical Tier 1 papers. The links below point to the canonical source; the parenthetical names the local mirror that distills it.

- Anthropic, "Effective context engineering for AI agents" — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (local mirror: `research/context-engineering/anthropic-effective-context-engineering.md`)
- Anthropic, "Writing tools for agents" — https://www.anthropic.com/engineering/writing-tools-for-agents (local mirror: `research/tool-design/anthropic-writing-tools-for-agents.md`)
- Claude blog, "Equipping agents for the real world with agent skills" — https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills (local mirror: `research/agent-skills/anthropic-equipping-agents-with-skills.md`)
- "How to Build AI Agents by Augmenting LLMs with Codified Human Expert Domain Knowledge?" arXiv:2601.15153 — https://arxiv.org/abs/2601.15153; "Procedural Knowledge Improves Agentic LLM Workflows" arXiv:2511.07568 — https://arxiv.org/abs/2511.07568 (local mirror: `research/domain-knowledge/domain-knowledge-impact-on-quality.md`)
- "Automatic Credibility Assessment Survey" arXiv:2410.21360 — https://arxiv.org/abs/2410.21360; CRAAP Test (Meriam Library, CSU Chico); Google E-E-A-T Quality Rater Guidelines (local mirror: `research/source-quality/web-research-quality-evaluation.md`)
- Wu et al., "Multi-Agent System Failure Taxonomy (MAST)" arXiv:2503.13657 — https://arxiv.org/abs/2503.13657; "Towards a Science of AI Agent Reliability" arXiv:2602.16666 — https://arxiv.org/abs/2602.16666; AGENTIF (arXiv:2505.16944) — https://arxiv.org/abs/2505.16944 (local mirror: `research/autonomous-agent-reliability/autonomous-agent-reliability.md`, added 2026-05-18 issue #28; MAST taxonomy + R1–R10 rubric)
- "Mind the Blind Spots: A Focus-Level Evaluation Framework for LLM Reviews" arXiv:2502.17086 — https://arxiv.org/abs/2502.17086; Augment Code, "Code Review Best Practices That Actually Scale"; Kim/Yegge, "The Three Developer Loops" (IT Revolution) (local mirror: `research/change-discipline/change-discipline-workflow-research.md`, added 2026-05-18 issue #28; multi-perspective review canon)

## Open Questions

- Which currently embedded operational thresholds in `engineering-baseline.md` are directly benchmark-backed and which should remain explicit repo defaults?
- Should domain cache behavior remain at its current complexity, or be reduced until stronger evidence exists for this exact plugin pattern?
- Which additional local `research/*` summaries, beyond the currently cited set, should receive provenance metadata in a future maintenance pass?
