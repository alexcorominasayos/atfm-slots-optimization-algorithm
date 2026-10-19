"""How much delay is saved if a train replaces some flights? Two ways to estimate it.

Replaces compute_delay_reduction_train.py and CompareDelayReduction.py:
  1. From the GDP schedule: take the delay each replaced flight has there and remove it.
  2. From the slots: give the slots again, in ETA order, to the flights that remain.
The GHP version of this comparison is in run_ghp.py.
Run substitute_flights.py first (it writes the reduced demand), then:  python compare_delay_reduction.py
"""
import numpy as np

from gdp import run_gdp, slot_window
from flight_data import flights
from regulation import regulation_end_minute
from train import load_reduced_arcids, substitutable_mask
from utils import minutes_to_hhmm


def slot_order_delays(day_flights, regulation_end):
    """Delay of every flight if the slots went to the flights in ETA order (slot k to flight k), never negative."""
    window, slot_times = slot_window(day_flights, regulation_end)
    return np.maximum(slot_times - window["eta_min"].to_numpy(), 0)


def run():
    regulation_end = regulation_end_minute(flights["eta_min"].to_numpy())

    # 1. Remove, from the GDP schedule, the delay of the flights that a train replaces
    schedule = run_gdp(flights, regulation_end)
    replaced = substitutable_mask(schedule)
    total = schedule["delay"].sum()
    removed = schedule.loc[replaced, "delay"].sum()
    print("1. Delay removed from the GDP schedule")
    print(f"   Flights replaced by train: {replaced.sum()}")
    print(f"   Total delay: {total} min | removed: {removed} min | remaining: {total - removed} min")
    print(f"   Reduction: {100 * removed / total:.2f} %")

    # 2. Give the slots again to the flights that remain (same slots as the full schedule)
    reduced_flights = flights[flights["arcid"].isin(load_reduced_arcids())]
    full_delays = slot_order_delays(flights, regulation_end)
    reduced_delays = slot_order_delays(reduced_flights, regulation_end)
    recovered = full_delays.sum() - reduced_delays.sum()
    print("\n2. Slots given again in ETA order")
    print(f"   Full schedule:    total {full_delays.sum()} min, mean {full_delays.mean():.2f} min/flight")
    print(f"   Reduced schedule: total {reduced_delays.sum()} min, mean {reduced_delays.mean():.2f} min/flight")
    print(f"   Delay recovered: {recovered} min ({100 * recovered / full_delays.sum():.2f} %)")

    reduced_end = regulation_end_minute(reduced_flights["eta_min"].to_numpy())
    print(f"   The delay ends at {minutes_to_hhmm(regulation_end)} in the full schedule "
          f"and at {minutes_to_hhmm(reduced_end)} without the replaced flights")


if __name__ == "__main__":
    run()
