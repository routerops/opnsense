# shellcheck shell=bash
# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Writes meta/fields/<id>.yml from each entry's model XML at its newest tested version; needs network.
# Usage: bash tools/fetch-fields.sh <catalog> [<id>]; run from the repository root (make fields).
set -euo pipefail

catalog=$1
only=${2:-}
tmp=$(mktemp -d)
trap 'rm -r "$tmp"' EXIT
mkdir -p meta/fields

ids=$(yq '.opnsense_areas | keys | .[]' "$catalog")
if [ -n "$only" ] && ! grep -qx "$only" <<<"$ids"; then
    echo "fetch-fields: no catalog entry '$only' in $catalog" >&2
    exit 1
fi

for id in $ids; do
    [ -z "$only" ] || [ "$id" = "$only" ] || continue
    repo=$(yq ".opnsense_areas.$id.model.repo" "$catalog")
    file=$(yq ".opnsense_areas.$id.model.file" "$catalog")
    node=$(yq ".opnsense_areas.$id.model.node // \"\"" "$catalog")
    version=$(yq ".opnsense_areas.$id.tested[-1]" "$catalog")
    url="https://raw.githubusercontent.com/opnsense/$repo/$version/$file"
    if ! curl -fsSL "$url" -o "$tmp/$id.xml"; then
        echo "fetch-fields: entry '$id': download of $url failed" >&2
        exit 1
    fi
    if ! bash tools/extract-fields.sh "$tmp/$id.xml" "$node" > "$tmp/$id.fields.yml"; then
        echo "fetch-fields: entry '$id' failed" >&2
        exit 1
    fi
    {
        printf '# SPDX-%s: routerops.opnsense contributors\n' FileCopyrightText
        printf '# SPDX-%s: GPL-3.0-or-later\n' License-Identifier
        printf '# Generated from the OPNsense model XML by make fields; do not edit.\n---\n'
        V=$version S="opnsense/$repo@$version:$file${node:+#$node}" F="$tmp/$id.fields.yml" \
            yq -n '.version = strenv(V) | .source = strenv(S) | .fields = load(strenv(F)) | (.. | select(tag == "!!str")) style = "double"'
    } > "$tmp/$id.out"
    mv "$tmp/$id.out" "meta/fields/$id.yml"
    echo "meta/fields/$id.yml: $version"
done
