---
domain: kubernetes-platform-reliability
last_refreshed: 2026-03-24
queries:
  - "Kubernetes platform reliability review best practices infrastructure code review 2025 2026"
  - "Claude Code agent SKILL.md prompt engineering best practices for code review agents"
sources:
  - url: https://komodor.com/learn/14-kubernetes-best-practices-you-must-know-in-2025/
    title: "14 Kubernetes Best Practices You Must Know in 2025"
  - url: https://cast.ai/blog/enterprise-kubernetes-best-practices/
    title: "Enterprise Kubernetes Best Practices"
  - url: https://www.cncf.io/blog/2025/12/15/kubernetes-security-2025-stable-features-and-2026-preview/
    title: "Kubernetes Security: 2025 Stable Features and 2026 Preview"
---

# Kubernetes Platform Reliability — Domain Best Practices

- Pre-merge reviews must check resource requests/limits, RBAC least-privilege, network policy completeness, and secret management hygiene
- Every infrastructure change requires a documented rollback plan with estimated recovery time and dependency ordering
- GitOps workflows should enforce PR-based approval gates, automated policy validation, and audit trails
- Pre-deployment validation: YAML schema compliance, admission controller policies, resource quota availability
- Reviews should confirm observability instrumentation: health probes, alert thresholds, log aggregation for changed components
- Container image provenance and vulnerability scanning status should be verified during review
- 99.94% of clusters are over-provisioned (Cast AI 2025 benchmark) — resource limit review is high-impact
- Kubernetes 1.32-1.35 graduated key security features to stable; reviews should verify alignment with current hardening guidance
- Severity-based finding classification (BLOCKING/WARNING/INFO) with deterministic output format enables downstream automation
- Read-only tool scoping for reviewer agents is textbook least-privilege and prevents accidental mutations
