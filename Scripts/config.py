"""Project-wide constants and file paths.

Every number that used to be repeated (or hard-coded) in several scripts lives here,
so a change is made in exactly one place.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Files (the Data folder sits next to the Scripts folder)
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
ARRIVALS_CSV = DATA_DIR / "EDDM_10AUG2025.csv"              # every flight of the day
FLEET_CSV = DATA_DIR / "fleet_cat_seat.csv"                 # aircraft type -> category, seats
REDUCED_DEMAND_CSV = DATA_DIR / "EDDM_reduced_demand.csv"   # written by substitute_flights.py

AIRPORT = "EDDM"                # Munich: only the flights landing here are analysed
MINUTES_PER_DAY = 24 * 60

# ---------------------------------------------------------------------------
# Regulation (Ground Delay Program)
# ---------------------------------------------------------------------------
NOMINAL_CAPACITY = 60           # arrivals per hour
REDUCED_CAPACITY = 20           # arrivals per hour while the regulation lasts
REGULATION_START_MIN = 5 * 60   # 05:00
REGULATION_END_MIN = 13 * 60    # 13:00

FILING_MINUTE = 210             # 03:30, when the regulation is filed
FILING_EXTENSION_MIN = 30       # a flight departing before 03:30 + 30 min is already airborne
EXEMPT_RADIUS_KM = 2000         # flights from further away are exempt from ground delay
MAX_AIR_DELAY_MIN = 30          # most delay an exempt flight can absorb (in the air)

# ---------------------------------------------------------------------------
# Aircraft and airports
# ---------------------------------------------------------------------------
# Typical cruise speed (km/h) of each aircraft category; used to turn flight time into distance
CRUISE_SPEED_KMH = {"A": 225, "B": 425, "C": 780, "D": 850, "E": 900, "F": 875}

# First two letters of the airport codes of the ECAC states
ECAC_PREFIXES = (
    "LA", "UD", "LO", "UB", "EB", "LQ", "LB", "LD", "LC", "LK", "EK", "EE", "EF", "LF",
    "UG", "ED", "LG", "LH", "BI", "EI", "LI", "EV", "EY", "EL", "LM", "LN", "EH", "LJ",
    "EN", "EP", "LP", "MD", "LR", "SM", "YU", "LE", "ES", "LS", "TC", "UR", "EG",
)

# ---------------------------------------------------------------------------
# Emissions
# ---------------------------------------------------------------------------
# A minute of delay on the ground counts 33 % of what the same minute in the air emits
GROUND_DELAY_EMISSION_FACTOR = 0.33

# ---------------------------------------------------------------------------
# Delay cost model (EUR)
# ---------------------------------------------------------------------------
LOAD_FACTOR = 0.82                  # share of the seats that are occupied
AIR_DELAY_COST_PER_MIN = 212        # EUR per minute of air delay
GROUND_DELAY_COST_PER_MIN = 166     # EUR per minute of ground delay
ROTATION_MULTIPLIER = 1.97          # extra cost when the delay also breaks the aircraft rotation
ROTATION_DELAY_MIN = 30             # ...and only for delays longer than this

EU261_MIN_DELAY_MIN = 180           # EU261 compensation starts at 3 hours of delay
EU261_CLAIM_FRACTION = 0.3          # share of the passengers that claim it

CONNECTING_FRACTION = 0.4           # share of the passengers with a connection
MISSED_GROUP_FRACTION = 0.3         # share of those that is lost at each threshold below
MISSED_CONNECTION_THRESHOLDS_MIN = (40, 95)   # a new group misses its connection at each one
MISSED_CONNECTION_FACTOR = 0.3      # extra weighting kept from the original model
REBOOKING_COST = 30                 # EUR per rebooked passenger
