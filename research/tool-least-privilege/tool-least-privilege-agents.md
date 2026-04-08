---
last_refreshed: 2026-04-08
---

# Least-Privilege Tool Grants for LLM Agents

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: OWASP GenAI Security Project (Tier 1), Anthropic official documentation (Tier 1), peer-reviewed arXiv papers (Tier 1), OWASP AI Agent Security Cheat Sheet (Tier 1), Anthropic Engineering Blog (Tier 2)
- Last reviewed: 2026-04-08

**Sources:**
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) — Tier 1
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) — Tier 1
- [Claude Code Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents) — Tier 1
- [Claude Agent SDK Permissions](https://platform.claude.com/docs/en/agent-sdk/permissions) — Tier 1
- [Anthropic Engineering: Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode) — Tier 2
- [MiniScope: Least Privilege Framework for Tool-Calling Agents (arXiv 2512.11147)](https://arxiv.org/abs/2512.11147) — Tier 1
- [Progent: Programmable Privilege Control for LLM Agents (arXiv 2504.11703)](https://arxiv.org/html/2504.11703v1) — Tier 1
- [Design Patterns for Securing LLM Agents against Prompt Injections (arXiv 2506.08837)](https://arxiv.org/html/2506.08837v1) — Tier 1
- [allowedTools does not restrict built-in tools — GitHub Issue anthropics/claude-agent-sdk-typescript#115](https://github.com/anthropics/claude-agent-sdk-typescript/issues/115) — Tier 2 (documented Anthropic SDK behavior)
- [Feature Request: disallowed-tools in sub-agent frontmatter — GitHub Issue anthropics/claude-code#6005](https://github.com/anthropics/claude-code/issues/6005) — Tier 2

## Key Finding

Granting LLM agents more tools than their task requires creates a force-multiplier for prompt injection: an agent that can read files, execute shell commands, and make network requests presents a "lethal trifecta" in which a single injected instruction can escalate to full system compromise. Empirical enforcement of least privilege (Progent framework) reduces agent attack success rates from 41–70% down to 2–7%. In Claude Code specifically, `allowedTools` is an allowlist that does **not** constrain built-in tools (Bash, Edit, Write) when `bypassPermissions` is active; only `disallowedTools` creates an absolute deny that holds across all permission modes.

## Evidence

### Over-Provisioning Patterns Leading to Security and Reliability Incidents

#### OWASP LLM06:2025 — Excessive Agency Root Causes
**Source:** [OWASP GenAI — LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)

OWASP identifies three root causes of excessive agency, all of which are tool-grant concerns:

1. **Excessive Functionality** — Extensions expose capabilities beyond operational requirements (e.g., a document reader that also has delete permission; deprecated plugins remaining accessible from earlier development phases).
2. **Excessive Permissions** — Tools operate with broader downstream access than the task requires (e.g., a DB plugin connecting with `UPDATE/INSERT/DELETE` when only `SELECT` is needed; a generic high-privileged account used instead of per-user-context credentials).
3. **Excessive Autonomy** — High-impact, often irreversible actions proceed without human confirmation.

Documented anti-patterns from OWASP:
- Open-ended shell functions without command filtering (shell execution without allowlists)
- Email plugin that can both read and send when only reading is required
- Extensions that accumulate permissions across development iterations and are never trimmed

The email case study demonstrates the amplification chain: read-only task scope → plugin with send capability → OAuth without read-only scope restriction → malicious prompt injection in an incoming email → autonomous reply to attacker. Mitigations: read-only extensions, scoped OAuth, manual approval before send.

#### The "Lethal Trifecta" — Privileged Access + Untrusted Input + Exfiltration Capability
**Source:** [AI Agents Hacking in 2026 — penligent.ai](https://www.penligent.ai/hackinglabs/ai-agents-hacking-in-2026-defending-the-new-execution-boundary/) — Tier 2

Security practitioners have characterized a specific three-way combination as the highest-risk configuration for LLM agents:

1. Agent has privileged access (shell, file write, network)
2. Agent processes untrusted input (user content, web pages, emails, issue bodies)
3. Agent can share data externally (network calls, file writes to shared paths)

One documented post-mortem: an AI-powered CI/CD issue triage agent had shell access and processed untrusted GitHub issue input. Prompt injection led to code execution on GitHub Actions runners. The conclusion: "giving an LLM shell access in a CI context where it processes untrusted input is functionally equivalent to giving every GitHub user shell access."

CVE-2025-53773 (VS Code / GitHub Copilot Agent): a prompt injection vulnerability allowed the agent to create files without user authorization; a single-line injected command caused automatic tool approval. The combination of file-write capability and untrusted web content was the attack vector.

*Note: The CI/CD post-mortem is Tier 2 (practitioner blog without peer-reviewed metrics). The CVE is documented but the specific post-mortem source lacked the primary report URL. Claim class: cross-validated by OWASP pattern (Tier 1) + practitioner incident (Tier 2).*

#### Empirical Attack Success Rates vs. Least-Privilege Enforcement
**Source:** [Progent — arXiv 2504.11703](https://arxiv.org/html/2504.11703v1) — Tier 1

Progent (programmable privilege control via DSL applied at tool-call time) evaluated on two agent security benchmarks:

| Benchmark | Baseline ASR | With Progent (manual policies) | With Progent (LLM-generated policies) |
|-----------|-------------|-------------------------------|---------------------------------------|
| AgentDojo | 41.2% | 2.2% | 2.2% |
| ASB | 70.3% | 0% | 7.3% |
| KB poisoning | high | 0% | 0% |

Attack Success Rate (ASR) drops by 10–35x with least-privilege enforcement, while task utility is maintained.

Progent's key design decisions:
- Policies target specific tools with conditional expressions over **parameters**, not just tool names (e.g., `send_money` is dangerous only when `recipient` is attacker-controlled)
- Inherently high-risk operations (delete, transfer, external write) are treated as categorically dangerous regardless of context
- Even read-only tools accessing sensitive data (health records, SSNs) require context-specific restriction

#### MiniScope — Permission Hierarchies for Tool-Calling Agents
**Source:** [MiniScope — arXiv 2512.11147](https://arxiv.org/abs/2512.11147) — Tier 1

MiniScope is the first framework to rigorously enforce least privilege for tool-calling agents through mechanical (non-LLM-based) enforcement. Key findings:

- Constructs permission hierarchies by grouping tool calls by sensitivity and functionality similarity (analogous to mobile OS permission groups)
- Adds only 1–6% latency overhead vs. vanilla tool calling agents
- Outperforms LLM-based permission minimization on both permission minimization and computational cost
- Evaluated against 10 real-world applications, not simplified benchmarks

*The paper abstract does not enumerate the specific permission groups; full group taxonomy requires full-paper access.*

### Framework for Task Type → Minimal Required Tool Set

#### OWASP AI Agent Security Cheat Sheet — Task-to-Tool Mapping
**Source:** [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) — Tier 1

The cheat sheet provides explicit task-type to tool-set mappings:

| Agent Task Type | Permitted Tools | Blocked Tools |
|----------------|----------------|---------------|
| Document Processing | read_file, search_documents, summarize | execute_code, send_email, database_write |
| Customer Service | search_documents, retrieve_policies, calculate_refunds | modify_customer_records, process_payments (without approval) |
| Data Analysis | read_file, query_database (read-only), generate_reports | execute_arbitrary_queries, modify_schema |
| Email Management | retrieve_emails, classify_messages, draft_responses | send_email (without human preview), access_contact_data |

Risk classification for tool call types:

- **Low Risk (auto-approve):** Read operations, safe queries, document searches
- **Medium Risk (review recommended):** File writes, API calls with limited scope
- **High Risk (human approval required):** Email transmission, code execution, external communications
- **Critical Risk (mandatory approval):** Irreversible deletions, financial operations, security-sensitive changes

Principle: "Grant agents the minimum tools required for their specific task." Granting tools "just in case" without documented necessity is explicitly identified as an implementation gap.

#### Claude Code Official Examples — Minimal Tool Sets by Agent Role
**Source:** [Claude Code Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents) — Tier 1

Anthropic's own documentation provides reference minimal tool sets:

| Agent Role | Minimal Tool Set | Rationale |
|-----------|-----------------|-----------|
| Code reviewer (read-only) | Read, Grep, Glob, Bash | Analysis without modification; Bash for grep/find patterns |
| Debugger | Read, Grep, Glob, Bash, Edit | Fixing bugs requires modifying code |
| Database validator | Bash (with hook restricting to read-only SQL) | Validated access only |

The read-only reviewer example explicitly demonstrates: "because the allowedTools list excludes Edit and Write, the agent literally cannot modify the codebase, only inspect it."

#### Progent DSL — Tool-Level Policy Primitives
**Source:** [Progent — arXiv 2504.11703](https://arxiv.org/html/2504.11703v1) — Tier 1

Progent's DSL formalizes the task → tool mapping problem with five policy elements per tool:
1. **Effect** (allow/forbid)
2. **Target tool identifier**
3. **Conditional expression** over tool parameters (not just tool name)
4. **Fallback function** when call is blocked
5. **Priority level** for policy conflicts

Key insight: tool-level restriction is insufficient — parameter-level restriction is also required. The `send_money` tool is safe with a known recipient and dangerous with an attacker-controlled recipient. This means `allowedTools: ["send_money"]` does not capture the full risk surface.

### Claude Code `allowedTools` / `disallowedTools` Interaction with Safety

#### Permission Evaluation Order and the bypassPermissions Paradox
**Source:** [Claude Agent SDK Permissions](https://platform.claude.com/docs/en/agent-sdk/permissions) — Tier 1

Claude Code evaluates permissions in this order (first match wins):

1. Hooks (can allow, deny, or continue)
2. **Deny rules** (`disallowedTools`) — absolute block, holds in **all** permission modes including `bypassPermissions`
3. Permission mode (global behavioral rules)
4. Allow rules (`allowedTools`) — pre-approves listed tools only
5. `canUseTool` callback — prompts for unlisted tools

**Critical behavior:** `allowedTools` is **not a denylist**. It pre-approves listed tools but does not block unlisted ones. When `permissionMode: "bypassPermissions"` is active, all permission checks are skipped — `allowedTools: ["Read"]` still allows Bash, Write, and Edit.

**Documented issue:** [anthropics/claude-agent-sdk-typescript#115](https://github.com/anthropics/claude-agent-sdk-typescript/issues/115) confirms that even outside `bypassPermissions`, `allowedTools` in the SDK does not restrict built-in tools (Edit, Write, Bash, NotebookEdit) from executing. This was resolved by clarifying that `bypassPermissions` disables all checks; the workaround is to avoid `bypassPermissions` for security-critical agents.

**Safe configuration pattern** (confirmed by Anthropic SDK docs):
```yaml
# Correct: allowlist + restrictive mode
tools: [Read, Glob, Grep]
# permissionMode: dontAsk  (denies everything not listed, no prompt)
```

```yaml
# Incorrect for security: allowedTools alone does not deny unlisted tools
# when bypassPermissions is active
```

#### Sub-agent Inheritance and MCP Tool Over-Provisioning Risk
**Source:** [Claude Code Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents) — Tier 1

Subagents **inherit all tools from the main conversation by default**, including MCP tools. Without explicit restriction, a sub-agent launched from a session with broad MCP tool access inherits that access. The documentation notes this as a potential over-provisioning scenario requiring intentional declaration.

`disallowedTools` can be used to remove specific tools from the inherited set:
```yaml
disallowedTools: [Write, Edit]  # inherit everything except these
```

`tools:` (allowlist) provides stricter scoping:
```yaml
tools: [Read, Grep, Glob, Bash]  # only these; no MCP tools
```

When both are specified, `disallowedTools` is applied first, then `tools` is resolved against the remaining pool.

#### Anthropic Auto Mode Safety Classifier — Internal Tool Taxonomy
**Source:** [Anthropic Engineering: Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode) — Tier 2

Anthropic's internal safety classifier (used in `auto` permission mode) treats these as safe without review:
- File reads and searches
- Code navigation and text operations
- In-project file edits (reviewable via version control)

And flags these patterns for classification/blocking:
- **Scope escalation:** Vague deletion commands triggering irreversible remote deletions
- **Credential exploration:** Systematic searching of env vars or config files for API tokens
- **Agent-inferred parameters:** Selecting targets by name similarity without explicit user confirmation
- **Data exfiltration:** Sharing scripts or data to external services without explicit authorization
- **Safety bypass:** Retrying failed commands with skip-verification flags

Block categories: destruction, exfiltration, security degradation, trust boundary violations, shared infrastructure bypasses.

Performance: 0.4% false positive rate on real traffic; 17% false negatives on documented overeager actions.

### Design Patterns That Structurally Reduce Tool Risk

#### Architectural Patterns Ranked by Attack Surface Reduction
**Source:** [Design Patterns for Securing LLM Agents — arXiv 2506.08837](https://arxiv.org/html/2506.08837v1) — Tier 1

Six patterns, ordered by how much they constrain tool risk:

1. **Action-Selector Pattern** — LLM selects from hardcoded pre-defined actions only; tool outputs cannot feedback into decision-making. Lowest attack surface.
2. **Plan-Then-Execute Pattern** — Fixed plan before execution; injected tool outputs cannot change the plan (parameters still vulnerable).
3. **LLM Map-Reduce Pattern** — Isolated LLM instances per data item; blast radius of injection limited to one item.
4. **Dual LLM Pattern** — Privileged LLM (tool access) separated from quarantined LLM (processes untrusted data text-only). Requires discipline to maintain separation.
5. **Code-Then-Execute Pattern** — Agent writes explicit programs; formal structure replaces planning.
6. **Context-Minimization Pattern** — User prompts removed from context after initial action trigger.

Key principle: "Once an LLM agent has ingested untrusted input, it must be constrained so that it is impossible for that input to trigger any consequential actions."

The highest-risk tool combination identified: **shell + arbitrary file access** ("any file on the computer might contain malicious instructions, which if read cause the LLM to execute arbitrary code"). Second-highest: **code execution + external data** (database contents enabling RCE and exfiltration). Third: **email/communication + untrusted feedback** (confidential data leakage).

## High-Risk Tool Combinations

Evidence-backed checklist. Each combination is flagged as requiring explicit documented justification when present in an agent definition.

### Tier A — Critical Risk (mandatory justification required)

| # | Combination | Risk Pattern | Evidence |
|---|------------|-------------|---------|
| A1 | `Bash` + any network tool (`WebFetch`, `WebSearch`, MCP web) | Shell execution + external data fetch creates exfiltration + RCE chain if untrusted input processed | OWASP LLM06, arXiv 2506.08837, practitioner incidents |
| A2 | `Bash` + `Write`/`Edit` | Arbitrary code + file modification: agent can self-modify or write malicious scripts | OWASP LLM06, Anthropic auto-mode classifier |
| A3 | Broad Bash (no `allowedTools` restriction) + untrusted input source | Functionally equivalent to giving every input source shell access | Documented CI/CD incident (Tier 2, cross-validated by OWASP Tier 1) |
| A4 | `Write`/`Edit` + `WebFetch`/`WebSearch` | Untrusted web content → file write; enables persistent code injection | arXiv 2506.08837, OWASP cheat sheet |
| A5 | Communication tools (email, Slack MCP) + file read + no human approval gate | Allows data exfiltration via email/messaging from any readable file | OWASP LLM06 email case study |

### Tier B — High Risk (strong justification required)

| # | Combination | Risk Pattern | Evidence |
|---|------------|-------------|---------|
| B1 | `Write`/`Edit` without path restriction in an agent that processes external input | Injection can trigger writes to sensitive paths (.env, credentials, hooks) | Anthropic auto-mode classifier, OWASP cheat sheet |
| B2 | Database MCP with write/delete permissions | Irreversible data modification; SELECT-only is sufficient for most read tasks | OWASP LLM06, Progent analysis |
| B3 | `Bash` without command allowlist in an agent with `disableModelInvocation: false` (auto-dispatch) | Auto-dispatched agents with shell access cannot be manually reviewed before each call | OWASP cheat sheet, Claude Code docs |
| B4 | All tools inherited from parent session (no `tools:` or `disallowedTools:` specified) | MCP tool proliferation; agent receives tools it never needs | Claude Code sub-agent docs |
| B5 | `Bash` + secrets/credential-adjacent file paths accessible | Credential exploration pattern identified by Anthropic's classifier | Anthropic auto-mode engineering blog |

### Tier C — Medium Risk (document justification)

| # | Combination | Risk Pattern | Evidence |
|---|------------|-------------|---------|
| C1 | `WebFetch` + `Write` without read-only mode or output sandboxing | Fetched content written to disk without sanitization | OWASP cheat sheet |
| C2 | Read tools (`Read`, `Glob`, `Grep`) with unrestricted path scope in agents processing untrusted input | Path traversal to sensitive files; exfiltration via output | OWASP cheat sheet, Progent parameter-level analysis |
| C3 | `allowedTools` specified but `permissionMode: bypassPermissions` active | `allowedTools` is nullified; all tools effectively granted | Claude Agent SDK docs, GitHub issue #115 |

## Rubric Guidance

### Upgrading Safety Dimension from `[Repo default]` to `[Engineering guidance]`

Current Safety dimension evaluations of tool grants in agent files rely on heuristic judgment. The following criteria, grounded in Tier 1 sources, replace that with specific, checkable signals.

#### A. Presence of Tool Scope Declaration

**[Engineering guidance]** An agent that modifies files, executes shell commands, or makes network requests MUST have an explicit `tools:` allowlist or `disallowedTools:` denylist in its frontmatter. Absence of either, when the agent's task scope is narrower than the parent session's full tool set, is a finding.

- Pass: `tools: [Read, Grep, Glob]` for a read-only analysis agent
- Fail: No `tools:` or `disallowedTools:` declaration in an agent that could inherit Bash + MCP tools from parent

#### B. Tool-Task Alignment

**[Engineering guidance]** Each tool in `allowedTools`/`tools:` must be traceable to a concrete step in the agent's described task. Tools present "just in case" are a finding.

Evaluation approach:
1. Read the agent's description and task body
2. For each listed tool, ask: "Which step of this agent's task requires this tool?"
3. If no step requires it: flag as over-provisioned

Reference task→tool maps (from OWASP cheat sheet + Anthropic docs):
- Read-only review: `Read, Grep, Glob` (Bash only if grep/find patterns needed)
- Code fix: add `Edit`
- Validation with DB: `Bash` with hook restricting to read-only SQL
- Document processing: `Read, search_documents` — never `execute_code` or `send_email`

#### C. High-Risk Combination Detection

**[Engineering guidance]** Any Tier A combination (A1–A5 above) present in an agent definition is a **High** finding in the Safety dimension unless the agent's CLAUDE.md or frontmatter contains explicit documented justification for why the combination is required and what mitigates the risk.

Any Tier B combination (B1–B5) without documentation is a **Medium** finding.

#### D. `disallowedTools` as Hard Deny vs. `allowedTools` as Soft Allow

**[Engineering guidance]** Agents operating in `bypassPermissions` mode or used in CI/unattended contexts MUST use `disallowedTools` (not just `allowedTools`) to enforce restrictions. `allowedTools` alone does not block tools when `bypassPermissions` is active.

- Pass: `disallowedTools: [Bash, Write, Edit]` for a read-only agent in any permission mode
- Fail: `tools: [Read, Grep]` without `disallowedTools` if the agent might run under `bypassPermissions`

#### E. MCP Tool Inheritance Explicit Handling

**[Engineering guidance]** Agents that do NOT need MCP tools should declare either `tools:` (allowlist that excludes MCP) or `disallowedTools: [mcp__*]` (denylist pattern). Silence means MCP tool inheritance — a common source of unintentional over-provisioning.

#### F. Auto-Dispatch Agents Require Stricter Scoping

**[Engineering guidance]** Agents with `disable-model-invocation: false` (auto-dispatched by the model, not only by explicit `/` invocation) MUST have narrower tool grants than manually invoked agents, because the human cannot review tool scope before each dispatch.

### Audit Signals

These signals, when present, reliably indicate over-broad tool grants and should be raised as findings:

#### Structural Signals (checkable from frontmatter alone)

1. **No `tools:` or `disallowedTools:` declaration** in an agent that handles external input or performs write/execute operations — indicates inherited-everything configuration.

2. **`allowedTools`/`tools:` includes `Bash` without a corresponding hook** restricting command scope — Bash is the broadest possible tool grant; without a hook, any shell command is permitted.

3. **`allowedTools`/`tools:` includes both a write tool (`Write`, `Edit`) and a network fetch tool (`WebFetch`, `WebSearch`, any MCP web tool)** — Tier A1/A4 combination requiring explicit justification.

4. **`allowedTools`/`tools:` includes communication MCP tools** (email, Slack, etc.) without documented approval-gate mechanism — Tier A5 pattern.

5. **Agent declares `bypassPermissions` or is called from a `bypassPermissions` context** but relies only on `tools:`/`allowedTools:` — these are nullified; needs `disallowedTools`.

6. **Zero tool scope declaration** in an agent with `user-invocable: false` (always auto-dispatched) — auto-dispatched agents with unconstrained tool access are the highest-risk configuration.

#### Semantic Signals (require reading agent body + description)

7. **Description scope is narrow (e.g., "reads and summarizes files") but tool list includes write or execute tools** — mismatch between described purpose and actual capability.

8. **Tool list includes more than 5-7 tools** for an agent with a single, well-defined task — signals "just in case" provisioning rather than task-derived minimal set.

9. **Tool list includes deprecated or development-phase tools** not referenced in the agent's current task body — stale permissions from earlier iterations.

10. **Agent processes untrusted input** (web content, user-supplied text, email, GitHub issues) AND has `Bash`, `Write`, or `Edit` in its tool list without documented mitigation — highest-risk combination per arXiv 2506.08837 and OWASP LLM06.

#### Runtime / Configuration Signals

11. **Tool call frequency anomalies** — >30 tool calls per minute from a focused single-task agent suggests unbounded tool usage.

12. **Cross-domain tool combinations** — tools from unrelated domains present in a single-purpose agent (e.g., database write + email send + file delete all in a "summarizer" agent).

## Unverified Claims and Gaps

- **Specific "lethal trifecta" terminology**: This framing appears in practitioner security blogs (Tier 2) but has not been found in a Tier 1 peer-reviewed paper with that specific label. The underlying pattern (privileged access + untrusted input + exfiltration capability) is validated by OWASP LLM06 and arXiv papers. The label itself is unverified as a standard term.

- **CI/CD post-mortem incident**: The specific "giving every GitHub user shell access" quote was found in a practitioner security analysis. The primary post-mortem URL was not retrieved; it is cross-validated by OWASP's general pattern (Tier 1) but the specific incident details should be treated as Tier 2 only.

- **`allowedTools` bypass for built-in tools outside `bypassPermissions` mode**: GitHub issue #115 documents this for the TypeScript Agent SDK. It may not apply identically to Claude Code agent frontmatter `tools:` field, which uses a different resolution path. The `bypassPermissions` nullification is confirmed by Tier 1 SDK docs.

- **MiniScope permission group taxonomy**: The paper abstract does not enumerate specific permission groups. The claim that MiniScope uses "mobile-style permission groups" is from the abstract only; the full taxonomy requires full-paper access. Flagged as partially verified.

- **Parameter-level tool risk**: Progent's finding that parameter values (not just tool identity) determine risk is Tier 1 (arXiv). The implication for `allowedTools` declarations — that listing a tool name is insufficient to capture its full risk — follows logically but is not directly tested in the context of Claude Code's frontmatter syntax specifically.
