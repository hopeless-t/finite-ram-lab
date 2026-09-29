import assert from 'node:assert/strict';
import { analyze } from './math002.mjs';

function makeTrial(block, arm, drops) {
  return {
    block,
    arm,
    records: drops.map((drop, i) => ({
      m: i + 1,
      passive_drop_pages: drop,
    })),
  };
}

const trials = [];
for (let b = 0; b < 4; b++) {
  trials.push(makeTrial(b, 'distinct_churn', [0,0,0,0,0,0,63,0]));
  trials.push(makeTrial(b, 'same_memcg_activity', [0,0,0,0,0,0,0,0]));
  trials.push(makeTrial(b, 'six_only', [0,0,0,0,0,0]));
  trials.push(makeTrial(b, 'no_churn', [0,0,0,0,0,0,0,0]));
}

const result = analyze({
  experiment_id: 'synthetic',
  decision: 'SUPPORT_K7_SLOT_MODEL_B',
  trials,
});

assert.equal(result.permutation.observed_g, 4);
assert.equal(Object.keys(result.per_block).length, 4);
assert.ok(result.permutation.empirical_tail_probability < 0.02);
assert.ok(result.distinct_hull.area > 0);
assert.equal(result.control_hull.area, 0);

console.log('MATH-002 synthetic PASS');
