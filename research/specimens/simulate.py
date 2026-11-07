"""Metropolis simulation of the two-dimensional Ising model for the specimen data.

Writes one CSV row per temperature: the mean absolute magnetisation per spin
and the susceptibility per spin, each with a blocking error. Units: J = k_B = 1.

Usage:
    python simulate.py OUTPUT.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

LATTICE_SIZE = 32
TEMPERATURES = np.round(np.arange(1.6, 3.41, 0.1), 2)
THERMALISATION_SWEEPS = 2_000
MEASUREMENT_SWEEPS = 20_000
BLOCK_COUNT = 20
SEED = 20261107

Lattice = NDArray[np.int8]
Series = NDArray[np.float64]


def checkerboard_masks(size: int) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
    rows, cols = np.indices((size, size))
    even = (rows + cols) % 2 == 0
    return even, ~even


def neighbour_sum(spins: Lattice) -> NDArray[np.int64]:
    wide = spins.astype(np.int64)
    return (
        np.roll(wide, 1, axis=0)
        + np.roll(wide, -1, axis=0)
        + np.roll(wide, 1, axis=1)
        + np.roll(wide, -1, axis=1)
    )


def sweep(
    spins: Lattice,
    beta: float,
    masks: tuple[NDArray[np.bool_], NDArray[np.bool_]],
    rng: np.random.Generator,
) -> None:
    """One Metropolis sweep, updating each sublattice of the checkerboard at once."""
    for mask in masks:
        energy_change = 2 * spins * neighbour_sum(spins)
        boltzmann = np.exp(-beta * energy_change)
        accept = rng.random(spins.shape) < boltzmann
        spins[mask & accept] *= -1


def blocking_error(samples: Series) -> float:
    blocks = samples[: len(samples) // BLOCK_COUNT * BLOCK_COUNT].reshape(BLOCK_COUNT, -1)
    means = blocks.mean(axis=1)
    return float(means.std(ddof=1) / np.sqrt(BLOCK_COUNT))


def susceptibility_with_error(
    magnetisation: Series, beta: float, spin_count: int
) -> tuple[float, float]:
    """Susceptibility per spin, with a jackknife error over the same blocks."""

    def estimate(sample: Series) -> float:
        return float(beta * spin_count * (np.mean(sample**2) - np.mean(sample) ** 2))

    blocks = np.array_split(magnetisation, BLOCK_COUNT)
    leave_one_out = np.array(
        [estimate(np.concatenate(blocks[:i] + blocks[i + 1 :])) for i in range(BLOCK_COUNT)]
    )
    spread = np.sqrt((BLOCK_COUNT - 1) * np.mean((leave_one_out - leave_one_out.mean()) ** 2))
    return estimate(magnetisation), float(spread)


def run(output: Path) -> None:
    rng = np.random.default_rng(SEED)
    masks = checkerboard_masks(LATTICE_SIZE)
    spins: Lattice = np.ones((LATTICE_SIZE, LATTICE_SIZE), dtype=np.int8)
    spin_count = LATTICE_SIZE**2
    rows = []
    for temperature in TEMPERATURES:
        beta = 1.0 / float(temperature)
        for _ in range(THERMALISATION_SWEEPS):
            sweep(spins, beta, masks, rng)
        magnetisation = np.empty(MEASUREMENT_SWEEPS)
        for i in range(MEASUREMENT_SWEEPS):
            sweep(spins, beta, masks, rng)
            magnetisation[i] = abs(int(spins.sum())) / spin_count
        chi, chi_error = susceptibility_with_error(magnetisation, beta, spin_count)
        rows.append(
            (
                float(temperature),
                magnetisation.mean(),
                blocking_error(magnetisation),
                chi,
                chi_error,
            )
        )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["temperature", "abs_m", "abs_m_err", "chi", "chi_err"])
        writer.writerows([f"{value:.6g}" for value in row] for row in rows)


if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004
        sys.exit("usage: simulate.py OUTPUT.csv")
    run(Path(sys.argv[1]))
