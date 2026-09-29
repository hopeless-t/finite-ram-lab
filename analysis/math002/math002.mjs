import fs from 'node:fs';
import { quickhull2 } from 'math/geometry';
import { mulberry32 } from 'math/random';

const SEED = 20260929;
const PERMUTATIONS = 100000;
const WINDOW = new Set([6, 7, 8]);

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 2) out[argv[i]] = argv[i + 1];
  return out;
}

function polygonArea(flat, indices) {
  if (indices.length < 3) return 0;
  let twice = 0;
  for (let i = 0; i < indices.length; i++) {
    const a = indices[i];
    const b = indices[(i + 1) % indices.length];
    twice += flat[2 * a] * flat[2 * b + 1] - flat[2 * b] * flat[2 * a + 1];
  }
  return Math.abs(twice) / 2;
}

function hullFor(rows) {
  const flat = [];
  for (const r of rows) flat.push(Number(r.m), Number(r.passive_drop_pages));
  const indices = quickhull2(flat);
  return {
    indices,
    vertices: indices.map(i => ({
      m: flat[2 * i],
      passive_drop_pages: flat[2 * i + 1],
      source_index: i,
    })),
    area: polygonArea(flat, indices),
  };
}

function maxDropM(rows) {
  let best = null;
  for (const r of rows) {
    const drop = Number(r.passive_drop_pages);
    const m = Number(r.m);
    if (best === null || drop > best.drop || (drop === best.drop && m < best.m)) {
      best = { m, drop };
    }
  }
  return best;
}

function observedScore(distinctByBlock) {
  let score = 0;
  for (const rows of distinctByBlock.values()) {
    const best = maxDropM(rows);
    if (best && WINDOW.has(best.m)) score += 1;
  }
  return score;
}

function shuffleLabels(rows, rng) {
  const labels = rows.map(r => Number(r.m));
  for (let i = labels.length - 1; i > 0; i--) {
    const j = Math.floor(mulberry32.sample(rng) * (i + 1));
    [labels[i], labels[j]] = [labels[j], labels[i]];
  }
  return rows.map((r, i) => ({ ...r, m: labels[i] }));
}

function permutationNull(distinctByBlock) {
  const rng = mulberry32.create(SEED);
  const observed = observedScore(distinctByBlock);
  const hist = Array(5).fill(0);
  let ge = 0;

  for (let p = 0; p < PERMUTATIONS; p++) {
    const perm = new Map();
    for (const [block, rows] of distinctByBlock.entries()) {
      perm.set(block, shuffleLabels(rows, rng));
    }
    const g = observedScore(perm);
    hist[g] += 1;
    if (g >= observed) ge += 1;
  }

  return {
    seed: SEED,
    permutations: PERMUTATIONS,
    observed_g: observed,
    null_histogram: Object.fromEntries(hist.map((v, i) => [String(i), v])),
    empirical_tail_probability: (ge + 1) / (PERMUTATIONS + 1),
  };
}

export function analyze(summary) {
  const trials = summary.trials ?? [];
  const distinctByBlock = new Map();
  const distinctRows = [];
  const controlRows = [];

  for (const t of trials) {
    const rows = t.records ?? [];
    if (t.arm === 'distinct_churn') {
      distinctByBlock.set(Number(t.block), rows);
      for (const r of rows) distinctRows.push({ ...r, block: Number(t.block), arm: t.arm });
    } else {
      for (const r of rows) controlRows.push({ ...r, block: Number(t.block), arm: t.arm });
    }
  }

  if (distinctByBlock.size !== 4) throw new Error('expected four distinct-churn blocks');

  const perBlock = {};
  for (const [block, rows] of distinctByBlock.entries()) {
    perBlock[String(block)] = {
      hull: hullFor(rows),
      max_drop: maxDropM(rows),
    };
  }

  return {
    experiment_id: 'MATH-002-PMNDRS-GEOMETRIC-LENS-v1',
    source_experiment: summary.experiment_id,
    primary_decision: summary.decision,
    pmndrs_math_commit: '98762395c1f34d7d594d31165e8005fd6915c431',
    distinct_hull: hullFor(distinctRows),
    control_hull: hullFor(controlRows),
    per_block: perBlock,
    permutation: permutationNull(distinctByBlock),
    inference_boundary:
      'Secondary geometry/permutation diagnostic only; cannot override MEMCG-003B primary decision.',
  };
}

function main() {
  const args = parseArgs(process.argv);
  const input = args['--input'];
  const output = args['--output'];
  if (!input || !output) throw new Error('--input and --output required');
  const summary = JSON.parse(fs.readFileSync(input, 'utf8'));
  const result = analyze(summary);
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({
    observed_g: result.permutation.observed_g,
    empirical_tail_probability: result.permutation.empirical_tail_probability,
    distinct_hull_area: result.distinct_hull.area,
    control_hull_area: result.control_hull.area,
  }, null, 2));
}

const invoked = process.argv[1] && import.meta.url === new URL('file://' + process.argv[1]).href;
if (invoked) main();
