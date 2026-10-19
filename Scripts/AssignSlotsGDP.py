import numpy as np
from graph import StartRedCapacity, EndRedCapacity, LastDelay, NomCapacity, RedCapacity
from accategory import acseats, actype
from slots import ComputeSlots
from CancelledFlightsGDP import PrintNewSlotsGDP
from main import ETDmin, ETAmin, ARCID, ATYP, flightdistance, flighttimeNOtt, TT, ADEP, RM_affected, turnaround_times
from Plotfunction import PlotHistogram, PlotDelayPie
from AircraftStatus import NotAffected, AirDelay, GroundDelay
from UnrecoverableDelay import UnrecoverableDelay
from emissions_fuel_model import compute_co2_ask, compute_fuel_ask

(sloti, slotf, airline, id, etd, eta, DelayFlight, indexcopy, notaffected, airdelay,
grounddelay, atyp, distance, time, taxi, adep) = ComputeSlots(StartRedCapacity, EndRedCapacity, LastDelay, ETDmin,
                                                            ETAmin, ARCID, NotAffected,
                                                            AirDelay, GroundDelay, ATYP, flightdistance,
                                                            flighttimeNOtt, TT, ADEP)

def ComputeSlotsGDP(sloti, slotf, airline, id, etd, eta, DelayFlight, notaffected, airdelay, grounddelay, atyp,
                 distance, time, adep):
 # Lista para guardar la asignación final
 asignacion = [None] * len(sloti)
 sloti_disponibles = sloti.copy()
 slotf_disponibles = slotf.copy()

 # Asignar primero aviones con preferencia
 for i, pref in enumerate(airdelay):
     if pref:
         # Buscar el slot más cercano al minuto deseado
         difs = [(s - eta[i]) for s in sloti_disponibles]
         min_positivo = None
         indexslot = None
         for j, x in enumerate(difs):
             if x >= 0 and (min_positivo is None or x < min_positivo):
                 min_positivo = x
                 indexslot = j
         if indexslot is None:
             # Tomar el slot con menor |diferencia|
             difs_abs = [abs(x) for x in difs if x >= 0]
             indexslot = difs_abs.index(min(difs_abs))
         asignacion[i] = sloti_disponibles.pop(indexslot)

 # Asignar aviones restantes
 for i, pref in enumerate(airdelay):
     if not pref:
         asignacion[i] = sloti_disponibles.pop(0)  # toma el primer slot disponible

 # Imprimir los resultados ordenados por slot
 resultado = list(zip(asignacion, airline, id, etd, eta, notaffected, airdelay, grounddelay, atyp, distance, time, adep))

 resultado.sort()  # ordena por el primer elemento de la tupla (slot)
 etd_out = [item[3] for item in resultado]  # ETD
 eta_out = [item[4] for item in resultado]  # ETA
 atyp_out = [item[8] for item in resultado] # ATYP
 distance_out = [item[9] for item in resultado]  #
 time_out = [item[10] for item in resultado]
 adep_out = [item[11] for item in resultado]  # Adep

 return adep_out, etd_out, eta_out, atyp_out, distance_out, time_out, resultado, asignacion

