---
domain: assumption-framework
last_refreshed: 2026-04-03
queries:
  - "structured assumption management AI agents knowledge classification governance 2024 2025"
  - "assumption ledger knowledge classification framework AI decision governance site:arxiv.org OR site:acm.org OR site:ieee.org OR site:martinfowler.com"
sources:
  - url: https://reports.weforum.org/docs/WEF_AI_Agents_in_Action_Foundations_for_Evaluation_and_Governance_2025.pdf
    title: "AI Agents in Action: Foundations for Evaluation and Governance"
    tier: 2
  - url: https://air-governance-framework.finos.org/
    title: "FINOS AI Governance Framework"
    tier: 1
  - url: https://pmc.ncbi.nlm.nih.gov/articles/PMC12913532/
    title: "An auditable and source-verified framework for clinical AI decision support: integrating retrieval-augmented generation with data provenance"
    tier: 1
---

# Assumption Framework — Domain Best Practices

**Knowledge classification**
- Epistemic typing (fact vs. assumption vs. unknown) is foundational to defensible AI governance; mixing classes inflates apparent confidence and undermines audit trails (FINOS AI Governance Framework, Tier 1).
- Knowledge types map to three tiers: explicit (documented), implicit (inferable), tacit (experiential). Structured assumption frameworks must enforce explicit labeling because implicit and tacit knowledge is routinely mistaken for fact under time pressure.
- Confidence levels must be structurally constrained, not self-reported: agents that self-assign confidence without class-based rules systematically inflate scores.

**Falsifiability and auditability**
- Clinical AI governance literature (PMC 2025, Tier 1) requires each decision-support assertion to carry provenance metadata and explicit falsification criteria — directly supports `what_confirms_it` / `what_falsifies_it` columns in assumption ledgers.
- A Decision Traceability Model links inputs, assumptions, approvals, and overrides into a directed graph; assumption ledgers implement a simplified row-oriented version of this pattern.

**Archetype and gap-filling**
- Sector archetypes function as prior distributions over unknown domains. WEF 2025 (Tier 2): agent classification by role and operational context is the standard method for filling gaps when direct evidence is unavailable.
- Gap entries should carry explicit reasoning basis to remain auditable; unlabeled defaults erode trust in the ledger over time.

**Confirmation gates for write operations**
- Governance frameworks uniformly require that any write to an auditable record be preceded by a human-in-the-loop or explicit approval step, particularly when prior versions exist (FINOS, Tier 1).

**Trigger and activation precision**
- Agent descriptions used as activation signals should echo domain vocabulary (e.g., "governance placement", "knowledge class", rule identifiers) so orchestrators route accurately at scale (WEF 2025, Tier 2).
