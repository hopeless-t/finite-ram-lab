# FR-META-002 Receipt

Status: **PASS / METHOD-TELEMETRY OBSERVATION PLANE QUALIFIED**

- workflow run: 37134620221
- job: 111236510984
- execution head: cee3731705a9ba03bbf38f35d0d1265a959636e0
- artifact ID: 11277184312
- artifact ZIP SHA256: cd79075d59a5fe28e042e5b43a78abda7df157d69bf361a8e3884c41e88843d8
- spec SHA256: 0c4299d99769acd15b16065c11928b8ba5f15dca2b477f27852da0601614c3a4
- result SHA256: c55c18eb0251bca3eadf7ec2929030a8e5dda5076880349c52688fc654d307e4

Unit tests:

- panel PASS
- STALL fixture -> REVIEW
- synthetic MC cannot mutate operational policy
- UNKNOWN telemetry is not imputed to zero

Synthetic call-budget sensitivity (20,000 paired draws):

| threshold | safe flag | stall miss | balanced loss | checkpoint-cost weighted | stall-cost weighted |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.27395 | 0.01395 | 0.28790 | 0.56185 | 0.30185 |
| 5 | 0.07070 | 0.05730 | 0.12800 | 0.19870 | 0.18530 |
| 6 | 0.01005 | 0.16440 | 0.17445 | 0.18450 | 0.33885 |
| 7 | 0.00085 | 0.35650 | 0.35735 | 0.35820 | 0.71385 |
| 8 | 0.00005 | 0.59480 | 0.59485 | 0.59490 | 1.18965 |

Interpretation:

- threshold 5 minimizes the balanced toy loss;
- threshold 6 minimizes the checkpoint-cost-heavy toy loss;
- lower thresholds reduce synthetic stall misses at the cost of more checkpoints;
- therefore the optimizer depends materially on the loss function.

Frozen governance decision:

**NO_THRESHOLD_CHANGE_FROM_SYNTHETIC_ONLY**

The existing six-call operating rule remains unchanged until real dogfood
telemetry supports a fresh Council review.

Data boundary:

- durable / explicit operational metadata only;
- private chain-of-thought and hidden reasoning data excluded;
- missing values remain UNKNOWN;
- observation does not expand execution authority.

Claim ceiling:

**SYNTHETIC_METHOD_TELEMETRY_SCHEMA_AND_ALERT_LOGIC_ONLY**

Next:

Accumulate real canonical bounce records and fit empirical L1/L2 method-cost,
failure-capture, and frontier-movement distributions.