def PrintSlotsGDP(resultado):
 print("\n🛫 Todos los slots :")
 sloti_vector = []
 slotf_vector = []
 airline_vector = []
 id_vector = []
 etd_vector = []
 eta_vector = []
 DelayFlight_vector = []
 notaffected_vector = []
 airdelay_vector = []
 grounddelay_vector = []
 distance_vector = []
 time_vector = []
 atyp_vector = []
 sumad = 0
 maxad = 0
 countad = 0
 sumgd = 0
 maxgd = 0
 countgd = 0
 delayad = []
 delaygd = []
 cancelled = []
 index = 0

 for slot, avion1, avion2, expecteddep, expectedarr, notaffected, airdelay, grounddelay, type, dist, t, adep in resultado:

     # inicio slot
     horasloti = int(slot) // 60
     minutosloti = int(slot) % 60
     # final slot
     if int(slot) < (EndRedCapacity * 60):
         horaslotf = (int(slot) + 2) // 60
         minutoslotf = (int(slot) + 2) % 60
         if (expectedarr >= slot) and ((expectedarr <= slot + 2)):
             delay = 0
         else:
             delay = slot - expectedarr
     else:
         horaslotf = (int(slot) + 1) // 60
         minutoslotf = (int(slot) + 1) % 60
         if (expectedarr >= slot) and ((expectedarr <= slot + 1)):
             delay = 0
         else:
             delay = slot - expectedarr

     if delay > 120 and avion1 == "DLH":
         cancelled.append(index)

     horaetd = int(expecteddep) // 60
     minutoetd = int(expecteddep) % 60
     horaeta = int(expectedarr) // 60
     minutoeta = int(expectedarr) % 60

     notaff = notaffected
     adelay = airdelay
     if adelay:
         sumad = sumad + delay
         if delay > maxad:
             maxad = delay
         delayad.append(delay)
         countad = countad + 1
     gdelay = grounddelay
     if gdelay:
         sumgd = sumgd + delay
         if delay > maxgd:
             maxgd = delay
         delaygd.append(delay)
         countgd = countgd + 1

     sloti_vector.append(horasloti * 60 + minutosloti)
     slotf_vector.append(horaslotf * 60 + minutoslotf)
     airline_vector.append(avion1)
     id_vector.append(avion2)
     etd_vector.append(horaetd * 60 + minutoetd)
     eta_vector.append(horaeta * 60 + minutoeta)
     DelayFlight_vector.append(delay)
     notaffected_vector.append(notaff)
     airdelay_vector.append(adelay)
     grounddelay_vector.append(gdelay)
     distance_vector.append(dist)
     time_vector.append(t)
     atyp_vector.append(type)

     print(f"{horasloti:02d}:{minutosloti:02d}-{horaslotf:02d}:{minutoslotf:02d} | {avion1:3} | {avion2:4} | "
           f"{horaeta:02d}:{minutoeta:02d} | {delay:3} | {notaff:5} | {adelay:5} | {gdelay:5}")

     index = index + 1

 return (sloti_vector, slotf_vector, airline_vector, id_vector, etd_vector, eta_vector,
         DelayFlight_vector, notaffected_vector, airdelay_vector, grounddelay_vector,
         atyp_vector, distance_vector, time_vector, sumad, maxad, countad, delayad, sumgd, maxgd, countgd, delaygd,
         cancelled)

adep_out, etd_out, eta_out, atyp_out, distance_out, time_out, res, asignacion = ComputeSlotsGDP(
 sloti, slotf, airline, id, etd, eta, DelayFlight, notaffected, airdelay, grounddelay,
 atyp, distance, time, adep)

(inislot, endslot, airline, id, etd, eta, DelayFlight, notaffected, airdelay, grounddelay, atyp, distance, time, sumad,
maxad, countad,
delayad, sumgd, maxgd, countgd, delaygd, cancelled) = PrintSlotsGDP(res)

sumud = UnrecoverableDelay(DelayFlight, StartRedCapacity, etd, grounddelay)

# -------------------------------------------------------------------------------
# Calculo de emisiones totales del GDP (misma logica que el GHP)

