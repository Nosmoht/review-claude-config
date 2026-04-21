---
last_refreshed: 2026-04-19
---

# Claude Code Plugin System

Authoritative reference for `.claude-plugin/plugin.json` manifest schema, marketplace distribution, skill/agent namespacing, validation tooling, and known failure modes. Written for the `/review-plugin` skill and for any plugin maintainer in this repo.

## TL;DR

- Plugin manifest requires exactly 3 fields: `name`, `description`, `version`. 12 optional fields cover author, homepage, license, keywords, and component paths.
- **Components MUST live in the plugin root** (`skills/`, `agents/`, `hooks/`, `commands/`), **not** inside `.claude-plugin/`. This is the single most common failure mode and silent — the plugin loads without components and emits no error.
- Skill and agent invocation uses plugin-scoped namespacing: `/plugin-name:skill-name`. Standalone skills in `.claude/skills/` call without a prefix.
- `claude plugin validate .` validates JSON syntax, YAML frontmatter, required fields, and marketplace duplicate-name checks.
- Marketplace names `claude-code-*`, `anthropic-*`, and variants like `official-claude-plugins` are reserved.

## Manifest Schema (`.claude-plugin/plugin.json`)

### Required fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, max 64 chars, unique across loaded plugins, cannot contain "anthropic" or "claude" as substring |
| `description` | string | max 1024 chars, no XML tags, surfaced in marketplace UI |
| `version` | string | semver (e.g. `1.0.0`, `2.1.0-beta`) |

### Optional metadata fields

| Field | Type | Notes |
|-------|------|-------|
| `author` | object | `{ name: string, email?: string }` |
| `homepage` | string | Full URL |
| `repository` | string | Full URL |
| `license` | string | SPDX identifier (e.g. `MIT`, `Apache-2.0`) |
| `keywords` | array | Tags for discovery |

### Component path fields (optional)

| Field | Type | Notes |
|-------|------|-------|
| `skills` | string \| array | Default `skills/`; each entry a directory relative to plugin root |
| `agents` | string \| array | Default `agents/`; file or directory |
| `commands` | string | Legacy — prefer `skills/` |
| `hooks` | string \| object | Path to `hooks.json` or inline hook-event object |

All component paths are **relative to the plugin root**, never to `.claude-plugin/`.

## Marketplace Manifest (`.claude-plugin/marketplace.json`)

```json
{
  "name": "company-tools",
  "owner": { "name": "Team", "email": "team@example.com" },
  "metadata": { "description": "Internal plugin catalog", "version": "1.0.0" },
  "plugins": [
    {
      "name": "review-plugin",
      "source": "./plugins/review-plugin",
      "description": "Code review automation",
      "version": "1.0.0",
      "category": "development",
      "tags": ["review", "quality"]
    }
  ]
}
```

### Plugin `source` variants

| Variant | Example |
|---------|---------|
| Relative path (git-based marketplaces only) | `"source": "./plugins/my-plugin"` |
| GitHub | `"source": { "source": "github", "repo": "owner/repo", "ref": "v1.0.0", "sha": "..." }` |
| Git URL (GitLab, etc.) | `"source": { "source": "url", "url": "https://...", "ref": "main" }` |
| Git subdirectory (monorepos) | `"source": { "source": "git-subdir", "url": "...", "path": "tools/plugin", "ref": "main" }` |
| npm registry | `"source": { "source": "npm", "package": "@acme/plugin", "version": "^2.0.0" }` |

### Reserved marketplace names

