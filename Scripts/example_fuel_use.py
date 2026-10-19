from accategory import acseats, actype
from main import flightdistance, ATYP, flighttimeNOtt
from pprint import pprint
from emissions_fuel_model import (
    compute_fuel_ask,
    compute_co2_ask,
    compute_nox_ask,
    compute_co_ask,
    compute_sox_ask,
    compute_water_vapour_ask
)

Part = "WP1"

def PrintEmissions(ATYP,flightdistance,flighttimeNOtt,Part):
    fuelpertime = [] # in kg/min
    co2pertime = [] # in kg/min
    fuel = [] # in kg
    co2 = [] # in kg
    test_cases = []

    i = 0
    while i < len(ATYP):
        index = actype.index(ATYP[i])
        test_cases.append({"distance_km": int(flightdistance[i]), "available_seats": int(acseats[index]), "time_min": int(flighttimeNOtt[i])})
        i = i+1

    """print("=== Aircraft Emissions per ASK ===")"""
    for case in test_cases:
        distance = case["distance_km"]
        seats = case["available_seats"]
        time = case["time_min"]
        force = case.get("force", True)

        try:
            emissions = {
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
            """print(emissions)
            print("-" * 50)"""
            fuelpertime.append(round((compute_fuel_ask(distance, seats, force)*seats*distance)/(time*1000),2))
            co2pertime.append(round((compute_co2_ask(distance, seats, force)*seats*distance)/(time*1000),2))
            fuel.append(round((compute_fuel_ask(distance, seats, force)*seats*distance)/(1000),2))
            co2.append(round((compute_co2_ask(distance, seats, force)*seats*distance)/(1000),2))
        except ValueError as e:
            """print(f"Error for case {case}: {e}")
            print("-" * 50)"""
            fuelpertime.append("---")
            co2pertime.append("---")
            fuel.append("---")
            co2.append("---")

    """print(fuelpertime)
    print(co2pertime)"""
    print("\nEmissions "+Part+":")
    print("Fuel burned:",round(sum(fuel)),"kg")
    print("CO2 emitted:",round(sum(co2)),"kg")
    return fuel, co2