def Calc_Emissions(atyp_out, distance_out, DelayFlight, notaffected, airdelay, grounddelay, time_out):

   total_emis_gdp = 0.0
   total_cons_gdp = 0.0
   emis_gdp_por_vuelo = []
   cons_gdp_por_vuelo = []

   def get_seats_for_aircraft(aircraft_type: str) -> int:
       idx = actype.index(aircraft_type)
       return int(float(acseats[idx]))

   Seats = np.array([get_seats_for_aircraft(atyp_out[i][:6]) for i in range(len(distance_out))])

   n_gdp_flights = len(distance_out)

   for i in range(n_gdp_flights):

       delay_real = DelayFlight[i]

       if notaffected[i]:
           air_delay = 0
           ground_delay = 0

       elif airdelay[i]:
           air_delay = delay_real
           ground_delay = 0

       elif grounddelay[i]:
           air_delay = 0
           ground_delay = delay_real

       #  Emisiones base del vuelo
       base_distance = distance_out[i]
       co2_ask_base = compute_co2_ask(base_distance, Seats[i], force=True)
       fuel_ask_base = compute_fuel_ask(base_distance, Seats[i], force=True)
       emis_base = co2_ask_base * base_distance * Seats[i] / 1000.0
       cons_base = fuel_ask_base * base_distance * Seats[i] / 1000.0

       # Emisiones del delay
       speed = base_distance / time_out[i]

       distance_air_delay = air_delay * speed
       distance_ground_delay = ground_delay * speed

       emis_air = co2_ask_base * distance_air_delay * Seats[i] / 1000.0
       cons_air = fuel_ask_base * distance_air_delay * Seats[i] / 1000.0
       emis_ground = co2_ask_base * distance_ground_delay * Seats[i] * 0.33 / 1000.0
       cons_ground = fuel_ask_base * distance_ground_delay * Seats[i] * 0.33 / 1000.0

       # Total emisiones del vuelo
       emis_total_vuelo = emis_base + emis_air + emis_ground
       cons_total_vuelo = cons_base + cons_air + cons_ground
       total_emis_gdp += emis_total_vuelo
       total_cons_gdp += cons_total_vuelo

       emis_gdp_por_vuelo.append(
           (f"{airline[i]}_{id[i]}", emis_base, emis_air, emis_ground, emis_total_vuelo)
       )
       cons_gdp_por_vuelo.append(
           (f"{airline[i]}_{id[i]}", cons_base, cons_air, cons_ground, cons_total_vuelo)
       )

   emis_base_total = sum(x[1] for x in emis_gdp_por_vuelo)
   emis_air_total = sum(x[2] for x in emis_gdp_por_vuelo)
   emis_ground_total = sum(x[3] for x in emis_gdp_por_vuelo)
   cons_base_total = sum(x[1] for x in cons_gdp_por_vuelo)
   cons_air_total = sum(x[2] for x in cons_gdp_por_vuelo)
   cons_ground_total = sum(x[3] for x in cons_gdp_por_vuelo)

   print(f"\nEmisiones totales GDP:",round(total_emis_gdp),"kg CO2 and",round(total_cons_gdp),"kg fuel")
   print(f"Emisiones base GDP:",round(emis_base_total),"kg CO2 and",round(cons_base_total),"kg fuel")
   print(f"Emisiones air delay GDP:",round(emis_air_total),"kg CO2 and",round(cons_air_total),"kg fuel")
   print(f"Emisiones ground delay GDP:",round(emis_ground_total),"kg CO2 and",round(cons_ground_total),"kg fuel")
   print(f"Emisiones delay total GDP:",round(emis_ground_total+emis_air_total),"kg CO2 and",round(cons_ground_total+cons_air_total),"kg fuel")

   return (emis_ground_total+emis_air_total)

co2_emis = Calc_Emissions(atyp_out, distance_out, DelayFlight, notaffected, airdelay, grounddelay, time_out)

