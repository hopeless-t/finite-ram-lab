# HYP-001 Design Council — Future-Reuse Alignment

> **Status:** DESIGN STUDY

## Question

Can future application demand become expensive when it is misaligned with the recency information available from the application's past access history?

## Why this path

The explicit pageout instrument was only partially effective under low pressure.

Rather than add increasingly invasive control machinery, HYP-001 uses ordinary memory accesses to create a cleaner information-gap experiment.

## Pseudo-Council

### Application/runtime reviewer

Split the 64 MiB hot set into two equal semantic regions:

```text
A = 32 MiB
B = 32 MiB
```

Give A and B the same number of pre-burst touches. Only their final touch order differs.

### Kernel / VM reviewer

Do not assume the kernel implements plain LRU.

The experiment manipulates observable access history and future reuse, not an internal kernel policy.

### Experimental reviewer

Randomize which physical mapping is made “more recent” to remove address/allocation identity as an explanation.

After the 96 MiB burst, randomly choose the next reused region according to one of two pre-registered arms:

- **ALIGNED:** reuse the more-recent region;
- **MISALIGNED:** reuse the less-recent region.

Total live memory, region sizes, number of pre-burst touches, and burst work remain matched.

### Measurement reviewer

Primary arms run without pre-retouch residency probes.

Region residency may be measured later in separate validation arms.

### Falsification reviewer

The hypothesis is weakened if ALIGNED and MISALIGNED arms have indistinguishable next-phase latency and fault behavior across independent runner blocks.

### Statistics reviewer

Runner identity is a block.

Analyze the log latency contrast within runner blocks.

Use permutation/randomization inference in the real experiment.

### Monte Carlo reviewer

Before freezing runner count and repeats, simulate several blocked designs under heavy-tail and runner-heterogeneity scenarios.

## Design candidates for Monte Carlo

```text
D1:  8 runner blocks × 4 repeats / arm
D2:  8 runner blocks × 6 repeats / arm
D3: 12 runner blocks × 4 repeats / arm
D4: 12 runner blocks × 6 repeats / arm
```

The design study reports detection probability under several plausible effect/noise models and does not use a single weighted score.

## Primary physical experiment level

The leading transition condition is 164 MiB `MemoryHigh`.

160 MiB and 168 MiB controls will be retained after the design study.

## Authority boundary

HYP-001 tests whether future semantic demand contains value beyond matched past-access counts and recency ordering.

It does not test an application hint, coordinator, or kernel modification.
