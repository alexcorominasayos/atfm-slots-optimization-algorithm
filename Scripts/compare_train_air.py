"""Train against flight for the flights a train could replace: CO2 and door-to-door time.

Replaces the old compare_train_air.py:  python compare_train_air.py
"""
import matplotlib.pyplot as plt
import pandas as pd

from gdp import run_gdp
from flight_data import flights
from regulation import regulation_end_minute
from train import TRAIN_CITIES, substitutable_mask
from utils import minutes_to_hhmm

SHOW_FLIGHT_TABLE = False       # one line per replaceable flight (long)

# Time (hours) that a door-to-door trip needs besides the trip itself
AIRPORT_TIME_BEFORE_H = 105 / 60    # be at the airport 1 h 45 min before departure
AIRPORT_TIME_AFTER_H = 45 / 60      # 45 min from the landing to the destination
STATION_TIME_BEFORE_H = 40 / 60     # be at the station 40 min before departure
STATION_TIME_AFTER_H = 20 / 60      # 20 min from the arrival to the destination

CITY_COLUMNS = ["city", "train_co2_per_h", "air_co2_per_h", "train_hours"]


def compare_trips(schedule):
    """One row per flight that a train could replace, with CO2 (kg per passenger) and door-to-door time (h).

    The delay of each flight is the one it gets in the GDP schedule.
    """
    cities = pd.DataFrame.from_dict(TRAIN_CITIES, orient="index", columns=CITY_COLUMNS)
    trips = schedule[substitutable_mask(schedule)].join(cities, on="origin")

    flight_h = trips["flight_min"] / 60
    delay_h = trips["delay"] / 60
    airport_h = AIRPORT_TIME_BEFORE_H + AIRPORT_TIME_AFTER_H

    trips["air_co2_no_delay"] = trips["air_co2_per_h"] * flight_h
    trips["air_co2_with_delay"] = trips["air_co2_per_h"] * (flight_h + delay_h)
    trips["train_co2"] = trips["train_co2_per_h"] * trips["train_hours"]
    trips["air_d2d_no_delay"] = flight_h + airport_h
    trips["air_d2d_with_delay"] = flight_h + airport_h + delay_h
    trips["train_d2d"] = trips["train_hours"] + STATION_TIME_BEFORE_H + STATION_TIME_AFTER_H
    return trips


def print_summary(trips):
    """Average CO2 and door-to-door time of both options, and the CO2 saved by taking the train."""
    columns = ["air_co2_no_delay", "air_co2_with_delay", "train_co2",
               "air_d2d_no_delay", "air_d2d_with_delay", "train_d2d"]
    average = trips[columns].mean()
    print(f"\nAverages over {len(trips)} flights")
    print(f"  CO2 (kg per passenger): flight {average['air_co2_no_delay']:.1f} without delay, "
          f"{average['air_co2_with_delay']:.1f} with delay, train {average['train_co2']:.1f}")
    print(f"  Door to door (h):       flight {average['air_d2d_no_delay']:.2f} without delay, "
          f"{average['air_d2d_with_delay']:.2f} with delay, train {average['train_d2d']:.2f}")
    for label, column in (("without", "air_co2_no_delay"), ("including", "air_co2_with_delay")):
        saving = 100 * (1 - average["train_co2"] / average[column])
        print(f"  CO2 saved by the train, {label} the delay of the flight: {saving:.1f} %")


def plot_train_vs_air(trips):
    """Emissions (left axis) and door-to-door time (right axis) against the distance, flight against train."""
    trips = trips.sort_values("distance_km")
    km = trips["distance_km"]
    # Same formulas as the original script: per-passenger CO2 divided by the seat-km of the flight
    flight_emissions = trips["air_co2_with_delay"] * 1000 / (km * trips["seats"])
    train_emissions = trips["train_co2"] * 1000 / (km * trips["seats"])
    flight_time = trips["air_d2d_with_delay"] * 3600 / km     # seconds per km
    train_time = trips["train_d2d"] * 3600 / km

    figure, emissions_axis = plt.subplots(figsize=(10, 5))
    emissions_axis.set_xlabel("distance (km)")
    emissions_axis.set_ylabel("gCO₂ / ASK", color="tab:blue")
    emissions_axis.plot(km, flight_emissions, "o-", label="Flight emissions", markerfacecolor="white", color="tab:blue")
    emissions_axis.plot(km, train_emissions, "o--", label="Rail emissions", markerfacecolor="white", color="tab:blue")
    emissions_axis.tick_params(axis="y", labelcolor="tab:blue")
    emissions_axis.set_ylim(0, flight_emissions.max() * 1.25)

    time_axis = emissions_axis.twinx()
    time_axis.set_ylabel("door-to-door travel time (s/km)", color="tab:orange")
    time_axis.plot(km, flight_time, "x-", label="Flight time", color="tab:orange")
    time_axis.plot(km, train_time, "x--", label="Rail time", color="tab:orange")
    time_axis.tick_params(axis="y", labelcolor="tab:orange")
    time_axis.axvline(400, color="gray", linestyle=":", linewidth=1)       # distance of a 2 h 30 rail trip
    time_axis.axvline(600, color="gray", linestyle="-.", linewidth=1)      # distance of a 4 h rail trip

    figure.legend(loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=emissions_axis.transAxes)
    plt.title("Equivalent D2D times between high-speed train and short flights (EDDM) "
              "— Emissions: gCO₂/ASK, D2D: s/km")
    plt.tight_layout()
    return figure


def run():
    regulation_end = regulation_end_minute(flights["eta_min"].to_numpy())
    trips = compare_trips(run_gdp(flights, regulation_end))
    print(f"{len(trips)} flights could be replaced by train")

    if SHOW_FLIGHT_TABLE:
        table = trips.assign(eta=trips["eta_min"].map(minutes_to_hhmm))
        print(table[["arcid", "origin", "city", "eta", "air_co2_no_delay", "air_co2_with_delay", "train_co2",
                     "air_d2d_no_delay", "air_d2d_with_delay", "train_d2d"]].to_string(index=False, float_format="%.2f"))
    print_summary(trips)
    plot_train_vs_air(trips)
    plt.show()


if __name__ == "__main__":
    run()
