from main import ARCID, ADES, ADEP

def EcacArline(ARCID, ADES, ADEP):
    ECAC = ['LA','UD','LO','UB','EB','LQ','LB','LD','LC','LK','EK','EE',
          'EF','LF','UG','ED','LG','LH','BI','EI','LI','EV','EY','EL',
          'LM','LN','EH','LJ','EN','EP','LP','MD','LR','SM','YU','LE',
          'ES','LS','TC','UR','EG']

    Arrivals = []
    ArrivalsEcac = []
    ArrivalsNonEcac = []

    for i in range(len(ARCID)):
      adep = ADEP[i]
      Arrivals.append((adep, ADES[i]))
      adeppref = adep[:2]
      print(adeppref)
      if adeppref in ECAC:
        ArrivalsEcac.append((ARCID[i], adep))
      else:
        ArrivalsNonEcac.append((ARCID[i], adep))

    print("Total llegadas:", len(Arrivals))
    print("Llegadas desde ECAC:", len(ArrivalsEcac))
    print("Llegadas desde fuera ECAC:", len(ArrivalsNonEcac))

    AIRLINE = []
    for i in ARCID:
      AIRLINE.append(i[:3])

    TotalAerolineas = []
    for a in AIRLINE:
      if a not in TotalAerolineas:
          TotalAerolineas.append(a)
    print("Aerolíneas encontradas:", TotalAerolineas)

    count = {}
    for a in AIRLINE:
      if a in count:
          count[a] += 1
      else:
          count[a] = 1

    print("Número de vuelos por aerolínea:")
    for a in count:
      print(a, ":", count[a])
    
    return ArrivalsEcac, ECAC

ArrivalsEcac, ECAC = EcacArline(ARCID, ADES, ADEP)