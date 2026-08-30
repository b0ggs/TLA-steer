"""Synchronous semantic-step SMC for the fixed TLA-Steer prototype.

The model boundary and semantic scorer are injected callables.  The engine
therefore stays offline-testable and never executes generated controller or
candidate code itself.
"""

from __future__ import annotations

import math
import random
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Callable, Mapping, Sequence

from .contract import (
    Controller,
    ControllerStep,
    ContractError,
    Proposal,
    State,
    validate_controller,
    validate_proposal,
    validate_state,
)


@dataclass(frozen=True, slots=True)
class SMCConfig:
    population_size: int = 8
    concurrency: int = 4
    seed: int = 0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.population_size, int)
            or isinstance(self.population_size, bool)
            or self.population_size <= 0
        ):
            raise ValueError("population_size must be a positive integer")
        if (
            not isinstance(self.concurrency, int)
            or isinstance(self.concurrency, bool)
            or not 1 <= self.concurrency <= self.population_size
        ):
            raise ValueError("concurrency must be in 1..population_size")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")

    @property
    def ess_threshold(self) -> float:
        return self.population_size / 2.0


@dataclass(frozen=True, slots=True)
class IncrementalScore:
    value: float
    components: tuple[tuple[str, float], ...] = ()
    error: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("incremental score must be numeric")
        numeric = float(self.value)
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise ValueError("incremental score must be finite and in 0..1")
        object.__setattr__(self, "value", numeric)
        clean_components: list[tuple[str, float]] = []
        seen: set[str] = set()
        for name, amount in self.components:
            if not isinstance(name, str) or not name or name in seen:
                raise ValueError("score component names must be unique nonempty strings")
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                raise ValueError("score components must be numeric")
            component = float(amount)
            if not math.isfinite(component):
                raise ValueError("score components must be finite")
            seen.add(name)
            clean_components.append((name, component))
        object.__setattr__(self, "components", tuple(clean_components))
        if self.error is not None and not isinstance(self.error, str):
            raise ValueError("score error must be a string or None")


@dataclass(frozen=True, slots=True)
class ScoreRecord:
    step_index: int
    step_id: str
    value: float
    components: tuple[tuple[str, float], ...]
    error: str | None


@dataclass(frozen=True, slots=True)
class Particle:
    particle_id: str
    parent_id: str | None
    ancestry: tuple[str, ...]
    completed_step_index: int
    fragments: tuple[Proposal, ...]
    current_log_weight: float
    score_history: tuple[ScoreRecord, ...]
    status: str

    @property
    def partial_artifact(self) -> str:
        if not self.fragments:
            return ""
        return "\n\n".join(fragment.python_fragment.rstrip() for fragment in self.fragments) + "\n"

    @property
    def fragment_map(self) -> dict[str, str]:
        return {
            fragment.step_id: fragment.python_fragment for fragment in self.fragments
        }


@dataclass(frozen=True, slots=True)
class StepTrace:
    step_index: int
    step_id: str
    target: str
    input_particle_ids: tuple[str, ...]
    incremental_scores: tuple[float | None, ...]
    log_weights: tuple[float, ...]
    normalized_weights: tuple[float, ...]
    ess: float
    resampled: bool
    ancestor_ids: tuple[str, ...]
    output_particle_ids: tuple[str, ...]
    errors: tuple[str | None, ...]
    particle_collapse: bool


@dataclass(frozen=True, slots=True)
class SMCResult:
    controller: Controller
    config: SMCConfig
    particles: tuple[Particle, ...]
    traces: tuple[StepTrace, ...]
    official_particle: Particle | None
    official_particle_index: int | None
    selection_weights: tuple[float, ...]
    stopping_reason: str

    @property
    def collapsed(self) -> bool:
        return self.stopping_reason == "particle_collapse"

    @property
    def completed(self) -> bool:
        return self.stopping_reason == "completed"

    @property
    def selected_particle(self) -> Particle | None:
        """Readable alias for integrations that call the official output selected."""

        return self.official_particle


