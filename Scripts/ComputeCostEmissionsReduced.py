import pandas as pd
import numpy as np
from AssignSlotsGDP import airline, id, distance_out, eta, time_out, atyp_out, adep_out, etd_out
from accategory import actype, acseats
from emissions_fuel_model import compute_co2_ask
from EcacAirline import ECAC

def normalize_arcid(arc):
   if "_" in arc:
       return arc.strip().upper()
   arc = arc.strip().upper()
   if len(arc) > 3:
       return arc[:3] + "_" + arc[3:]
   return arc

df = pd.read_csv("EDDM_reduced_demand.csv")
df["ARCID"] = df["ARCID"].astype(str).apply(normalize_arcid)

# GHP list
full_arcids = [f"{a}_{i}" for a, i in zip(airline, id)]

# només vols de GHP
mask = df["ARCID"].isin(full_arcids)
df = df.loc[mask].reset_index(drop=True)

arcids_red = df["ARCID"].tolist()

indices_red = [i for i, key in enumerate(full_arcids) if key in arcids_red]

if len(indices_red) == 0:
   raise RuntimeError("No reduced flights matched the GHP lists.")

# funcions de GHP
def get_seats_for_aircraft(aircraft_type: str) -> int:
   try:
       idx = actype.index(aircraft_type)
       return int(float(acseats[idx]))
   except ValueError:
       return 150

def is_international(adep: str) -> bool:
   return adep is not None and adep[:2] not in ECAC

# arrays de reduced flights
dist_red = np.array([distance_out[i] for i in indices_red])
eta_red = np.array([eta[i] for i in indices_red])
time_red = np.array([time_out[i] for i in indices_red])
adep_red = [adep_out[i] for i in indices_red]
atyp_red = [atyp_out[i][:6] for i in indices_red]
etd_red = [etd_out[i] for i in indices_red]

Seats_red = np.array([get_seats_for_aircraft(a) for a in atyp_red])
International_red = np.array([is_international(a) for a in adep_red])
InRadius_red = np.array([d <= 2000 for d in dist_red])

# Same constants que en GHP
SLF = 0.82
conn_frac = 0.4
group_frac = 0.3
c_rebook = 30

# same formulas
def compute_cost_and_emissions(dist, seats, adep_arr):
   total_cost = 0
   total_emis = 0

   for i in range(len(dist)):
       distance = dist[i]
       seats_f = seats[i]

       # Emissions
       co2_ask_base = compute_co2_ask(distance, seats_f, force=True)
       emis = co2_ask_base * distance * seats_f / 1000
       total_emis += emis

       # cost (no delay costs — pure cost of operating flight)
       pax_real = max(1.0, seats_f * SLF)

       # Rebooking cost
       if is_international(adep_arr[i]):
           rebook_cost = pax_real * conn_frac * c_rebook
       else:
           rebook_cost = pax_real * group_frac * c_rebook

       total_cost += rebook_cost

   return total_cost, total_emis

# Full GHP cost i emissions
Seats_full = np.array([get_seats_for_aircraft(a[:6]) for a in atyp_out])

total_cost_full, total_emis_full = compute_cost_and_emissions(
   dist=np.array(distance_out),
   seats=Seats_full,
   adep_arr=adep_out
)

# reduced cost i emissions
total_cost_red, total_emis_red = compute_cost_and_emissions(
   dist=dist_red,
   seats=Seats_red,
   adep_arr=adep_red
)

# Savings
cost_savings = total_cost_full - total_cost_red
emis_savings = total_emis_full - total_emis_red

print("\nGHP cost and emissions")
print(f"Full schedule cost:      {total_cost_full:,.2f} €")
print(f"Reduced schedule cost:   {total_cost_red:,.2f} €")
print(f"Cost saved:            {cost_savings:,.2f} €")

print("\nFull schedule emissions:   {0:.2f} kg CO₂".format(total_emis_full))
print("Reduced schedule emissions: {0:.2f} kg CO₂".format(total_emis_red))
print("Emissions saved:         {0:.2f} kg CO₂".format(emis_savings))