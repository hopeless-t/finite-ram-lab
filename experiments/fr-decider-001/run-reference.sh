#!/usr/bin/env bash
set -euo pipefail

# Prepare a pinned Strands Decider worktree and copy the FR-DECIDER configs into it.
# This script intentionally does not start a multi-hour training run automatically.

UPSTREAM_URL="https://github.com/strands-labs/strands-decider.git"
UPSTREAM_SHA="890947e7ccd44c3de4115e26a7f46cc5c3147b44"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="${FR_DECIDER_WORK:-${ROOT}/.work/fr-decider-001}"

mkdir -p "$(dirname "${WORK}")"
if [[ ! -d "${WORK}/.git" ]]; then
  git clone "${UPSTREAM_URL}" "${WORK}"
fi

git -C "${WORK}" fetch origin "${UPSTREAM_SHA}"
git -C "${WORK}" checkout --detach "${UPSTREAM_SHA}"

python -m pip install -e "${WORK}"

cp "${ROOT}/experiments/fr-decider-001/config-qwen35-0p8b.yaml"    "${WORK}/configs/fr-decider-qwen35-0p8b.yaml"
cp "${ROOT}/experiments/fr-decider-001/config-qwen25-0p5b.yaml"    "${WORK}/configs/fr-decider-qwen25-0p5b.yaml"

cat <<EOF
Pinned Strands worktree ready:
  ${WORK}
  commit: ${UPSTREAM_SHA}

Next, inside that worktree, reproduce the upstream corpus/teacher pipeline first.
Then run ONE lane at a time:

  strands-decider train --config configs/fr-decider-qwen35-0p8b.yaml
  strands-decider calibrate checkpoints/kitten-decider-qwen35-0p8b --data data/holdout_v5_norule.jsonl

or

  strands-decider train --config configs/fr-decider-qwen25-0p5b.yaml
  strands-decider calibrate checkpoints/kitten-decider-qwen25-0p5b --data data/holdout_v5_norule.jsonl

Do not publish a checkpoint before the FR-DECIDER-001 publication gate is satisfied.
EOF
