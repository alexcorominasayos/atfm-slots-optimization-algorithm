"""Example of how to use the emission model: fuel burned and CO2 emitted by a list of flights.

Only the names of the variables were changed from the original file; the calculations are the same
(the seats are now read from the fleet dictionary instead of searching the list of aircraft types).
Run it with:  python example_fuel_use.py
"""
from emissions_fuel_model import (
    compute_fuel_ask,
    compute_co2_ask,
    compute_nox_ask,
    compute_co_ask,
    compute_sox_ask,
    compute_water_vapour_ask
)
from fleet import seats_by_type
from flight_data import flights

PART_NAME = "WP1"

def print_emissions(aircraft_types,distances_km,flight_minutes,part_name):
    """Print the fuel burned and the CO2 emitted by the flights, and return both lists (kg per flight).

    Args:
        aircraft_types: aircraft type of every flight (it must be in the fleet table).
        distances_km: distance of every flight.
        flight_minutes: flight time of every flight, without taxi time.
        part_name: label shown in the title.
    """
    fuel_per_minute = [] # in kg/min
    co2_per_minute = [] # in kg/min
    fuel = [] # in kg
    co2 = [] # in kg
    cases = []

    i = 0
    while i < len(aircraft_types):
        cases.append({"distance_km": int(distances_km[i]), "available_seats": seats_by_type[aircraft_types[i]], "time_min": int(flight_minutes[i])})
        i = i+1

    """print("=== Aircraft Emissions per ASK ===")"""
    for case in cases:
        distance = case["distance_km"]
        seats = case["available_seats"]
        minutes = case["time_min"]
        force = case.get("force", True)

        try:
            emissions_per_ask = {
                "Distance (km)": distance,
                "Seats": seats,
                "Force Mode": force,
                "Fuel (g/ASK)": compute_fuel_ask(distance, seats, force),
                "CO2 (g/ASK)": compute_co2_ask(distance, seats, force),
                "SOX (g/ASK)": compute_sox_ask(distance, seats, force),
                "Water vapour (g/ASK)": compute_water_vapour_ask(distance, seats, force),
                "NOx (g/ASK)": compute_nox_ask(distance, seats, force),
                "CO (g/ASK)": compute_co_ask(distance, seats, force),
            }
            """print(emissions_per_ask)
            print("-" * 50)"""
            fuel_per_minute.append(round((compute_fuel_ask(distance, seats, force)*seats*distance)/(minutes*1000),2))
            co2_per_minute.append(round((compute_co2_ask(distance, seats, force)*seats*distance)/(minutes*1000),2))
            fuel.append(round((compute_fuel_ask(distance, seats, force)*seats*distance)/(1000),2))
            co2.append(round((compute_co2_ask(distance, seats, force)*seats*distance)/(1000),2))
        except ValueError as error:
            """print(f"Error for case {case}: {error}")
            print("-" * 50)"""
            fuel_per_minute.append("---")
            co2_per_minute.append("---")
            fuel.append("---")
            co2.append("---")

    """print(fuel_per_minute)
    print(co2_per_minute)"""
    print("\nEmissions "+part_name+":")
    print("Fuel burned:",round(sum(fuel)),"kg")
    print("CO2 emitted:",round(sum(co2)),"kg")
    return fuel, co2

if __name__ == "__main__":
    print_emissions(flights["aircraft_type"].tolist(), flights["distance_km"].tolist(),
                    flights["flight_min"].tolist(), PART_NAME)