# ------------------------------------------------------------------------------
def Calc_Cost(atyp_out, distance_out, DelayFlight, notaffected, airdelay, grounddelay, time_out):

   total_cost_gdp = 0.0

   # Necesario para multiplicadores de rotación
   turnaround_dict = dict(zip(RM_affected, [t[3] for t in turnaround_times]))

   SLF = 0.82
   conn_frac = 0.4
   group_frac = 0.3
   c_rebook = 30
   total_cost_real = 0
   cost_por_vuelo = []

   # Seats por avión
   def get_seats_for_aircraft(aircraft_type: str) -> int:

       try:
           idx = actype.index(aircraft_type)
           return int(float(acseats[idx]))
       except ValueError:
           return 150  # default

   Seats = np.array([get_seats_for_aircraft(atyp_out[i][:6]) for i in range(len(distance_out))])

   n_gdp_flights = len(distance_out)

   for i in range(n_gdp_flights):

       delay_real = DelayFlight[i]

       # Clasificación tipo delay GDP
       if notaffected[i]:
           air_delay = 0
           ground_delay = 0

       elif airdelay[i]:
           air_delay = delay_real
           ground_delay = 0

       elif grounddelay[i]:
           air_delay = 0
           ground_delay = delay_real

       total_delay_local = air_delay + ground_delay
       pax_real = max(1.0, Seats[i] * SLF)

       # Multiplicador rotación (igual que GHP)
       mult = 1.0
       tat = turnaround_dict.get(ARCID[i], None)

       if total_delay_local > 30:
           if ARCID[i] in RM_affected:
               if tat is not None and total_delay_local > tat:
                   mult = 1.97
           else:
               mult = 1.97

       # Coste operativo
       cost_air_oper = mult * ((212.0 / pax_real) * air_delay)
       cost_ground_oper = mult * ((166.0 / pax_real) * ground_delay)

       # Compensación EU261
       comp_EU261 = 0.0
       Dist = distance_out[i]

       if total_delay_local >= 180:
           if Dist <= 1500:
               comp_amount = 250
           elif Dist <= 3500:
               comp_amount = 400
           else:
               comp_amount = 600

           comp_EU261 = comp_amount * pax_real * 0.3

       # Lost connections
       lost_conn = 0.0
       n_conn = pax_real * conn_frac

       if total_delay_local > 40:
           lost_conn += (n_conn * group_frac) * c_rebook * 0.3
       if total_delay_local > 95:
           lost_conn += (n_conn * group_frac) * c_rebook * 0.3

       # Coste total del vuelo
       if total_delay_local > 0:
           p_air = air_delay / total_delay_local
           p_ground = ground_delay / total_delay_local
       else:
           p_air = p_ground = 0

       cost_air_total = cost_air_oper + p_air * (comp_EU261 + lost_conn)
       cost_ground_total = cost_ground_oper + p_ground * (comp_EU261 + lost_conn)

       # Coste total vuelo (consistente con la suma)
       cost_flight = cost_air_total + cost_ground_total
       total_cost_real += cost_flight

       # Guardar desglose: (vuelo, coste_air, coste_ground, EU261, lost_conn, total)
       cost_por_vuelo.append((
           f"{airline[i]}_{id[i]}",
           cost_air_total,
           cost_ground_total,
           comp_EU261,
           lost_conn,
           cost_flight
       ))
       total_cost_air = sum(c[1] for c in cost_por_vuelo)
       total_cost_ground = sum(c[2] for c in cost_por_vuelo)

   print("\nCoste total GDP:", round(total_cost_real), "€")
   print(f"    Coste total air delay:     {total_cost_air:.2f} €")
   print(f"    Coste total ground delay:  {total_cost_ground:.2f} €")
   return total_cost_gdp

cost_gdp = Calc_Cost(atyp_out, distance_out, DelayFlight, notaffected, airdelay, grounddelay, time_out)

# -------------------------------------------------------------------------------

answer = input("\nPrint other interesting data? ")
if answer == "yes":
 affectedregulation = 0
 for gd in grounddelay:
     if gd:
         affectedregulation += 1
 print(f"\nTotal de slots: {len(inislot)}")
 print("Aircrafts affected:", affectedregulation)
 print("Total delay:", sum(DelayFlight), "min")
 AvgDelay = sum(DelayFlight) / len(inislot)
 print("Average delay per aircraft:", round(AvgDelay, 2), "min")
 std_delay = np.std(DelayFlight)
 print("Standard deviation of the delay:", round(std_delay, 2), "min")
 rsd_delay = (std_delay / AvgDelay) * 100
 print("Relative standard deviation of the delay:", round(rsd_delay, 2), "%")
 print("Unrecoverable delay:", sumud)
 print("\nTotal air delay:", sumad)
 print("Maximum air delay:", maxad)
 print("Average air delay:", sumad / countad)
 print("Standard deviation of air delay:", round(np.std(delayad), 2), "min")
 print("Relative standard deviation of air delay:", (np.std(delayad) / (sumad / countad)) * 100)
 print("\nTotal ground delay:", sumgd)
 print("Maximum ground delay:", maxgd)
 print("Average ground delay:", sumgd / countgd)
 print("Standard deviation of ground delay:", round(np.std(delaygd), 2), "min")
 print("Relative standard deviation of ground delay:", (np.std(delaygd) / (sumgd / countgd)) * 100)
 countnotdelayed_b = sum(1 for delay in DelayFlight if int(delay) == 0)
 print("\nAircrafts not delayed:", countnotdelayed_b, "aircrafts")
 countdelayed30_b = sum(1 for delay in DelayFlight if int(delay) <= 30 and int(delay) > 0)
 print("Aircrafts delayed between 1 and 30 min:", countdelayed30_b, "aircrafts")
 countdelayed60_b = sum(1 for delay in DelayFlight if int(delay) <= 60 and int(delay) > 30)
 print("Aircrafts delayed between 31 and 60 min:", countdelayed60_b, "aircrafts")
 countmoredelayed_b = sum(1 for delay in DelayFlight if int(delay) > 60)
 print("Aircrafts delayed more than 60 min:", countmoredelayed_b, "aircrafts")

