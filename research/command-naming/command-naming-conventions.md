# Command Naming Conventions: Evidence-Based Findings

Research compiled 2026-03-26. Covers CLI commands, slash commands, and plugin/skill naming across authoritative sources.

## 1. CLI Command Naming Conventions

### GNU/POSIX Standards

- Program names: lowercase only, dashes to separate words if needed. No camelCase, no underscores.
- Short options: single hyphen + single letter (`-v`). POSIX-defined.
- Long options: double hyphen + lowercase hyphenated words (`--verbose`). GNU convention, not POSIX.
- All programs should support `--version` and `--help`.
- Long-form options should always exist alongside short forms for scriptability.

Sources:
- [GNU Coding Standards: Command-Line Interfaces](https://www.gnu.org/prep/standards/html_node/Command_002dLine-Interfaces.html)
- [POSIX Utility Conventions](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html)
- [GNU C Library: Argument Syntax](https://www.gnu.org/software/libc/manual/html_node/Argument-Syntax.html)

### clig.dev (Command Line Interface Guidelines)

- Command names: "simple, memorable word" using "only lowercase letters, and dashes if you really need to."
- Short names reserved for frequently-used utilities (`cd`, `ls`, `ps`). Longer names acceptable for niche tools.
- Typability matters: "plum" was renamed to "fig" because the original was physically awkward to type.
- "Avoid ambiguous or similarly-named commands" -- having both `update` and `upgrade` creates confusion.
- Do not allow "arbitrary abbreviations of subcommands" to prevent future compatibility issues.
- For multi-level subcommands: "either noun verb or verb noun ordering works, but noun verb seems to be more common."
- Use consistent ordering across the entire command hierarchy.

Source: [Command Line Interface Guidelines](https://clig.dev/)

### Ergonomics and Naming Quality (Smallstep Analysis)

- Short names (2-5 chars) for frequently-used commands; longer names acceptable for niche tools.
- Verb-based names work well: `curl` ("see URL") is praised as excellent naming.
- Semantic meaninglessness is acceptable if the name is typeable and brief (`vim`, `emacs`).
- Anti-patterns: generic descriptors (`tool`, `kit`, `util`), shift-key requirements (`VirtualBox`), version numbers in names (`python3.7m`), overly broad claims (`convert`).
- Ergonomic test: can you type it comfortably with one hand while using a mouse?

Source: [The Poetics of CLI Command Names](https://smallstep.com/blog/the-poetics-of-cli-command-names/)

## 2. Verb-Noun vs Noun-Verb Patterns in Major CLIs

### Pattern Summary Across CLIs

| CLI | Pattern | Example |
|-----|---------|---------|
| kubectl | verb-noun | `kubectl get pods`, `kubectl delete service` |
| docker (management) | noun-verb | `docker container ls`, `docker image rm` |
| git | noun-verb (with subcommands) | `git remote add`, `git branch delete` |
| gh (GitHub CLI) | noun-verb | `gh pr create`, `gh issue list` |
| aws | noun-verb | `aws s3 ls`, `aws sts get-caller-identity` |
| PowerShell | verb-noun | `Get-Process`, `Remove-Item` |
| fn (proposed) | verb-noun | `fn create app`, `fn list apps` |

### kubectl: Verb-Noun

Syntax: `kubectl [command] [TYPE] [NAME]` where command is the verb (get, create, delete, describe) and TYPE is the noun (pods, services, deployments). Verbs come first, nouns second.

Source: [Overview of kubectl](https://kubernetes.io/docs/reference/kubectl/)

### Docker: Noun-Verb (Management Commands)

Docker introduced "management commands" to organize its growing command set. Pattern: `docker <noun> <verb>`. Example: `docker container ls` replaced `docker ps`; `docker image rm` replaced `docker rmi`. Rationale: same verbs reusable across different resource types. "More descriptive, less error-prone and is therefore recommended."

Source: [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)

### GitHub CLI: Noun-Verb

Pattern: `gh <noun> <verb>`. Examples: `gh pr create`, `gh issue list`, `gh repo clone`. The noun (pr, issue, repo) groups related operations.

Source: [GitHub CLI Manual](https://cli.github.com/manual/)

### AWS CLI: Noun-Verb

Pattern: `aws <service> <operation>`. The service name is the noun, the operation is the verb. Example: `aws s3 ls`, `aws ec2 describe-instances`.

Source: [AWS CLI Command Structure](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-commandstructure.html)

### PowerShell: Verb-Noun (Enforced Convention)

PowerShell is the only major system that formally enforces verb-noun with a curated list of ~98 approved verbs. Pattern: `Verb-Noun` (e.g., `Get-Process`, `Set-Variable`, `Remove-Item`).

Key design rules:
- Never use synonyms: always `Remove`, never `Delete` or `Eliminate`.
- Paired verbs: `Add/Remove`, `Enable/Disable`, `Open/Close`, `Connect/Disconnect`, `Lock/Unlock`, `Show/Hide`, `Start/Stop`.
- Distinguish similar verbs precisely: `New` (create resource) vs `Set` (modify existing); `Find` (look for object) vs `Search` (create reference); `Get` (retrieve info) vs `Read` (extract from open resource); `Invoke` (synchronous) vs `Start` (asynchronous).

Source: [Approved Verbs for PowerShell Commands](https://learn.microsoft.com/en-us/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands?view=powershell-7.5)

### Usability Comparison

Noun-verb advantages:
- Better auto-completion: after typing the noun, the verb list is constrained to valid operations on that resource type.
- Removes modes: selecting an object first allows easy deselection/change before committing to an action.
- Grouping: all operations on a resource type are co-located in help output.

Verb-noun advantages:
- Reads like natural English imperative: "Get the process", "Remove the item".
- PowerShell demonstrates it scales to large ecosystems with enforced verb vocabulary.
- Fn CLI proposal argues it is "more intuitive, human-readable."

The clig.dev guide observes noun-verb "seems to be more common" in modern CLIs.

Sources:
- [Usability First: Noun-Verb Paradigm](https://www.usabilityfirst.com/glossary/noun-verb-paradigm/index.html)
- [Fn CLI Verb-Noun Proposal](https://github.com/fnproject/cli/wiki/CLI-Proposal:--verb--noun--structure)
- [Hacker News: Verb-Noun vs Noun-Verb Discussion](https://news.ycombinator.com/item?id=21271212)

## 3. Slash Command Naming Conventions

### Slack

- Names must be descriptive yet concise: "easy to recall and type."
- Avoid generic names (`/search`) -- prefer scoped names (`/confluence-search`, `/zendesk-ticket`).
- Brand-prefixed names work well for recognition (`/lyft`, `/uber`).
- Slash commands are NOT namespaced -- name collisions are possible. Choose unique names.
- Support `/command help` as a default action.
- Avoid copyrighted brand names you do not own.

Sources:
- [Slack: Slash Commands Style Guide](https://medium.com/slack-developer-blog/slash-commands-style-guide-4e91272aa43a)
- [Slack: Implementing Slash Commands](https://docs.slack.dev/interactivity/implementing-slash-commands/)

### Discord

- Names must match regex `^[-_'\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` -- lowercase required, 1-32 chars.
- No capital letters, no spaces. Hyphens and underscores allowed.
- Command names are unique per application per scope.
- Maximum 8000 characters for combined name + description + value properties.

Source: [Discord: Application Commands](https://discord.com/developers/docs/interactions/application-commands)

### Common Slash Command Patterns

Both Slack and Discord favor:
- Short, lowercase names.
- Hyphens as word separators (not underscores).
- Descriptive action-oriented names.
- No spaces or special characters beyond hyphens/underscores.

## 4. Plugin/Skill Naming Conventions

### Prefix-Based Discovery

Multiple systems use a standard prefix for plugin discovery:
- Docker CLI: plugins must be executables named `docker-<name>`.
- Confluent CLI: plugin filenames must begin with `confluent-`, with subcommands separated by dashes.
- Manim: plugins prefixed with `manim-` for PyPI discoverability.
- WordPress: plugin directory name should match the plugin slug; use hyphens, not underscores.

### Fully Qualified Names (Namespace Collision Prevention)

- Kubebuilder: plugins use DNS1123 labels with domain suffixes (e.g., `go.kubebuilder.io`). Both `go.kubebuilder.io` and `go.example.com` can coexist.
- Modern.js: `plugin-xxx` or `@scope/plugin-xxx` pattern.

### GitHub CLI Extensions

- Extensions are repositories named `gh-<name>`.
- The `gh-` prefix is required for discovery and installation.

Sources:
- [Docker CLI Plugin Architecture](https://deepwiki.com/docker/cli/3-plugin-architecture)
- [Kubebuilder: CLI and Plugins](https://book.kubebuilder.io/plugins/extending/extending_cli_features_and_plugins)
- [WordPress Plugin Best Practices](https://developer.wordpress.org/plugins/plugin-basics/best-practices/)
- [GitHub CLI: Creating Extensions](https://docs.github.com/en/github-cli/github-cli/creating-github-cli-extensions)
- [Confluent CLI Plugins](https://docs.confluent.io/confluent-cli/current/plugins.html)

## 5. Discoverability and Memorability

### How Users Discover Commands

Users follow a predictable hierarchy when learning a new CLI:
1. Tab-completion (type partial name + Tab)
2. Run command with no args to see usage
3. Try `-h`, then `--help`, then `help` subcommand
4. Read man pages
5. Search the internet

Source: [Ubuntu: Command-Line Usability](https://ubuntu.com/blog/command-line-usability-a-terminal-users-thought-process)

### Memorability Principles

- Use "familiar words where possible (e.g., `help`, `clean`, `create`)."
- Maintain "a clear philosophy behind your use of subcommands vs options, verbs vs nouns."
- Use long-form options in documentation for self-explanation.
- Discoverable CLIs: comprehensive help text, lots of examples, suggest next commands, suggest fixes on errors.

Sources:
- [Ubuntu: Command-Line Usability](https://ubuntu.com/blog/command-line-usability-a-terminal-users-thought-process)
- [Command Line Interface Guidelines](https://clig.dev/)
- [UX Patterns for CLI Tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools)

### Research Gaps

The Ubuntu blog explicitly notes: formal UX research on CLI naming and command recall is scarce. Most conventions are derived from practitioner consensus rather than controlled studies. The open questions include: Do users prefer subcommands or options? Noun-verb or verb-noun? These remain empirically untested.

Source: [Ubuntu: Command-Line Usability](https://ubuntu.com/blog/command-line-usability-a-terminal-users-thought-process)

## Summary of Cross-Cutting Findings

| Principle | Evidence Strength | Sources |
|-----------|-------------------|---------|
| Lowercase only, hyphens as separators | Strong (GNU, POSIX, clig.dev, Discord, Slack) | 6+ authoritative sources |
| Short names for frequent commands | Strong (clig.dev, Smallstep, GNU) | 3+ sources |
| Noun-verb more common in modern CLIs | Moderate (docker, gh, aws, git vs kubectl, PowerShell) | clig.dev observation + CLI survey |
| Avoid synonyms, pick one verb per action | Strong (PowerShell enforced, clig.dev recommended) | 2 authoritative sources |
| Prefix-based plugin discovery | Strong (docker, gh, confluent, manim) | 4+ systems |
| Namespace/scope names to prevent collision | Strong (Slack, kubebuilder, Discord) | 3+ systems |
| No formal UX research on naming recall | Acknowledged gap | Ubuntu blog |
