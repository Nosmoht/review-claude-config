---
domain: argocd
last_refreshed: 2026-03-24
queries:
  - "ArgoCD sync failure troubleshooting best practices 2025 2026"
  - "ArgoCD application health triage remediation patterns GitOps"
sources:
  - url: https://argo-cd.readthedocs.io/en/latest/operator-manual/health/
    title: "Resource Health - Argo CD Official Docs"
  - url: https://oneuptime.com/blog/post/2026-02-26-argocd-sync-failed-events/view
    title: "How to Handle Sync Failed Events in ArgoCD"
  - url: https://oneuptime.com/blog/post/2026-02-26-argocd-runbook-sync-loop/view
    title: "ArgoCD Runbook: Application Stuck in Sync Loop"
---

# ArgoCD — Domain Best Practices

- Health states: Healthy, Progressing, Degraded, Suspended. Application health = worst health of immediate children
- Sync failure diagnosis: Check `operationState.message` first; if empty, inspect argocd-application-controller and argocd-repo-server logs
- Common failure classes: immutable field changes, CRD ordering, webhook drift/rejection, RBAC permission denied, resource quota exceeded, sync loops from external controllers (HPA, VPA, cert-manager), hook failures
- Sync loops: Caused by external controllers modifying ArgoCD-managed fields. Fix with `ignoreDifferences` on drifting fields or `jqPathExpressions`
- Custom health checks: Lua scripts in `argocd-cm` ConfigMap. Use `argocd.argoproj.io/ignore-healthcheck: "true"` to exclude from health
- Retry policy: Configure `syncPolicy.retry` with exponential backoff (limit, duration, factor, maxDuration)
- GitOps safety: Never `kubectl apply` managed resources. Clear stale operation state with JSON patch, then trigger git-based resync
- Sync waves execute in ascending numeric order; omitted annotation = wave 0
- Use `argocd app get <app> -o json` for structured diagnostic output
- Pre/post-sync hooks: Check hook pod logs with `kubectl logs -l app.kubernetes.io/managed-by=argocd`
