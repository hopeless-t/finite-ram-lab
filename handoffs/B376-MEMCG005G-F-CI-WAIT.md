# B376 — MEMCG-005G-F CI wait

Implementation:
`b4583bba8ab8a25654560ec887526c678d15258a`

Ordinary CI:
`36576017389`

Single B376 read:
`in_progress`

No second poll this bounce.
No scientific launch marker exists.

Frozen arms:
`{8,9,10,11,12,32}`

Scale:
48 independent blocks x60 candidates =2880.
480 candidates/arm.

Monte Carlo design calibration:
- expected valid LOW ~=225/arm
- P(MAP=true T) ~=99.1%
- P(true T posterior mass >=.90) ~=97.3%

Next fresh bounce:
read CI `36576017389` exactly once.
If success, explicitly launch MEMCG-005G-F.

Hosted research only.
