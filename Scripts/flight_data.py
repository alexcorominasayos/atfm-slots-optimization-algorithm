"""Load the arrivals at EDDM and build `flights`, the table the whole project works with.

Importing this module reads the CSV once; the other modules import the ready-made `flights`.
"""
import numpy as np
import pandas as pd

from config import (AIRPORT, ARRIVALS_CSV, CRUISE_SPEED_KMH, ECAC_PREFIXES, MINUTES_PER_DAY,
                    REGULATION_END_MIN, REGULATION_START_MIN, ROTATION_DELAY_MIN)
from emissions_fuel_model import compute_co2_ask, compute_fuel_ask
from fleet import category_by_type, seats_by_type
from utils import time_to_minutes

# CSV columns we use: position -> name (column 5 is never needed)
CSV_COLUMNS = {0: "arcid", 1: "aircraft_type", 2: "origin", 3: "destination",
               4: "registration", 6: "etd", 7: "taxi_min", 8: "eta"}


def load_arrivals(csv_path=ARRIVALS_CSV):
    """Read the CSV and return one row per flight landing at AIRPORT, sorted by arrival time.

    Columns of the result:
        arcid, airline, aircraft_type, origin, destination, registration
        etd_min, eta_min       departure and arrival, in minutes since midnight
        taxi_min, flight_min   taxi time, and flight time without taxi
        distance_km            estimated from the flight time and the aircraft category
        seats                  seats of the aircraft type
        international          True when the departure airport is outside ECAC
        co2_g_per_ask, fuel_g_per_ask   emission factors of the flight (g per seat-km)
        rotation_limit         see compute_rotation_limit()
    """
    raw = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False)  # pandas skips the header row
    flights = raw.iloc[:, list(CSV_COLUMNS)].copy()
    flights.columns = list(CSV_COLUMNS.values())
    flights = flights[flights["destination"] == AIRPORT].copy()
    if flights.empty:
        raise ValueError(f"No flights landing at {AIRPORT} in {csv_path}")

    # Times in minutes since midnight; sorting by arrival keeps the order of the original code
    flights["etd_min"] = flights["etd"].apply(time_to_minutes)
    flights["eta_min"] = flights["eta"].apply(time_to_minutes)
    flights["taxi_min"] = flights["taxi_min"].astype(int)
    flights = flights.drop(columns=["etd", "eta"])
    flights = flights.sort_values(["eta_min", "etd_min", "arcid"]).reset_index(drop=True)

    # Flight time: a flight that lands "before" it departed crossed midnight
    gate_to_gate = flights["eta_min"] - flights["etd_min"]
    gate_to_gate = gate_to_gate.where(gate_to_gate >= 0, gate_to_gate + MINUTES_PER_DAY)
    flights["flight_min"] = gate_to_gate - flights["taxi_min"]
    if (flights["flight_min"] <= 0).any():
        wrong = flights.loc[flights["flight_min"] <= 0, "arcid"].tolist()
        raise ValueError(f"Flights with no flight time left after taking away the taxi time: {wrong}")

    # Distance = flight time x typical speed of the aircraft category
    speed_kmh = flights["aircraft_type"].map(category_by_type).map(CRUISE_SPEED_KMH)
    if speed_kmh.isna().any():
        unknown = sorted(flights.loc[speed_kmh.isna(), "aircraft_type"].unique())
        raise ValueError(f"No cruise speed for aircraft types {unknown}: check the fleet CSV "
                         f"(the type must be listed and its category must be one of A-F)")
    # km/h -> m/s (/ 3.6) -> km per minute (* 0.06); same operations as the original code,
    # because dividing by 60 directly changes the rounded distance of a few flights
    flights["distance_km"] = (flights["flight_min"] * (speed_kmh / 3.6 * 0.06)).round().astype(int)

    flights["airline"] = flights["arcid"].str[:3]
    flights["seats"] = flights["aircraft_type"].map(seats_by_type)
    flights["international"] = ~flights["origin"].str[:2].isin(ECAC_PREFIXES)

    # Emission factors depend only on distance and seats, so they are computed once here.
    # tolist() gives plain Python numbers: the emission model rounds exactly as before.
    distances = flights["distance_km"].tolist()
    seats = flights["seats"].tolist()
    flights["co2_g_per_ask"] = [compute_co2_ask(km, n, force=True) for km, n in zip(distances, seats)]
    flights["fuel_g_per_ask"] = [compute_fuel_ask(km, n, force=True) for km, n in zip(distances, seats)]

    flights["rotation_limit"] = compute_rotation_limit(flights)
    return flights


def compute_rotation_limit(flights):
    """Delay (minutes) above which a delay also breaks the rotation of the aircraft.

    The cost model charges an extra multiplier to those delays, because the next flight of the
    same aircraft is hit too. The limit depends on how much we know about the rotation:
      - lands outside the reduced-capacity window: no rotation data, so the general 30 minutes;
      - lands inside the window and the aircraft flies again in it: its turnaround (at least 30);
      - lands inside the window and the aircraft does not fly again: it never breaks a rotation.
    """
    in_window = flights["eta_min"].between(REGULATION_START_MIN, REGULATION_END_MIN)
    window = flights[in_window].sort_values(["registration", "eta_min"])

    # Turnaround = departure of the next flight of the same aircraft - arrival of this one
    next_departure = window.groupby("registration")["etd_min"].shift(-1)
    turnaround = (next_departure - window["eta_min"]).dropna()

    limit = pd.Series(float(ROTATION_DELAY_MIN), index=flights.index)
    limit[window.index] = np.inf
    limit[turnaround.index] = np.maximum(turnaround, ROTATION_DELAY_MIN)
    return limit


flights = load_arrivals()
