#!/bin/bash

set -e

GIT_REPOSITORY_URL="$(git config --get remote.origin.url)"
GIT_REPOSITORY_NAME="$(basename -s .git "$GIT_REPOSITORY_URL")"
TLD="$(git rev-parse --show-toplevel)"
REL_TO_ROOT="$(realpath --relative-to="$PWD" "$TLD")"

jq -n \
  --arg git_repository_name "$GIT_REPOSITORY_NAME" \
  --arg tld "$TLD" \
  --arg rel_to_root "$REL_TO_ROOT" \
  '{"name":$git_repository_name,"tld":$tld,"rel_to_root":$rel_to_root}'