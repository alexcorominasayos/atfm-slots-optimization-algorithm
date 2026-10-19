"""Reusable plots. They only draw: every number comes from the caller.

The functions return the figure and never call plt.show(); call it once at the end of the script
so all the figures open together.
"""
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d

from config import NOMINAL_CAPACITY, REDUCED_CAPACITY, REGULATION_END_MIN, REGULATION_START_MIN

HOUR_EDGES = np.arange(25)    # one histogram bin per hour of the day
DELAY_LABELS = ["None", "1 to 30 min", "31 to 60 min", "Over 60 min"]


def plot_arrival_histogram(arrival_hours, other_hours=None):
    """Arrivals per hour together with the capacity lines.

    Args:
        arrival_hours: arrival time of the flights to draw, in hours (5.5 = 05:30).
        other_hours: optional second group, stacked on top of the first one (the flights that are
                     outside the regulation when the first group is the regulated traffic).
    """
    figure = plt.figure(figsize=(8, 8))
    first_group, _ = np.histogram(arrival_hours, bins=HOUR_EDGES)
    n_flights = len(arrival_hours)

    if other_hours is None:
        plt.bar(HOUR_EDGES[:-1], first_group, width=1, color="midnightblue", edgecolor="black", align="edge")
        plt.title("Histogram of arrivals (non-regulated traffic)")
        capacity_line_width = 2
    else:
        second_group, _ = np.histogram(other_hours, bins=HOUR_EDGES)
        n_flights += len(other_hours)
        plt.bar(HOUR_EDGES[:-1], first_group, width=1, color="orange", edgecolor="black", align="edge",
                label="Regulated traffic")
        plt.bar(HOUR_EDGES[:-1], second_group, width=1, bottom=first_group, color="midnightblue",
                edgecolor="black", align="edge", label="Non-regulated traffic")
        plt.title("Histogram of arrivals with assigned slots (CTA)")
        capacity_line_width = 6

    start, end = REGULATION_START_MIN / 60, REGULATION_END_MIN / 60
    plt.plot([0, start], [NOMINAL_CAPACITY] * 2, color="green", linewidth=capacity_line_width,
             label="Nominal capacity")
    plt.plot([start, end], [REDUCED_CAPACITY] * 2, color="red", linewidth=2, label="Reduced capacity")
    plt.plot([end, 24], [NOMINAL_CAPACITY] * 2, color="green", linewidth=capacity_line_width)

    plt.xticks(HOUR_EDGES)
    plt.xlabel("Time (hours), UTC")
    plt.ylabel(f"Arrivals ({n_flights} aircraft)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    return figure


def plot_aggregate_demand(demand, minutes, capacity):
    """Cumulative demand against the cumulative capacity (the output of regulation.simulate_regulation)."""
    figure = plt.figure(figsize=(8, 8))
    hours_of_day = np.arange(1, len(demand) + 1) / 60
    # The demand is smoothed only to draw it; astype(float) because smoothing integers would truncate
    plt.plot(hours_of_day, gaussian_filter1d(demand.astype(float), sigma=2), "k-", label="Aggregate demand")

    reduced = minutes <= REGULATION_END_MIN
    nominal = minutes >= REGULATION_END_MIN
    plt.plot(minutes[reduced] / 60, capacity[reduced], "k:", linewidth=1.25, label="Reduced capacity")
    plt.plot(minutes[nominal] / 60, capacity[nominal], "k--", linewidth=1.25, label="Nominal capacity")

    plt.xticks(HOUR_EDGES)
    plt.xlabel("Time (hours), UTC")
    plt.ylabel("Demand (number of aircraft)")
    plt.title("Aggregate demand")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    return figure


def plot_delay_pies(counts_before, counts_after):
    """Two pie charts of the delay groups (reports.delay_distribution) before and after the cancellations."""
    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    titles = ("Delay before cancelling", "Delay after cancelling and reassigning")
    for axis, counts, title in zip(axes, (counts_before, counts_after), titles):
        axis.pie(counts, labels=DELAY_LABELS, autopct="%1.1f%%", startangle=90)
        axis.set_title(title)
    figure.tight_layout()
    return figure
