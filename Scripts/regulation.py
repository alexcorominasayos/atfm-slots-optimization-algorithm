"""Fluid model of the regulation: when does the queue created by the reduced capacity disappear?

Idea: draw the cumulative demand (arrivals so far) and a cumulative capacity line. While the
capacity is reduced the line grows slowly, so the demand curve stays above it; the area between
both curves is the total delay. After the reduced-capacity period the line grows faster until
it meets the demand curve again. That minute is the end of the delay (called `Hnoreg` or
`LastDelay` in the old code, which hard-coded it as 907 in two files).
"""
import numpy as np

from config import (MINUTES_PER_DAY, NOMINAL_CAPACITY, REDUCED_CAPACITY,
                    REGULATION_END_MIN, REGULATION_START_MIN)


def cumulative_demand(eta_min):
    """Number of arrivals up to the end of every minute of the day (position 0 = minute 1).

    Args:
        eta_min: arrival time of every flight, in minutes since midnight.
    """
    arrivals_per_minute = np.bincount(eta_min, minlength=MINUTES_PER_DAY + 1)[1:MINUTES_PER_DAY + 1]
    return np.cumsum(arrivals_per_minute)


def simulate_regulation(demand):
    """Walk the capacity line minute by minute.

    Args:
        demand: cumulative demand, as returned by cumulative_demand().

    Returns:
        minutes: every minute from the start of the regulation to the end of the delay.
        capacity: cumulative capacity at those minutes.
        end_minute: minute at which the capacity line meets the demand curve.
        total_delay: area between both curves, in minutes of delay for all the flights together.
    """
    capacity = [demand[REGULATION_START_MIN - 1]]   # the line starts on the demand curve
    total_delay = 0.0

    # Phase 1: reduced capacity. Per minute the line grows REDUCED_CAPACITY / 60 arrivals
    for minute in range(REGULATION_START_MIN + 1, REGULATION_END_MIN + 1):
        capacity.append(capacity[-1] + REDUCED_CAPACITY / 60)
        total_delay += demand[minute - 1] - capacity[-1]

    # Phase 2: nominal capacity, until the line reaches the demand curve (and stays on it)
    minute = REGULATION_END_MIN
    while capacity[-1] < demand[minute - 1]:
        if minute == len(demand):
            raise RuntimeError("The queue is not cleared before midnight: check the capacities in config.py")
        minute += 1
        capacity.append(min(capacity[-1] + NOMINAL_CAPACITY / 60, demand[minute - 1]))
        total_delay += demand[minute - 1] - capacity[-1]

    minutes = np.arange(REGULATION_START_MIN, minute + 1)
    return minutes, np.array(capacity), minute, round(total_delay)


def regulation_end_minute(eta_min):
    """Minute at which the delay caused by the regulation disappears (907 = 15:07 in the old code)."""
    return simulate_regulation(cumulative_demand(eta_min))[2]
