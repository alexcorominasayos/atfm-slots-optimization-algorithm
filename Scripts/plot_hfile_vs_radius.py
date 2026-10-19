"""What does the regulation cost for every filing time and every exemption radius?

Replaces OtherPlotsGDP.py. It runs the GDP once per (filing time, radius) pair and draws three
surfaces: air delay, CO2 of the delay and unrecoverable delay. It takes about two minutes:
    python plot_hfile_vs_radius.py
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, MultipleLocator

from gdp import run_gdp, unrecoverable_delay
from flight_data import flights
from models import delay_emissions_kg
from regulation import regulation_end_minute
from utils import minutes_to_hhmm

FILING_MINUTES = np.arange(0, 301)       # filing time of the regulation: from 00:00 to 05:00, every minute
RADII_KM = np.arange(0, 3001, 50)        # exemption radius: from 0 to 3000 km, every 50 km


def sweep(regulation_end, filing_minutes, radii_km):
    """Run the GDP for every (radius, filing time) pair.

    Returns three matrices with one row per radius and one column per filing time: air delay (min),
    CO2 emitted because of the delay (tonnes) and unrecoverable delay (min). A pair for which the
    GDP cannot place every flight stays as NaN (the original script stopped with an error).
    """
    shape = (len(radii_km), len(filing_minutes))
    air_delay, co2_tonnes, unrecoverable = (np.full(shape, np.nan) for _ in range(3))

    for row, radius in enumerate(radii_km):
        for column, filing in enumerate(filing_minutes):
            try:
                # extension=0: a flight is already airborne if it departs before the filing time itself
                schedule = run_gdp(flights, regulation_end, filing_minute=filing, extension=0, radius_km=radius)
            except ValueError:
                continue
            air_kg, ground_kg = delay_emissions_kg(schedule["air_delay"], schedule["ground_delay"],
                                                   schedule["co2_g_per_ask"], schedule["seats"],
                                                   schedule["distance_km"], schedule["flight_min"])
            air_delay[row, column] = schedule["air_delay"].sum()
            co2_tonnes[row, column] = (air_kg.sum() + ground_kg.sum()) / 1000
            unrecoverable[row, column] = unrecoverable_delay(schedule)
        print(f"Radius {radius:>4} km done")
    return air_delay, co2_tonnes, unrecoverable


def draw_surface(figure, position, filing_minutes, radii_km, values, title, z_label):
    """Draw one 3D surface: filing time (x), radius (y) and the value (z)."""
    axis = figure.add_subplot(position, projection="3d")
    filing_grid, radius_grid = np.meshgrid(filing_minutes, radii_km)
    axis.plot_surface(filing_grid, radius_grid, values, rstride=1, cstride=1, cmap="viridis", edgecolor="none")
    axis.xaxis.set_major_formatter(FuncFormatter(lambda minutes, _position: minutes_to_hhmm(minutes)))
    axis.xaxis.set_major_locator(MultipleLocator(60))
    axis.yaxis.set_major_locator(MultipleLocator(1000))
    axis.set_title(title)
    axis.set_xlabel("Filing time", fontsize=10, rotation=30, labelpad=10)
    axis.set_ylabel("Radius (km)", fontsize=10, rotation=150, labelpad=10)
    axis.set_zlabel(z_label, fontsize=10, rotation=60, labelpad=10)


def plot_surfaces(filing_minutes, radii_km, air_delay, co2_tonnes, unrecoverable):
    """The three surfaces side by side."""
    figure = plt.figure(figsize=(25, 14))
    draw_surface(figure, 131, filing_minutes, radii_km, air_delay, "Air delay", "Air delay (min)")
    draw_surface(figure, 132, filing_minutes, radii_km, co2_tonnes, "CO2 of the delay", "CO2 emissions (tonnes)")
    draw_surface(figure, 133, filing_minutes, radii_km, unrecoverable, "Unrecoverable delay", "Unrecoverable delay (min)")
    return figure


def print_best_air_delay(filing_minutes, radii_km, air_delay):
    """Print the minimum air delay and the (filing time, radius) pairs that reach it."""
    best = np.nanmin(air_delay)
    rows, columns = np.where(air_delay == best)
    print(f"\nMinimum air delay: {best:.0f} min, reached in {len(rows)} combinations. The first ones:")
    for row, column in list(zip(rows, columns))[:10]:
        print(f"  filing time {minutes_to_hhmm(filing_minutes[column])}, radius {radii_km[row]} km")


def run():
    regulation_end = regulation_end_minute(flights["eta_min"].to_numpy())
    air_delay, co2_tonnes, unrecoverable = sweep(regulation_end, FILING_MINUTES, RADII_KM)
    if np.isnan(air_delay).any():
        print(f"\n{int(np.isnan(air_delay).sum())} combinations could not be scheduled and are left empty")
    print_best_air_delay(FILING_MINUTES, RADII_KM, air_delay)
    plot_surfaces(FILING_MINUTES, RADII_KM, air_delay, co2_tonnes, unrecoverable)
    plt.show()


if __name__ == "__main__":
    run()
