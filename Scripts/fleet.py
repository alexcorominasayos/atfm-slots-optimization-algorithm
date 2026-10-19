"""Fleet table (Data/fleet_cat_seat.csv): aircraft type -> ICAO category and number of seats."""
import pandas as pd

from config import FLEET_CSV


def load_fleet(csv_path=FLEET_CSV):
    """Read the fleet CSV and return two dictionaries: category by aircraft type, and seats by aircraft type.

    Columns 1, 2 and 3 of the CSV hold the type, the category and the seats (column 0 is not used).
    If a type appears twice, the first row wins.
    """
    table = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    category_by_type = {}
    seats_by_type = {}
    for aircraft_type, category, seats in zip(table.iloc[:, 1], table.iloc[:, 2], table.iloc[:, 3]):
        category_by_type.setdefault(aircraft_type, category)
        seats_by_type.setdefault(aircraft_type, int(float(seats)))
    return category_by_type, seats_by_type


category_by_type, seats_by_type = load_fleet()
