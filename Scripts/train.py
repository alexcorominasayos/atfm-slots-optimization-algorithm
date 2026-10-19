"""Flights that a high-speed train could replace, and the reduced demand that is left without them.

Replaces the logic of SubstitutedFlights.py. The old code had three different lists of airports
with a train connection (one had LSZW, another LKPZ, another neither); TRAIN_CITIES is now the only one.
"""
from pathlib import Path

import pandas as pd

from config import REDUCED_DEMAND_CSV, REGULATION_END_MIN, REGULATION_START_MIN

# Airport -> (city, train CO2 per passenger-hour, air CO2 per passenger-hour, train trip in hours).
# LKPR is the Prague airport, used for Pilsen because it is the closest one.
TRAIN_CITIES = {
    "EDDB": ("Berlin", 19.9, 117.4, 4.07),
    "LOWW": ("Vienna", 13.5, 136.8, 4.02),
    "LSZH": ("Zurich", 8.0, 131.1, 3.53),
    "LSZW": ("Winterthur", 8.0, 131.8, 3.10),
    "LFSB": ("Basel", 8.1, 126.3, 4.82),
    "LOWL": ("Linz", 10.8, 98.2, 2.77),
    "LKPR": ("Pilsen", 40.5, 122.0, 4.05),
    "EDDF": ("Frankfurt", 11.4, 117.8, 3.20),
    "EDDS": ("Stuttgart", 6.6, 104.3, 1.93),
    "EDDL": ("Dusseldorf", 18.7, 120.5, 4.30),
    "LOWS": ("Salzburg", 3.7, 101.4, 1.37),
    "LFST": ("Strasbourg", 11.2, 117.9, 3.77),
}


def substitutable_mask(flights):
    """True for the flights that arrive during the regulation from an airport with a train connection."""
    in_regulation = flights["eta_min"].between(REGULATION_START_MIN, REGULATION_END_MIN)
    return in_regulation & flights["origin"].isin(list(TRAIN_CITIES))


def save_reduced_demand(flights, path=REDUCED_DEMAND_CSV):
    """Save the flights that stay (the ones the train does not replace), in the CSV format used so far."""
    remaining = flights.loc[~substitutable_mask(flights), ["arcid", "origin", "destination", "eta_min"]]
    remaining.columns = ["ARCID", "ADEP", "ADES", "ETAmin"]
    remaining.to_csv(path, index=False)
    return remaining


def load_reduced_arcids(path=REDUCED_DEMAND_CSV):
    """ARCIDs of the flights that stay after the substitution, as a set.

    Old files wrote 'DLH_4AB' where the arrivals file says 'DLH4AB', so the underscore is dropped.
    """
    arcids = pd.read_csv(path, dtype=str)["ARCID"]
    return set(arcids.str.strip().str.upper().str.replace("_", "", regex=False))
