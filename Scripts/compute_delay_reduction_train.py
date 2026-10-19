import numpy as np
from main import ADEP, ADES, ARCID, ETAmin
from graph import StartRedCapacity, EndRedCapacity
from AssignSlotsGDP import res as resultado

# Vols substituibles
train_substitutable = {
   "EDDB",
   "LOWW",
   "LSZH",
   "LFSB",
   "LOWL",
   "LKPR",
   "LKPZ",
   "EDDF",
   "EDDS",
   "EDDL",
   "LOWS",
   "LFST"
}

# Delay de AssignSlotsGDP
assigned_by_arcid = {}
all_delays = []

# resultado format:
# (slot, airline3, id, etd, eta, notaff, airdel, grounddel, atyp, distance, time, adep)
for row in resultado:
   slot_time = row[0]
   airline3 = row[1]
   id_rest = row[2]
   eta_val = row[4]

   arcid = f"{airline3}{id_rest}"
   delay = max(0, slot_time - eta_val)

   assigned_by_arcid[arcid] = delay
   all_delays.append(delay)

total_delay_current = float(np.sum(all_delays))

# trobar vols substituibles
Hstart = StartRedCapacity * 60
Hend = EndRedCapacity * 60

substituted_indices = [
   i for i, dep in enumerate(ADEP)
   if dep[:4] in train_substitutable
      and ADES[i] == "EDDM"
      and Hstart <= ETAmin[i] <= Hend
]

substituted_flights = []
remaining_flights = []

for adep, ades, arcid, eta in zip(ADEP, ADES, ARCID, ETAmin):

   if ades != "EDDM":
       remaining_flights.append((arcid, adep, ades, eta))
       continue

   if Hstart <= eta <= Hend and adep[:4] in train_substitutable:
       substituted_flights.append((arcid, adep, ades, eta))
   else:
       remaining_flights.append((arcid, adep, ades, eta))

print(f"Found {len(substituted_flights)} substitutable flights (tuple based).")

# Delay recuperat
removed_delay = 0.0

for i in substituted_indices:
   arc = ARCID[i]
   if arc in assigned_by_arcid:
       removed_delay += assigned_by_arcid[arc]

remaining_delay = total_delay_current - removed_delay
reduction_percent = 100 * removed_delay / total_delay_current if total_delay_current > 0 else 0

print(f"\nTotal current delay (GDP):            {total_delay_current:.1f} min")
print(f"Substitutable flights identified:     {len(substituted_indices)}")
print(f"Total delay removed:                  {removed_delay:.1f} min")
print(f"Remaining delay:                      {remaining_delay:.1f} min")
print(f"Relative reduction:                   {reduction_percent:.2f}%\n")