@dataclass(frozen=True, slots=True)
class ActionObservation:
    expected_successor: State | Mapping[str, object] | None
    actual_successor: State | Mapping[str, object] | None
    input_mutated: bool = False
    deterministic: bool = True
    error: str | None = None


Follower = Callable[[Particle, ControllerStep], Proposal | Mapping[str, object]]
Scorer = Callable[
    [Particle, ControllerStep, Proposal], IncrementalScore | float
]


def _coerce_state(value: State | Mapping[str, object] | None) -> State | None:
    if value is None or isinstance(value, State):
        return value
    return validate_state(value)


def score_initial_state(
    actual: State | Mapping[str, object] | None,
    expected: State | Mapping[str, object],
) -> IncrementalScore:
    """Score exact-key INITIAL output by the five frozen state fields."""

    try:
        actual_state = _coerce_state(actual)
        expected_state = _coerce_state(expected)
    except ContractError as exc:
        return IncrementalScore(0.0, error=str(exc))
    if actual_state is None or expected_state is None:
        return IncrementalScore(0.0, error="INITIAL is missing")
    matches = sum(
        getattr(actual_state, key) == getattr(expected_state, key)
        for key in ("clock", "lightA", "timerA", "lightB", "timerB")
    )
    value = matches / 5.0
    return IncrementalScore(
        value,
        components=(("matching_fields", float(matches)), ("field_match_rate", value)),
    )


def score_action_observations(
    observations: Sequence[ActionObservation],
) -> IncrementalScore:
    """Apply the frozen balanced enabledness/successor scoring formula."""

    if not observations:
        raise ValueError("action scoring requires observations")
    normalized: list[tuple[State | None, State | None]] = []
    for observation in observations:
        if observation.error:
            return IncrementalScore(0.0, error=observation.error)
        if observation.input_mutated:
            return IncrementalScore(0.0, error="action mutated its input")
        if not observation.deterministic:
            return IncrementalScore(0.0, error="action was nondeterministic")
        try:
            expected = _coerce_state(observation.expected_successor)
            actual = _coerce_state(observation.actual_successor)
        except ContractError as exc:
            return IncrementalScore(0.0, error=str(exc))
        normalized.append((expected, actual))

    expected_enabled = sum(expected is not None for expected, _actual in normalized)
    expected_disabled = len(normalized) - expected_enabled
    if not expected_enabled or not expected_disabled:
        raise ValueError("action observations need expected-enabled and disabled cases")
    predicted_enabled = sum(actual is not None for _expected, actual in normalized)
    enabled_true_positives = sum(
        expected is not None and actual is not None for expected, actual in normalized
    )
    exact_successors = sum(
        expected is not None and actual == expected for expected, actual in normalized
    )

    precision = (
        enabled_true_positives / predicted_enabled if predicted_enabled else 0.0
    )
    recall = enabled_true_positives / expected_enabled
    successor_rate = exact_successors / expected_enabled
    value = 0.25 * precision + 0.25 * recall + 0.50 * successor_rate
    return IncrementalScore(
        value,
        components=(
            ("enabledness_precision", precision),
            ("enabledness_recall", recall),
            ("exact_successor_rate", successor_rate),
        ),
    )


def normalize_log_weights(log_weights: Sequence[float]) -> tuple[float, ...]:
    """Normalize log weights; all-zero mass is represented by all zeros."""

    finite = [weight for weight in log_weights if math.isfinite(weight)]
    if not finite:
        return tuple(0.0 for _weight in log_weights)
    maximum = max(finite)
    masses = [
        0.0 if not math.isfinite(weight) else math.exp(weight - maximum)
        for weight in log_weights
    ]
    total = sum(masses)
    if not total or not math.isfinite(total):
        return tuple(0.0 for _weight in log_weights)
    return tuple(mass / total for mass in masses)


