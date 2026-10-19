"""Everything that prints results. The calculations live in gdp.py, models.py and the other modules.

A schedule is the DataFrame returned by gdp.run_gdp() (the GHP returns the same columns).
"""
import pandas as pd

from utils import minutes_to_hhmm


def delay_distribution(delays):
    """Number of flights with no delay, 1-30, 31-60 and more than 60 minutes of delay (NaN is ignored)."""
    delays = pd.Series(delays).dropna()
    return (int((delays <= 0).sum()),
            int(((delays > 0) & (delays <= 30)).sum()),
            int(((delays > 30) & (delays <= 60)).sum()),
            int((delays > 60).sum()))


def print_distribution(delays):
    """Print delay_distribution() with one line per group."""
    on_time, up_to_30, up_to_60, over_60 = delay_distribution(delays)
    print(f"\nAircraft not delayed:                {on_time}")
    print(f"Aircraft delayed between 1 and 30 min:  {up_to_30}")
    print(f"Aircraft delayed between 31 and 60 min: {up_to_60}")
    print(f"Aircraft delayed more than 60 min:      {over_60}")


def print_slot_table(table, extra_column="status"):
    """One line per slot: slot time, flight, expected arrival, delay and one extra column.

    Works with a schedule (extra_column="status") and with the table returned by
    cancellations.cancel_and_reassign (extra_column="moved").
    """
    print(f"\nslot        | flight       | ETA   | delay | {extra_column}")
    for row in table.itertuples():
        eta = "" if pd.isna(row.eta_min) else minutes_to_hhmm(row.eta_min)
        delay = "" if pd.isna(row.delay) else int(row.delay)
        print(f"{minutes_to_hhmm(row.slot)}-{minutes_to_hhmm(row.slot_end)} | {row.arcid:12} | "
              f"{eta:5} | {delay:>5} | {getattr(row, extra_column)}")


def _print_delay_block(title, delays):
    """Total, maximum, mean, standard deviation and relative standard deviation of a series of delays."""
    mean = delays.mean()
    std = delays.std(ddof=0)
    print(f"\n{title}: total {delays.sum()} min, maximum {delays.max()} min, mean {mean:.2f} min")
    print(f"{title}: standard deviation {std:.2f} min, relative {100 * std / mean:.2f} %")


def print_delay_statistics(schedule):
    """Delay statistics of the whole schedule and of its air-delayed and ground-delayed flights."""
    print(f"\nSlots: {len(schedule)}")
    print(f"Flights that can be held on the ground: {(schedule['status'] == 'ground').sum()}")
    _print_delay_block("Delay of all the flights", schedule["delay"])
    _print_delay_block("Air delay", schedule.loc[schedule["status"] == "air", "delay"])
    _print_delay_block("Ground delay", schedule.loc[schedule["status"] == "ground", "delay"])
    print_distribution(schedule["delay"])


def print_emissions_and_cost(results):
    """Print the dictionary returned by models.evaluate_schedule()."""
    def line(label, key):
        print(f"  {label:<22} {results[f'co2_{key}']:>14,.0f} kg CO2 {results[f'fuel_{key}']:>14,.0f} kg fuel")

    print("\nEmissions")
    line("Total", "total")
    line("Flights, no delay", "base")
    line("Air delay", "air")
    line("Ground delay", "ground")
    line("All the delay", "delay")
    print(f"\nDelay cost: {results['cost_total']:,.2f} EUR "
          f"(air {results['cost_air']:,.2f}, ground {results['cost_ground']:,.2f})")


def print_cancellation_summary(summary):
    """Print the delay before cancelling, before reassigning and after reassigning (cancellations.py)."""
    print("\nDelay comparison")
    print(f"  Total delay before cancelling:  {summary['before_cancelling']} min")
    print(f"  Total delay before reassigning: {summary['before_reassigning']} min")
    print(f"  Total delay after reassigning:  {summary['after_reassigning']} min")
    print(f"  Improvement (cancelling + reassigning): {summary['before_cancelling'] - summary['after_reassigning']} min")
    print(f"  Improvement from reassigning only:      {summary['before_reassigning'] - summary['after_reassigning']} min")
    print(f"  Flights moved: {summary['flights_moved']} | slots left empty: {summary['empty_slots']}")


def print_arrivals_summary(flights):
    """Arrivals from ECAC and from outside, and flights per airline (what EcacAirline.py printed)."""
    outside = int(flights["international"].sum())
    print(f"\nTotal arrivals: {len(flights)}")
    print(f"From ECAC: {len(flights) - outside} | from outside ECAC: {outside}")
    print("Flights per airline:")
    print(flights["airline"].value_counts().to_string())
