from EcacAirline import ArrivalsEcac, ECAC
from main import ETAmin, ETDmin, flightdistance, ADEP
from graph import LastDelay

Hfile=210
Extension=30
Hstart=300
LastDelay=907
radius=2000

def computeAircraftStatus(ETA, ETD, Distances, International, Hfile, Extension, Hstart, LastDelay, radius):

   Hstart_min = Hstart
   HNoReg_min = LastDelay

   NotAffected = []
   Controlled = []
   AirDelay = []
   GroundDelay = []

   for i in range(len(ETA)):
       eta = ETA[i]
       etd = ETD[i]
       dist = Distances[i]
       intl = International[i]

       # No afectado (fuera de regulación)
       if eta < Hstart_min or eta >= HNoReg_min:
           NotAffected.append(True)
           Controlled.append(False)
           AirDelay.append(False)
           GroundDelay.append(False)
       else:
            # Exento (en regulación pero excluido)
            if etd < (Hfile+Extension):  # volando
                NotAffected.append(False)
                Controlled.append(False)
                AirDelay.append(True)
                GroundDelay.append(False)
            elif dist > radius:
                NotAffected.append(False)
                Controlled.append(False)
                AirDelay.append(True)
                GroundDelay.append(False)
            elif intl:  # Internacional (fuera de la ECAC)
                NotAffected.append(False)
                Controlled.append(False)
                AirDelay.append(True)
                GroundDelay.append(False)
            else:
                # Controlado (afectado y no exento)
                NotAffected.append(False)
                Controlled.append(True)
                AirDelay.append(False)
                GroundDelay.append(True)

   return (NotAffected, Controlled, AirDelay, GroundDelay)

International = [True if adep[:2] not in ECAC else False for adep in ADEP]

NotAffected, Controlled, AirDelay, GroundDelay = computeAircraftStatus(ETAmin, ETDmin, flightdistance, International, Hfile, Extension, Hstart, LastDelay, radius)

# No afectados y controlados
print("Not affected:", sum(NotAffected))
print("Controlled:", sum(Controlled))

print("ETAmin min/max:", min(ETAmin), max(ETAmin))
print("ETDmin min/max:", min(ETDmin), max(ETDmin))
print("Num internacionales:", sum(International), "de", len(International))