---
name: scaffold-mcp-server
description: >
  Scaffolds a single MCP server entry inside .mcp.json with valid 2026
  schema fields. Use to add a new MCP server declaration to a project's
  .mcp.json. Do NOT use to author the MCP server's executable code — this
  scaffold writes the declaration only.
argument-hint: "<server-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# MCP Server Declaration Scaffolding

You are a configuration builder for the `.mcp.json` declaration of a
single MCP server. Scope: `.mcp.json` entry only — the server itself
(executable, transport handler, tool implementations) is out of scope
per repo decision Q7. Naming guidance is repo convention, not universal.

## Workflow

### 1. Validate server name

Parse `$ARGUMENTS` as `<server-name>`.

- If the argument is empty, ask for the server name.

Validate:
- Kebab-case (lowercase, hyphens only, no spaces or underscores).
- Max 64 characters.
- No `anthropic` or `claude` substring (avoid namespace collision).
- Not already declared in the target `.mcp.json` (read it if present).

If validation fails, report the specific issue and stop. Do not continue
until a valid name is provided.

### 2. Resolve target `.mcp.json` path

Glob, in order:

1. `.mcp.json` at current working directory.
2. `<repo-root>/.mcp.json` if a `.git/` exists upwards.

If none exists, ask the user whether to create a new `.mcp.json` at the
project root, or accept a path. Confirm the chosen path before any write.

### 3. Load template

Read `references/mcp-server-template.md` for the canonical declaration
fragments (stdio + remote + 2026 schema additions). If unreadable, stop
and report: "mcp-server-template.md not found — cannot scaffold without
the canonical fragment. Verify the file exists at
skills/scaffold-mcp-server/references/mcp-server-template.md."

### 4. Gather requirements

Ask the user for the following via AskUserQuestion (one batch):

1. **Transport** — `stdio` (local subprocess) OR `remote` (sse/http URL).
2. **Command or URL** — the launch `command` + `args` for stdio, or the
   `url` for remote.
3. **Environment variables** — names + whether each is a secret. Secret
   env values MUST use `${VAR}` expansion, not literal strings.
4. **Tool count estimate** — used to decide whether to set
   `defer_loading: true` (recommend if >50 tools or >10 K description
   tokens, per `mcp-evaluation-guide.md` TD-1).

### 5. Render the entry

Render the entry from the template, substituting the gathered values.
Apply these defaults:

- `disabled: false` unless the user is registering an opt-in/optional
  server.
- `metadata.description` populated; `metadata.homepage` populated if a
  URL is known.
- `defer_loading: true` if the user reports >50 tools.
- For stdio: `command` is the binary path; `args` is the array of
  arguments. Use `${VAR}` expansion in `env`, never literal secrets.

### 6. Write to `.mcp.json`

If `.mcp.json` exists: read it, parse JSON, merge the new entry into
`mcpServers.<name>`. Reject if the name is already present (validation
should have caught this earlier — reaching this branch indicates a race;
abort).

If creating fresh `.mcp.json`: emit the minimal envelope
`{"mcpServers": { "<name>": { ... } }}`.

Use atomic write semantics — write to a sibling temp path, then rename.

### 7. Post-write checks

After write:

1. Glob for `.gitignore` at the same level as `.mcp.json`. If the new
   entry contains any `${VAR}` referencing a credential-like name
   (`*_TOKEN`, `*_SECRET`, `*_KEY`, `*_PASSWORD`), warn the user that
   `.mcp.json` MUST appear in `.gitignore` (SP-3 in
   `mcp-evaluation-guide.md`).
2. Recommend running `/review-mcp-server .mcp.json` to confirm zero
   Medium findings.

## Output

Report:

- The target file path.
- The entry rendered (compact JSON).
- The two post-write recommendations from step 7.
- Any warnings (e.g., kebab-case downgraded, defer_loading auto-enabled).

## Hard Rules

- Never write a literal secret into `env` — always `${VAR}`.
- Never write outside the resolved `.mcp.json` path.
- Never invoke the MCP server (no `claude mcp` or subprocess executions).
- Never touch the server-side executable code; this skill is declaration-
  only.
