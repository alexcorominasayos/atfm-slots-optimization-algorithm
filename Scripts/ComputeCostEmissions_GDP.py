import numpy as np
from AssignSlotsGDP import (
   airline, id, eta, etd, atyp_out,
   distance_out, time_out, adep_out, res
)
from emissions_fuel_model import compute_co2_ask
from EcacAirline import ECAC
from accategory import actype, acseats

def get_seats(ac):
   try:
       return int(float(acseats[actype.index(ac[:6])]))
   except:
       return 150

# Cost del GDP
def compute_cost_GDP(resultado):
   SLF = 0.82
   conn_frac = 0.4
   group_frac = 0.3
   c_rebook = 30

   total_cost = 0

   for row in resultado:
       (
           slot, al, flight_id, etd_f, eta_f, notaff,
           air_delay_flag, ground_delay_flag,
           atyp, dist, t, adep
       ) = row

       seats = get_seats(atyp)
       pax_real = max(1.0, seats * SLF)

       # ECAC dependent rebooking model
       if adep[:2] not in ECAC:
           rebook_cost = pax_real * conn_frac * c_rebook
       else:
           rebook_cost = pax_real * group_frac * c_rebook

       total_cost += rebook_cost

   return total_cost

# Emissions del GDP
def compute_emissions_GDP(resultado):
   total = 0
   delay_total = 0
   air_total = 0
   ground_total = 0

   for row in resultado:
       (
           slot, al, flight_id, etd_f, eta_f, notaff,
           air_delay_flag, ground_delay_flag,
           atyp, dist, t, adep
       ) = row

       seats = get_seats(atyp)

       # Base emissions
       co2_ask = compute_co2_ask(dist, seats, force=True)
       emis_base = co2_ask * dist * seats / 1000

       delay = slot - eta_f
       if delay < 0:
           delay = 0

       # Exempts
       exempt = (adep[:2] not in ECAC) or (dist > 2000)

       if exempt:
           air_delay = min(delay, 30)
           ground_delay = 0
       else:
           air_delay = 0
           ground_delay = delay

       speed = dist / t
       d_air = air_delay * speed
       d_ground = ground_delay * speed

       # Emissions
       emis_air = co2_ask * d_air * seats / 1000
       emis_ground = co2_ask * d_ground * seats * 0.3 / 1000

       total += emis_base + emis_air + emis_ground
       air_total += emis_air
       ground_total += emis_ground
       delay_total += emis_air + emis_ground

   return total, delay_total, air_total, ground_total

print("Cost + emissions (GDP)")

GDP_cost = compute_cost_GDP(res)

GDP_total_emis, GDP_delay_emis, GDP_air_emis, GDP_ground_emis = compute_emissions_GDP(res)

print("\nGDP results:")
print(f" Total cost:             {GDP_cost:,.2f} €")
print(f" Total emissions:        {GDP_total_emis:,.2f} kg CO₂")
print(f" Delay emissions:        {GDP_delay_emis:,.2f} kg CO₂")
print(f"   - Air delay:          {GDP_air_emis:,.2f} kg CO₂")
print(f"   - Ground delay:       {GDP_ground_emis:,.2f} kg CO₂")