# KSLA-002 — Imaginary Kitten Random Action Solver

Status: **SYNTHETIC / EXACT INTEGER LINEAR-SYSTEM FIXTURE**

Parent: **KSLA-001**

## The conceptual correction

A kitten is not a model.

A kitten is not a process.

A kitten is not even necessarily a worker.

In KSLA-002 a kitten is only this:

```text
(coordinate, random step)
```

It appears, performs a meaningless local action proposal, and disappears.

The kitten does not know:

- the matrix;
- the right-hand side;
- the residual;
- the gradient;
- the objective;
- whether its action is useful.

The external mathematical validator knows whether an action should survive.

This is the literal **imaginary kitten** interpretation.

## Research question

Can a large stream of ignorant random local actions solve an exact linear
system if a cheap external validator accepts only actions that reduce a
certifiable residual?

## Prior-art boundary

This is not claimed as a new optimization primitive.

The closest established relatives include:

- randomized coordinate descent;
- randomized Kaczmarz;
- zeroth-order Random Pursuit / random search.

The KSLA-specific question is systems-oriented:

> How little state and intelligence can be assigned to the action generator
> when correctness and selection are moved entirely into the verifier?

## Frozen system

Solve `Qx=c`, where Q is a 64 × 64 symmetric positive-definite tridiagonal
matrix with diagonal 6 and upper/lower off-diagonal -1.

The exact integer target vector is generated from a frozen SHA256 domain, with
coordinates in [-7, 7]. The right-hand side is constructed as `c = Qx*`.

The solver starts at the zero vector.

## Imaginary kitten action

Each kitten chooses, without observing the problem:

- coordinate j in {0,...,63};
- delta in {-4,-2,-1,+1,+2,+4}.

It proposes only:

`x' = x + delta * e_j`

That is the kitten's entire existence.

## External validator

The validator maintains the exact residual `r = Qx-c`.

Because Q is tridiagonal, changing one coordinate touches at most three
residual entries.

For a proposal, the validator computes only the local change in `||r||_2^2`.

If the residual norm increases or stays equal, the kitten dies.

If it decreases, the action is eligible.

When multiple kittens appear in one round, the validator accepts the best
improving proposal from that batch.

No gradient is given to the kittens.

## Frozen results

Every filtered swarm reaches the exact integer solution:

| imaginary kittens / round | rounds | proposals evaluated | accepted actions |
|---:|---:|---:|---:|
| 1 | 2753 | 2753 | 183 |
| 4 | 635 | 2540 | 189 |
| 8 | 305 | **2440** | 150 |
| 16 | 232 | 3712 | 148 |
| 32 | 185 | 5920 | 137 |
| 64 | 155 | 9920 | 132 |
| 128 | **122** | 15616 | 122 |

All terminate with exact zero residual.

## The surprising middle regime

One random kitten per round eventually solves the system, but wastes many
rounds proposing useless moves.

Eight imaginary kittens per round produce:

- 305 rounds instead of 2753;
- 2440 total proposal evaluations instead of 2753.

So in this fixture, a modest swarm improves both serial decision depth and
total candidate-evaluation count.

The 8-kitten arm is the frozen proposal-efficiency minimum among the tested
swarm widths. This is not claimed as a universal optimum.

## Too many kittens

Increasing the batch from 8 to 128 keeps reducing rounds from 305 to 122,
but total proposal work grows from 2440 to 15616.

Therefore:

`more imaginary kittens != free speed`

Swarm width trades parallel depth against validator work.

This gives KSLA its own pressure-knee problem.

## Exhaustive smart-search baseline

A comparison arm evaluates every `64 × 6 = 384` possible coordinate/step
action each round and chooses the best improving action.

It reaches the exact solution in:

- 124 rounds;
- 47,616 candidate evaluations.

The 8-kitten random swarm takes more rounds, 305 vs 124, but only 2,440
candidate evaluations.

Thus a globally smarter action search can spend far more validator work merely
finding the best move.

This does not establish wall-clock superiority. It establishes a trade between
decision quality per round and the cost of finding that decision.

## Unfiltered chaos baseline

To test whether randomness itself is doing the work, a second arm applies one
random kitten action every round with **no validator filtering**.

It runs for the same 2753 rounds as the one-kitten filtered arm.

Frozen result:

- starting residual norm: 51,431;
- final residual norm: 585,361;
- exact solution: false.

The residual grows by more than an order of magnitude.

Therefore:

`randomness is not the intelligence`

The useful system is:

`random action generation + external mathematical selection pressure`

## Where the intelligence moved

The kitten itself has effectively zero intelligence.

The system still has structure. It moved into:

1. a decomposable action space;
2. a cheap local validator;
3. a monotone acceptance rule;
4. an exact terminal condition.

So the stronger statement is not that stupid agents become intelligent.

It is that a system can obtain goal-directed behavior from ignorant action
generation when the environment exposes cheap, reliable selection pressure.

## Finite RAM angle

The tridiagonal structure matters.

One proposal touches at most three residual entries.

For a modeled dimension of one million, the touched fraction is:

`3 / 1,000,000 = 3e-6`

The logical kitten itself stores only:

```text
coordinate
step
```

It does not need a copy of the vector or matrix.

This makes the distinction explicit:

`logical kittens >> resident workers`

A million logical kittens can be represented as a stream of tiny action tuples.
There is no requirement to instantiate a million Python processes, threads, or
LLMs.

## What this does not prove

KSLA-002 does not prove that random local search beats modern linear solvers.

It does not measure:

- wall-clock speed;
- CPU cache effects;
- real parallel synchronization;
- floating-point stability;
- energy;
- dense-matrix behavior.

The matrix is intentionally sparse and well-behaved so the systems abstraction
can be isolated.

## New system abstraction

```text
problem state
     ↓
random action fountain
  🐱 🐱 🐱 🐱 🐱
     ↓
cheap local validator
     ↓
reject reject accept reject
              ↓
          state update
              ↓
          repeat
```

The swarm can be completely imaginary.

## Next lane

### KSLA-003 — Residual ecology

Make kittens more chaotic:

- multiple action types;
- multiple step scales;
- sparse block actions;
- stale actions;
- delayed actions;
- duplicated actions;
- corrupted actions.

Then introduce:

- finite validator budget;
- queue pressure;
- adaptive swarm width;
- action-family selection;
- rare-event capture.

The question becomes:

> Can a controller learn how much chaos to permit before verification cost
> dominates progress?

That connects directly to Finite RAM pressure-knee methodology.

## Claim ceiling

**SYNTHETIC_IMAGINARY_KITTEN_RANDOM_ACTION_SOLVER_ONLY**