# -------------------------------------------------------------------------------

# Compute CTA (Calculated Time of Arrival)
CTA = []  # Lista para guardar el CTA de cada vuelo
CTAnoreg = []

for i, (slot_time, expected_arr) in enumerate(zip(asignacion, eta)):
 # CTA = ETA + delay (el delay ya está implícito en la diferencia entre slot y ETA)
 delay = slot_time - expected_arr
 cta = expected_arr + delay
 CTA.append(cta)

print("\n CTA de todos los vuelos:")
for i, cta in enumerate(CTA):
 horas = int(cta) // 60
 minutos = int(cta) % 60
 print(f"{airline[i]:3} | {id[i]:4} | CTA: {horas:02d}:{minutos:02d} | Delay: {DelayFlight[i]:3} min")

# --------------------------------------------------------------------------------------

# Histograma de llegadas basado en los slots asignados (CTA)

# Convertimos los slots asignados a horas
CTA_hours = [slot / 60 for slot in asignacion]  # slot está en minutos, pasamos a horas

# Convertimos a horas los vuelos no regulados
i = 0
while i < indexcopy:
 CTAnoreg.append(int(ETAmin[i]) / 60)
 i = i + 1
i = indexcopy + len(asignacion) - 1
while i < len(ETAmin):
 CTAnoreg.append(int(ETAmin[i]) / 60)
 i = i + 1

time = [np.linspace(0, 24, 24, endpoint=False), np.linspace(0, 24, 24, endpoint=False)]
RegulatedArrivalData, Borders = np.histogram(np.array(CTA_hours), bins=np.arange(25))
NonRegulatedArrivalData, Borders = np.histogram(np.array(CTAnoreg), bins=np.arange(25))
Arrivals = [RegulatedArrivalData, NonRegulatedArrivalData]
PlotHistogram(time, Arrivals, NomCapacity, RedCapacity, StartRedCapacity, EndRedCapacity, len(ETAmin), 2)

# -------------------------------------------------------------------------------

answer = input("\nPrint slots after cancelling the ones with more than 2 hours of delay? ")
if answer == "yes":
 Delay_After = PrintNewSlotsGDP(inislot, endslot, airline, id, eta, DelayFlight, cancelled)
 Delay_After = [d for d in Delay_After if d is not None]  # Para quitar todos los None
 countnotdelayed_a = sum(1 for delay in Delay_After if int(delay) == 0)
 print("\nAircrafts not delayed:", countnotdelayed_a, "aircrafts")
 countdelayed30_a = sum(1 for delay in Delay_After if int(delay) <= 30 and int(delay) > 0)
 print("Aircrafts delayed between 0 and 30 min:", countdelayed30_a, "aircrafts")
 countdelayed60_a = sum(1 for delay in Delay_After if int(delay) <= 60 and int(delay) > 30)
 print("Aircrafts delayed between 30 and 60 min:", countdelayed60_a, "aircrafts")
 countmoredelayed_a = sum(1 for delay in Delay_After if int(delay) > 60)
 print("Aircrafts delayed more than 60 min:", countmoredelayed_a, "aircrafts")

# -------------------------------------------------------------------------------

answer = input("\nPlot delay pie? ")
if answer == "yes":
 PlotDelayPie(countnotdelayed_b, countdelayed30_b, countdelayed60_b, countmoredelayed_b,
              countnotdelayed_a, countdelayed30_a, countdelayed60_a, countmoredelayed_a)