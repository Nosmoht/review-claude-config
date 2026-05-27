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

After write, run these preflight checks. Each cites the `/review-mcp-server`
checklist ID it defends (see
`skills/review-claude-config/references/mcp-evaluation-guide.md`):

1. **MC-1, SP-2 (location)** — confirm `.mcp.json` is at project root, not
   nested in `settings.json` (the latter is silently ignored per #24477).
2. **MC-2 (required fields)** — for stdio entries, both `command` and
   (if non-empty) `args` are present; for remote, both `type` and `url`.
3. **MC-4, MC-5 (secret hygiene)** — `env` and `headers` contain no literal
   credentials; every credential-shaped value uses `${VAR}` or
   `${VAR:-default}` expansion.
4. **SP-3 (gitignore)** — Glob for `.gitignore` at the `.mcp.json` directory
   level. If the new entry contains any `${VAR}` referencing a
   credential-like name (`*_TOKEN`, `*_SECRET`, `*_KEY`, `*_PASSWORD`),
   warn the user that `.mcp.json` MUST appear in `.gitignore`.
5. **MC-9 (metadata)** — `metadata.description` is populated for non-trivial
   servers; `metadata.homepage` populated if a URL is known.
6. **TD-1 (defer_loading)** — for servers with >50 tools or >10 K
   tool-description tokens, `defer_loading: true` is set; otherwise the
   server auto-injects all tool defs at session start (~10% context cost).
7. **MG-1, MG-2 (relevance + cap)** — confirm total tool count across all
   servers stays ≤50 (warn) / ≤128 (hard limit) and the new server is
   topically distinct from existing entries (no overlap).
8. Recommend running `/review-mcp-server .mcp.json` to confirm zero High
   findings.

## Quality measurement (mandatory before Output)

Per [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) (deep-research retrofit 2026-05-26), SCAFFOLD-class verification is deterministic — `make validate` exit-0 plus idempotency plus the transport-shape assertion plus the secret-leakage sweep is the sufficient verification primitive for this output class. Adversarial-critic (Layer B) and binary-rubric (Layer C) layers were dropped because the scaffolder's contract is "did you produce a schema-valid `.mcp.json` entry with the correct transport shape and no credential leakage," not "is this a high-quality MCP-server declaration" — quality assessment belongs in `/review-mcp-server`, not here. Only Layer A (mechanical invariants) remains; the secret-leakage sweep is load-bearing because `.mcp.json` is NOT in `block-sensitive-content.sh`'s doc-class scope.

After Step 6 writes the merged `.mcp.json` and before Step 7's post-write recommendations, record the artifact path, the server name, and the chosen transport for the verification layer:

```bash
TMPDIR=$(mktemp -d -t scaffold-mcp-XXXX)
PROMISED="$TMPDIR/promised.txt"     # one absolute path per line (the .mcp.json path)
NAME_FILE="$TMPDIR/name.txt"        # the kebab-case server name from Step 1
TRANSPORT_FILE="$TMPDIR/transport.txt"   # exactly one of: stdio | remote
# Write the resolved .mcp.json absolute path to $PROMISED.
# Write the server name token from Step 1 to $NAME_FILE.
# Write the transport token from Step 4 to $TRANSPORT_FILE.
```

### Pipeline — Layer A (mechanical invariants, deterministic, fail-fast)

Run all five metrics. Any `STRICT` non-zero exit → abort and report; `SOFT` deltas → log and surface to the user, do not auto-overwrite.

**A.1 STRICT — promised `.mcp.json` exists and contains the new entry.**

```bash
fail=0
NAME=$(cat "$NAME_FILE")
while IFS= read -r p; do
  if [ ! -s "$p" ]; then
    echo "STRICT FAIL existence $p (missing or empty)"
    fail=$((fail+1))
    continue
  fi
  python3 -c "import json,sys; d=json.load(open('$p')); sys.exit(0 if '$NAME' in d.get('mcpServers',{}) else 1)" \
    || { echo "STRICT FAIL entry-missing $p (mcpServers.$NAME absent)"; fail=$((fail+1)); }
done < "$PROMISED"
```

**A.2 STRICT — `make validate` exits 0.** Runs the full chain: ruff lint, ruff format, JSON Schema, token budget, description-graph regression, pytest. A malformed `.mcp.json` (invalid JSON, schema mismatch) fails here.

```bash
( cd "$REPO_ROOT" && make validate ) > "$TMPDIR/make-validate.log" 2>&1
mv_exit=$?
[ $mv_exit -ne 0 ] && { echo "STRICT FAIL make-validate exit=$mv_exit"; fail=$((fail+1)); }
```

Additionally assert the transport-conditional shape against `$TRANSPORT_FILE`:

```bash
python3 - "$PROMISED" "$NAME_FILE" "$TRANSPORT_FILE" <<'PY'
import json, sys
path = open(sys.argv[1]).read().strip()
name = open(sys.argv[2]).read().strip()
transport = open(sys.argv[3]).read().strip()
entry = json.load(open(path))["mcpServers"][name]
fail = 0
if transport == "stdio":
    if "command" not in entry or "args" not in entry:
        print(f"STRICT FAIL transport-shape stdio missing command/args"); fail += 1
    if "url" in entry:
        print(f"STRICT FAIL transport-shape stdio has url"); fail += 1
elif transport == "remote":
    if "url" not in entry:
        print(f"STRICT FAIL transport-shape remote missing url"); fail += 1
    if "command" in entry or "args" in entry:
        print(f"STRICT FAIL transport-shape remote has command/args"); fail += 1
sys.exit(1 if fail else 0)
PY
```

**A.3 STRICT — secret-leakage sweep on the written `.mcp.json`.** Because `.mcp.json` is NOT in `block-sensitive-content.sh`'s doc-class scope, the user-global hook cannot enforce this — the sweep runs here. Source the home-path regex set from `hooks/block-sensitive-content.sh` at runtime (do NOT duplicate literals here). Apply three checks to the written file:

```bash
python3 - "$PROMISED" "$HOOK_HOME_PATTERNS_FILE" <<'PY'
import re, sys, json, pathlib
home_patterns = [line.strip() for line in open(sys.argv[2]) if line.strip()]
RFC1918 = r"\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b"
# Strict literal-secret regex: any env key whose name matches credential
# patterns must reference a ${VAR} expansion, never a literal token.
LITERAL_SECRET = r'"(?:[A-Za-z_]*(?:TOKEN|SECRET|KEY|PASSWORD|PASSWD|PAT|APIKEY|ACCESS)[A-Za-z_]*)"\s*:\s*"(?!\$\{)[^"]{4,}"'
# High-entropy token shape (>=20 chars of base64/hex/alnum without ${)
HIGH_ENTROPY = r'"[A-Za-z0-9_/+=-]{32,}"'
# GitHub PAT shape
GH_PAT = r'\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b'
# JWT shape: three base64url segments separated by dots
JWT = r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b'
fail = 0
for line in open(sys.argv[1]):
    p = pathlib.Path(line.strip())
    if not p.exists() or not p.is_file(): continue
    t = p.read_text(errors="replace")
    for pat in home_patterns:
        if re.search(pat, t):
            print(f"STRICT FAIL home-path-leak {p} pattern={pat}"); fail += 1
    if re.search(RFC1918, t):
        print(f"STRICT FAIL rfc1918-leak {p}"); fail += 1
    if re.search(LITERAL_SECRET, t):
        print(f"STRICT FAIL literal-secret {p} (credential-named env value not in ${{VAR}} form)"); fail += 1
    if re.search(GH_PAT, t):
        print(f"STRICT FAIL github-pat-shape {p}"); fail += 1
    if re.search(JWT, t):
        print(f"STRICT FAIL jwt-shape {p}"); fail += 1
    # High-entropy check restricted to env-value positions (avoid false positives on long URLs/hashes elsewhere)
    try:
        d = json.loads(t)
        for sname, sentry in d.get("mcpServers", {}).items():
            for k, v in (sentry.get("env") or {}).items():
                if isinstance(v, str) and not v.startswith("${") and re.fullmatch(HIGH_ENTROPY, f'"{v}"'):
                    print(f"STRICT FAIL high-entropy-env {p} mcpServers.{sname}.env.{k}"); fail += 1
    except Exception:
        pass
sys.exit(1 if fail else 0)
PY
```

**A.4 STRICT — path-placement matches the `.mcp.json` predicate.** The written file MUST end in `.mcp.json` (any depth). Reject any non-`.mcp.json` target:

```bash
while IFS= read -r p; do
  case "$p" in
    *.mcp.json) ;;
    *) echo "STRICT FAIL path-placement $p (not .mcp.json)"; fail=$((fail+1)) ;;
  esac
done < "$PROMISED"
```

**A.5 SOFT — `.gitignore` advisory when credential env vars are present.** If the rendered entry's `env` block contains any key matching `*_TOKEN`, `*_SECRET`, `*_KEY`, or `*_PASSWORD`, glob for `.gitignore` at the same level as the `.mcp.json` and grep for `.mcp.json`. Absence is a SOFT warning (SP-3 in `mcp-evaluation-guide.md`), not a STRICT fail — the user may have an organization-wide gitignore policy.

What each metric catches:

| Metric | Catches |
|---|---|
| A.1 file-existence + entry-presence | F1, F6 |
| A.2 `make validate` + transport-shape | F1, F2 |
| A.3 secret-leakage sweep (literal/PAT/JWT/high-entropy/RFC1918/home-path) | F7 |
| A.4 path-placement | F5 |
| A.5 `.gitignore` advisory | F7 (soft) |

### Reconciliation outcomes

- **All STRICT pass (Layer A: A.1 file + entry presence, A.2 `make validate` + transport-shape assertion, A.3 secret-leakage sweep, A.4 path predicate)** → SCAFFOLD reported successful; proceed to Step 7 post-write recommendations.
- **Any STRICT fail** → restore inline. For transport/leakage issues the fix is mechanical (re-render the entry with the missing key, redact the literal, switch transport shape, repair the env expansion). Max **2 iterations**, then surface to the user with the exact failing predicate + the candidate diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 `.gitignore` advisory missed)** → report in the Step 7 success notice but proceed. The Step 4 AskUserQuestion preview gate is the final human-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

The deterministic Layer A checks bound **structural correctness and credential hygiene**, not **quality**. Semantic defects (wrong-server-name-with-valid-form, tool-grant overreach in the running server, `.gitignore` policy false-negatives, credential-rotation drift) and template-drift detection live in `/review-mcp-server` and the 90-day baseline-refresh cadence. See [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) for the full residual catalog and per-output-class form mapping rationale. Two representative residuals worth surfacing at the Step 7 notice:

1. **Semantic-wrong server name with valid form.** A `mcpServers.<name>` whose name is schema-valid kebab-case but describes the wrong tool. All Layer A checks pass; only the Step 4 human preview gate catches.
2. **Credential rotation drift.** The entry uses `${GITHUB_TOKEN}` correctly, but the user's environment variable holds a stale or revoked token. No declarative scaffold can detect runtime-credential validity; detected only by the MCP server's own auth handshake.

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
