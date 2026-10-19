from main import arrivalfile, Hfile, Extension
from graph import StartRedCapacity, EndRedCapacity, LastDelay
from slots import ComputeSlots
import pandas as pd
import numpy as np

# CSV original
(ETAmin_full, ETDmin_full, ARCID_full, ATYP_full, ADEP_full, ADES_full,
RM_full, ARF_full, ETD_full, TT_full, ETA_full,
flighttime_full, flighttimeNOtt_full, flightdistance_full,
Affected_full, GroundDelay_full, AirDelay_full) = \
   arrivalfile("EDDM_10AUG2025.csv", Hfile, Extension)

(sloti_full, slotf_full, airline_full, id_full, etd_full, eta_full,
DelayFlight_full, indexcopy_full, notaffected_full,
airdelay_full, grounddelay_full, atyp_full,
distance_full, time_full, taxi_full, adep_full) = ComputeSlots(
   StartRedCapacity, EndRedCapacity, LastDelay,
   ETDmin_full, ETAmin_full, ARCID_full,
   Affected_full, AirDelay_full, GroundDelay_full,
   ATYP_full, flightdistance_full, flighttimeNOtt_full,
   TT_full, ADEP_full
)

# Print del delay
total_delay_full = float(np.sum(DelayFlight_full))
avg_delay_full = float(np.mean(DelayFlight_full))
print("\nOriginal schedule:")
print(f"  Total delay: {total_delay_full:.1f} min")
print(f"  Average delay: {avg_delay_full:.2f} min/flight")

# CSV reduït
reduced_df = pd.read_csv("EDDM_reduced_demand.csv")

# Mandatory fields
ETAmin_red = reduced_df["ETAmin"].tolist()
ARCID_red = reduced_df["ARCID"].tolist()
ADEP_red = reduced_df["ADEP"].tolist()
ADES_red = reduced_df["ADES"].tolist()

ETDmin_red = []
ATYP_red = []
TT_red = []
flighttimeNOtt_red = []
flightdistance_red = []
Affected_red = []
AirDelay_red = []
GroundDelay_red = []

for arc in ARCID_red:
   i = ARCID_full.index(arc)   # índex original

   ETDmin_red.append(ETDmin_full[i])
   ATYP_red.append(ATYP_full[i])
   TT_red.append(TT_full[i])
   flighttimeNOtt_red.append(flighttimeNOtt_full[i])
   flightdistance_red.append(flightdistance_full[i])
   Affected_red.append(Affected_full[i])
   AirDelay_red.append(AirDelay_full[i])
   GroundDelay_red.append(GroundDelay_full[i])

# slots per demanda reduida
(sloti_red, slotf_red, airline_red, id_red, etd_red, eta_red,
DelayFlight_red, indexcopy_red, notaffected_red,
airdelay_red, grounddelay_red, atyp_red,
distance_red, time_red, taxi_red, adep_red) = ComputeSlots(

   StartRedCapacity, EndRedCapacity, LastDelay,

   ETDmin_red, ETAmin_red, ARCID_red,
   Affected_red, AirDelay_red, GroundDelay_red,

   ATYP_red, flightdistance_red, flighttimeNOtt_red,
   TT_red, ADEP_red
)

total_delay_red = float(np.sum(DelayFlight_red))
avg_delay_red = float(np.mean(DelayFlight_red))

print("\nReduced schedule (after substituting train flights):")
print(f"  Total delay: {total_delay_red:.1f} min")
print(f"  Average delay: {avg_delay_red:.2f} min/flight")

# delay recuperat
recovered_delay = total_delay_full - total_delay_red
reduction_percent = 100 * (recovered_delay / total_delay_full)

print("\nDelay reduction after removing train-replaceable flights:")
print(f"  Recovered delay: {recovered_delay:.1f} min")
print(f"  Reduction: {reduction_percent:.2f}%")