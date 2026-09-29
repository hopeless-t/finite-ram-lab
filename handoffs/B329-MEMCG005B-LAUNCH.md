# Bounce Handoff

> **Bounce ID:** B329
> **Status:** MEMCG-005B EXPLICIT HOSTED LAUNCH

Implementation:
`4d899453a4ffaf8aaaf68f285ede6ea1e9e1ae1b`

CI:
`36547079561 = success`

Exact launch commit:
`73baca88f9701c1d819cdb9a11da38d033669aff`

Scientific design:
- C controller;
- P startup/prep;
- S stock-test;
- workers never touch S before measured insertion;
- 14 verified wash insertions before target;
- m={0,5,6,7,8};
- one-shot target probe.

Next: discover/read exact-head MEMCG-005B run once.

Hosted research only.
No local-PC execution.
