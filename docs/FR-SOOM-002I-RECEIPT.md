# FR-SOOM-002I — Event-Time Daemon Qualification Receipt

Status: **PASS / SYNTHETIC ASYNCHRONOUS DAEMON STATE MACHINE VALIDATED**

## Frozen qualification

- workflow run: 37094039907
- job: 111120183852
- execution head: 246d1775cf1120c8c6013f18e073fab1d72f5519
- targeted tests: 7/7 PASS
- artifact ID: 11262818212
- artifact ZIP SHA256: 2b307da462512c090d12eed80334357f93a7b54b2df61db7ee015207eff5e058
- spec SHA256: 79c7c461998aea5d15688b7e956ff3acee6c9267136bac655ac7caaa67117568
- result SHA256: 5f58e58018b1a50b6c50e98b7a15a2036e943a7fc1ceab82cdf3d17261d0bc00

## Frozen result

| strategy | current-task losses | unnecessary protection | switches |
|---|---:|---:|---:|
| STATIC_COOPERATIVE | 6 | 0 | 0 |
| STICKY_EVER_DEPENDENCE | 0 | 6 | 1 |
| RAW_LAST_EVIDENCE | 1 | 3 | 8 |
| DECAY_HYSTERESIS_COOLDOWN | 1 | 0 | 2 |

For DECAY_HYSTERESIS_COOLDOWN:

- sustained-pressure detection delay: 10 s
- recovery release delay: 40 s
- cooldown-blocked contradictory exit events: 1

## Qualification repair

The initial PR metadata, spec, documentation, and dedicated workflow still
carried an obsolete RAW_LAST_EVIDENCE.switch_count = 6 value.

The executable source and targeted test already froze the actual event-sequence
result at **8 switches**.

The event sequence changes mode at:

`17 -> 23 -> 103 -> 150 -> 167 -> 310 -> 470 -> 480 s`.

No threshold, event timestamp, confidence rule, semantic cost, or controller
strategy was changed.

The repair synchronized:

- specs/FR-SOOM-002I.json
- docs/FR-SOOM-002I-EVENT-TIME-DAEMON.md
- .github/workflows/fr-soom-002i.yml

to the executable reference of 8.

## Primary finding

In the frozen event-time fixture:

`wall-clock decay + hysteresis + cooldown`

reduces stale protection and policy churn relative to raw latest-signal control,
while keeping a bounded detection delay.

This is the first lane whose control state is structurally daemon-like rather
than batch-window-only.

## Claim ceiling

**SYNTHETIC_EVENT_TIME_DAEMON_STATE_MACHINE_ONLY**

No live process was controlled.
