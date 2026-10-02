# FR-SOOM-002I — Event-Time Daemon State Machine

Status: **SYNTHETIC ASYNCHRONOUS CONTROL QUALIFICATION**

## Goal

FR-SOOM-002H modeled adaptation in equal-sized observation windows.

A resident earlyoom successor will not receive evidence in neat batches.

FR-SOOM-002I moves the control model to irregular wall-clock events.

The daemon now has to answer:

- how quickly old evidence should decay;
- how much evidence is needed to enter a protective mode;
- when stale protection should be released;
- whether one contradictory event should immediately undo a protective decision;
- how to avoid oscillation when evidence arrives in bursts.

## Frozen event-time sequence

Evidence arrives at irregular timestamps.

The synthetic schedule contains:

- an isolated early dependence burst;
- a return to IID-compatible evidence;
- a sustained dependence period;
- one contradictory IID evidence event inside that sustained period;
- a long quiet interval;
- recovery;
- another isolated late burst.

Pressure episodes also arrive at irregular times.

The regime label attached to a pressure episode is harness-only scoring truth.

The controller never sees it.

## Daemon modes

The control surface is deliberately small:

`COOPERATIVE`

and

`PROTECTIVE`.

PROTECTIVE corresponds to selecting the synthetic lower-value background
sacrifice plan from FR-SOOM-002G.

It does not mean killing the active task.

## Confidence model

The adaptive daemon carries a scalar dependence-confidence state.

Frozen controls:

- half-life: 60 s;
- DEPENDENCE evidence: +1.0;
- IID evidence: -1.5;
- enter PROTECTIVE at confidence >= 1.6;
- exit at confidence <= 0.6;
- minimum protective hold: 60 s.

Confidence decays continuously with wall-clock time:

`c(t+dt) = c(t) * exp(-ln(2) * dt / half_life)`.

These values are synthetic controls, not host tuning.

## Strategies

### STATIC_COOPERATIVE

Never protects.

Result:

- current-task losses: 6;
- unnecessary protective episodes: 0;
- switches: 0.

### STICKY_EVER_DEPENDENCE

The first dependence event permanently enables protective mode.

Result:

- current-task losses: 0;
- unnecessary protective IID episodes: 6;
- switches: 1.

This demonstrates stale belief.

### RAW_LAST_EVIDENCE

The latest evidence event directly selects the mode.

Result:

- current-task losses: 1;
- unnecessary protective IID episodes: 3;
- switches: 6;
- recovery release delay to the next cooperative pressure episode: 75 s.

It reacts fast but oscillates and follows isolated bursts.

### DECAY_HYSTERESIS_COOLDOWN

Uses wall-clock decay, separate entry/exit thresholds, and a minimum hold.

Frozen result:

- current-task losses: 1;
- unnecessary protective IID episodes: 0;
- switches: 2;
- detection delay to the first protected sustained-pressure episode: 10 s;
- recovery release delay to a cooperative pressure episode: 40 s;
- one contradictory exit was explicitly blocked by the cooldown.

The daemon ignores both isolated bursts, enters protective mode only after
sustained evidence, survives one contradictory observation during the
protective hold, and later exits from confidence decay even before a new IID
evidence event arrives.

## Primary finding

In the frozen asynchronous fixture:

`wall-clock decay + hysteresis + cooldown`

can reduce both stale protection and policy churn while retaining bounded
detection delay.

This is qualitatively different from:

`latest signal wins`

or:

`once bad, always bad`.

## Mean semantic cost

Frozen pressure-episode mean semantic loss:

- STATIC_COOPERATIVE: 139.23077;
- STICKY_EVER_DEPENDENCE: 68.15385;
- RAW_LAST_EVIDENCE: 70.30769;
- DECAY_HYSTERESIS_COOLDOWN: 55.76923.

This fixture is intentionally constructed so the adaptive state machine does
well on both mean cost and overprotection.

That should not be generalized beyond the synthetic schedule.

The earlier tail-risk constraints still apply.

## Earlyoom-successor implication

The daemon now needs explicit control state:

```text
mode
confidence
confidence_timestamp
entry_threshold
exit_threshold
minimum_hold_until
latest_evidence
latest_action_receipt
```

This is the first SOOM lane that looks structurally like a resident service
state machine rather than a batch experiment.

A future implementation could map the modes to real mechanisms only after
read-only shadow validation:

```text
COOPERATIVE
  -> systemd pressure callback / application shrink / cgroup reclaim

PROTECTIVE
  -> background workload sacrifice / stronger reclaim / controlled termination

EMERGENCY
  -> last-resort active-task sacrifice
```

EMERGENCY is intentionally not implemented in this live control surface.

## Important non-claim

All timestamps, evidence values, costs, and thresholds are synthetic.

No live process is controlled.

No half-life, threshold, or cooldown is proposed for a real host.

## Claim ceiling

**SYNTHETIC_EVENT_TIME_DAEMON_STATE_MACHINE_ONLY**

## Next

FR-SOOM-002J should turn the state machine into a **read-only daemon contract**.

It should define:

- input telemetry schema;
- semantic registry schema;
- action-capability advertisements;
- persistent belief state;
- restart/recovery semantics;
- receipt format;
- explicit no-signal shadow mode.

That would create the software boundary needed for a real earlyoom-successor
prototype while still remaining non-destructive.
