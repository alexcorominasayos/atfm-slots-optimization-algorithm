from graph import StartRedCapacity, EndRedCapacity
from main import ADEP, ADES, ARCID, ETAmin
import pandas as pd

Hstart = StartRedCapacity * 60  # 05:00
Hend = EndRedCapacity * 60  # 13:00

# Ciutats amb possible substitució (codis ICAO)
train_substitutable = ["EDDB",  # Berlin
                      "LOWW",  # Vienna
                      "LSZH",  # Zurich
                      "LFSB",  # Basel
                      "LOWL",  # Linz
                      "LKPR",  # Pilsen (Aeroport Praga per proximitat)
                      "EDDF",  # Frankfurt
                      "LSZW",  # Winterthur
                      "EDDS",  # Stuttgart
                      "EDDL",  # Dusseldorf
                      "LOWS",  # Salzburg
                      "LFST"  # Strasbourg
                      ]

substituted_flights = []
remaining_flights = []
flights_in_regulation = 0

for adep, ades, arcid, eta in zip(ADEP, ADES, ARCID, ETAmin):
   if ades != "EDDM":
       remaining_flights.append((arcid, adep, ades, eta))
       continue

   if Hstart <= eta <= Hend:
       flights_in_regulation += 1

   # Mira si es poden substituir
   if Hstart <= eta <= Hend and adep in train_substitutable:
       substituted_flights.append((arcid, adep, ades, eta))
   else:
       remaining_flights.append((arcid, adep, ades, eta))

print("🚄 Flights substituted by rail (within regulation interval):")

for flight in substituted_flights:
   hora = int(flight[3]) // 60
   minuto = int(flight[3]) % 60
   print(f" {flight[0]} | {flight[1]} → {flight[2]} | ETA {hora:02d}:{minuto:02d}")

print(f"\nTotal substituted flights: {len(substituted_flights)}")
print(f"Remaining flights in reduced schedule: {len(remaining_flights)}")

if flights_in_regulation > 0:
   percentage = 100 * len(substituted_flights) / flights_in_regulation
   print(f"Percentage of flights substituted inside regulation window: "
         f"{percentage:.2f}%  ({len(substituted_flights)}/{flights_in_regulation})")
else:
   print("No flights inside regulation window.")

# Guardar vols per torna a aplicar el GDP i GHP
df_remaining = pd.DataFrame(remaining_flights, columns=["ARCID", "ADEP", "ADES", "ETAmin"])
df_remaining.to_csv("EDDM_reduced_demand.csv", index=False)