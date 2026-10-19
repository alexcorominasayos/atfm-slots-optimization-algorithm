import pandas as pd
import numpy as np
from AssignSlotsGDP import airline, id, distance_out, eta, time_out, atyp_out, adep_out, etd_out
from emissions_fuel_model import compute_co2_ask
from EcacAirline import ECAC
from GHP import solve_GHP
from GHP_reduced import solve_GHP_reduced
from accategory import actype, acseats

def normalize_arcid(arc):
   arc = str(arc).strip().upper()
   if "_" in arc:
       return arc
   if len(arc) > 3:
       return arc[:3] + "_" + arc[3:]
   return arc

def get_seats(ac):
   try:
       return int(float(acseats[actype.index(ac[:6])]))
   except:
       return 150

# Load reduced demand
df = pd.read_csv("EDDM_reduced_demand.csv")
df["ARCID"] = df["ARCID"].astype(str).apply(normalize_arcid)

full_arcids = [f"{a}_{i}" for a, i in zip(airline, id)]
mask = df["ARCID"].isin(full_arcids)
df = df.loc[mask].reset_index(drop=True)
arcids_red = df["ARCID"].tolist()

# Full GHP mode = "emissions"
print("\nRunning full GHP in emissions mode")
assign_full, cost_full_obj = solve_GHP(mode="emissions")

if assign_full is None:
   raise RuntimeError("Full schedule GHP (emissions) failed.")

# Emissions + cost extractor
def extract_all(assign, dist, times, seats, adeps, full_keys):
   total_emis = 0
   delay_emis = 0
   air_emis = 0
   ground_emis = 0

   total_cost = 0
   total_cost_air = 0
   total_cost_ground = 0

   SLF = 0.82
   conn_frac = 0.4
   group_frac = 0.3
   c_rebook = 30
   max_air_delay = 30

   for row in assign:

       if len(row) == 4:
           name, eta_f, slot, delay = row
       else:
           name, eta_f, slot, delay, _ = row

       idx = full_keys.index(name)

       base_dist = dist[idx]
       fl_time = times[idx]
       seats_i = seats[idx]
       adep = adeps[idx]

       # Emissions
       co2_base = compute_co2_ask(base_dist, seats_i, force=True)
       emis_base = co2_base * base_dist * seats_i / 1000

       exempt = (adep[:2] not in ECAC) or (base_dist > 2000)

       if exempt:
           air_delay = min(delay, max_air_delay)
           ground_delay = 0
       else:
           air_delay = 0
           ground_delay = delay

       speed = base_dist / fl_time
       d_air = air_delay * speed
       d_ground = ground_delay * speed

       emis_air = co2_base * d_air * seats_i / 1000
       emis_ground = co2_base * d_ground * seats_i * 0.33 / 1000

       total_emis += emis_base + emis_air + emis_ground
       delay_emis += emis_air + emis_ground
       air_emis += emis_air
       ground_emis += emis_ground

       # cost
       pax_real = seats_i * SLF
       total_d = air_delay + ground_delay

       # Rotation multiplier
       from main import ARCID, RM_affected, turnaround_times
       turnaround_dict = dict(zip(RM_affected, [t[3] for t in turnaround_times]))

       mult = 1.0
       tat = turnaround_dict.get(ARCID[idx], None)

       if total_d > 30:
           if ARCID[idx] in RM_affected:
               if tat is not None and total_d > tat:
                   mult = 1.97
           else:
               mult = 1.97

       # Operative cost
       cost_air_oper = mult * ((212.0 / max(pax_real, 1)) * air_delay)
       cost_ground_oper = mult * ((166.0 / max(pax_real, 1)) * ground_delay)

       # EU261
       if total_d >= 180:
           if base_dist <= 1500:
               comp = 250
           elif base_dist <= 3500:
               comp = 400
           else:
               comp = 600
           comp *= pax_real * 0.3
       else:
           comp = 0

       # Lost connections
       n_conn = pax_real * conn_frac
       lost = 0
       if total_d > 40:
           lost += n_conn * group_frac * c_rebook * 0.3
       if total_d > 95:
           lost += n_conn * group_frac * c_rebook * 0.3

       # Split proportionally
       if total_d > 0:
           p_air = air_delay / total_d
       else:
           p_air = 0

       cost_air_total = cost_air_oper + p_air * (comp + lost)
       cost_ground_total = cost_ground_oper + (1 - p_air) * (comp + lost)

       total_cost += cost_air_total + cost_ground_total
       total_cost_air += cost_air_total
       total_cost_ground += cost_ground_total

   return (total_emis, delay_emis, air_emis, ground_emis,
           total_cost, total_cost_air, total_cost_ground)

seats_full = np.array([get_seats(a) for a in atyp_out])
full_keys = [f"{a}_{i}" for a, i in zip(airline, id)]

(full_total, full_delay, full_air, full_ground,
full_cost, full_cost_air, full_cost_ground) = extract_all(
   assign_full, distance_out, time_out, seats_full, adep_out, full_keys
)

print("\nFull schedule:")
print(f"  Total emissions:        {full_total:.2f} kg CO₂")
print(f"  Delay emissions:        {full_delay:.2f} kg CO₂")
print(f"  Air delay emissions:    {full_air:.2f} kg CO₂")
print(f"  Ground delay emissions: {full_ground:.2f} kg CO₂")
print(f"\n  Total cost:             {full_cost:,.2f} €")
print(f"  Air-delay cost:         {full_cost_air:,.2f} €")
print(f"  Ground-delay cost:      {full_cost_ground:,.2f} €")

# Reduced GHP mode emissions
print("\nRunning reduced GHP in emissions mode")
assign_red, cost_red_obj = solve_GHP_reduced("emissions", arcids_red)

selected_idx = [i for i, k in enumerate(full_arcids) if k in arcids_red]

dist_red = np.array([distance_out[i] for i in selected_idx])
time_red = np.array([time_out[i] for i in selected_idx])
seats_red = np.array([get_seats(atyp_out[i]) for i in selected_idx])
adep_red = [adep_out[i] for i in selected_idx]
reduced_keys = [full_arcids[i] for i in selected_idx]

(red_total, red_delay, red_air, red_ground,
red_cost, red_cost_air, red_cost_ground) = extract_all(
   assign_red, dist_red, time_red, seats_red, adep_red, reduced_keys
)

print("\nReduced schedule:")
print(f"  Total emissions:        {red_total:.2f} kg CO₂")
print(f"  Delay emissions:        {red_delay:.2f} kg CO₂")
print(f"  Air delay emissions:    {red_air:.2f} kg CO₂")
print(f"  Ground delay emissions: {red_ground:.2f} kg CO₂")
print(f"\n  Total cost:             {red_cost:,.2f} €")
print(f"  Air-delay cost:         {red_cost_air:,.2f} €")
print(f"  Ground-delay cost:      {red_cost_ground:,.2f} €")

print("\nSavings")
print(f"Total emissions saved:      {full_total - red_total:.2f} kg CO₂")
print(f"Delay emissions saved:      {full_delay - red_delay:.2f} kg CO₂")
print(f"Air delay saved:            {full_air - red_air:.2f} kg CO₂")
print(f"Ground delay saved:         {full_ground - red_ground:.2f} kg CO₂")

print(f"\nTotal cost saved:           {full_cost - red_cost:,.2f} €")
print(f"Air-delay cost saved:       {full_cost_air - red_cost_air:,.2f} €")
print(f"Ground-delay cost saved:    {full_cost_ground - red_cost_ground:,.2f} €")