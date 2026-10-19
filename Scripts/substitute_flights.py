"""Find the flights that a high-speed train could replace and save the demand that remains.

Replaces SubstitutedFlights.py. Run it before the scripts that compare the full schedule with the
reduced one (it writes Data/EDDM_reduced_demand.csv):  python substitute_flights.py
"""
from config import REDUCED_DEMAND_CSV, REGULATION_END_MIN, REGULATION_START_MIN
from flight_data import flights
from train import save_reduced_demand, substitutable_mask
from utils import minutes_to_hhmm


def run():
    replaced = flights[substitutable_mask(flights)]
    in_regulation = flights["eta_min"].between(REGULATION_START_MIN, REGULATION_END_MIN).sum()

    print("Flights replaced by the train (arriving during the regulation):")
    for flight in replaced.itertuples():
        print(f"  {flight.arcid} | {flight.origin} -> {flight.destination} | ETA {minutes_to_hhmm(flight.eta_min)}")

    print(f"\nFlights replaced: {len(replaced)}")
    print(f"Flights that remain in the reduced schedule: {len(flights) - len(replaced)}")
    print(f"Share of the flights of the regulation replaced: {100 * len(replaced) / in_regulation:.2f} % "
          f"({len(replaced)}/{in_regulation})")

    save_reduced_demand(flights)
    print(f"\nReduced demand saved in {REDUCED_DEMAND_CSV}")


if __name__ == "__main__":
    run()
