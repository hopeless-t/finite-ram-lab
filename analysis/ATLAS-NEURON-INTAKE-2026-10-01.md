# Atlas Neuron intake — finite-RAM catfood v0

Source: Arth Singh, “The Atlas Neuron”, 2026-09-30  
https://www.arthsingh.com/blog/atlas-neuron

## Why this is relevant

The useful mechanism for finite-ram-lab is not the digit classifier itself. It is the
task-free world-change detector:

1. encode inputs;
2. score familiarity against current landmarks;
3. freeze a world's usual familiarity after an initial window;
4. withhold suspicious batches;
5. fork a new page only after sustained unfamiliarity;
6. stop old pages from drifting when the world changes.

The source uses a 256-dimensional fixed random projection, the first 50 batches for
usual familiarity, and forks after three consecutive batches below 85% of that
baseline. Each source page then uses per-class online k-means landmarks and
incremental-PCA charts.

## finite-RAM translation

This candidate intentionally borrows only the gate. A “world” is provisionally a
stable telemetry regime, not an image task. Candidate features include memory.current,
high-event deltas, scan/steal deltas, faults, residual stock and latency.

The immediate question is whether rare residual-stock failures appear as sustained
familiarity breaks before the old SUCCESS/FAIL classifier notices them.

## Important limitation

Atlas memory and test cost grow with world count; the source reports roughly 100x the
multiply-add cost of its small-network baseline after 20 worlds. On natural images,
the source's raw-pixel charts are weak and streaming LDA on frozen features eventually
wins at larger memory. Therefore this is a novelty sidecar candidate, not a proposal
to replace the main classifier with Atlas.

No code from the article was copied. The implementation here is an independent,
minimal reproduction of the described familiarity/fork rule only.
