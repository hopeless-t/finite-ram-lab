#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-memcg-tracefs-capability.json}"
TRACE=/sys/kernel/tracing

if [[ ! -d "$TRACE" ]]; then
  echo "missing tracefs mountpoint: $TRACE" >&2
  exit 2
fi

if [[ ! -e "$TRACE/dynamic_events" && ! -e "$TRACE/kprobe_events" ]]; then
  sudo mount -t tracefs nodev "$TRACE" 2>/dev/null || true
fi

if [[ -e "$TRACE/dynamic_events" ]]; then
  EVENTS_FILE="$TRACE/dynamic_events"
elif [[ -e "$TRACE/kprobe_events" ]]; then
  EVENTS_FILE="$TRACE/kprobe_events"
else
  echo "no dynamic_events or kprobe_events" >&2
  exit 3
fi

symbols=(
  try_charge_memcg
  consume_stock
  refill_stock
  memcg_uncharge
)

missing=()
for sym in "${symbols[@]}"; do
  if ! grep -Eq "[[:space:]]${sym}$" /proc/kallsyms; then
    missing+=("$sym")
  fi
done

cleanup() {
  set +e
  for ev in try_charge consume refill uncharge; do
    if [[ -e "$TRACE/events/frl_obs/$ev/enable" ]]; then
      echo 0 | sudo tee "$TRACE/events/frl_obs/$ev/enable" >/dev/null
    fi
  done
  if [[ -e "$TRACE/events/frl_obs/uncharge/trigger" ]]; then
    echo '!stacktrace' | sudo tee "$TRACE/events/frl_obs/uncharge/trigger" >/dev/null 2>&1
  fi
  for ev in uncharge refill consume try_charge; do
    echo "-:frl_obs/$ev" | sudo tee -a "$EVENTS_FILE" >/dev/null 2>&1
  done
}
trap cleanup EXIT

if ((${#missing[@]})); then
  printf 'missing symbols:' >&2
  printf ' %s' "${missing[@]}" >&2
  printf '\n' >&2
  exit 4
fi

defs=(
'p:frl_obs/try_charge try_charge_memcg memcg=$arg1:x64 request_pages=$arg3:u32'
'r:frl_obs/consume consume_stock memcg=$arg1:x64 request_pages=$arg2:u32 ret=$retval:u64'
'p:frl_obs/refill refill_stock memcg=$arg1:x64 pages=$arg2:u32'
'p:frl_obs/uncharge memcg_uncharge memcg=$arg1:x64 pages=$arg2:u32'
)

for def in "${defs[@]}"; do
  echo "$def" | sudo tee -a "$EVENTS_FILE" >/dev/null
done

formats_ok=true
for ev in try_charge consume refill uncharge; do
  fmt="$TRACE/events/frl_obs/$ev/format"
  [[ -r "$fmt" ]] || formats_ok=false
done

grep -q 'field:.*memcg' "$TRACE/events/frl_obs/try_charge/format" || formats_ok=false
grep -q 'field:.*request_pages' "$TRACE/events/frl_obs/try_charge/format" || formats_ok=false
grep -q 'field:.*ret' "$TRACE/events/frl_obs/consume/format" || formats_ok=false
grep -q 'field:.*pages' "$TRACE/events/frl_obs/uncharge/format" || formats_ok=false

echo stacktrace | sudo tee "$TRACE/events/frl_obs/uncharge/trigger" >/dev/null
trigger_text="$(cat "$TRACE/events/frl_obs/uncharge/trigger")"
if ! grep -q 'stacktrace' <<<"$trigger_text"; then
  echo "stacktrace trigger registration failed" >&2
  exit 5
fi
echo '!stacktrace' | sudo tee "$TRACE/events/frl_obs/uncharge/trigger" >/dev/null

python - "$OUT" "$EVENTS_FILE" "$formats_ok" <<'PY'
import json
import platform
import sys
from pathlib import Path

out, events_file, formats_ok = sys.argv[1:]
trace = Path('/sys/kernel/tracing')
payload = {
    'schema_version': 'memcg-tracefs-capability-v1',
    'status': 'PASS' if formats_ok == 'true' else 'FAIL',
    'kernel_release': platform.release(),
    'platform': platform.platform(),
    'events_file': events_file,
    'required_symbols': [
        'try_charge_memcg',
        'consume_stock',
        'refill_stock',
        'memcg_uncharge',
    ],
    'formats_ok': formats_ok == 'true',
    'probe_formats': {},
}
for ev in ['try_charge', 'consume', 'refill', 'uncharge']:
    path = trace / 'events' / 'frl_obs' / ev / 'format'
    payload['probe_formats'][ev] = path.read_text(encoding='utf-8')
Path(out).write_text(
    json.dumps(payload, indent=2, sort_keys=True) + '\n',
    encoding='utf-8',
)
if payload['status'] != 'PASS':
    raise SystemExit(6)
PY

echo "PASS: tracefs dynamic memcg observer capability"
