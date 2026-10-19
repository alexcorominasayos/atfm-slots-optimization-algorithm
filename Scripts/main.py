from accategory import actype, accategory, acseats

ETAmin = []
ARCID = []
flightdistance = []
Hfile = 210  # 03:30:00
Extension = 30  # 04:00:00

# Read the CSV file and process lines
def arrivalfile(filename, Hfile, Extension):
   # Initialize empty lists for storing flight data
   ARCID = []
   ATYP = []
   ADEP = []
   ADES = []
   RM = []
   ARF = []
   ETD = []
   TT = []
   ETA = []

   ETDmin = []  # ETD in minutes from midnight
   ETAmin = []  # ETA in minutes from midnight
   flighttime = []  # Total flight time (ETA - ETD)
   flighttimeNOtt = []  # Flight time excluding taxi time
   flightdistance = []
   Affected = []
   AirDelay = []
   GroundDelay = []

   Hstart = 300  # 05:00:00
   Hend = 780  # 13:00:00

   # Velocities in m/s
   velA = 225 / 3.6
   velB = 425 / 3.6
   velC = 780 / 3.6
   velD = 850 / 3.6
   velE = 900 / 3.6
   velF = 875 / 3.6
   velL = 200 / 3.6

   ECAC = ['LA', 'UD', 'LO', 'UB', 'EB', 'LQ', 'LB', 'LD', 'LC', 'LK', 'EK', 'EE',
           'EF', 'LF', 'UG', 'ED', 'LG', 'LH', 'BI', 'EI', 'LI', 'EV', 'EY', 'EL',
           'LM', 'LN', 'EH', 'LJ', 'EN', 'EP', 'LP', 'MD', 'LR', 'SM', 'YU', 'LE',
           'ES', 'LS', 'TC', 'UR', 'EG']

   radius = 2000  # outside of it air delay

   with open(filename, "r") as file:
       next(file)  # Skip the first line

       for line in file:
           parts = line.strip().split(";")

           # Only process flights where ADES (arrival airport) is EDDM
           if parts[3] == "EDDM":
               ARCID.append(parts[0])
               ATYP.append(parts[1])
               ADEP.append(parts[2])
               ADES.append(parts[3])
               RM.append(parts[4])
               ARF.append(parts[5])
               ETD.append(parts[6])
               TT.append(parts[7])
               ETA.append(parts[8])

   # Convert ETA to minutes since midnight
   for eta_str in ETA:
       hours, minutes, seconds = map(int, eta_str.split(":"))
       ETAmin.append(hours * 60 + minutes)

   # Convert ETD to minutes since midnight
   for etd_str in ETD:
       hours, minutes, seconds = map(int, etd_str.split(":"))
       ETDmin.append(hours * 60 + minutes)

   # Zip all lists together to sort by ETA
   combined = list(zip(ETAmin, ETDmin, ARCID, ATYP, ADEP, ADES, RM, ARF, ETD, TT, ETA))
   # Sort combined data by ETAmin (first element of each tuple)
   combinedsorted = sorted(combined)
   # Unpack sorted tuples back into separate lists
   ETAmin, ETDmin, ARCID, ATYP, ADEP, ADES, RM, ARF, ETD, TT, ETA = zip(*combinedsorted)

   # Compute flight time and flight time without taxi time
   for i in range(len(ETDmin)):
       etd = ETDmin[i]
       eta = ETAmin[i]

       # Account for overnight flights (i.e., ETA is on the next day)
       total_time = eta - etd if eta >= etd else (24 * 60) + (eta - etd)
       flighttime.append(total_time)

       # Subtract taxi time (TT) from total time
       flighttimeNOtt.append(total_time - int(TT[i]))

   # Determine the flightdistance
   k = 0
   for j in ATYP:
       index = actype.index(j)
       if accategory[index] == "A":
           dist = flighttimeNOtt[k] * (velA * 0.06)
           flightdistance.append(int(round(dist)))
       elif accategory[index] == "B":
           dist = flighttimeNOtt[k] * (velB * 0.06)
           flightdistance.append(int(round(dist)))
       elif accategory[index] == "C":
           dist = flighttimeNOtt[k] * (velC * 0.06)
           flightdistance.append(int(round(dist)))
       elif accategory[index] == "D":
           dist = flighttimeNOtt[k] * (velD * 0.06)
           flightdistance.append(int(round(dist)))
       elif accategory[index] == "E":
           dist = flighttimeNOtt[k] * (velE * 0.06)
           flightdistance.append(int(round(dist)))
       elif accategory[index] == "F":
           dist = flighttimeNOtt[k] * (velF * 0.06)
           flightdistance.append(int(round(dist)))
       k = k + 1

   # Determine if the flight is affected or not by the regulation
   n = 0
   for eta in ETAmin:
       if (eta >= 300) and (eta <= 780):  # if eta in regulation time --> affected --> ground delay or air delay
           Affected.append(True)
           if (ETDmin[n] < (Hfile + Extension)):  # already flying --> only air delay
               GroundDelay.append(False)
               AirDelay.append(True)
           elif (flightdistance[n] > radius):  # further than radius --> only air delay
               GroundDelay.append(False)
               AirDelay.append(True)
           elif (ADEP[n][:2] not in ECAC):  # ac not from ECAC --> only air delay
               GroundDelay.append(False)
               AirDelay.append(True)
           else:  # if none --> ground delay
               GroundDelay.append(True)
               AirDelay.append(False)
       else:  # if eta in non regulation time --> not affected --> only air delay
           Affected.append(False)
           GroundDelay.append(False)
           AirDelay.append(True)
       n = n + 1

   return ETAmin, ETDmin, ARCID, ATYP, ADEP, ADES, RM, ARF, ETD, TT, ETA, flighttime, flighttimeNOtt, flightdistance, Affected, GroundDelay, AirDelay

