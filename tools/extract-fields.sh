# shellcheck shell=bash
# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Prints the fields of one OPNsense model node as a YAML list; offline, no side effects.
# Usage: bash tools/extract-fields.sh <model xml> [<node below model.items, dot-separated>]
set -euo pipefail

xml=$1
node=${2:-}

if [[ ! $node =~ ^[A-Za-z0-9_.]*$ ]]; then
    echo "extract-fields: node '$node' may only hold letters, digits, _ and ." >&2
    exit 1
fi
path=".model.items${node:+.$node}"

if [ "$(yq -p xml -oy "$path | tag" "$xml")" != "!!map" ]; then
    echo "extract-fields: node '$node' not found below model.items in $xml" >&2
    exit 1
fi

read -r -d '' program <<'YQ' || true
PATH_EXPR
| to_entries
| map(select(.key | test("^[+]") | not))
| map(
    if (.value | tag) == "!!map" and (.value | has("+@type")) then [{"prefix": "", "e": .}]
    elif (.value | tag) == "!!map" then
      (.key as $c | .value | to_entries
        | map(select((.value | tag) == "!!map" and (.value | has("+@type"))))
        | map({"prefix": $c + ".", "e": .}))
    else [] end)
| flatten(1)
ROOT_FILTER
| map({
    "name": .prefix + .e.key,
    "type": (.e.value["+@type"] | split("\\") | .[-1]),
    "required": ((.e.value.Required // "") == "Y"),
    "default": .e.value.Default,
    "multiple": ((.e.value.Multiple // "") == "Y"),
    "volatile": ((.e.value["+@volatile"] // "") == "true"),
    "options": ((.e.value.OptionValues // {}) | to_entries
      | map(select(.key | test("^[+]") | not))
      | map(
          if (.value | tag) == "!!map" and ([.value | keys | .[] | select(test("^[+]") | not)] | length) > 0
          then .value | to_entries | map(select(.key | test("^[+]") | not)) | map((.value | select(tag == "!!map") | .["+@value"]) // .key)
          else [(.value | select(tag == "!!map") | .["+@value"]) // .key] end)
      | flatten)
  })
| map(with(select(.default == null); del(.default)))
| (.. | select(tag == "!!str")) style = "double"
YQ

read -r -d '' deep <<'YQ' || true
PATH_EXPR
| [to_entries | .[] | select((.value | tag) == "!!map" and (.value | has("+@type") | not))
   | .value | to_entries | .[] | select((.value | tag) == "!!map" and (.value | has("+@type") | not))
   | .value | to_entries | .[] | select((.value | tag) == "!!map" and (.value | has("+@type")))]
| length
YQ

if [ "$(yq -p xml -oy "${deep/PATH_EXPR/$path}" "$xml")" != 0 ]; then
    echo "extract-fields: node '$node' holds fields more than one container deep, which is not supported" >&2
    exit 1
fi

# A model root lists its item lists next to its fields; each list is its own area.
root_filter='| map(select(.e.value["+@type"] | test("ArrayField$") | not))'
[ -n "$node" ] && root_filter=''
program=${program/ROOT_FILTER/$root_filter}
out=$(yq -p xml -oy "${program/PATH_EXPR/$path}" "$xml")
if [ "$out" = "[]" ]; then
    echo "extract-fields: node '$node' below model.items in $xml holds no fields" >&2
    exit 1
fi
printf '%s\n' "$out"
