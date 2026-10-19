actype = []
accategory = []
acseats = []

F = open("fleet_cat_seat.csv","r")
linea = F.readline()

while True:
   linea = F.readline()
   if not linea:
       break
   trozos = linea.split(",")
   actype.append(str(trozos[1]))
   accategory.append(str(trozos[2]))
   acseats.append(str(trozos[3]))