# Call the function
(ETAmin, ETDmin, ARCID, ATYP, ADEP, ADES, RM, ARF, ETD, TT, ETA, flighttime, flighttimeNOtt, flightdistance,
Affected, GroundDelay, AirDelay) = arrivalfile("EDDM_10AUG2025.csv", Hfile, Extension)

# Calcular turnaround de vuelos dentro de la regulación
Hstart_min = 300  # 05:00
Hend_min = 907    # 15:07

# Lista para almacenar los turnarounds
turnaround_times = []

# Lista para almacenar los RM de vuelos afectados (para identificar después)
RM_affected = []

# Filtramos vuelos dentro de la regulación y afectados
flights_in_reg = []
for i in range(len(RM)):
   if Affected[i] and Hstart_min <= ETAmin[i] <= Hend_min:
       flights_in_reg.append((RM[i], ARCID[i], ADEP[i], ADES[i], ETAmin[i], ETDmin[i]))
       RM_affected.append(ARCID[i])  # Guardamos el RM

# Ordenamos por RM y por hora de llegada
flights_in_reg.sort(key=lambda x: (x[0], x[4]))  # primero RM, luego ETA

# Recorremos la lista y calculamos turnaround si el mismo avión tiene otra salida
for i in range(len(flights_in_reg)-1):
   rm_current = flights_in_reg[i][0]
   rm_next = flights_in_reg[i+1][0]
   if rm_current == rm_next:
       arrival_eta = flights_in_reg[i][4]
       next_etd = flights_in_reg[i+1][5]
       turnaround = next_etd - arrival_eta
       turnaround_times.append((rm_current, flights_in_reg[i][1], flights_in_reg[i+1][1], turnaround))

# Imprimir resultados
print("\nTurnaround times for flights affected by regulation:")
for t in turnaround_times:
   print(f"RM {t[0]}: arrival {t[1]} -> next departure {t[2]} | Turnaround: {t[3]} min")
print(RM_affected)

# Ajuste para vuelos "already flying" que salen el día anterior
for n in range(len(ETDmin)):
   # Si el vuelo llega en la ventana de regulación pero su ETD es mayor que ETA (overnight)
   if Affected[n] and ETDmin[n] > ETAmin[n]:
       GroundDelay[n] = False
       AirDelay[n] = True