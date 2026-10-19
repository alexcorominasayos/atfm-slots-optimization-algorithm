import numpy as np
import matplotlib.pyplot as plt
from main import ADEP, ADES, ARCID, ETAmin, flightdistance, flighttimeNOtt, ATYP
from slots import DelayFlight
from graph import StartRedCapacity, EndRedCapacity
from accategory import actype, acseats

# (ciutat, CO2 en tren per passatger per hora, CO2 en aire per passatger per hora, durada viatge tren en hores)
train_cities = {
   "EDDB": ("Berlin", 19.9, 117.4, 4.07),
   "LOWW": ("Vienna", 13.5, 136.8, 4.02),
   "LSZH": ("Zurich", 8.0, 131.1, 3.53),
   "LSZW": ("Winterthur", 8.0, 131.8, 3.10),
   "LFSB": ("Basel", 8.1, 126.3, 4.82),
   "LOWL": ("Linz", 10.8, 98.2, 2.77),
   "LKPR": ("Pilsen", 40.5, 122.0, 4.05),  # Praga per proximitat
   "EDDF": ("Frankfurt", 11.4, 117.8, 3.20),
   "EDDS": ("Stuttgart", 6.6, 104.3, 1.93),
   "EDDL": ("Dusseldorf", 18.7, 120.5, 4.30),
   "LOWS": ("Salzburg", 3.7, 101.4, 1.37),
   "LFST": ("Strasbourg", 11.2, 117.9, 3.77)
}

# Contants per arriba a l'estació/aeroport
AIRPORT_BUFFER_BEFORE = 105 / 60.0  # 1h45
AIRPORT_BUFFER_AFTER = 45 / 60.0  # 45 min
TRAIN_BUFFER_BEFORE = 40 / 60.0  # 40 min
TRAIN_BUFFER_AFTER = 20 / 60.0  # 20 min

ADEP_fixed = list(ADEP)

# Troba vols substituibles
Hstart_min = int(StartRedCapacity * 60)
Hend_min = int(EndRedCapacity * 60)

substituted_indices = [
   i for i, dep in enumerate(ADEP_fixed)
   if dep[:4] in train_cities
      and ADES[i] == "EDDM"
      and (Hstart_min <= ETAmin[i] <= Hend_min)
]

print(f"\n🚄 Found {len(substituted_indices)} substitutable flights.")

if not substituted_indices:
   print("No substitutable flights found in regulation window.")

# Valors de CO2 i D2D
total_air_co2_no_delay = []
total_air_co2_with_delay = []
total_train_co2 = []
total_air_d2d_no_delay = []
total_air_d2d_with_delay = []
total_train_d2d = []
distances_km = []
seat_array = []
per_flight_print_records = []  # per mantindre l'ordre

for i in substituted_indices:
   dep_code = ADEP_fixed[i][:4]  # ICAO
   if dep_code not in train_cities:
       continue

   city, train_co2_h, air_co2_h, train_time_h = train_cities[dep_code]

   try:
       air_time_h = float(flighttimeNOtt[i]) / 60.0
   except Exception:
       air_time_h = np.nan

   try:
       air_delay_min = DelayFlight[i] if i < len(DelayFlight) else 0
       air_delay_h = max(0.0, float(air_delay_min)) / 60.0
   except Exception:
       air_delay_h = 0.0

   air_co2_no_delay = air_co2_h * air_time_h if np.isfinite(air_time_h) else np.nan
   air_co2_with_delay = air_co2_h * (air_time_h + air_delay_h) if np.isfinite(air_time_h) else np.nan
   train_co2_total = train_co2_h * train_time_h

   air_d2d_no_delay = (air_time_h + AIRPORT_BUFFER_BEFORE + AIRPORT_BUFFER_AFTER) if np.isfinite(
       air_time_h) else np.nan
   air_d2d_with_delay = (air_time_h + AIRPORT_BUFFER_BEFORE + AIRPORT_BUFFER_AFTER + air_delay_h) if np.isfinite(
       air_time_h) else np.nan
   train_d2d = train_time_h + TRAIN_BUFFER_BEFORE + TRAIN_BUFFER_AFTER

   try:
       dist_km = float(flightdistance[i])
   except Exception:
       dist_km = np.nan

   try:
       idx_at = actype.index(ATYP[i])
       seats = int(float(acseats[idx_at]))
   except Exception:
       seats = 150

   total_air_co2_no_delay.append(air_co2_no_delay)
   total_air_co2_with_delay.append(air_co2_with_delay)
   total_train_co2.append(train_co2_total)
   total_air_d2d_no_delay.append(air_d2d_no_delay)
   total_air_d2d_with_delay.append(air_d2d_with_delay)
   total_train_d2d.append(train_d2d)
   distances_km.append(dist_km)
   seat_array.append(seats)

   per_flight_print_records.append({
       "dep": dep_code,
       "city": city,
       "air_co2_no": air_co2_no_delay,
       "air_co2_with": air_co2_with_delay,
       "train_co2": train_co2_total,
       "air_d2d_no": air_d2d_no_delay,
       "air_d2d_with": air_d2d_with_delay,
       "train_d2d": train_d2d,
       "dist": dist_km,
       "seats": seats,
       "eta": ETAmin[i],
       "arcid": ARCID[i]
   })

