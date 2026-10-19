import numpy as np
from graph import StartRedCapacity, EndRedCapacity, LastDelay, NomCapacity, RedCapacity
from main import ETDmin, ETAmin, ARCID, ATYP, flightdistance, flighttimeNOtt, TT, ADEP
from AircraftStatus import NotAffected, AirDelay, GroundDelay

def ComputeSlots(Hstart, Hend, HNoReg, ETDmin, ETAmin, ARCID, NotAffected, AirDelay, GroundDelay, ATYP, flightdistance,
                flighttimeNOtt, TT, ADEP):
   
   start_min = int(Hstart * 60)
   end_red_min = int(Hend * 60)
   end_noreg_min = int(HNoReg)

   # Vectores para llenar cada slot
   sloti = []
   slotf = []
   airline = []
   id = []
   etd = []
   eta = []
   notaffected = []
   airdelay = []
   grounddelay = []
   DelayFlight = []
   distance = []
   time = []
   atyp = []
   adep = []

   step = int(NomCapacity / RedCapacity)  # intervalo de 3 minutos en reduced capacity

   # periodo de regulación (capacidad reducida)
   t = start_min
   index = ETAmin.index(t)
   indexcopy = index
   arcid1 = ARCID[index][:3]
   arcid2 = ARCID[index][3:]

   while t < end_red_min:
       sloti.append(t)
       slotf.append(t + 2)
       airline.append(arcid1)
       id.append(arcid2)
       eta.append(ETAmin[index])
       etd.append(ETDmin[index])
       DelayFlight.append(t - ETAmin[index])
       notaffected.append(NotAffected[index])
       airdelay.append(AirDelay[index])
       grounddelay.append(GroundDelay[index])
       distance.append(flightdistance[index])
       time.append(flighttimeNOtt[index])
       atyp.append(ATYP[index])
       adep.append(ADEP[index])
       t += step
       index = index + 1
       arcid1 = ARCID[index][:3]
       arcid2 = ARCID[index][3:]

   count = 0
   step = int(NomCapacity / NomCapacity) * 2  # 2 operaciones cada 2 minutos
   # periodo nominal
   while t <= end_noreg_min + 3:  # para hacer que entre el último con delay, sumar dos más del necesario porque los slots van de 2 en 2
       sloti.append(t)
       slotf.append(t + 1)
       airline.append(arcid1)
       id.append(arcid2)
       eta.append(ETAmin[index])
       etd.append(ETDmin[index])
       DelayFlight.append(t - ETAmin[index])
       notaffected.append(NotAffected[index])
       airdelay.append(AirDelay[index])
       grounddelay.append(GroundDelay[index])
       distance.append(flightdistance[index])
       time.append(flighttimeNOtt[index])
       atyp.append(ATYP[index])
       adep.append(ADEP[index])
       count = count + 1
       if count == 2:
           t += step
           count = 0
       index = index + 1
       arcid1 = ARCID[index][:3]
       arcid2 = ARCID[index][3:]

   return sloti, slotf, airline, id, etd, eta, DelayFlight, indexcopy, notaffected, airdelay, grounddelay, atyp, distance, time, 1, adep

(sloti, slotf, airline, id, etd, eta, DelayFlight, indexcopy,
notaffected, airdelay, grounddelay, atyp, distance, time, taxi, adep) = ComputeSlots(StartRedCapacity, EndRedCapacity,
                                                                               LastDelay, ETDmin, ETAmin, ARCID,
                                                                               NotAffected, AirDelay, GroundDelay,
                                                                               ATYP, flightdistance, flighttimeNOtt,
                                                                               TT, ADEP)

def PrintSlots(sloti, slotf, airline, id, etd, eta, DelayFlight, notaffected, airdelay, grounddelay):
   print("\n🛫 All the slots: ")
   i = 0
   while i < len(sloti):
       # inicio slot
       horasloti = int(sloti[i]) // 60
       minutosloti = int(sloti[i]) % 60
       # final slot
       if int(sloti[i]) < EndRedCapacity * 60:
           horaslotf = (int(slotf[i])) // 60
           minutoslotf = (int(slotf[i])) % 60
       else:
           horaslotf = (int(slotf[i])) // 60
           minutoslotf = (int(slotf[i])) % 60
       horaeta = int(eta[i]) // 60
       minutoeta = int(eta[i]) % 60
       notaff = notaffected[i]
       airdel = airdelay[i]
       grounddel = grounddelay[i]
       print(
           f"{horasloti:02d}:{minutosloti:02d}-{horaslotf:02d}:{minutoslotf:02d} | {airline[i]:3} | {id[i]:4} | {horaeta:02d}:{minutoeta:02d} | {DelayFlight[i]:3} | {notaff:5} | {airdel:5} | {grounddel:5}")
       i = i + 1

answer = input("\nPrint the non-regulated slots? ")
if answer == "yes":
   PrintSlots(sloti, slotf, airline, id, etd, eta, DelayFlight, notaffected, airdelay, grounddelay)

def PrintOtherData():
   affectedregulation = 0
   for gd in grounddelay:
       if gd:
           affectedregulation = affectedregulation + 1

   print(f"\n Total de slots: {len(sloti)}")

   print("\nAircrafts affected:", affectedregulation)

   print("Total delay:", sum(DelayFlight), "min")
   AvgDelay = sum(DelayFlight) / len(sloti)
   print("Average delay per aircraft:", round(AvgDelay, 2), "min")

   std_delay = np.std(DelayFlight)
   print("Standard deviation of the delay:", round(std_delay, 2), "min")
   rsd_delay = (std_delay / AvgDelay) * 100
   print("Relative standard deviation of the delay:", round(rsd_delay, 2), "%")

   countdelayed = sum(1 for delay in DelayFlight if int(delay) > 0)
   print("\nAircrafts delayed:", countdelayed, "aircrafts")
   countdelayed15 = sum(1 for delay in DelayFlight if int(delay) > 15)
   print("Aircrafts delayed more than 15 min:", countdelayed15, "aircrafts")
   countdelayed120 = sum(1 for delay in DelayFlight if int(delay) > 120)
   print("Aircrafts delayed more than 2 hours:", countdelayed120, "aircrafts")

"""answer = input("\nPrint other interesting data? ")
if answer == "yes":
   PrintOtherData()"""