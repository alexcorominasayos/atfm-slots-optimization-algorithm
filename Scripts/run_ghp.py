"""Compare the GHP of the full schedule with the one without the flights a train could replace.

Replaces GHP.py, GHP_reduced.py, ComputeCost_GHP.py, ComputeEmissions_GHP.py,
CompareDelayReduction_GHP.py and ComputeCostEmissionsReduced.py.
Run substitute_flights.py first (it writes the reduced demand), then:  python run_ghp.py
"""
import pandas as pd

import reports
from gdp import slot_window
from ghp import MODES, solve_ghp
from flight_data import flights
from models import base_emissions_kg, evaluate_schedule, rebooking_cost
from regulation import regulation_end_minute
from train import load_reduced_arcids
from utils import minutes_to_hhmm

SHOW_FULL_SCHEDULE_STATISTICS = False   # delay statistics of the full schedule, for every objective


def print_comparison(full, reduced):
    """Print a table with one row per number and the columns full, reduced and saved (full - reduced)."""
    table = pd.DataFrame({"full": full, "reduced": reduced})
    table["saved"] = table["full"] - table["reduced"]
    print(table.to_string(float_format=lambda value: f"{value:,.2f}"))


def summarise(schedule):
    """The numbers that are compared between the full and the reduced schedule."""
    results = evaluate_schedule(schedule)
    return {
        "Total delay (min)": schedule["delay"].sum(),
        "Mean delay (min/flight)": schedule["delay"].mean(),
        "CO2 total (kg)": results["co2_total"],
        "CO2 of the delay (kg)": results["co2_delay"],
        "  of which air delay": results["co2_air"],
        "  of which ground delay": results["co2_ground"],
        "Delay cost (EUR)": results["cost_total"],
    }


def without_delay(window):
    """Rebooking cost and CO2 of the flights themselves, as if nobody were delayed."""
    cost = sum(rebooking_cost(seats, international)
               for seats, international in zip(window["seats"], window["international"]))
    co2 = base_emissions_kg(window["co2_g_per_ask"], window["seats"], window["distance_km"]).sum()
    return {"Rebooking cost (EUR)": cost, "CO2 (kg)": co2}


def run():
    regulation_end = regulation_end_minute(flights["eta_min"].to_numpy())
    window, slot_times = slot_window(flights, regulation_end)
    reduced = window[window["arcid"].isin(load_reduced_arcids())]
    if reduced.empty:
        raise ValueError("None of the flights of the reduced demand is in the regulation window")
    print(f"Flights in the GHP: {len(window)} | after replacing flights by train: {len(reduced)}")

    for mode in MODES:
        full_schedule, _ = solve_ghp(window, slot_times, mode)
        reduced_schedule, _ = solve_ghp(reduced, slot_times, mode)

        print(f"\n=== GHP that minimises the {mode} ===")
        print_comparison(summarise(full_schedule), summarise(reduced_schedule))
        saved = full_schedule["delay"].sum() - reduced_schedule["delay"].sum()
        print(f"Delay recovered: {saved} min ({100 * saved / full_schedule['delay'].sum():.2f} %)")
        print(f"New end of the regulation (reduced schedule): {minutes_to_hhmm(reduced_schedule['slot'].max())}")
        if SHOW_FULL_SCHEDULE_STATISTICS:
            reports.print_delay_statistics(full_schedule)

    print("\n=== Without any delay (just removing the flights) ===")
    print_comparison(without_delay(window), without_delay(reduced))


if __name__ == "__main__":
    run()
