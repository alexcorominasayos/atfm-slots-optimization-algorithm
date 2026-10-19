import pandas as pd
from AssignSlotsGDP import airline, id
from GHP import solve_GHP
from GHP_reduced import solve_GHP_reduced

def normalize_arcid(arc):
   if "_" in arc:
       return arc.strip().upper()
   arc = arc.strip().upper()
   if len(arc) > 3:
       return arc[:3] + "_" + arc[3:]
   return arc

# Load reduced CSV
df = pd.read_csv("EDDM_reduced_demand.csv")
df["ARCID"] = df["ARCID"].astype(str).apply(normalize_arcid)

# ARCIDs in GHP
full_arcids = [f"{a}_{i}" for a, i in zip(airline, id)]

mask = df["ARCID"].isin(full_arcids)
missing = df.loc[~mask, "ARCID"].tolist()

if missing:
   print("\nThe following flights do not exist in the full GHP dataset:")
   for m in missing[:200]:
       print("  -", m)
   print(f"(Dropped {len(missing)})")

df = df.loc[mask].reset_index(drop=True)
arcids_red = df["ARCID"].tolist()

# Full schedule GHP
print("GHP for full schedule")

assign_full, cost_full = solve_GHP(mode="delay")

if assign_full is None:
   raise RuntimeError("Full schedule GHP failed.")

delay_full = sum(a[3] for a in assign_full)
mean_full = delay_full / len(assign_full)

print(f"\nFull schedule:")
print(f" Total delay: {delay_full:.1f} min")
print(f" Avg delay:   {mean_full:.2f} min/flight")

# Reduced schedlued GHP
print("\nGHP for reduced schedule")

result = solve_GHP_reduced("delay", arcids_red)

if len(result) == 2:
   assign_red, cost_red = result
   delay_red = sum(a[3] for a in assign_red)

else:
   raise RuntimeError("solve_GHP_reduced returned an unexpected number of values.")

if assign_red is None:
   raise RuntimeError("Reduced schedule GHP failed.")

mean_red = delay_red / len(assign_red)

print(f"\nReduced schedule:")
print(f" Total delay: {delay_red:.1f} min")
print(f" Avg delay:   {mean_red:.2f} min/flight")

print("\nDelay reduction results")

recovered = delay_full - delay_red
percent = 100 * recovered / delay_full

print(f" Delay recovered: {recovered:.1f} min")
print(f" Reduction:       {percent:.2f} %")
print(f"\n Avg delay full:    {mean_full:.2f} min/flight")
print(f" Avg delay reduced: {mean_red:.2f} min/flight")
print(f" Improvement:       {mean_full - mean_red:.2f} min/flight")

reg_end_red = max(a[2] for a in assign_red)
reg_end_h = reg_end_red // 60
reg_end_m = reg_end_red % 60

print(f"\nNew regulation end time (GHP reduced): {reg_end_h:02d}:{reg_end_m:02d}")