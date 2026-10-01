from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class AtlasForkConfig:
    calibration_batches: int = 50
    familiarity_ratio: float = 0.85
    consecutive_below: int = 3

    def validate(self) -> None:
        if type(self.calibration_batches) is not int or self.calibration_batches <= 0:
            raise ValueError("calibration_batches_invalid")
        if not (0.0 < self.familiarity_ratio < 1.0):
            raise ValueError("familiarity_ratio_invalid")
        if type(self.consecutive_below) is not int or self.consecutive_below <= 0:
            raise ValueError("consecutive_below_invalid")


@dataclass(frozen=True)
class AtlasForkObservation:
    world_index: int
    phase: str
    familiarity: float
    baseline_familiarity: float | None
    threshold: float | None
    below_streak: int
    learning_disposition: str
    forked: bool


class AtlasForkGate:
    """Atlas-inspired familiarity fork trigger.

    This implements only the world-change gate described in Arth Singh's
    2026-09-30 Atlas Neuron article. It does not implement Atlas landmarks,
    online k-means, class charts, incremental PCA, or classification.
    """

    def __init__(self, config: AtlasForkConfig | None = None) -> None:
        self.config = config or AtlasForkConfig()
        self.config.validate()
        self.world_index = 0
        self._calibration: list[float] = []
        self._baseline: float | None = None
        self._below_streak = 0

    @property
    def baseline_familiarity(self) -> float | None:
        return self._baseline

    @property
    def threshold(self) -> float | None:
        if self._baseline is None:
            return None
        return self._baseline * self.config.familiarity_ratio

    def observe(self, familiarity: float) -> AtlasForkObservation:
        value = float(familiarity)
        if not math.isfinite(value):
            raise ValueError("familiarity_not_finite")

        if self._baseline is None:
            self._calibration.append(value)
            if len(self._calibration) == self.config.calibration_batches:
                self._baseline = sum(self._calibration) / len(self._calibration)
            return AtlasForkObservation(
                world_index=self.world_index,
                phase="CALIBRATE",
                familiarity=value,
                baseline_familiarity=self._baseline,
                threshold=self.threshold,
                below_streak=0,
                learning_disposition="LEARN_CURRENT",
                forked=False,
            )

        threshold = self.threshold
        assert threshold is not None

        if value < threshold:
            self._below_streak += 1
            if self._below_streak >= self.config.consecutive_below:
                old_world = self.world_index
                self.world_index += 1
                observation = AtlasForkObservation(
                    world_index=old_world,
                    phase="FORK",
                    familiarity=value,
                    baseline_familiarity=self._baseline,
                    threshold=threshold,
                    below_streak=self._below_streak,
                    learning_disposition="WITHHOLD",
                    forked=True,
                )
                self._calibration = []
                self._baseline = None
                self._below_streak = 0
                return observation

            return AtlasForkObservation(
                world_index=self.world_index,
                phase="SUSPECT",
                familiarity=value,
                baseline_familiarity=self._baseline,
                threshold=threshold,
                below_streak=self._below_streak,
                learning_disposition="WITHHOLD",
                forked=False,
            )

        self._below_streak = 0
        return AtlasForkObservation(
            world_index=self.world_index,
            phase="STABLE",
            familiarity=value,
            baseline_familiarity=self._baseline,
            threshold=threshold,
            below_streak=0,
            learning_disposition="LEARN_CURRENT",
            forked=False,
        )


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("vector_shape_invalid")
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    aa = sum(float(x) * float(x) for x in a)
    bb = sum(float(y) * float(y) for y in b)
    if aa <= 0.0 or bb <= 0.0:
        raise ValueError("zero_norm_vector")
    return dot / math.sqrt(aa * bb)


def nearest_landmark_familiarity(
    codes: Iterable[Sequence[float]],
    landmarks: Sequence[Sequence[float]],
) -> float:
    landmark_list = list(landmarks)
    code_list = list(codes)
    if not landmark_list or not code_list:
        raise ValueError("empty_codes_or_landmarks")
    nearest = [
        max(cosine_similarity(code, landmark) for landmark in landmark_list)
        for code in code_list
    ]
    return sum(nearest) / len(nearest)
