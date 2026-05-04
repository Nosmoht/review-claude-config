#!/usr/bin/env bash
# Sync marketplace.json plugins[0].{version,source.ref} from plugin.json#version.
# Format-preserving (regex-targeted) so inline owner/tags/source stay inline.
# Idempotent. Run after release-please-action bumps plugin.json#version.
set -euo pipefail
PLUGIN=".claude-plugin/plugin.json"
M=".claude-plugin/marketplace.json"
[[ -f "$PLUGIN" && -f "$M" ]] || { echo "sync-marketplace-ref: missing input files" >&2; exit 1; }
VERSION=$(jq -r '.version' "$PLUGIN")
REF="v${VERSION}"
SEMVER='[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?'
# plugins[0].source.ref — anchored to the source-object's "ref" key.
# `-e :a -e N -e $!ba` slurps the file so regex can span newlines (BSD sed has
# no -z; semicolon-joined `:a;N;$!ba;` is GNU-only — use separate -e flags).
sed -E -i.bak -e ':a' -e 'N' -e '$!ba' -e 's|("source"[[:space:]]*:[[:space:]]*\{[^}]*"ref"[[:space:]]*:[[:space:]]*)"v'"${SEMVER}"'"|\1"'"${REF}"'"|' "$M"
# plugins[0].version — first "version" after "plugins": [ (skips metadata.version)
awk -v ver="$VERSION" '
  /"plugins"[[:space:]]*:[[:space:]]*\[/ { in_p=1 }
  in_p == 1 && /"version"[[:space:]]*:[[:space:]]*"[^"]+"/ {
    sub(/"version"[[:space:]]*:[[:space:]]*"[^"]+"/, "\"version\": \"" ver "\""); in_p=2
  }
  { print }' "$M" > "${M}.new" && mv "${M}.new" "$M"
rm -f "${M}.bak"
# Verify on-disk: jq catches structural drift / malformed substitutions / missing keys.
JV=$(jq -r '.plugins[0].version' "$M")
JR=$(jq -r '.plugins[0].source.ref' "$M")
[[ "$JV" == "$VERSION" && "$JR" == "$REF" ]] || { echo "sync-marketplace-ref: verify failed (version=$JV ref=$JR want=$VERSION/$REF)" >&2; exit 1; }
echo "sync-marketplace-ref: version=$VERSION, ref=$REF"