def effective_sample_size(weights: Sequence[float]) -> float:
    denominator = sum(weight * weight for weight in weights)
    return 0.0 if denominator == 0.0 else 1.0 / denominator


def _draw_index(weights: Sequence[float], rng: random.Random) -> int:
    if not weights or sum(weights) <= 0.0:
        raise ValueError("cannot draw from zero weights")
    point = rng.random()
    cumulative = 0.0
    last_positive = 0
    for index, weight in enumerate(weights):
        if weight > 0.0:
            last_positive = index
        cumulative += weight
        if point < cumulative:
            return index
    # Protect against the final cumulative sum being 0.9999999999999999.
    return last_positive


def multinomial_resample(
    particles: Sequence[Particle],
    weights: Sequence[float],
    *,
    rng: random.Random,
    step_index: int,
) -> tuple[tuple[Particle, ...], tuple[str, ...]]:
    """Draw independent categorical ancestors and reset weights uniformly."""

    if len(particles) != len(weights) or not particles:
        raise ValueError("particles and weights must have the same nonzero length")
    uniform_log_weight = -math.log(len(particles))
    children: list[Particle] = []
    ancestor_ids: list[str] = []
    for child_index in range(len(particles)):
        ancestor = particles[_draw_index(weights, rng)]
        child_id = f"p{step_index + 1:02d}-{child_index:04d}"
        children.append(
            replace(
                ancestor,
                particle_id=child_id,
                parent_id=ancestor.particle_id,
                ancestry=ancestor.ancestry + (ancestor.particle_id,),
                current_log_weight=uniform_log_weight,
                status="alive",
            )
        )
        ancestor_ids.append(ancestor.particle_id)
    return tuple(children), tuple(ancestor_ids)


def _score_value(value: IncrementalScore | float) -> IncrementalScore:
    return value if isinstance(value, IncrementalScore) else IncrementalScore(value)


def _zero_record(step_index: int, step: ControllerStep, error: str) -> ScoreRecord:
    return ScoreRecord(
        step_index=step_index,
        step_id=step.id,
        value=0.0,
        components=(),
        error=error,
    )


