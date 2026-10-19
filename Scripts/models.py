"""Cost and emission models, written once and shared by the GDP and the GHP.

A "schedule" is a DataFrame with one row per flight and at least these columns:
air_delay and ground_delay (minutes), distance_km, seats, flight_min,
co2_g_per_ask and fuel_g_per_ask (grams per seat-km), and rotation_limit (minutes).
"""
from config import (AIR_DELAY_COST_PER_MIN, CONNECTING_FRACTION, EU261_CLAIM_FRACTION,
                    EU261_MIN_DELAY_MIN, GROUND_DELAY_COST_PER_MIN, GROUND_DELAY_EMISSION_FACTOR,
                    LOAD_FACTOR, MISSED_CONNECTION_FACTOR, MISSED_CONNECTION_THRESHOLDS_MIN,
                    MISSED_GROUP_FRACTION, REBOOKING_COST, ROTATION_MULTIPLIER)


# ---------------------------------------------------------------------------
# Emissions
# ---------------------------------------------------------------------------
def base_emissions_kg(g_per_ask, seats, distance_km):
    """Emissions (kg) of the flight itself, with no delay: grams per seat-km x seat-km / 1000."""
    return g_per_ask * distance_km * seats / 1000


def delay_emissions_kg(air_delay, ground_delay, g_per_ask, seats, distance_km, flight_min):
    """Extra emissions (kg) caused by the delay. Returns (air, ground).

    A minute of air delay is modelled as one more minute flown at the average speed of the
    flight. A minute of ground delay counts only GROUND_DELAY_EMISSION_FACTOR of that.
    """
    kg_per_minute_flown = g_per_ask * seats * (distance_km / flight_min) / 1000
    return (kg_per_minute_flown * air_delay,
            kg_per_minute_flown * GROUND_DELAY_EMISSION_FACTOR * ground_delay)


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------
def eu261_compensation(distance_km):
    """EU261 compensation (EUR per passenger) for a delay of 3 hours or more."""
    if distance_km <= 1500:
        return 250
    if distance_km <= 3500:
        return 400
    return 600


def delay_cost(air_delay, ground_delay, seats, distance_km, rotation_limit):
    """Cost (EUR) of the delay of one flight. Returns (air_cost, ground_cost).

    Three parts: operating cost, EU261 compensation and passengers who miss a connection.
    The last two are split between air and ground in proportion to the minutes of each.
    """
    total_delay = air_delay + ground_delay
    if total_delay <= 0:
        return 0.0, 0.0
    passengers = max(1.0, seats * LOAD_FACTOR)

    # 1. Operating cost, higher when the delay also breaks the rotation of the aircraft
    multiplier = ROTATION_MULTIPLIER if total_delay > rotation_limit else 1.0
    operating_air = multiplier * ((AIR_DELAY_COST_PER_MIN / passengers) * air_delay)
    operating_ground = multiplier * ((GROUND_DELAY_COST_PER_MIN / passengers) * ground_delay)

    # 2. EU261 compensation: only from 3 hours of delay, and only a share of passengers claims it
    compensation = 0.0
    if total_delay >= EU261_MIN_DELAY_MIN:
        compensation = eu261_compensation(distance_km) * passengers * EU261_CLAIM_FRACTION

    # 3. Missed connections: a new group of connecting passengers is lost at each threshold
    connecting = passengers * CONNECTING_FRACTION
    missed_connections = 0.0
    for threshold in MISSED_CONNECTION_THRESHOLDS_MIN:
        if total_delay > threshold:
            missed_connections += (connecting * MISSED_GROUP_FRACTION) * REBOOKING_COST * MISSED_CONNECTION_FACTOR

    shared_cost = compensation + missed_connections
    air_share = air_delay / total_delay
    ground_share = ground_delay / total_delay
    return operating_air + air_share * shared_cost, operating_ground + ground_share * shared_cost


def rebooking_cost(seats, international):
    """Baseline cost (EUR) of rebooking the passengers of a flight, whatever the delay.

    Used to compare two schedules with no delay at all (see run_ghp.py).
    """
    passengers = max(1.0, seats * LOAD_FACTOR)
    share = CONNECTING_FRACTION if international else MISSED_GROUP_FRACTION
    return passengers * share * REBOOKING_COST


# ---------------------------------------------------------------------------
# Whole schedule
# ---------------------------------------------------------------------------
def evaluate_schedule(schedule):
    """Total emissions (kg of CO2 and of fuel) and delay cost (EUR) of a schedule. Returns a dict."""
    results = {}
    for name, factor_column in (("co2", "co2_g_per_ask"), ("fuel", "fuel_g_per_ask")):
        base = base_emissions_kg(schedule[factor_column], schedule["seats"], schedule["distance_km"]).sum()
        air, ground = delay_emissions_kg(schedule["air_delay"], schedule["ground_delay"],
                                         schedule[factor_column], schedule["seats"],
                                         schedule["distance_km"], schedule["flight_min"])
        results[f"{name}_base"] = base
        results[f"{name}_air"] = air.sum()
        results[f"{name}_ground"] = ground.sum()
        results[f"{name}_delay"] = air.sum() + ground.sum()
        results[f"{name}_total"] = base + air.sum() + ground.sum()

    costs = [delay_cost(*flight) for flight in zip(schedule["air_delay"], schedule["ground_delay"],
                                                   schedule["seats"], schedule["distance_km"],
                                                   schedule["rotation_limit"])]
    results["cost_air"] = sum(air for air, _ in costs)
    results["cost_ground"] = sum(ground for _, ground in costs)
    results["cost_total"] = results["cost_air"] + results["cost_ground"]
    return results
