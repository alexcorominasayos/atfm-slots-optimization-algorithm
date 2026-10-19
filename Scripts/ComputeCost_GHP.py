import pandas as pd
import numpy as np
from AssignSlotsGDP import airline, id, distance_out, eta, time_out, atyp_out, adep_out
from emissions_fuel_model import compute_co2_ask
from GHP import solve_GHP
from GHP_reduced import solve_GHP_reduced
from EcacAirline import ECAC
from accategory import actype, acseats

def normalize_arcid(arc):
   arc = arc.strip().upper()
   if "_" in arc:
       return arc
   if len(arc) > 3:
       return arc[:3] + "_" + arc[3:]
   return arc

df = pd.read_csv("EDDM_reduced_demand.csv")
df["ARCID"] = df["ARCID"].astype(str).apply(normalize_arcid)

full_arcids = [f"{a}_{i}" for a, i in zip(airline, id)]
df = df[df["ARCID"].isin(full_arcids)]
arcids_red = df["ARCID"].tolist()

def get_seats(ac):
   try:
       return int(float(acseats[actype.index(ac[:6])]))
   except:
       return 150

# Cost in mode = "cost"
def extract_cost(assign, seat_list, dist, keys):
   SLF = 0.82
   conn_frac = 0.4
   group_frac = 0.3
   c_rebook = 30

   total_cost = 0

   for row in assign:
       name, eta_f, slot, delay = row[:4]

       i = keys.index(name)
       seats = seat_list[i]
       pax_real = max(1.0, seats * SLF)

       if adep_out[i][:2] not in ECAC:
           rebook_cost = pax_real * conn_frac * c_rebook
       else:
           rebook_cost = pax_real * group_frac * c_rebook

       total_cost += rebook_cost

   return total_cost

# Emissions with mode = "cost"
def extract_emissions(assign, dist, times, seats, keys):
   total = 0
   air = 0
   ground = 0
   delay_total = 0

   for row in assign:
       name, eta_f, slot, delay = row[:4]
       i = keys.index(name)

       base_dist = dist[i]
       seats_f = seats[i]
       t_f = times[i]

       co2_ask = compute_co2_ask(base_dist, seats_f, force=True)
       emis_base = co2_ask * base_dist * seats_f / 1000

       exempt = (adep_out[i][:2] not in ECAC) or (base_dist > 2000)
       if exempt:
           air_delay = min(delay, 30)
           ground_delay = 0
       else:
           air_delay = 0
           ground_delay = delay

       speed = base_dist / t_f
       d_air = air_delay * speed
       d_ground = ground_delay * speed

       emis_air = co2_ask * d_air * seats_f / 1000
       emis_ground = co2_ask * d_ground * seats_f * 0.33 / 1000

       total += emis_base + emis_air + emis_ground
       air += emis_air
       ground += emis_ground
       delay_total += emis_air + emis_ground

   return total, delay_total, air, ground

# Full GHP mode cost
assign_full, cost_full = solve_GHP("cost")
if assign_full is None:
   raise RuntimeError("Full GHP cost mode failed.")

seats_full = np.array([get_seats(a) for a in atyp_out])
full_keys = [f"{a}_{i}" for a, i in zip(airline, id)]

full_cost = cost_full

full_total_emis, full_delay_emis, full_air, full_ground = extract_emissions(
   assign_full, distance_out, time_out, seats_full, full_keys
)

print("\nFull schedule:")
print(f" Total cost:              {full_cost:,.2f} €")
print(f" Emissions total:         {full_total_emis:.2f} kg CO₂")
print(f"  - Air delay:            {full_air:.2f} kg CO₂")
print(f"  - Ground delay:         {full_ground:.2f} kg CO₂")

## Reduced GHP mode cost
assign_red, cost_red = solve_GHP_reduced("cost", arcids_red)
if assign_red is None:
   raise RuntimeError("Reduced GHP cost mode failed.")

selected_idx = [i for i, k in enumerate(full_keys) if k in arcids_red]

dist_red = np.array([distance_out[i] for i in selected_idx])
time_red = np.array([time_out[i] for i in selected_idx])
seats_red = np.array([get_seats(atyp_out[i]) for i in selected_idx])
reduced_keys = [full_keys[i] for i in selected_idx]

red_cost = cost_red

red_total_emis, red_delay_emis, red_air, red_ground = extract_emissions(
   assign_red, dist_red, time_red, seats_red, reduced_keys
)

print("\nReduced scheduled:")
print(f" Total cost:              {red_cost:,.2f} €")
print(f" Emissions total:         {red_total_emis:.2f} kg CO₂")
print(f"  - Air delay:            {red_air:.2f} kg CO₂")
print(f"  - Ground delay:         {red_ground:.2f} kg CO₂")

print("Savings")
print(f" Cost saved:              {full_cost - red_cost:,.2f} €")
print(f" Emissions saved:         {full_total_emis - red_total_emis:.2f} kg CO₂")