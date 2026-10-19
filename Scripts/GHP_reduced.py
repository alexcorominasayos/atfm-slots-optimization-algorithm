import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from AssignSlotsGDP import (sloti, airline, id, eta, distance_out, etd_out, adep_out, time_out, atyp_out)
from accategory import actype, acseats
from emissions_fuel_model import compute_co2_ask
from main import ARCID, RM_affected, turnaround_times
from EcacAirline import ECAC

# GHP functions
def get_seats_for_aircraft(aircraft_type: str) -> int:
   try:
       idx = actype.index(aircraft_type)
       return int(float(acseats[idx]))
   except ValueError:
       return 150

def is_international(adep: str) -> bool:
   return adep is not None and adep[:2] not in ECAC

# Same as GHP but with reduced demand
def solve_GHP_reduced(mode, arcids_reduced):

   # Build full ARCIDs from AssignSlotsGDP
   full_keys = [f"{airline[i]}_{id[i]}" for i in range(len(eta))]

   # Select indices belonging to the reduced demand
   selected_idx = [i for i, key in enumerate(full_keys) if key in arcids_reduced]

   if not selected_idx:
       print("ERROR: No matching flights in reduced schedule!")
       return None, 0

   # Extract reduced dataset
   eta_sel = np.array([eta[i] for i in selected_idx])
   dist_sel = np.array([distance_out[i] for i in selected_idx])
   etd_sel = np.array([etd_out[i] for i in selected_idx])
   adep_sel = [adep_out[i] for i in selected_idx]
   time_sel = np.array([time_out[i] for i in selected_idx])
   atyp_sel = [atyp_out[i] for i in selected_idx]
   arcid_sel = [ARCID[i] for i in selected_idx]

   flights = [full_keys[i] for i in selected_idx]

   n_flights = len(selected_idx)

   # Slots exactly same as full GHP
   slots_min = np.array(sloti)
   n_slots = len(slots_min)

   Seats = np.array([get_seats_for_aircraft(a[:6]) for a in atyp_sel])

   International = np.array([is_international(dep) for dep in adep_sel])
   InRadius = np.array([d <= 2000 for d in dist_sel])
   AlreadyFlying = np.array([etd_sel[i] < (210 + 30) for i in range(n_flights)])

   turnaround_dict = dict(zip(RM_affected, [t[3] for t in turnaround_times]))

   # igual que GHP
   n_vars = n_flights * n_slots
   lb = np.zeros(n_vars)
   ub = np.ones(n_vars)

   # Each flight 1 slot
   Aeq = np.zeros((n_flights, n_vars))
   for i in range(n_flights):
       Aeq[i, i*n_slots:(i+1)*n_slots] = 1
   beq = np.ones(n_flights)

   # Each slot 1 flight
   A = np.zeros((n_slots, n_vars))
   for j in range(n_slots):
       for i in range(n_flights):
           A[j, i*n_slots + j] = 1
   b = np.ones(n_slots)

   # No slot before ETA
   for i in range(n_flights):
       for j in range(n_slots):
           if slots_min[j] < eta_sel[i]:
               ub[i*n_slots + j] = 0

   # Máximo air delay constarints para exempt flights
   max_air_delay = 30
   for i in range(n_flights):
       exempt = International[i] or (not InRadius[i]) or AlreadyFlying[i]
       if exempt:
           for j in range(n_slots):
               delay_real = slots_min[j] - eta_sel[i]
               if delay_real > max_air_delay:
                   ub[i*n_slots + j] = 0

   # Cost vector
   C = np.zeros(n_vars)

   for i in range(n_flights):
       flight_min = time_sel[i]
       base_dist = dist_sel[i]

       for j in range(n_slots):
           delay = max(slots_min[j] - eta_sel[i], 0)

           exempt = International[i] or (not InRadius[i]) or AlreadyFlying[i]

           if exempt:
               air_delay = min(delay, max_air_delay)
               ground_delay = 0
           else:
               air_delay = 0
               ground_delay = delay

           if mode == "delay":
               cost = air_delay + ground_delay

           elif mode == "emissions":
               co2_ask_base = compute_co2_ask(base_dist, Seats[i], force=True)
               speed = base_dist / flight_min
               distance_air = air_delay * speed
               distance_ground = ground_delay * speed

               emis_air = co2_ask_base * distance_air * Seats[i] / 1000
               emis_ground = co2_ask_base * distance_ground * Seats[i] * 0.33 / 1000

               cost = emis_air + emis_ground

           elif mode == "cost":
               SLF = 0.82
               pax_real = max(1.0, Seats[i] * SLF)
               total_d = air_delay + ground_delay

               # rotation penalty
               mult = 1.0
               tat = turnaround_dict.get(arcid_sel[i], None)

               if total_d > 30:
                   if arcid_sel[i] in RM_affected:
                       if tat is not None and total_d > tat:
                           mult = 1.97
                   else:
                       mult = 1.97

               cost_air = mult * ((212.0 / pax_real) * air_delay)
               cost_ground = mult * ((166.0 / pax_real) * ground_delay)

               # EU261 compensation
               if total_d >= 180:
                   if base_dist <= 1500:
                       comp = 250
                   elif base_dist <= 3500:
                       comp = 400
                   else:
                       comp = 600
                   comp *= pax_real
               else:
                   comp = 0

               # missed connections
               conn_frac = 0.4
               group_frac = 0.3
               c_rebook = 30
               lost = 0
               n_conn = pax_real * conn_frac

               if total_d > 40:
                   lost += n_conn * group_frac * c_rebook
               if total_d > 95:
                   lost += n_conn * group_frac * c_rebook

               # split compensations
               if total_d > 0:
                   p_air = air_delay / total_d
               else:
                   p_air = 0


               cost = cost_air + cost_ground + p_air * (comp + lost)

           else:
               raise ValueError("Unknown mode for GHP_reduced")

           C[i*n_slots + j] = cost

   constraints = [
       LinearConstraint(Aeq, beq, beq),
       LinearConstraint(A, -np.inf, b)
   ]
   bounds = Bounds(lb, ub)
   integrality = np.ones(n_vars, dtype=bool)

   result = milp(c=C, constraints=constraints, bounds=bounds, integrality=integrality)

   if not result.success:
       print("MILP failed:", result.message)
       return None, 0

   X = result.x.reshape((n_flights, n_slots))
   TotalCost = result.fun

   # Assignment list
   assignment = []

   for i in range(n_flights):
       j = np.argmax(X[i])
       assigned = slots_min[j]
       delay = max(assigned - eta_sel[i], 0)

       exempt = International[i] or (not InRadius[i]) or AlreadyFlying[i]
       if exempt:
           delay = min(delay, max_air_delay)

       assignment.append((flights[i], eta_sel[i], assigned, delay))

   return assignment, TotalCost