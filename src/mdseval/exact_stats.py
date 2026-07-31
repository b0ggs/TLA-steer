"""Minimal exact probability helpers for the bad-control sign test."""

from __future__ import annotations

import math
from dataclasses import dataclass


def _plain_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    return value


def _count(name: str, value: int) -> int:
    value = _plain_int(name, value)
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class ExactProbability:
    """A canonical probability represented only by exact integers."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _plain_int("numerator", self.numerator)
        denominator = _plain_int("denominator", self.denominator)
        if denominator <= 0:
            raise ValueError("denominator must be positive")
        if numerator < 0 or numerator > denominator:
            raise ValueError("numerator must be between zero and denominator")
        divisor = math.gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // divisor)
        object.__setattr__(self, "denominator", denominator // divisor)

    @property
    def as_float(self) -> float:
        """Return a derived approximation; exact integers remain authoritative."""

        return self.numerator / self.denominator

    def __float__(self) -> float:
        return self.as_float


def is_at_or_below(
    probability: ExactProbability, threshold: ExactProbability
) -> bool:
    """Compare two exact probabilities without converting to floats."""

    if not isinstance(probability, ExactProbability):
        raise TypeError("probability must be an ExactProbability")
    if not isinstance(threshold, ExactProbability):
        raise TypeError("threshold must be an ExactProbability")
    return (
        probability.numerator * threshold.denominator
        <= threshold.numerator * probability.denominator
    )


def one_sided_sign_test(wins: int, losses: int) -> ExactProbability:
    """Return P[X >= wins] for X ~ Binomial(wins + losses, 1/2)."""

    wins = _count("wins", wins)
    losses = _count("losses", losses)
    decisive_cases = wins + losses
    numerator = sum(
        math.comb(decisive_cases, value)
        for value in range(wins, decisive_cases + 1)
    )
    return ExactProbability(numerator, 1 << decisive_cases)
