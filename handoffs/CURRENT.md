# CURRENT

> Latest bounce: B376
> Stage: MEMCG-005G-F CONFIRMATORY THRESHOLD IMPLEMENTED / CI
> Stop: EXTERNAL_WAIT

Implementation:
`b4583bba8ab8a25654560ec887526c678d15258a`

Ordinary CI:
`36576017389`

Single B376 read:
`in_progress`

Frozen arms:
`{8,9,10,11,12,32}`

Scale:
48 independent blocks x60 candidates =2880.
480 candidates/arm.

Monte Carlo design calibration:
- expected valid LOW ~=225/arm
- P(MAP=true T) ~=99.1%
- P(true T posterior mass >=.90) ~=97.3%

No launch marker exists.
Do not poll again in this bounce.

Next fresh bounce:
read CI `36576017389` exactly once.
If success, explicitly launch MEMCG-005G-F.

Hosted research only.
No local-PC execution.
