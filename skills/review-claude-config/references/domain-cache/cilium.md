---
domain: cilium
last_refreshed: 2026-03-24
queries:
  - "Cilium network policy debugging best practices hubble troubleshooting 2025 2026"
  - "Cilium CiliumNetworkPolicy least privilege policy design patterns"
sources:
  - url: https://support.tools/post/cilium-troubleshooting-2025/
    title: "Advanced Cilium Troubleshooting Guide for 2025"
  - url: https://www.cncf.io/blog/2025/11/06/safely-managing-cilium-network-policies-in-kubernetes-testing-and-simulation-techniques/
    title: "Safely managing Cilium network policies in Kubernetes (CNCF)"
  - url: https://docs.cilium.io/en/stable/operations/troubleshooting/
    title: "Cilium Troubleshooting Documentation"
  - url: https://www.datadoghq.com/blog/cilium-network-policy-misconfigurations/
    title: "Datadog: CiliumNetworkPolicy Misconfigurations"
---

# Cilium — Domain Best Practices

- Evidence-first: always capture drop verdicts via Hubble or cilium-dbg monitor before proposing policy changes
- Use audit mode (`policy.cilium.io/audit-mode`) to validate policies before enforcement; verdicts appear as AUDIT not DROP
- EnableDefaultDeny field in CNP specs provides policy-centric control over enforcement behavior per-direction
- Hubble `policy_match_type` field reveals why verdicts occurred (L3-only, L3/L4, L7, implicit allow, explicit deny, audit)
- Implement L7 allow-all scaffolding before restrictive L7 rules to prevent unexpected drops
- Inspect eBPF maps for capacity issues; connection tracking table saturation causes silent drops
- Enable targeted debug logging (`debug-verbose map[datapath:true policy:true]`) rather than global debug to minimize performance impact
- Automate diagnostic scripts for controller status, policy computation, endpoint health, and service backend sync
- Cilium only supports consecutive minor releases for upgrade and rollback; staged path required for multi-minor hops
- Use `cilium preflight check` before upgrades to validate cluster readiness
