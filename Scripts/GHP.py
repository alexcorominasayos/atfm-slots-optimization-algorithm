import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from AssignSlotsGDP import sloti, airline, id, eta, distance_out, etd_out, adep_out, time_out, atyp_out
from accategory import actype, acseats
from emissions_fuel_model import compute_co2_ask
from main import ARCID, RM_affected, turnaround_times
from EcacAirline import ECAC

def get_seats_for_aircraft(aircraft_type: str):
  try:
      idx = actype.index(aircraft_type)
      return int(float(acseats[idx]))
  except ValueError:
      return 150

def is_international(adep: str):
  return adep is not None and adep[:2] not in ECAC

def solve_GHP(mode):

  flights = [f"{airline[i]}_{id[i]}" for i in range(len(eta))]
  Hfile = 210
  Extension = 30
  n_flights = len(flights)
  slots_min = np.array(sloti)
  n_slots = len(slots_min)
  ETA_min = np.array(eta)
  Dist = np.array(distance_out)
  Seats = np.array([get_seats_for_aircraft(atyp_out[i][:6]) for i in range(n_flights)])

  International = np.array([is_international(dep) for dep in adep_out])
  InRadius = np.array([d <= 2000 for d in Dist])
  AlreadyFlying = np.array([etd_out[i] < (Hfile + Extension) for i in range(n_flights)])

  print(f" Vuelos controlados: {n_flights}")
  print(f" Slots disponibles:  {n_slots}\n")

  n_vars = n_flights * n_slots

  # Cada vuelo solo a un slot
  Aeq = np.zeros((n_flights, n_vars))
  for i in range(n_flights):
      Aeq[i, i * n_slots:(i + 1) * n_slots] = 1
  beq = np.ones(n_flights)

  # Cada slot como máximo un vuelo
  A = np.zeros((n_slots, n_vars))
  for j in range(n_slots):
      for i in range(n_flights):
          A[j, i * n_slots + j] = 1
  b = np.ones(n_slots)

  lb = np.zeros(n_vars)
  ub = np.ones(n_vars)

  for i in range(n_flights):
      for j in range(n_slots):
          if slots_min[j] < ETA_min[i]:
              ub[i * n_slots + j] = 0

  max_air_delay = 30

  for i in range(n_flights):
      exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])
      if exempt_flight:
          for j in range(n_slots):
              delay_real = slots_min[j] - ETA_min[i]
              if delay_real > max_air_delay:
                  ub[i * n_slots + j] = 0

  turnaround_dict = dict(zip(RM_affected, [t[3] for t in turnaround_times]))

  # Vector de costes
  C = np.zeros(n_vars)

  for i in range(n_flights):
      flight_minutes = time_out[i]
      flight_distancebase = distance_out[i]
      for j in range(n_slots):
          delay = max(slots_min[j] - ETA_min[i], 0)

          if mode == "delay":

              exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])
              # Si es vuelo exento solo puede tener air delay limitado
              if exempt_flight:
                  air_delay = min(delay, max_air_delay)
                  ground_delay = 0
              else:
                  air_delay = 0
                  ground_delay = delay

              # Coste base = delay total ponderado
              cost = air_delay + ground_delay

          elif mode == "emissions":

              exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])
              if exempt_flight:
                  air_delay = min(delay, max_air_delay)
                  ground_delay = 0
              else:
                  air_delay = 0
                  ground_delay = delay

              # Factores de emisión (por minuto)

              co2_ask_base = compute_co2_ask(flight_distancebase, Seats[i], force=True)

              emis_rate_air = 1
              emis_rate_ground = 0.33
              speed = flight_distancebase / flight_minutes
              distance_air_delay = air_delay * speed
              distance_ground_delay = ground_delay * speed

              emis_air = co2_ask_base * distance_air_delay * Seats[i] * emis_rate_air / 1000
              emis_ground = co2_ask_base * distance_ground_delay * Seats[i] * emis_rate_ground / 1000

              cost = emis_air + emis_ground

          # Modo Cost
          elif mode == "cost":
              # Exento o no
              exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])

              # Delay en aire o tierra
              if exempt_flight:
                  air_delay = min(delay, max_air_delay)
                  ground_delay = 0
              else:
                  air_delay = 0
                  ground_delay = delay

              # Pax reales
              SLF = 0.82
              pax_real = Seats[i] * SLF  # evitar división por 0

              # Coste operativo (EUROCONTROL por vuelo convertido a €/pax)
              delay_aux = air_delay + ground_delay  # delay total en minutos
              tat = turnaround_dict.get(ARCID[i], None)

              mult = 1.0  # Delay menor de 30 multiplicador base
              if delay_aux > 30:  # Delay mayor a 30 y con rotacion
                  if ARCID[i] in RM_affected:
                      # si hay TAT aplicar solo cuando se rompe la rotación
                      if tat is not None and delay_aux > tat:
                          mult = 1.97
                  else:
                      # vuelos sin rotación especial solo con >30 ya aplicamos
                      mult = 1.97

              cost_operativo = mult * ((212.0 / pax_real) * air_delay +(166.0 / pax_real) * ground_delay)

              # Compensación EU261 (si delay >= 180 min)
              total_delay = air_delay + ground_delay
              comp_EU261 = 0.0
              if total_delay >= 180:
                  if Dist[i] <= 1500:
                      comp_amount = 250
                  elif Dist[i] <= 3500:
                      comp_amount = 400
                  else:
                      comp_amount = 600
                  comp_EU261 = comp_amount * pax_real * 0.3

              # Lost connections (casos hipoteticos de pasajeros con conexiones)
              conn_frac = 0.4
              group_frac = 0.3
              c_rebook = 30
              n_conn = pax_real * conn_frac
              lost_conn_cost_passengers = 0
              # Grupo 40 min
              if total_delay > 40:
                  n_loss1 = n_conn * group_frac
                  lost_conn_cost_passengers += n_loss1 * c_rebook * 0.3

              # Grupo 95 min
              if total_delay > 95:
                  n_loss2 = n_conn * group_frac
                  lost_conn_cost_passengers += n_loss2 * c_rebook * 0.3
              # Coste total para esa asignaciónç
              cost = cost_operativo + comp_EU261 + lost_conn_cost_passengers

          else:
              raise ValueError("Modo no reconocido.")

          C[i * n_slots + j] = cost

  # Definición del problema MILP
  constraints = [LinearConstraint(A, -np.inf, b),LinearConstraint(Aeq, beq, beq)]
  boundaries = Bounds(lb, ub)
  integrality = np.ones(n_vars, dtype=bool)

  result = milp(c=C, constraints=constraints, integrality=integrality, bounds=boundaries)

  if not result.success:
      print("    No se encontró solución óptima:", result.message)
      return None

  X = result.x.reshape((n_flights, n_slots))
  TotalCost = result.fun

  # Procesar resultados
  affected = -1
  assignment = []
  for i in range(n_flights):
      j = np.argmax(X[i, :])
      assigned_slot = slots_min[j]
      delay_real = assigned_slot - ETA_min[i]

      exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])

      if exempt_flight:
          delay_type = "Air"
          # Si el delay real supera el máximo permitido en aire → mostrar 0
          if delay_real > max_air_delay:
              delay = 0
          else:
              delay = delay_real
      else:
          delay_type = "Ground"
          delay = delay_real
          affected += 1

      assignment.append((flights[i], ETA_min[i], assigned_slot, delay, delay_type))

  delays = np.array([a[3] for a in assignment])
  delayed_flights = np.sum(delays > 0)
  mean_delay = np.mean(delays)
  total_delay = np.sum(delays)

  # Cálculo de emisiones totales
  total_emis = 0
  total_emis_air = 0
  total_emis_ground = 0
  total_emis_delay = 0
  emis_por_vuelo = []

  for i in range(n_flights):
      # Slot asignado según MILP
      j = np.argmax(X[i, :])
      delay = max(slots_min[j] - ETA_min[i], 0)

      exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])

      if exempt_flight:
          air_delay = min(delay, max_air_delay)
          ground_delay = 0
      else:
          air_delay = 0
          ground_delay = delay

      # Emisiones del vuelo
      base_distance = distance_out[i]
      co2_ask_base = compute_co2_ask(base_distance, Seats[i], force=True)
      emis_base = co2_ask_base * base_distance * Seats[i] / 1000  # kg CO2

      # Emisiones del delay
      speed = base_distance / time_out[i]
      distance_air_delay = air_delay * speed
      distance_ground_delay = ground_delay * speed
      co2_ask_air = compute_co2_ask(distance_air_delay, Seats[i], force=True)
      co2_ask_ground = compute_co2_ask(distance_ground_delay, Seats[i], force=True)
      emis_air = co2_ask_base * distance_air_delay * Seats[i] / 1000
      emis_ground = co2_ask_base * distance_ground_delay * Seats[i] * 0.33 / 1000

      # Suma total de emisiones
      vuelo_total = emis_base + emis_air + emis_ground
      vuelo_delay = emis_air + emis_ground
      total_emis_air += emis_air
      total_emis_ground += emis_ground
      total_emis_delay += vuelo_delay
      total_emis += vuelo_total

      # Guardar valores por vuelo para report
      emis_por_vuelo.append((flights[i], emis_base, emis_air, emis_ground, vuelo_total))

  total_air_delay = 0.0
  total_ground_delay = 0.0
  all_delays = []
  air_delays = []
  ground_delays = []

  for i in range(n_flights):
      j = np.argmax(X[i, :])
      delay = max(slots_min[j] - ETA_min[i], 0)
      all_delays.append(delay)

      exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])

      if exempt_flight:
          air_delay = min(delay, max_air_delay)
          ground_delay = 0
          air_delays.append(air_delay)
      else:
          air_delay = 0
          ground_delay = delay
          ground_delays.append(ground_delay)

      total_air_delay += air_delay
      total_ground_delay += ground_delay
      ground_delays.append(ground_delay)

  std_delay = np.std(all_delays)
  mean_air_delay = total_air_delay/len(air_delays)
  mean_ground_delay = total_ground_delay/len(ground_delays)
  std_air_delay = np.std(air_delays)
  std_ground_delay = np.std(ground_delays)
  max_air_delay = np.max(air_delays)
  max_ground_delay = np.max(ground_delays)

  # Calculo coste
  total_cost_real = 0
  cost_por_vuelo = []

  SLF = 0.82   # Load factor
  conn_frac = 0.4
  group_frac = 0.3
  c_rebook = 30

  for i in range(n_flights):

      j = np.argmax(X[i, :])
      delay = max(slots_min[j] - ETA_min[i], 0)
      exempt_flight = (International[i] or not InRadius[i] or AlreadyFlying[i])

      if exempt_flight:
          air_delay = min(delay, max_air_delay)
          ground_delay = 0
      else:
          air_delay = 0
          ground_delay = delay

      total_delay_local = air_delay + ground_delay
      pax_real = max(1.0, Seats[i] * SLF)

      # Multiplicador rotación
      mult = 1.0
      if total_delay_local > 30:
          tat = turnaround_dict.get(ARCID[i], None)
          if ARCID[i] in RM_affected:
              if tat is not None and total_delay_local > tat:
                  mult = 1.97
          else:
              mult = 1.97

      cost_air_oper = mult * ((212.0 / pax_real) * air_delay)
      cost_ground_oper = mult * ((166.0 / pax_real) * ground_delay)

      # EU261
      comp_EU261 = 0.0
      if total_delay_local >= 180:
          if Dist[i] <= 1500:
              comp_amount = 250
          elif Dist[i] <= 3500:
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
      cost_por_vuelo.append((flights[i],cost_air_total,cost_ground_total,comp_EU261,lost_conn,cost_flight))
      total_cost_air = sum(c[1] for c in cost_por_vuelo)
      total_cost_ground = sum(c[2] for c in cost_por_vuelo)

  # Distribución delays
  on_time = 0
  d_1_30 = 0
  d_31_60 = 0
  d_more_60 = 0

  for a in assignment:
      delay_val = a[3]
      if delay_val <= 0:
          on_time += 1
      elif 1 <= delay_val <= 30:
          d_1_30 += 1
      elif 31 <= delay_val <= 60:
          d_31_60 += 1
      else:
          d_more_60 += 1

  # Print resultados
  print(" ---RESULTADOS OPTIMIZACIÓN: ---")
  print(f"{'Vuelo':<12}{'ETA':>8}{'Slot':>10}{'Delay [min]':>14}{'TipoDelay':>14}")
  for a in assignment:
      print(f"{a[0]:<12}{a[1]:>8.0f}{a[2]:>10.0f}{a[3]:>14.1f}{a[4]:>14}")
  print(f"    Total vuelos: {n_flights}")
  print(f"    Vuelos con delay: {delayed_flights}")
  print(f"    Vuelos afectados: {affected}")
  print(f"    Delay medio: {mean_delay:.2f} min")
  print(f"    Delay total: {total_delay:.1f} min")
  print(f"    Std. delay: {std_delay:.2f} min")
  print(f"    Emisiones totales (kg CO2): {total_emis:.2f}")
  print(f"    Emisiones delay (kg CO2): {total_emis_delay:.2f}")
  print(f"    Emisiones air delay(kg CO2): {total_emis_air:.2f}")
  print(f"    Emisiones ground delay(kg CO2): {total_emis_ground:.2f}")
  print(f"    Coste total objetivo: {TotalCost:.2f}")
  print(f"    Coste total (recalculado vuelo a vuelo) : {total_cost_real:.2f} €")
  print(f"    Coste total air delay:     {total_cost_air:.2f} €")
  print(f"    Coste total ground delay:  {total_cost_ground:.2f} €")
  print(f"    Suma comprobación:         {(total_cost_air + total_cost_ground):.2f} €")
  print("\n    --- DETALLE DE DELAYS ---")
  print(f"    Air delay total:     {total_air_delay:.1f} min")
  print(f"    Ground delay total:  {total_ground_delay:.1f} min")
  print(f"    Mean air delay:       {mean_air_delay:.2f} min")
  print(f"    Mean ground delay:    {mean_ground_delay:.2f} min")
  print(f"    Std air delay:        {std_air_delay:.2f} min")
  print(f"    Std ground delay:     {std_ground_delay:.2f} min")
  print(f"    Max air delay:        {max_air_delay:.2f} min")
  print(f"    Max ground delay:     {max_ground_delay:.2f} min")
  print("\n    --- DISTRIBUCIÓN DE DELAYS ---")
  print(f"    On time flights:              {on_time}")
  print(f"    Aircraft delayed 1–30  min:   {d_1_30}")
  print(f"    Aircraft delayed 31–60 min:   {d_31_60}")
  print(f"    Aircraft delayed > 60  min:   {d_more_60}")

  return assignment, TotalCost

# Minimizar retraso
e,f = solve_GHP(mode="delay")
# Minimizar emisiones
c,d = solve_GHP(mode="emissions")
# Minimizar coste
a,b = solve_GHP(mode="cost")