# FR-SOOM-002H — Regime Drift Qualification Receipt

Status: **PASS / SYNTHETIC REGIME-DRIFT CONTROL VALIDATED**

## Frozen qualification

- workflow run: 37026282276
- job: 110901623377
- execution head: d8d62e094d6de90c3078b654d8201263305f5e89
- targeted tests: 7/7 PASS
- artifact ID: 11235258023
- artifact ZIP SHA256: 6551c824a9896941ccd119cb6654b8d7bd1bca5f1a1cea76ce3fdb41a5e5d856
- spec SHA256: 023ca24abb9bc42723a7fe73ada834fe2d90cf2b7aba96a62e568ddbe681a15b
- result SHA256: f08c5a150ee8fa6c07fd43a127dc957db3e3bdfcae8e91adcf0deccbc0c71076

## Frozen sequence

Twelve windows:

```text
IID
IID
one-window correlated BURST
IID
SHARED
SHARED
SHARED
SHARED
IID
IID
IID
IID
```

Each window contains 2048 episodes.

Each clustered action has exactly 20 late outcomes.

The regime labels exist only for harness scoring.

The controller sees only observable co-failure evidence.

## Evidence sequence

The 199-permutation observable test produces:

```text
IID_COMPATIBLE
IID_COMPATIBLE
DEPENDENCE_EVIDENCE
IID_COMPATIBLE
DEPENDENCE_EVIDENCE
DEPENDENCE_EVIDENCE
DEPENDENCE_EVIDENCE
DEPENDENCE_EVIDENCE
IID_COMPATIBLE
IID_COMPATIBLE
IID_COMPATIBLE
IID_COMPATIBLE
```

The single burst therefore looks like dependence for one observation window.

## Strategy result

| metric | STATIC_INITIAL | RAW_SLIDING | HYSTERESIS_2_ENTER_1_EXIT |
|---|---:|---:|---:|
| current-task losses | 101 | 41 | 61 |
| unnecessary background-sacrifice windows | 0 | 2 | 1 |
| plan switches | 0 | 4 | 2 |
| sustained-SHARED detection delay | never | 1 window | 2 windows |
| recovery release delay | 0 | 1 window | 1 window |
| post-burst stale escalation | no | yes | no |
| mean semantic loss | 11.15072 | 36.71712 | 26.44499 |
| p99.9 semantic loss | 290 | 290 | 290 |

## Primary finding

No strategy dominates every endpoint.

STATIC avoids expensive background-sacrifice mode but underreacts badly to
persistent shared dependence.

RAW_SLIDING reacts fastest and has the fewest current-task losses, but it also:

- follows the isolated burst into the next healthy IID window;
- switches plan four times;
- spends two IID windows in unnecessary background-sacrifice mode.

HYSTERESIS requires two consecutive dependence windows before entering
protective mode and exits after one IID-compatible window.

It:

- removes the isolated-burst spillover;
- cuts plan switches from 4 to 2;
- cuts unnecessary background-sacrifice windows from 2 to 1.

But it raises current-task losses from 41 to 61 because sustained SHARED
dependence is acted on one window later.

Therefore:

`stability x responsiveness x semantic preservation`

is a real controller tradeoff in the synthetic lane.

## Tail result

All three strategies retain a p99.9 semantic-loss tail of 290.

Adaptation changes how often catastrophic outcomes occur.

It does not, by itself, remove the emergency tail.

This is another warning against optimizing only a mean:

`low expected cost != acceptable tail behavior`.

## Qualification correction

The scratch pilot used abstract action IDs `A/B/C` as deterministic draw
domains.

The committed harness uses canonical action IDs:

- CHROME_CACHE;
- MODEL_SHRINK;
- INDEXER_EXIT.

That changed the exact IID overlap specimens while preserving:

- marginal tail count;
- regime sequence;
- evidence threshold;
- strategy rules;
- qualitative evidence sequence.

The committed canonical stream yields:

- STATIC current-task losses: 101;
- RAW_SLIDING: 41;
- HYSTERESIS: 61.

No control threshold or policy rule was relaxed.

## Earlyoom-successor implication

The controller now requires belief lifecycle state:

```text
failure-domain evidence
  confidence
  age
  consecutive confirmations
  last contradictory evidence
  current intervention mode
```

This is no longer a static OOM victim-selection problem.

It is an adaptive state-estimation and control problem.

## Claim ceiling

**SYNTHETIC_REGIME_DRIFT_CONTROL_ONLY**

No live process was controlled.

No synthetic window size or hysteresis count is proposed as a host setting.

## Next

FR-SOOM-002I should replace equal-size windows with asynchronous event-time
evidence and wall-clock confidence decay.

That is the next bridge toward a real resident daemon state machine.
