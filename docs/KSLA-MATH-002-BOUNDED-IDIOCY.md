# KSLA-MATH-002 — Bounded Idiocy

Status: **ANALYTIC + MATCHED MONTE CARLO TOY MODEL**

Parent: **KSLA-BENCH-001**

## Question

Can intentionally mixing a cheap, ignorant proposal source into a strong expert
portfolio be mathematically rational?

The answer is not "always".

The useful condition is **complementarity**.

An idiot proposal must cover a blind spot or an upper-tail opportunity that the
expert proposal distribution does not cover cheaply.

## General portfolio model

Let nonnegative progress from an expert proposal have CDF F_E and progress from
an idiot proposal have CDF F_I.

With e experts and k idiots, and accepting the best useful proposal:

[
G_{e,k}=max(E_1,ldots,E_e,I_1,ldots,I_k).
]

Then:

[
E[G_{e,k}]
=
int_0^infty
left[
1-F_E(y)^eF_I(y)^k
ight]dy.
]

Replacing one expert proposal with one idiot proposal changes expected progress
by:

[
Delta_{E	o I}
=
int_0^infty
F_E(y)^{e-1}F_I(y)^k
left[
F_E(y)-F_I(y)
ight]dy.
]

This is the key result.

A low-average-quality idiot can still have positive portfolio value if its
upper tail is better exactly where the existing portfolio is weak.

If F_I is dominated everywhere and the idiot has positive cost, there is no
reason to include it.

## Closed-form blind-spot model

Take a two-regime expert:

- normal state probability 1-q: expert progress = g;
- blind state probability q: expert progress = 0.

Take a deliberately stupid proposal:

- progress H with probability p;
- zero otherwise.

With one expert plus k idiots:

[
E[G_{1,k}]
=
H-
left[
H-(1-q)g
ight](1-p)^k.
]

The marginal value of the next idiot is:

[
Delta_k
=
p(1-p)^k
left[
H-(1-q)g
ight].
]

Therefore the idiot contribution has geometrically diminishing value.

With resource price lambda and idiot cost c_I, add another idiot only while:

[
Delta_k > lambda c_I.
]

This gives a literal mathematical definition of **bounded idiocy**.

## Frozen richer toy fixture

The executable fixture uses:

- blind-state probability: 15%;
- expert cost: 8;
- expert normal progress: 8;
- expert blind progress: 0;
- idiot cost: 1;
- total hard budget: 16.

One idiot proposal has:

| progress | probability |
|---:|---:|
| 0 | 0.80 |
| 2 | 0.17 |
| 20 | 0.03 |

The idiot is usually useless.

Its value comes from the cheap 3% upper-tail event and from expert blind states.

## Hard-budget result

Under only the cost cap 16, exact order-statistic enumeration selects:

`1 expert + 8 idiots`.

Expected progress:

- expert-only: 6.8;
- 16 idiots: ~8.8871;
- 1 expert + 8 idiots: ~9.8394.

So the mixed portfolio beats both pure extremes in this toy model.

This is not a universal performance claim.

It is an existence proof for a portfolio regime where deliberate idiocy is
rational.

## Resource-priced result

Now price cost directly:

[
U = E[G]-0.39 C.
]

The exact optimum becomes:

`1 expert + 3 idiots`.

Cost is 11, even though the hard budget permits 16.

So the optimum deliberately leaves budget unused.

That is stronger than "add random search until the machine is full".

It demonstrates:

[
oxed{
0 < ho^*_{m idiot} < 1
}
]

under the frozen toy economics.

## Negative control

A second idiot family has only:

- 0 progress with probability 0.85;
- 2 progress with probability 0.15;

with no expert blind state.

Because an expert already gives progress 8, the first idiot adds exactly zero
progress value.

With any positive idiot cost, it must be rejected.

Therefore the model does not encode "idiocy is always good".

It encodes:

`complementary idiocy can be good`.

## Matched Monte Carlo

The analytic model is then validated with 200,000 episodes.

Every candidate portfolio sees the same:

- latent blind / normal draw;
- ordered idiot proposal tape.

A policy with k idiots consumes the prefix [0,k) of the same tape.

This follows the Finite RAM rule that random-stream identity is part of the
experimental state.

The Monte Carlo run is required to reproduce analytic expected progress within
a frozen tolerance and to preserve the mixed-vs-pure conclusions.

## Why this resembles exploration/exploitation but is not identical

Epsilon-greedy and randomized search already establish that occasionally taking
non-greedy actions can improve robustness when a heuristic is imperfect.

KSLA's narrower contribution under test is resource architectural:

- the exploratory source may have effectively zero intelligence;
- it can be much cheaper than the expert source;
- all proposals face the same external verifier;
- the exploration rate is treated as a priced resource allocation;
- RAM, latency, network, and verification load can become additional prices.

## Next experiment

The next lane should replace synthetic reward distributions with an actual
problem state.

Candidate design:

- expert solver has a finite resident view / heuristic blind spot;
- idiot proposals sample outside that view;
- matched tapes;
- adaptive idiot budget rises only when expert progress stalls.

Compare:

1. EXPERT_ONLY
2. IDIOT_ONLY
3. FIXED_LOW_IDIOCY
4. FIXED_HIGH_IDIOCY
5. STALL_ADAPTIVE_IDIOCY
6. ORACLE_PORTFOLIO

Endpoints:

- exact success;
- wall time;
- validator evaluations;
- state bytes touched;
- peak RSS;
- p95/p99 solve cost;
- blind-spot escape rate;
- wasted idiot proposals.

## Claim ceiling

**TOY_ANALYTIC_AND_MATCHED_MONTE_CARLO_BOUNDED_IDIOCY_ONLY**
