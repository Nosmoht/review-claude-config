---
domain: talos
last_refreshed: 2026-03-24
queries:
  - "Talos Linux cluster upgrade best practices safety gates rollback 2025 2026"
  - "Talos Linux talosctl upgrade node-by-node procedure etcd quorum safety"
sources:
  - url: https://docs.siderolabs.com/talos/v1.8/configure-your-talos-cluster/lifecycle-management/upgrading-talos
    title: "Upgrading Talos Linux - Sidero Documentation"
  - url: https://oneuptime.com/blog/post/2026-03-03-upgrade-talos-linux-control-plane-nodes-safely/view
    title: "How to Upgrade Talos Linux Control Plane Nodes Safely"
---

# Talos — Domain Best Practices

- A/B boot scheme: Talos retains previous kernel and OS image; bootloader auto-reverts on failed boot. Manual rollback via `talosctl rollback`
- Upgrade order: Upgrade Talos first, then Kubernetes. Within Talos, upgrade non-leader CP nodes first to minimize etcd leader elections
- Etcd quorum protection: Talos refuses CP upgrade if it would break quorum. Always back up etcd before starting. Verify all members healthy between each node
- Node drain: Talos auto-cordons and drains workloads before upgrade; services shut down sequentially for clean state
- Sequential only: Never upgrade all nodes simultaneously. One node at a time with health verification between each
- Per-node gates: Wait for node rejoin, etcd member recovery, Kubernetes Ready status, and system pod health before proceeding
- `--stage` flag: Use when standard upgrades fail due to persistent file handles; stages artifacts to disk and reboots
- Version matching: Match `talosctl` version to cluster version. Follow intermediate minor releases sequentially (no skipping)
- Default wait threshold: ~10 minutes between CP node upgrades for health verification
- `--preserve` flag: Prevents EPHEMERAL partition wipe during upgrade, preserving node identity
