import numpy as np
import matplotlib.pyplot as plt
from main import ETAmin
from Plotfunction import PlotHistogram, PlotAggregateDemand

ETAhour = []
NomCapacity = 60
RedCapacity = 20
LastDelay = 0
TotalDelay = 0

StartRedCapacity = 5
EndRedCapacity = 13

# --------------------------------------------------

def aggregateDemand():
  AggregateDemand = np.zeros((1440,2))
  i = 0
  cumsum = 0
  while i < 1440:
      AggregateDemand[i,0] = i+1
      countac = ETAmin.count(i+1)
      cumsum = cumsum + countac
      AggregateDemand[i,1] = cumsum
      i = i+1
  return AggregateDemand

ad = aggregateDemand()

# -------------------------------------------------

# Plot non-regulated histogram
for eta in ETAmin:
   ETAhour.append(float(eta)/60)

time = [np.linspace(0, 24, 24, endpoint=False)]
ArrivalData, Borders = np.histogram(np.array(ETAhour), bins=np.arange(25))
Arrivals = [ArrivalData]
PlotHistogram(time, Arrivals, NomCapacity, RedCapacity, StartRedCapacity, EndRedCapacity, len(ETAhour), 1)

# ---------------------------------------------------

# Plot aggregate demand

# Demand line
time = ad[:,0]
time = [float(i)/60 for i in time]
RawDemand = ad[:,1]

# Capacity reduced line
R = np.where(ad[:,0] == StartRedCapacity*60)[0][0]   # empieza la regulación
reduced = np.zeros((EndRedCapacity*60-StartRedCapacity*60+1, 2))
reduced[0, :] = ad[R, :]

LastDelay,TotalDelay = PlotAggregateDemand(time, RawDemand, reduced, NomCapacity, RedCapacity, StartRedCapacity, EndRedCapacity)
print("Total Delay of the regulation (WP1):",TotalDelay,"min")
print("Hnoreg:",str(LastDelay//60)+":0"+str(LastDelay%60)+"h")