"""Minimal end-to-end example: parse, roll up, and render a report."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pulsemetrics.rollup import rollup
from pulsemetrics.report import render_report
from pulsemetrics.samples import parse_line

RAW_LINES = [
    "cpu.load 1.5",
    "cpu.load 2.5",
    "mem.used 512.0 2.0",
]


def main():
    samples = [parse_line(line) for line in RAW_LINES]
    summary = rollup(samples)
    for line in render_report(summary):
        print(line)


if __name__ == "__main__":
    main()
