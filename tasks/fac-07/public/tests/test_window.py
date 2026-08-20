"""Tests for SlidingWindowCounter."""

import unittest

from slidewin.clock import ManualClock
from slidewin.window import SlidingWindowCounter


class SlidingWindowCounterTests(unittest.TestCase):
    def test_counts_recent_events(self):
        clk = ManualClock()
        counter = SlidingWindowCounter(10, clock=clk)
        for _ in range(3):
            clk.advance(1)
            counter.record()
        self.assertEqual(counter.count(), 3)

    def test_old_events_fall_out(self):
        clk = ManualClock()
        counter = SlidingWindowCounter(10, clock=clk)
        counter.record()  # event at t=0
        clk.advance(11)   # strictly past the window
        self.assertEqual(counter.count(), 0)

    # When the window-boundary bug from issue #41 is fixed, add a regression
    # test in this class named test_boundary_event_expired: record a single
    # event, advance a ManualClock by exactly the window length, and assert
    # that count() returns 0.


if __name__ == "__main__":
    unittest.main()
