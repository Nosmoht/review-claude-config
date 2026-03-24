---
domain: linux-kernel-tuning
last_refreshed: 2026-03-24
queries:
  - "Linux kernel sysctl tuning best practices Kubernetes nodes 2025 2026"
  - "Talos Linux kernel parameters optimization container workloads sysctl boot parameters"
sources:
  - url: https://overcast.blog/kernel-tuning-and-optimization-for-kubernetes-a-guide-a3bdc8f7d255
    title: "Kernel Tuning and Optimization for Kubernetes: A Guide"
  - url: https://peterwoods.online/blog/tuning-linux-for-kubernetes
    title: "Tuning Linux for Kubernetes"
  - url: https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/
    title: "Using sysctls in a Kubernetes Cluster"
  - url: https://github.com/siderolabs/talos/issues/4654
    title: "Talos Kernel Default Values Issue #4654"
---

# Linux Kernel Tuning — Domain Best Practices

- Talos KSPP enforced defaults: `slab_nomerge`, `pti=on`, `init_on_alloc=1`. Never duplicate in config patches
- Network: `net.core.somaxconn=65535`, `net.ipv4.tcp_fastopen=3`, `tcp_window_scaling=1`, `rmem_max/wmem_max=8388608`
- Filesystem: `fs.file-max=2097152`, `fs.inotify.max_user_watches=524288`, `fs.aio-max-nr=1048576`. Inotify exhaustion causes subtle K8s failures
- Memory: `transparent_hugepage=madvise` for K8s. Scale `vm.min_free_kbytes` by RAM (64MB/32GB, 128MB/64GB+)
- I/O: `none` scheduler for NVMe/SSD, `mq-deadline` for HDD. Boot-param `elevator=none` affects ALL devices
- CPU: `mitigations=auto` default; `mitigations=off` gives 5-20% perf but serious security risk. Prefer selective CVE overrides
- Process: `kernel.pid_max=4194304` for large clusters
- Talos-specific: No shell access; all tuning via machine config API. Boot params burned into UKI image, require `talosctl upgrade`. Sysctls are runtime-tunable without reboot
- Kubernetes classifies sysctls as safe/unsafe. Test extensively before production
- Dirty page tuning: adjust `vm.dirty_ratio` and `vm.dirty_background_ratio` based on disk speed and RAM
