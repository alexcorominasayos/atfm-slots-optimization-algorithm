"""Run the Ground Delay Program (GDP) on the arrivals of the day.

Replaces graph.py, slots.py and the script part of AssignSlotsGDP.py.
Switch on or off what you want to see with the flags below, then run:  python run_gdp.py
"""
import matplotlib.pyplot as plt

import reports
from cancellations import cancel_and_reassign, find_cancelled
from gdp import run_gdp, unrecoverable_delay
from flight_data import flights
from models import evaluate_schedule
from plots import plot_aggregate_demand, plot_arrival_histogram, plot_delay_pies
from regulation import cumulative_demand, simulate_regulation
from utils import minutes_to_hhmm

SHOW_ARRIVALS_SUMMARY = False   # ECAC / non-ECAC arrivals and flights per airline
SHOW_SLOT_TABLE = False         # one line per slot (long)
SHOW_CANCELLATIONS = True       # cancel the long-delayed flights and give their slots to other flights
SHOW_PLOTS = True


def run():
    if SHOW_ARRIVALS_SUMMARY:
        reports.print_arrivals_summary(flights)

    # 1. Demand against capacity: how long does the delay last?
    demand = cumulative_demand(flights["eta_min"].to_numpy())
    minutes, capacity, regulation_end, total_delay = simulate_regulation(demand)
    print(f"Total delay of the regulation (demand against capacity): {total_delay} min")
    print(f"The delay disappears at {minutes_to_hhmm(regulation_end)}")

    # 2. Assign the slots and look at the delays, emissions and cost
    schedule = run_gdp(flights, regulation_end)
    if SHOW_SLOT_TABLE:
        reports.print_slot_table(schedule)
    reports.print_delay_statistics(schedule)
    print(f"\nUnrecoverable delay: {unrecoverable_delay(schedule)} min")
    reports.print_emissions_and_cost(evaluate_schedule(schedule))

    # 3. Cancel the flights with a very long delay and reuse their slots
    if SHOW_CANCELLATIONS:
        cancelled = find_cancelled(schedule)
        after, summary = cancel_and_reassign(schedule, cancelled)
        print(f"\nCancelled flights: {len(cancelled)}")
        reports.print_cancellation_summary(summary)

    # 4. Plots
    if SHOW_PLOTS:
        plot_arrival_histogram(flights["eta_min"] / 60)
        plot_aggregate_demand(demand, minutes, capacity)
        outside_regulation = flights[~flights["arcid"].isin(schedule["arcid"])]
        plot_arrival_histogram(schedule["slot"] / 60, outside_regulation["eta_min"] / 60)
        if SHOW_CANCELLATIONS:
            plot_delay_pies(reports.delay_distribution(schedule["delay"]),
                            reports.delay_distribution(after["delay"]))
        plt.show()


if __name__ == "__main__":
    run()