# Resultats de cada vol
for rec in per_flight_print_records:
   hours = int(rec["eta"]) // 60
   mins = int(rec["eta"]) % 60
   print(f"\n✈️ {rec['dep']} → EDDM ({rec['city']})  ETA {hours:02d}:{mins:02d}")
   print(f"  Air CO₂ (no delay): {np.nanmean([rec['air_co2_no']]):.1f} kg/pax")
   print(f"  Air CO₂ (with delay): {np.nanmean([rec['air_co2_with']]):.1f} kg/pax")
   print(f"  Train CO₂:          {np.nanmean([rec['train_co2']]):.1f} kg/pax")
   print(f"  Air D2D (no delay): {rec['air_d2d_no']:.2f} h")
   print(f"  Air D2D (with delay): {rec['air_d2d_with']:.2f} h")
   print(f"  Train D2D:          {rec['train_d2d']:.2f} h")

# Average dels resultats anteriors
air_co2_no_arr = np.array(total_air_co2_no_delay, dtype=float)
air_co2_with_arr = np.array(total_air_co2_with_delay, dtype=float)
train_co2_arr = np.array(total_train_co2, dtype=float)
air_d2d_no_arr = np.array(total_air_d2d_no_delay, dtype=float)
air_d2d_with_arr = np.array(total_air_d2d_with_delay, dtype=float)
train_d2d_arr = np.array(total_train_d2d, dtype=float)
distances_km = np.array(distances_km, dtype=float)
seat_array = np.array(seat_array, dtype=float)

print("\nAverages (substituted flights):")
print(f"  Air CO₂ (no delay): {np.nanmean(air_co2_no_arr):.1f} kg/pax")
print(f"  Air CO₂ (with delay): {np.nanmean(air_co2_with_arr):.1f} kg/pax")
print(f"  Train CO₂: {np.nanmean(train_co2_arr):.1f} kg/pax")
print(f"  Air D2D (no delay): {np.nanmean(air_d2d_no_arr):.2f} h")
print(f"  Air D2D (with delay): {np.nanmean(air_d2d_with_arr):.2f} h")
print(f"  Train D2D: {np.nanmean(train_d2d_arr):.2f} h")

# Reducció (mean per evitar dividir entre 0
if np.nanmean(air_co2_with_arr) > 0:
   reduction_pct = 100.0 * (1.0 - np.nanmean(train_co2_arr) / np.nanmean(air_co2_with_arr))
   reduction_nd = 100.0 * (1.0 - np.nanmean(train_co2_arr)/ np.nanmean(air_co2_no_arr))
else:
   reduction_pct = np.nan
   reduction_nd = np.nan
print(f"\nAverage CO₂ reduction (without including delay): {reduction_nd:.1f}% if replaced by train")
print(f"Average CO₂ reduction (including delay): {reduction_pct:.1f}% if replaced by train")

# Emissions: gCO2/ASK = (kg CO2/pax * 1000) / (distance_km * seats)
# D2D: s / km
with np.errstate(divide='ignore', invalid='ignore'):
   flight_emissions = (air_co2_with_arr * 1000.0) / (distances_km * seat_array)  # gCO2/ASK
   train_emissions = (train_co2_arr * 1000.0) / (distances_km * seat_array)  # gCO2/ASK

   # D2D
   flight_time_skm = (air_d2d_with_arr * 3600.0) / distances_km
   train_time_skm = (train_d2d_arr * 3600.0) / distances_km

# Eliminar valors que donin errors
valid_mask = np.isfinite(distances_km) & (distances_km > 0) & np.isfinite(flight_emissions)
if not np.any(valid_mask):
   raise SystemExit("No valid distances or emissions to plot.")

distances_km = distances_km[valid_mask]
flight_emissions = flight_emissions[valid_mask]
train_emissions = train_emissions[valid_mask]
flight_time_skm = flight_time_skm[valid_mask]
train_time_skm = train_time_skm[valid_mask]

# Ordenar per distancia
idx_sort = np.argsort(distances_km)
distances_km = distances_km[idx_sort]
flight_emissions = flight_emissions[idx_sort]
train_emissions = train_emissions[idx_sort]
flight_time_skm = flight_time_skm[idx_sort]
train_time_skm = train_time_skm[idx_sort]

fig, ax1 = plt.subplots(figsize=(10, 5))

# Eix de l'esquerra — CO2 emissions
ax1.set_xlabel("distance (km)")
ax1.set_ylabel("gCO₂ / ASK", color="tab:blue")
ax1.plot(distances_km, flight_emissions, "o-", label="Flight emissions", markerfacecolor='white', color="tab:blue")
ax1.plot(distances_km, train_emissions, "o--", label="Rail emissions", markerfacecolor='white', color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.set_ylim(0, np.nanmax(flight_emissions) * 1.25)

# Eix de ka dreta — D2D (s/km)
ax2 = ax1.twinx()
ax2.set_ylabel("door-to-door travel time (s/km)", color="tab:orange")
ax2.plot(distances_km, flight_time_skm, "x-", label="Flight time", color="tab:orange")
ax2.plot(distances_km, train_time_skm, "x--", label="Rail time", color="tab:orange")
ax2.tick_params(axis="y", labelcolor="tab:orange")

# Línees a 2h30 i 4h rail
ax2.axvline(400, color="gray", linestyle=":", linewidth=1)
ax2.axvline(600, color="gray", linestyle="-.", linewidth=1)

# llegenda
fig.legend(loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
plt.title("Equivalent D2D times between high-speed train and short flights (EDDM) — Emissions: gCO₂/ASK, D2D: s/km")
plt.tight_layout()
plt.show()