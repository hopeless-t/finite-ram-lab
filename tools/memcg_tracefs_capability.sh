#!/usr/bin/env bash
set -u -o pipefail

OUT="${1:-memcg-tracefs-diagnostic.json}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

run_capture() {
  local name="$1"
  shift
  set +e
  "$@" >"$TMP/$name.out" 2>"$TMP/$name.err"
  local rc=$?
  set -e
  printf '%s' "$rc" >"$TMP/$name.rc"
}

set -e
uname -a >"$TMP/uname.out"
mount >"$TMP/mount.out" 2>&1 || true
ls -la /sys/kernel/tracing >"$TMP/sys_kernel_tracing.out" 2>&1 || true
ls -la /sys/kernel/debug >"$TMP/sys_kernel_debug.out" 2>&1 || true
ls -la /sys/kernel/debug/tracing >"$TMP/sys_kernel_debug_tracing.out" 2>&1 || true
cat /sys/kernel/security/lockdown >"$TMP/lockdown.out" 2>&1 || true
cat /proc/sys/kernel/kptr_restrict >"$TMP/kptr_restrict.out" 2>&1 || true
cat /proc/sys/kernel/perf_event_paranoid >"$TMP/perf_event_paranoid.out" 2>&1 || true

CONFIG_SRC=""
if [[ -r "/boot/config-$(uname -r)" ]]; then
  CONFIG_SRC="/boot/config-$(uname -r)"
  cp "$CONFIG_SRC" "$TMP/kernel_config.out"
elif [[ -r /proc/config.gz ]]; then
  CONFIG_SRC="/proc/config.gz"
  zcat /proc/config.gz >"$TMP/kernel_config.out"
else
  : >"$TMP/kernel_config.out"
fi

grep -E '^(CONFIG_(KPROBES|KPROBE_EVENTS|FTRACE|TRACING|TRACEPOINTS|DYNAMIC_EVENTS|DEBUG_FS))=' "$TMP/kernel_config.out" >"$TMP/config_interest.out" 2>&1 || true
grep -E '[[:space:]](try_charge_memcg|consume_stock|refill_stock|memcg_uncharge)$' /proc/kallsyms >"$TMP/symbols.out" 2>&1 || true

run_capture mount_tracefs_primary sudo mount -t tracefs tracefs /sys/kernel/tracing

if [[ -d /sys/kernel/debug ]]; then
  run_capture mount_debugfs sudo mount -t debugfs debugfs /sys/kernel/debug
fi

if [[ -d /sys/kernel/debug/tracing ]]; then
  run_capture mount_tracefs_debug sudo mount -t tracefs tracefs /sys/kernel/debug/tracing
fi

for base in /sys/kernel/tracing /sys/kernel/debug/tracing; do
  key="$(echo "$base" | tr '/-' '__')"
  {
    echo "BASE=$base"
    for f in dynamic_events kprobe_events available_events trace kprobe_profile; do
      if [[ -e "$base/$f" ]]; then
        stat -c '%n mode=%a uid=%u gid=%g type=%F' "$base/$f" 2>&1 || true
      else
        echo "$base/$f MISSING"
      fi
    done
  } >"$TMP/${key}_files.out" 2>&1
done

python - "$OUT" "$TMP" "$CONFIG_SRC" <<'PY'
import json
import platform
import sys
from pathlib import Path

out, tmp, config_src = sys.argv[1:]
root = Path(tmp)

def read(name):
    p = root / name
    return p.read_text(encoding='utf-8', errors='replace') if p.exists() else ''

def rc(name):
    p = root / (name + '.rc')
    if not p.exists():
        return None
    try:
        return int(p.read_text())
    except ValueError:
        return None

bases = {}
for base in ['/sys/kernel/tracing', '/sys/kernel/debug/tracing']:
    p = Path(base)
    bases[base] = {
        'exists': p.exists(),
        'dynamic_events': (p / 'dynamic_events').exists(),
        'kprobe_events': (p / 'kprobe_events').exists(),
        'available_events': (p / 'available_events').exists(),
        'trace': (p / 'trace').exists(),
    }

symbols = []
for line in read('symbols.out').splitlines():
    parts = line.split()
    if parts:
        symbols.append(parts[-1])

payload = {
    'schema_version': 'memcg-tracefs-diagnostic-v2',
    'kernel_release': platform.release(),
    'platform': platform.platform(),
    'config_source': config_src or None,
    'config_interest': read('config_interest.out').splitlines(),
    'lockdown': read('lockdown.out').strip(),
    'kptr_restrict': read('kptr_restrict.out').strip(),
    'perf_event_paranoid': read('perf_event_paranoid.out').strip(),
    'symbols_found': sorted(symbols),
    'bases': bases,
    'mount_attempts': {
        'tracefs_primary': {
            'rc': rc('mount_tracefs_primary'),
            'stdout': read('mount_tracefs_primary.out'),
            'stderr': read('mount_tracefs_primary.err'),
        },
        'debugfs': {
            'rc': rc('mount_debugfs'),
            'stdout': read('mount_debugfs.out'),
            'stderr': read('mount_debugfs.err'),
        },
        'tracefs_debug': {
            'rc': rc('mount_tracefs_debug'),
            'stdout': read('mount_tracefs_debug.out'),
            'stderr': read('mount_tracefs_debug.err'),
        },
    },
    'mount_table': read('mount.out'),
    'directory_receipts': {
        '/sys/kernel/tracing': read('sys_kernel_tracing.out'),
        '/sys/kernel/debug': read('sys_kernel_debug.out'),
        '/sys/kernel/debug/tracing': read('sys_kernel_debug_tracing.out'),
    },
}

payload['status'] = (
    'TRACEFS_AVAILABLE'
    if any(v['dynamic_events'] or v['kprobe_events'] for v in bases.values())
    else 'TRACEFS_HOLD'
)

Path(out).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({
    'status': payload['status'],
    'kernel_release': payload['kernel_release'],
    'config_interest': payload['config_interest'],
    'lockdown': payload['lockdown'],
    'symbols_found': payload['symbols_found'],
    'bases': payload['bases'],
    'mount_attempts': payload['mount_attempts'],
}, indent=2, sort_keys=True))
PY

exit 0
