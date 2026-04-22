---
last_refreshed: 2026-04-22
---

# Autonomous Agent Reliability: Frameworks and Failure Taxonomies

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Multiple arXiv papers + Tier 1/Tier 2 industry sources (AWS, Google Cloud, Microsoft Azure, Anthropic, Partnership on AI, Maxim.ai, Fast.io, UiPath, n8n, Inngest, Composio)
- Last reviewed: 2026-04-03

**Sources:** Academic papers (WebSearch 2026-04-03) + Industry implementation guidance (WebSearch 2026-04-03)

## Key Finding

Production agent reliability requires multi-dimensional evaluation beyond accuracy, incorporating systematic failure taxonomies and four critical architectural patterns: **circuit breakers** (three-state machines preventing cascade failures), **idempotency** (ensuring safe retries for 15-30% of tool calls), **progressive fallback** (degrading gracefully through self-correction → fallback → escalation), and **bounded execution** (stop conditions via failure thresholds, timeouts, and human oversight). Academic research identifies 12-15 distinct failure modes and establishes that reliability metrics are independent of raw accuracy, while industry implementations demonstrate 60-80% retry storm reduction through exponential backoff with jitter.

## Evidence

### Reliability Frameworks and Metrics

#### Multi-Dimensional Reliability Science
**Source:** [arXiv 2602.16666](https://arxiv.org/abs/2602.16666) — "Towards a Science of AI Agent Reliability"

- Proposes **twelve concrete metrics decomposing reliability into four key dimensions**: consistency (outcome, trajectory, resource), robustness (fault, environment, prompt), predictability (calibration, discrimination, Brier score), and safety (compliance, harm severity)
- Surveys reliability practices across safety-critical industries (aviation, nuclear power, automotive systems, industrial process control) to identify **four recurring evaluation dimensions emerging across fields**
- Critical finding: **Despite steady accuracy improvements over 18 months of model releases, reliability shows only modest overall improvement** when evaluating 14 agentic models across two benchmarks
- Metrics are **independent of raw accuracy, enabling comparison of reliability across agents with different capability levels**

#### Production-Scale Reliability Evaluation
**Source:** [arXiv 2601.06112](https://arxiv.org/abs/2601.06112) — "ReliabilityBench: Evaluating LLM Agent Reliability Under Production-Like Stress Conditions"

- Identifies **three orthogonal reliability dimensions**: consistency (identical correct outcomes across runs), robustness (handling semantically equivalent but syntactically varied instructions), and fault tolerance (graceful recovery from infrastructure failures)
- **First systematic application of chaos engineering principles to LLM agent evaluation**, providing configurable fault profiles simulating production failure modes
- Reveals critical brittleness gap: **GPT-4-based agents drop from 60% success (pass@1) to just 25% (pass@8)**, highlighting instability masked by single-run benchmarks
- Production systems require **consistent performance across thousands of similar requests with failure rates below 1-5%**
- Systematic fault injection shows **rate limiting causes largest reliability impact (2.5% degradation)**

### Failure Taxonomies

#### Multi-Agent System Failure Taxonomy (MAST)
**Source:** [arXiv 2503.13657](https://arxiv.org/abs/2503.13657) — "Why Do Multi-Agent LLM Systems Fail?" (March 2025)

- Introduces **first empirically grounded taxonomy of multi-agent system failures**, providing structured framework for defining, understanding, and annotating failures
- Analysis of **1600+ annotated traces across 7 popular MAS frameworks** (MetaGPT, ChatDev, HyperAgent, AppWorld, AG2) identifies **14 distinct failure modes clustered into 3 categories**
- Developed through rigorous analysis of 150 traces with **high inter-annotator agreement (kappa = 0.88)**; LLM-as-judge validation achieves 94% accuracy (kappa = 0.77)
- **State-of-the-art systems show failure rates exceeding 60–75%** across tested frameworks; no single category dominates, indicating diverse failure patterns

**MAST 14 Failure Modes:**

FC1 — Specification and System Design Failures:
- FM-1.1: Disobey task specification — agents fail to adhere to stated constraints
- FM-1.2: Disobey role specification — agents overstep defined boundaries
- FM-1.3: Step repetition — unnecessary reiteration without forward progress
- FM-1.4: Loss of conversation history — unexpected context truncation reverting to earlier state
- FM-1.5: Unaware of termination conditions — failure to recognize when interaction should end

FC2 — Inter-Agent Misalignment:
- FM-2.1: Conversation reset — unwarranted dialogue restart abandoning prior context
- FM-2.2: Fail to ask for clarification — proceeding without requesting needed information
- FM-2.3: Task derailment — deviation from intended objective toward unproductive actions
- FM-2.4: Information withholding — agent possesses relevant data but fails to communicate it
- FM-2.5: Ignored other agent's input — disregarding peer recommendations
- FM-2.6: Reasoning-action mismatch — discrepancy between stated reasoning and actual execution

FC3 — Task Verification and Termination:
- FM-3.1: Premature termination — ending before objectives are achieved
- FM-3.2: No or incomplete verification — omitting proper outcome validation
- FM-3.3: Incorrect verification — inadequate cross-checking of critical information

#### AgentCompass Production Error Taxonomy
**Source:** [arXiv 2509.14647](https://arxiv.org/abs/2509.14647) — "AgentCompass: Towards Reliable Evaluation of Agentic Workflows in Production" (Sept 2025)

- Formal hierarchical taxonomy providing structured ontology for classifying failures in agentic systems; evaluates traces via a four-stage pipeline (error identification → thematic clustering → quantitative scoring → synthesis)
- Validates framework quality via localization accuracy, categorization F1-scores, and Pearson correlation with human judgments

**AgentCompass 5-Category Error Taxonomy:**
1. Thinking & Response Issues — hallucinations, misinterpretation of retrieved information, flawed decision-making, output formatting violations
2. Safety & Security Risks — PII leakage, credential exposure, biased or unsafe content generation
3. Tool & System Failures — API failures, misconfigurations, rate limits, runtime exceptions
4. Workflow & Task Gaps — loss of conversational context, goal drift, redundant actions, task orchestration failures
5. Reflection Gaps — lack of self-correction after error, action without evidence of reasoning (most actionable for rubric checks)

#### Tool Invocation Reliability Framework
**Source:** [arXiv 2601.16280](https://arxiv.org/abs/2601.16280) — "When Agents Fail to Act: A Diagnostic Framework for Tool Invocation Reliability in Multi-Agent LLM Systems"

- Diagnostic framework features **12-category error taxonomy capturing failure modes** across tool initialization, parameter handling, execution, and result interpretation
- Leverages big data analytics to evaluate **procedural reliability in intelligent agent systems**

#### Agent Error Taxonomy
**Source:** [arXiv 2509.25370](https://arxiv.org/abs/2509.25370) — "Where LLM Agents Fail and How They can Learn From Failures"

- Introduces **AgentErrorTaxonomy providing modular classification** spanning memory, reflection, planning, action, and system-level operations
- Constructs AgentErrorBench dataset of systematically annotated failure trajectories from ALFWorld, GAIA, and WebShop
- Proposes AgentDebug framework that **isolates root-cause failures and provides corrective feedback**

#### System-Level Failure Mode Taxonomy
**Source:** [arXiv 2511.19933](https://arxiv.org/abs/2511.19933) — "Failure Modes in LLM Systems: A System-Level Taxonomy for Reliable AI Applications" (Nov 2025)

- Presents **taxonomy of fifteen hidden failure modes** arising in real-world LLM applications, framing them as distinct from traditional ML model failures
- Named modes include: multi-step reasoning drift, latent inconsistency, context-boundary degradation, incorrect tool invocation, version drift, cost-driven performance collapse (plus 9 additional)

#### Framework-Level Fault Taxonomy
**Source:** [arXiv 2602.19843](https://arxiv.org/abs/2602.19843) — "MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems"

- Establishes **taxonomy of 15 distinct fault types**, categorized into intra-agent faults and inter-agent faults
- Provides systematic fault injection methodology for reliability evaluation

#### 11-Layer Failure Stack
**Source:** [arXiv 2511.05511](https://arxiv.org/abs/2511.05511) — "From Failure Modes to Reliability Awareness in Generative and Agentic AI Systems" (Nov 2025)

- Introduces structured framework for identifying vulnerabilities from hardware/power foundations up through adaptive learning and agentic reasoning
- Spans infrastructure failures through emergent reasoning failures — relevant for rubric checks that must cover the full stack, not just prompt-level issues

### Circuit Breakers and Cascade Prevention

#### Distributional AGI Safety Framework
**Source:** [arXiv 2512.16856](https://arxiv.org/abs/2512.16856) — "Distributional AGI Safety: A Multi-Agent Framework"

- Discusses **circuit breakers as automated measures that halt or slow down agent activity** upon identifying breaches of risk and volatility thresholds
- Designed to **prevent rapid cascades**, with triggers based on monitoring systemic risk indicators like **rapid increases in inter-agent transaction frequency**
- Circuit breakers provide critical mechanism for **preventing cascading failures across multi-agent systems**

#### Agentic AI Architecture Patterns
**Source:** [arXiv 2512.09458](https://arxiv.org/abs/2512.09458) — "Architectures for Building Agentic AI"

- Recommends designing for tool flakiness with **"design for retry" mentality incorporating jitter, circuit breakers, and degrade to read-only patterns**
- Emphasizes **circuit breakers as standard architectural component** for production agent systems
- Practical implementation: **track failures across sliding window; if threshold exceeded, open circuit and block new requests; after cooldown, close and retry**
- Critical principle: **one tripped agent must not bring down entire system**—bounded permissions and distinct identity ensure **tripping one agent does not cascade into system-wide failure**

### Fault Tolerance and Recovery Mechanisms

#### Byzantine Fault Tolerance for Multi-Agent Systems
**Source:** [arXiv 2511.10400](https://arxiv.org/abs/2511.10400) — "Rethinking the Reliability of Multi-agent System: A Perspective from Byzantine Fault Tolerance"

- Investigates and quantifies reliability from **Byzantine fault tolerance perspective**
- Designs **CP-WBFT (confidence probe-based weighted Byzantine Fault Tolerant consensus mechanism)** to enhance stability by capitalizing on intrinsic reflective and discriminative capabilities of LLMs
- Demonstrates pattern: **"redundancy + agreement = safety"**—multiple entities weighing in reduces convergence on faulty predictions; requiring consensus provides assurance that actions are corroborated by independent analyses
- **Significantly reduces risk of unsafe outcomes due to single point of failure**

#### Step-Wise Failure Detection and Recovery
**Source:** [arXiv 2603.21522](https://arxiv.org/abs/2603.21522) — "EAGER: Efficient Failure Management for Multi-Agent Systems with Reasoning Trace Representation"

- Performs **step-wise detection that continuously evaluates each reasoning step** to identify potential failures in real time
- Upon detecting failure, **triggers reflexive mitigation mechanism** allowing agents to self-reflect, replan, or regenerate responses for recovery
- Enables **proactive failure management rather than post-hoc debugging**

#### Chaos Engineering for Agent Resilience
**Source:** [arXiv 2505.03096](https://arxiv.org/abs/2505.03096) — "Assessing and Enhancing the Robustness of LLM-based Multi-Agent Systems Through Chaos Engineering"

- Applies chaos engineering to enhance robustness of LLM-based Multi-Agent Systems in **production-like environments under real-world conditions**
- LLM-MAS in production can be vulnerable to **emergent errors or disruptions: hallucinations, agent failures, and agent communication failures**
- **Intentional fault injection identifies and addresses system weaknesses** that cause outages in production environments

### Industry Implementation Patterns

#### Circuit Breaker Implementation

**Source:** [AWS Prescriptive Guidance - Circuit Breaker Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html)

- Circuit breakers have **three states: Closed (normal operation), Open (failures detected, stop trying), Half-Open (testing if service recovered)**
- When failure rate exceeds threshold (e.g., **50% of last 100 requests**), stop sending requests and **return cached response or fallback value immediately**
- AWS implementation uses **Step Functions state machines to configure retry capabilities and decision-based control flow**; persistence layer stores circuit breaker status in **Amazon MemoryDB (Redis-based with persistent storage)**

**Source:** [Maxim.ai - Retries, Fallbacks, and Circuit Breakers in LLM Apps](https://www.getmaxim.ai/articles/retries-fallbacks-and-circuit-breakers-in-llm-apps-a-production-guide/)

- **Layered approach: exponential backoff for transient errors, circuit breakers for persistent failures, fallback models for LLM unavailability, and human escalation for unrecoverable errors**
- After certain number of failures, stop calling the failing service temporarily, **preventing cascade failures where one broken tool brings down the entire agent**

**Source:** [Microsoft Azure - Context Engineering for Azure SRE Agent](https://techcommunity.microsoft.com/blog/appsonazureblog/context-engineering-lessons-from-building-azure-sre-agent/4481200/)

- Microsoft's Agent Governance Toolkit addresses **cascading failures through circuit breakers and SLO enforcement**
- Emphasizes **bounded permissions and distinct identity to ensure tripping one agent does not cascade into system-wide failure**

#### Idempotency Patterns

**Source:** [Fast.io - AI Agent Idempotent Operations](https://fast.io/resources/ai-agent-idempotent-operations/)

- **Idempotent operations produce the same result regardless of how many times they are executed**, ensuring agents can safely retry file writes, API calls, and state changes without creating duplicates or corruption
- **LLM agents retry tool calls 15-30% of the time** due to timeouts, validation errors, or model uncertainty
- **Every write gets an idempotency key**, and the gateway rejects duplicates; if a tool call can create, refund, email, delete, or deploy, **it must be safe to retry**

**Source:** [Google Cloud Vertex AI - Retry Strategy](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/retry-strategy)

- **Idempotency is the guarantee that executing the same operation multiple times produces the same result as executing it once**—one of the most critical properties for resilient multi-agent systems
- While `generateContent` is not strictly idempotent due to stochastic nature, **it is generally safe to retry for transient errors as it does not modify server-side state**
- **Do not retry client errors (4xx other than 429/408)** as they indicate issues like invalid API keys or bad syntax

**Source:** [Inngest - Durable Execution for AI Agents](https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents)

- **Durable execution simplifies idempotency**: because step results are cached, you can safely retry the entire workflow without duplicate side effects
- **Each step records its completion and defines a compensation action**; the durable execution engine ensures **each step executes exactly once, even if the workflow function itself runs multiple times**

#### Retry Strategies with Exponential Backoff

**Source:** [Fast.io - AI Agent Retry Patterns](https://fast.io/resources/ai-agent-retry-patterns/)

- **Exponential backoff with jitter reduces retry storms by 60-80%** according to AWS research on distributed systems
- **Retry pattern where wait time doubles after each failure**: retry 1 waits 1 second, retry 2 waits 2 seconds, retry 3 waits 4 seconds, retry 4 waits 8 seconds
- **Safe retries require: idempotency keys, bounded retries, provider-aware backoff for 429s, timeouts, and a policy for when to stop and route to DLQ for manual review**

**Source:** [Google Cloud Vertex AI - Retry Strategy](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/retry-strategy)

- **Generally use exponential backoff with jitter to retry requests** that meet both response and idempotency criteria
- **Unconditionally retrying non-idempotent operations can lead to side effects, such as duplicate resources**

#### Fallback and Degradation Strategies

**Source:** [Fast.io - AI Agent Error Handling](https://fast.io/resources/ai-agent-error-handling/)

- **Two-phase execution: do not execute directly from model output**—first phase proposes a plan and dry-run summary; second phase executes only after policy gates pass
- **Progressive response to failure: first try to self-correct; if that fails, try a fallback; if that fails, degrade gracefully; if degradation isn't possible, escalate clearly**
- At every stage, **failure is visible, logged, and user receives maximum value the system can provide**

**Source:** [Composio - Production Migration Blueprint](https://composio.dev/content/outgrowing-make-zapier-n8n-ai-agents)

- **Scalable agents assume retries will happen and design every side effect to be idempotent**
- **Every external write uses an idempotency key tied to the task state**

#### State Management and Validation

**Source:** [Microsoft Azure - Context Engineering for Azure SRE Agent](https://techcommunity.microsoft.com/blog/appsonazureblog/context-engineering-lessons-from-building-azure-sre-agent/4481200/)

- **Todo planner: represent the plan as explicit checklist outside model's context**, and let model update it instead of re-deriving workflow on every turn
- **Compaction: continuously shrink history into summaries and structured state**, so context stays a small working set rather than ever-growing log
- Core principle: **give the model fewer, cleaner choices and spend effort making the context small, structured, and easy to operate on**

**Source:** [UiPath - Agent Builder Best Practices](https://www.uipath.com/blog/ai/agent-builder-best-practices)

- **State corruption is a silent killer**—agent continues operating with bad state, producing nonsensical outputs
- **Implement state validation at checkpoints** to validate state is consistent before agent makes decisions based on it

#### Tool Validation and Error Handling

**Source:** [n8n - Best Practices for Deploying AI Agents in Production](https://blog.n8n.io/best-practices-for-deploying-ai-agents-in-production/)

- **Every tool must have dedicated error handling**—tool errors should never crash the agent but should gracefully degrade or retry with backoff
- **Use schema-driven prompts: keep tool prompts concise and structured**, and validate output shapes while handling null or empty results explicitly

**Source:** [Anthropic - Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

- **Long-running agent failures**: agents tend to try to do too much at once and run out of context mid-implementation, leaving features half-implemented
- **Major failure mode: Claude's tendency to mark feature as complete without proper testing**, often failing to recognize features don't work end-to-end
- **Tool misuse and selection issues**: agents misuse tools or fail to match tools to user's intent, with higher failure rates in scenarios when agents select or operate tools poorly

#### Observability and Monitoring

**Source:** [Microsoft Azure - Agent Observability Best Practices](https://azure.microsoft.com/en-us/blog/agent-factory-top-5-agent-observability-best-practices-for-reliable-ai/)

- **Agent observability needs metrics, traces, logs, evaluations, and governance** for full visibility
- **OpenTelemetry (OTel) conventions unify traces** across Agent Framework, Foundry, and popular stacks—so you can see one coherent timeline for each task
- Multi-agent observability patterns ensure **workflow maintains context over long-running operations**

**Source:** [UiPath - Agent Builder Best Practices](https://www.uipath.com/blog/ai/agent-builder-best-practices)

- **Before agent executes, log inputs and configuration; during execution, log each tool call with parameters; after execution or failure, log outputs or detailed error**
- **Weak observability and immature guardrails are most common pain points in production**

#### Human Oversight and Escalation

**Source:** [Anthropic - Framework for Safe and Trustworthy Agents](https://www.anthropic.com/news/our-framework-for-developing-safe-and-trustworthy-agents)

- **While agents must work autonomously, humans should retain control over how goals are pursued**, particularly before high-stakes decisions
- In Claude Code, **humans can stop Claude whenever they want and redirect its approach, with read-only permissions by default requiring human approval before modifications**
- **Real-time failure detection: secondary models watch for signs of agent hijacking or monitor reasoning to track tool calls**

**Source:** [Partnership on AI - Real-Time Failure Detection in AI Agents](https://partnershiponai.org/wp-content/uploads/2025/09/agents-real-time-failure-detection.pdf)

- **Multi-layer safety controls**: contextual boundary detection must recognize competency limits, confidence thresholding with human escalation, drift detection for behavioral changes
- **Multi-factor authentication for critical actions, and rate limiting to prevent cascade failures**

**Source:** [UiPath - Agent Builder Best Practices](https://www.uipath.com/blog/ai/agent-builder-best-practices)

- **Structured human feedback helps systems learn what is right and wrong** while preventing small errors from becoming systemic failures
- **Production-ready AI agents need solid infrastructure, proper error handling, monitoring, and maintenance procedures**

#### Production Deployment Discipline

**Source:** [n8n - Best Practices for Deploying AI Agents in Production](https://blog.n8n.io/best-practices-for-deploying-ai-agents-in-production/)

- **Move agents to production only after evaluations pass and rollout plans are finalized**
- **Attach evaluations to version tags to ensure traceability from design to deployment**
- **Deploy to staged environment first, then monitor performance, latency, and safety signals continuously with rollback capabilities**

**Source:** [Anthropic - Framework for Safe and Trustworthy Agents](https://www.anthropic.com/news/our-framework-for-developing-safe-and-trustworthy-agents)

- **Do not deploy unlogged agents to production**—comprehensive logging is prerequisite for production deployment

## Quality Rubric Checks for Agent Reliability

These checks are derived from the taxonomies and production patterns above. Each maps to at least one empirically-grounded source.

### R1 — Termination Conditions Defined
Does the agent/skill definition specify explicit stop conditions (step limit, failure threshold, timeout, or success criteria)?
- Maps to: MAST FM-1.5 (unaware of termination conditions), FM-3.1 (premature termination)
- Signal: absence of any `max_steps`, timeout, or convergence criterion is a High finding
- Source: arXiv 2503.13657; arXiv 2512.09458

### R2 — Failure Path Specified (Not Just Happy Path)
Does the definition address what happens on tool error, model failure, or unexpected output?
- Maps to: AgentCompass Category 3 (Tool & System Failures); production pattern "every tool must have dedicated error handling"
- Signal: definitions with only success-case flows score Low on this check
- Source: arXiv 2509.14647; n8n production guide

### R3 — Retry / Backoff Strategy Present
Is retry behavior explicitly bounded (max retries, backoff interval)? Unbounded retry = retry storm risk.
- Maps to: circuit breaker pattern; exponential backoff with jitter reduces retry storms 60–80%
- Signal: missing retry bounds or infinite loop risk is a Medium finding
- Source: Fast.io retry patterns (Tier 2); Google Cloud Vertex AI retry strategy (Tier 1)

### R4 — Escalation / Human-in-the-Loop Defined
Does the definition specify what triggers human escalation or agent halt?
- Maps to: MAST FM-3.1/3.2; AgentCompass Reflection Gaps; production pattern HITL for high-privilege ops
- Signal: high-autonomy agents with no escalation path are a High finding for safety-adjacent work
- Source: arXiv 2602.16666; Partnership on AI real-time failure detection (Tier 2); Anthropic framework

### R4b — HITL Surface Resistant to Manipulation (Added 2026-04-22)
Is the HITL approval-request text itself resistant to prompt-injection? Specifically: is the user-facing confirmation prompt composed from fixed templates or constrained options, rather than from free-form model output derived from tool results or external content?
- Maps to: OWASP Top 10 for Agentic Applications 2026 **ASI09** Human-Agent Trust Exploitation; rubber-stamp attack surface
- Signal: HITL-heavy skills where the agent can synthesize the approval-prompt text from untrusted content are a **High** finding — the user rubber-stamps because the prompt looks legitimate, even when the underlying action has been redirected
- Fix patterns: `AskUserQuestion` with fixed `options` arrays (not free-text); `ExitPlanMode` renders a plan file the user sees directly rather than a summary the agent writes; confirmation prompts templated in the skill body, not composed at runtime
- Source: OWASP ASI2026 (Tier 1); Anthropic HITL guidance (Tier 1); `research/injection-taxonomy/injection-taxonomy.md` §indirect-via-tool-output

### R5 — State Validation / Checkpointing Mentioned
Does the definition include state consistency checks between steps, or specify checkpointing?
- Maps to: UiPath "state corruption is a silent killer" pattern; ReliabilityBench chaos engineering results
- Signal: multi-step agents (>3 steps) with no state validation are a Medium finding
- Source: arXiv 2601.06112; UiPath Agent Builder Best Practices (Tier 2)

### R6 — Verification Step Included
Does the agent verify task outcomes before declaring completion (not just check for absence of error)?
- Maps to: MAST FM-3.2 (no or incomplete verification), FM-3.3 (incorrect verification)
- Signal: agents that self-report success without output validation are a Medium finding
- Source: arXiv 2503.13657

### R7 — Reasoning-Action Consistency Required
Does the definition require or enforce that the agent's stated plan matches its executed actions?
- Maps to: MAST FM-2.6 (reasoning-action mismatch); AgentCompass Reflection Gaps
- Signal: agents with no reflection or self-review step are weaker on this dimension
- Source: arXiv 2503.13657; arXiv 2509.14647

### R8 — Scope / Role Boundaries Stated
Are the agent's responsibilities and authority limits explicitly defined?
- Maps to: MAST FM-1.2 (disobey role specification); MAST FM-2.3 (task derailment)
- Signal: agents with open-ended "do whatever is needed" instructions lack boundary definition
- Source: arXiv 2503.13657

### R9 — Safety / PII / Credential / Memory-Write Scope Addressed (Updated 2026-04-22 for OWASP ASI06)
Does the definition explicitly exclude unsafe outputs, credential handling, data leakage paths, **and persistent memory writes carrying content from untrusted sources**?
- Maps to: OWASP Top 10 for Agentic Applications 2026 **ASI06** Memory / Context Poisoning; AgentCompass Category 2 (Safety & Security Risks); adversarial robustness benchmarks
- Signal: agents with tool access to secrets/credentials, or with write access to persistent memory (auto-memory files, CLAUDE.md, scratch plans that later feed back into the agent) that lack explicit content-origin or sanitization constraints are a **High** finding. The 2026 scope extends the 2025 rubric to memory-poisoning vectors beyond read-side PII: every memory *write* from external content is a potential future injection
- Source: OWASP ASI2026 (Tier 1); arXiv 2509.14647; arXiv 2508.16481 (adversarial robustness); `research/memory-poisoning/memory-poisoning-patterns.md`

### R10 — Observability Hooks Specified
Does the definition require logging of inputs, tool calls, and outputs (not just final result)?
- Maps to: production pattern "do not deploy unlogged agents"; Azure Agent Observability Best Practices
- Signal: no mention of tracing, logging, or audit trail is a Low-Medium finding for production-facing agents
- Source: Microsoft Azure observability guidance (Tier 2); Anthropic framework (Tier 1)

### R11 — Cascading Containment on Deep Delegation (Added 2026-04-22)
For agents that dispatch subagent chains of depth ≥3 (A calls B calls C), does the definition specify a containment primitive — circuit breaker (open after N failed or timed-out children), rollback semantics (restore prior state on child failure), or a blast-radius limit (e.g., "no more than K downstream writes per root invocation")?
- Maps to: OWASP Top 10 for Agentic Applications 2026 **ASI08** Cascading Failures; circuit-breaker pattern (closed/open/half-open three-state machine, typical 50 % failure threshold of last 100 requests); Microsoft Agent Governance Toolkit
- Signal: multi-agent orchestrators with depth ≥3 that lack any containment primitive are a **High** finding — a single poisoned child can silently propagate through the chain, and retries at each level compound the blast radius
- Fix patterns: `max_depth: 3` declaration in orchestrator frontmatter; explicit "abort remaining subagents on first High finding" rule; write-operation count budget per root dispatch; SLO breaker that short-circuits when chain latency exceeds a threshold
- Source: OWASP ASI2026 (Tier 1); this file §"circuit breakers provide critical mechanism for preventing cascading failures" (L123, L174)

**Severity mapping (for rubric grading):**
- High findings: R1 (missing termination), R4 (no escalation on high-autonomy), R4b (HITL surface manipulable, ASI09), R9 (unsafe scope incl. persistent memory writes, ASI06), R11 (no cascading containment on depth ≥3, ASI08)
- Medium findings: R2 (no failure path), R3 (unbounded retry), R5 (no state validation), R6 (no verification), R8 (no role bounds)
- Low findings: R7 (no reflection), R10 (no observability hooks)

## Research-Level Implication

The academic literature establishes that agent reliability is fundamentally multi-dimensional, extending beyond raw accuracy to encompass consistency, robustness, predictability, safety, and fault tolerance. Comprehensive failure taxonomies identify 12-15 distinct failure modes across tool invocation, inter-agent communication, and system-level operations. Circuit breaker patterns emerge as critical architectural components for preventing cascading failures, with implementations tracking failure rates across sliding windows and implementing cooldown periods. Byzantine fault tolerance and step-wise detection provide concrete mechanisms for recovery.

Industry implementation patterns provide concrete production guidance: circuit breakers must implement three-state machines (closed/open/half-open) with configurable failure thresholds (typically 50% of last 100 requests); idempotency keys are mandatory for all write operations with agents retrying 15-30% of tool calls; exponential backoff with jitter reduces retry storms by 60-80%; two-phase execution separates plan proposal from execution; state validation at checkpoints prevents silent corruption; and human escalation serves as final safety layer for high-stakes decisions. Production deployment requires staged rollouts, comprehensive logging, multi-dimensional observability (metrics, traces, evaluations), and attachment of evaluations to version tags.

The evidence supports a reliability framework incorporating: (1) multi-dimensional metrics beyond accuracy, (2) systematic failure taxonomies for diagnostic classification, (3) circuit breakers with bounded permissions to prevent cascades, (4) consensus mechanisms for Byzantine fault tolerance, (5) chaos engineering for proactive resilience testing, (6) idempotency patterns for safe retries, (7) exponential backoff with jitter for transient failures, (8) progressive degradation strategies, (9) state validation at checkpoints, and (10) multi-layer human oversight with real-time failure detection. Repo-specific evaluation policy should be derived separately in dossier-level interpretation.