def run_smc(
    controller: Controller | Mapping[str, object],
    follower: Follower,
    scorer: Scorer,
    *,
    config: SMCConfig | None = None,
) -> SMCResult:
    """Run the fixed eight-step SMC loop and select before any verification.

    ``follower`` calls are concurrent within a semantic step and separated by
    a barrier between steps.  ``scorer`` receives the tentative particle with
    the new fragment already attached.  Exceptions are evidence-bearing zero
    weights rather than retries.
    """

    frozen_controller = validate_controller(controller)
    selected_config = config or SMCConfig()
    rng = random.Random(selected_config.seed)
    uniform_log_weight = -math.log(selected_config.population_size)
    particles: tuple[Particle, ...] = tuple(
        Particle(
            particle_id=f"p00-{index:04d}",
            parent_id=None,
            ancestry=(),
            completed_step_index=-1,
            fragments=(),
            current_log_weight=uniform_log_weight,
            score_history=(),
            status="alive",
        )
        for index in range(selected_config.population_size)
    )
    traces: list[StepTrace] = []

    with ThreadPoolExecutor(max_workers=selected_config.concurrency) as executor:
        for step_index, step in enumerate(frozen_controller.steps):
            input_particles = particles
            futures: dict[int, Future[Proposal | Mapping[str, object]]] = {}
            for index, particle in enumerate(input_particles):
                if particle.status == "alive":
                    futures[index] = executor.submit(follower, particle, step)

            next_particles: list[Particle] = list(input_particles)
            incremental_scores: list[float | None] = [None] * len(input_particles)
            errors: list[str | None] = [None] * len(input_particles)
            for index, particle in enumerate(input_particles):
                future = futures.get(index)
                if future is None:
                    continue
                try:
                    raw_proposal = future.result()
                    proposal = validate_proposal(raw_proposal, step=step)
                except Exception as exc:  # A failed hosted call kills one proposal.
                    error = f"follower proposal failed: {type(exc).__name__}: {exc}"
                    record = _zero_record(step_index, step, error)
                    next_particles[index] = replace(
                        particle,
                        current_log_weight=-math.inf,
                        score_history=particle.score_history + (record,),
                        status="dead",
                    )
                    incremental_scores[index] = 0.0
                    errors[index] = error
                    continue

                candidate = replace(
                    particle,
                    completed_step_index=step_index,
                    fragments=particle.fragments + (proposal,),
                )
                try:
                    score = _score_value(scorer(candidate, step, proposal))
                except Exception as exc:
                    score = IncrementalScore(
                        0.0,
                        error=f"scorer failed: {type(exc).__name__}: {exc}",
                    )
                record = ScoreRecord(
                    step_index=step_index,
                    step_id=step.id,
                    value=score.value,
                    components=score.components,
                    error=score.error,
                )
                new_log_weight = (
                    -math.inf
                    if score.value == 0.0
                    else particle.current_log_weight + math.log(score.value)
                )
                status = "dead" if score.value == 0.0 else "alive"
                if status == "alive" and step_index == len(frozen_controller.steps) - 1:
                    status = "complete"
                next_particles[index] = replace(
                    candidate,
                    current_log_weight=new_log_weight,
                    score_history=particle.score_history + (record,),
                    status=status,
                )
                incremental_scores[index] = score.value
                errors[index] = score.error

            scored_particles = tuple(next_particles)
            normalized = normalize_log_weights(
                [particle.current_log_weight for particle in scored_particles]
            )
            ess = effective_sample_size(normalized)
            collapsed = not any(normalized)
            is_final = step_index == len(frozen_controller.steps) - 1
            resampled = False
            ancestor_ids: tuple[str, ...] = ()
            particles = scored_particles
            if (
                not collapsed
                and not is_final
                and ess < selected_config.ess_threshold
            ):
                particles, ancestor_ids = multinomial_resample(
                    scored_particles,
                    normalized,
                    rng=rng,
                    step_index=step_index,
                )
                resampled = True

            traces.append(
                StepTrace(
                    step_index=step_index,
                    step_id=step.id,
                    target=step.target,
                    input_particle_ids=tuple(
                        particle.particle_id for particle in input_particles
                    ),
                    incremental_scores=tuple(incremental_scores),
                    log_weights=tuple(
                        particle.current_log_weight for particle in scored_particles
                    ),
                    normalized_weights=normalized,
                    ess=ess,
                    resampled=resampled,
                    ancestor_ids=ancestor_ids,
                    output_particle_ids=tuple(
                        particle.particle_id for particle in particles
                    ),
                    errors=tuple(errors),
                    particle_collapse=collapsed,
                )
            )
            if collapsed:
                return SMCResult(
                    controller=frozen_controller,
                    config=selected_config,
                    particles=particles,
                    traces=tuple(traces),
                    official_particle=None,
                    official_particle_index=None,
                    selection_weights=normalized,
                    stopping_reason="particle_collapse",
                )

    selection_weights = normalize_log_weights(
        [particle.current_log_weight for particle in particles]
    )
    if not any(selection_weights):
        # Defensive: the loop catches collapse at every step, including final.
        return SMCResult(
            controller=frozen_controller,
            config=selected_config,
            particles=particles,
            traces=tuple(traces),
            official_particle=None,
            official_particle_index=None,
            selection_weights=selection_weights,
            stopping_reason="particle_collapse",
        )
    official_index = _draw_index(selection_weights, rng)
    return SMCResult(
        controller=frozen_controller,
        config=selected_config,
        particles=particles,
        traces=tuple(traces),
        official_particle=particles[official_index],
        official_particle_index=official_index,
        selection_weights=selection_weights,
        stopping_reason="completed",
    )