`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, and any imitation (`official-claude-plugins`, `official-anthropic-*`). Pick a distinct brand name.

## Installation and Namespacing

| Method | Command | Use Case |
|--------|---------|----------|
| Dev testing | `claude --plugin-dir ./my-plugin` | Local plugin development |
| Marketplace install | `/plugin install <name>@<marketplace>` | Install from registered marketplace |
| Register marketplace | `/plugin marketplace add <owner>/<repo>` | Add a GitHub marketplace |
| Update marketplaces | `/plugin marketplace update` | Pull latest versions |

**Load order (higher wins on skill-name collisions):** `--plugin-dir` (dev override) > marketplace-installed > managed-settings forced plugins. Managed settings can override `--plugin-dir` when the org policy enforces it.

**Namespacing:**
- Standalone skill in `.claude/skills/hello/`: invoked as `/hello`.
- Plugin skill in `plugin-a/skills/hello/`: invoked as `/plugin-a:hello`.
- Two plugins with the same skill name coexist because they carry distinct namespaces.

Plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` on install. Relative paths like `../shared-utils` do not resolve across the cache boundary — inline all dependencies.

## Validation Tooling

```bash
claude plugin validate .
# Or from inside Claude Code:
/plugin validate .
```

Validates:
- JSON syntax in `plugin.json` and `marketplace.json`
- YAML frontmatter in skills, agents, commands
- Required-field presence
- Schema compliance
- Duplicate plugin names in a marketplace

Common validation errors:

| Error | Root cause | Fix |
|-------|------------|-----|
| `File not found: .claude-plugin/marketplace.json` | Manifest missing | Create it |
| `Invalid JSON syntax: Unexpected token` | JSON error | Check commas, quotes |
| `Duplicate plugin name "x"` | Marketplace collision | Rename plugins |
| `plugins[0].source: Path contains ".."` | Unsafe relative path | Use `./` relative to marketplace root |
| `YAML frontmatter failed to parse` | Bad YAML in skill/agent | Fix frontmatter syntax |

## Top 5 Failure Modes

1. **Components placed in `.claude-plugin/`** — Silent load failure. Move `skills/`, `agents/`, `hooks/` to plugin root.
2. **Relative paths in URL-based marketplaces** — `"./plugins/x"` does not resolve when the marketplace itself is fetched from a URL. Use GitHub/git-URL sources or inline.
3. **Version conflict between `plugin.json` and `marketplace.json`** — `plugin.json` silently wins; the marketplace version is ignored. Keep version in one place (`plugin.json`).
4. **Non-kebab-case skill names** — Load locally but rejected by the official marketplace. Stick to `lowercase-with-hyphens`.
5. **Private repos without auth token** — Background auto-updates fail silently. Set `GITHUB_TOKEN`/`GH_TOKEN` or `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` to preserve cache on failure.

## Marketplace Compliance (Anthropic submission)

Submission surfaces: `https://claude.ai/settings/plugins/submit`, `https://platform.claude.com/plugins/submit`.

Gating criteria (inferred from public docs; formal guidelines not yet published):
- kebab-case naming
- No hardcoded credentials
- Meaningful description, functional, tested
- Organization-level restrictions possible via `strictKnownMarketplaces` in managed settings:

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme/approved-plugins" }
  ]
}
```

## Sources

Tier 1 (authoritative):
- [Claude Code — Create Plugins](https://code.claude.com/docs/en/plugins) — accessed 2026-04-19
- [Claude Code — Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — accessed 2026-04-19
- [Claude Code — Plugins Reference](https://code.claude.com/docs/en/plugins-reference) — schema details
- [Claude Code — Discover Plugins](https://code.claude.com/docs/en/discover-plugins) — installation & usage

Tier 2:
- Local research: `research/claude-code/skill-agent-format-conventions.md`

Open gaps flagged during research:
- Plugin schema versioning (how future `plugin.json` schema changes are signaled) — not documented.
- Formal marketplace-submission validation ruleset — not published.
- Backward-compatibility semantics for major plugin upgrades — not documented.
- Performance limits on plugin count — not documented.

## Implementation Checklist for `/review-plugin`

- [ ] `.claude-plugin/plugin.json` present with 3 required fields
- [ ] Components in plugin root, not in `.claude-plugin/`
- [ ] Skill namespacing verified: `/plugin-name:skill-name`
- [ ] `plugin.json` and `marketplace.json` versions consistent
- [ ] No reserved marketplace names
- [ ] `claude plugin validate` passes
- [ ] No hardcoded credentials in manifest
- [ ] Private-repo auth documented if applicable
