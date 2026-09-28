PRAGMA foreign_keys=ON;

CREATE TABLE experiments (
  experiment_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  result_doc TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status='PASS'),
  runner TEXT NOT NULL,
  artifact_digest TEXT NOT NULL,
  accepted_at_bounce TEXT NOT NULL,
  inference_boundary TEXT NOT NULL
);

CREATE TABLE response_cells (
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  condition_id TEXT NOT NULL,
  runner TEXT NOT NULL,
  memory_high_mib REAL,
  memory_max_mib REAL,
  hot_anon_mib REAL,
  cold_file_mib REAL,
  release_interval_mib REAL,
  arm_kind TEXT NOT NULL,
  median_high_events REAL,
  positive_trials INTEGER,
  trial_count INTEGER,
  median_peak_mib REAL,
  median_floor_mib REAL,
  floor_scope TEXT NOT NULL CHECK(floor_scope IN ('total_cgroup','non_hot','none')),
  floor_semantics TEXT NOT NULL CHECK(floor_semantics IN ('clean_pre_observer','legacy_post_observer','post_observer_diagnostic','not_applicable')),
  median_file_residency REAL,
  advice_calls REAL,
  oom_any INTEGER NOT NULL DEFAULT 0 CHECK(oom_any IN (0,1)),
  PRIMARY KEY(experiment_id, condition_id)
);

CREATE TABLE onset_intervals (
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  condition_id TEXT NOT NULL,
  memory_high_mib REAL NOT NULL,
  hot_anon_mib REAL NOT NULL,
  cold_file_mib REAL NOT NULL,
  knee_lower_exclusive_mib REAL,
  knee_upper_inclusive_mib REAL,
  right_censored INTEGER NOT NULL CHECK(right_censored IN (0,1)),
  transformed_lower_exclusive_mib REAL,
  transformed_upper_inclusive_mib REAL,
  PRIMARY KEY(experiment_id, condition_id)
);

CREATE TABLE observer_cells (
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  condition_id TEXT NOT NULL,
  target_size_mib REAL NOT NULL,
  median_observer_delta_mib REAL,
  positive_trials INTEGER NOT NULL,
  trial_count INTEGER NOT NULL,
  retained_delta_mib REAL,
  measurement TEXT NOT NULL,
  PRIMARY KEY(experiment_id, condition_id)
);

CREATE TABLE measurement_notes (
  note_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  kind TEXT NOT NULL,
  text TEXT NOT NULL
);

CREATE VIEW v_live_set_transform AS
SELECT experiment_id, condition_id, memory_high_mib, hot_anon_mib,
       knee_lower_exclusive_mib, knee_upper_inclusive_mib,
       transformed_lower_exclusive_mib, transformed_upper_inclusive_mib
FROM onset_intervals
WHERE memory_high_mib=160 AND cold_file_mib=96
  AND experiment_id IN ('STRATA-004-KNEE-v1','STRATA-006-LIVESET-HEADROOM-v1');

CREATE VIEW v_capacity_knee AS
SELECT experiment_id, cold_file_mib, knee_lower_exclusive_mib,
       knee_upper_inclusive_mib
FROM onset_intervals
WHERE memory_high_mib=160 AND hot_anon_mib=64
  AND experiment_id IN (
    'STRATA-007-CROSS-IMAGE-v1',
    'STRATA-008-COLD-CAPACITY-v1',
    'STRATA-009-DATASET-GT-MEMORYMAX-v1'
  );

CREATE VIEW v_clean_floor AS
SELECT * FROM response_cells
WHERE floor_semantics='clean_pre_observer';

CREATE VIEW v_legacy_floor AS
SELECT * FROM response_cells
WHERE floor_semantics='legacy_post_observer';

CREATE VIEW v_observer_effect AS
SELECT * FROM observer_cells;
