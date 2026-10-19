import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d

def PlotHistogram(xaxis, yaxis, NomCapacity, RedCapacity, StartRedCapacity, EndRedCapacity, NumAircrafts, NumBars):
    plt.figure(figsize=(8, 8))
    if NumBars == 1:
        plt.bar(xaxis[0], yaxis[0], width=1, color='midnightblue', edgecolor='black', align='edge')
        plt.title('Histogram arrivals non-regulated traffic')
        greenline = 2
    elif NumBars == 2:
        plt.bar(xaxis[0], yaxis[0], width=1, color='orange', edgecolor='black', align='edge', label='Regulated traffic')
        plt.bar(xaxis[1], yaxis[1], width=1, bottom=yaxis[0], color='midnightblue', edgecolor='black', align='edge', label='Non-regulated traffic')
        plt.title('Histogram of arrivals with assigned slots (CTA)')
        greenline = 6
    else:
        print("Not possible")
        quit()
    # Capacity lines
    plt.plot([0, StartRedCapacity], [NomCapacity, NomCapacity], color='green', linewidth=greenline, label='Nominal capacity')
    plt.plot([StartRedCapacity, EndRedCapacity], [RedCapacity, RedCapacity], color='red', linewidth=2, label='Reduced capacity')
    plt.plot([EndRedCapacity, 24], [NomCapacity, NomCapacity], color='green', linewidth=greenline)
    # X axis from 0 to 24 hours
    plt.xticks(np.arange(0, 25, 1))
    plt.xlabel('Time (hours), UTC')
    plt.ylabel('Arrivals ('+str(NumAircrafts)+'aircrafts)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    # Show plot
    plt.show()

def PlotAggregateDemand(time, RawDemand, reduced, NomCapacity, RedCapacity, StartRedCapacity, EndRedCapacity):

    Total_Delay = 0
    index_min = 300
    # DEMAND LINE
    Demand = gaussian_filter1d(RawDemand, sigma=2)

    # REDUCED CAPACITY LINE
    for i in range(1, reduced.shape[0]):
        reduced[i, 0] = reduced[i-1, 0] + 1
        reduced[i, 1] = reduced[i-1, 1] + RedCapacity/60
        Total_Delay = Total_Delay + (RawDemand[index_min]-reduced[i,1])
        index_min = index_min + 1
    reduced_plot = reduced.copy()
    reduced_plot[:, 0] = reduced_plot[:, 0] / 60

    # NOMINAL CAPACITY LINE
    nominal = []
    nominal.append([reduced[-1,0], reduced[-1,1]]) # Starts where the reduced line finishes

    i = 0
    while nominal[-1][1] < RawDemand[int(nominal[-1][0])-1]:  # We compare it each minute with the Agg Demand
        last_time, last_val = nominal[-1]
        next_time = last_time + 1
        # Next value with nominal capacity slope
        next_val  = last_val + NomCapacity/60
        # if next value is higher than the demand we stop
        if next_val >= RawDemand[int(next_time)-1]:
            next_val = RawDemand[int(next_time)-1]
            LastDelay = int(next_time)
        nominal.append([next_time, next_val])
        i += 1
        Total_Delay = Total_Delay + (RawDemand[index_min]-nominal[-1][1])
        index_min = index_min + 1

    nominal = np.array(nominal)
    nominal_plot = nominal.copy()
    nominal_plot[:, 0] = nominal_plot[:, 0] / 60

    # Creat figure and plot
    plt.figure(figsize=(8, 8))
    plt.plot(time, Demand, color='black', label='Aggregate Demand', linestyle='-')
    plt.plot(reduced_plot[:,0], reduced_plot[:,1], 'k:', linewidth=1.25, label='Reduced Capacity')
    plt.plot(nominal_plot[:,0], nominal_plot[:,1], 'k--', linewidth=1.25, label='Nominal Capacity')
    plt.xticks(np.arange(0, 25, 1))
    plt.xlabel('Time (hours), UTC')
    plt.ylabel('Demand (number of aircrafts)')
    plt.title('Aggregate Demand')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()
    return LastDelay,round(Total_Delay)

def PlotDelayPie(OnTime_Initial,HalfHour_Initial,Hour_Initial,Over_Initial,OnTime_Final,HalfHour_Final,Hour_Final,Over_Final):

    Tipos_Delay = ["None","1 to 30 min", "31 to 60 min", "Over 60 min"]
    values_Pie1 = [OnTime_Initial, HalfHour_Initial, Hour_Initial, Over_Initial]
    values_Pie2 = [OnTime_Final, HalfHour_Final, Hour_Final, Over_Final]

    # Crear una figura con 2 subgráficos (1 fila, 2 columnas)
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))

    # Primer gráfico de pastel
    axs[0].pie(values_Pie1, labels=Tipos_Delay, autopct='%1.1f%%', startangle=90)
    axs[0].set_title('Delay before cancelling')

    # Segundo gráfico de pastel
    axs[1].pie(values_Pie2, labels=Tipos_Delay, autopct='%1.1f%%', startangle=90)
    axs[1].set_title('Delay after cancelling and reassigning')

    plt.tight_layout()
    plt.show()