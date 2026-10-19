import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np
from main import arrivalfile
from graph import StartRedCapacity, EndRedCapacity, LastDelay, NomCapacity, RedCapacity
from slots import ComputeSlots
from AssignSlotsGDP import ComputeSlotsGDP, PrintSlotsGDP, Calc_Emissions
from AircraftStatus import computeAircraftStatus, International
from UnrecoverableDelay import UnrecoverableDelay

Hfile = 210 # from 0 to 300
Extension = 0 # Not of interest in this case
Hstart = 300
radius = 2000 # from 0 to 3000

def min_to_hhmm(x,pos):
    horas = int(x // 60)
    minutos = int(x % 60)
    return f"{horas:02d}:{minutos:02d}"

def PlotHfileVSRadiusVSDelay(Extension,StartRedCapacity,EndRedCapacity,LastDelay,Hstart):

    # Value of the step of each variable
    step_radius = 50
    step_Hfile = 1

    # Minimum/Maximum radius considered and minimum/maximum filing time considered
    radius0 = 0
    radiusF = 3000
    Hfile0 = 0
    HfileF = 300

    # Number of steps
    n = int((HfileF-Hfile0)/step_Hfile)
    m = int((radiusF-radius0)/step_radius)

    # Discretization
    t=np.linspace(Hfile0,HfileF,n+1)
    y=np.linspace(radius0,radiusF,m+1)
    print("Hfile discretization:",t)
    print("Radius discretization:",y)

    # We create two matrixes (one to help us save the instantaneous values)
    Air_Delay_Matrix = np.zeros((n+1,m+1))
    """Ground_Delay_Matrix = np.zeros((n+1,m+1))"""
    Unrecoverable_Delay_Matrix = np.zeros((n+1,m+1))
    CO2_Matrix = np.zeros((n+1,m+1))

    for j in range(m+1):
        for i in range(n+1):

            (ETAmin, ETDmin, ARCID, ATYP, ADEP, ADES, RM, ARF, ETD, TT, ETA,flighttime, flighttimeNOtt, flightdistance,
            Affected, GroundDelay, AirDelay) = arrivalfile("EDDM_10AUG2025.csv",t[i],Extension)
            
            NotAffected, Controlled, AirDelay, GroundDelay = computeAircraftStatus(ETAmin, ETDmin, flightdistance, International, 
                                                                                t[i], Extension, Hstart, LastDelay, y[j])

            (sloti, slotf, airline, id, etd, eta, DelayFlight, indexcopy, notaffected, airdelay,
            grounddelay, atyp, distance, time, taxi, adep) = ComputeSlots(StartRedCapacity, EndRedCapacity, LastDelay, ETDmin, ETAmin, ARCID,
                                                                    NotAffected, AirDelay, GroundDelay, ATYP, flightdistance, flighttimeNOtt, TT, ADEP)
            
            (adep_out, etd_out, eta_out, atyp_out, distance_out, time_out, res,
             asignacion) = ComputeSlotsGDP(sloti,slotf,airline,id,etd,eta,DelayFlight,notaffected,airdelay,grounddelay,atyp,distance,time,adep)

            (inislot,endslot,airline,id,etd,eta,DelayFlight,notaffected,airdelay,grounddelay,atyp,distance,time,sumad,maxad,countad,
            delayad,sumgd,maxgd,countgd,delaygd,cancelled) = PrintSlotsGDP(res)

            sumud = UnrecoverableDelay(DelayFlight,StartRedCapacity,etd,grounddelay)

            co2_emissions = Calc_Emissions(atyp_out, distance_out, DelayFlight, notaffected, airdelay, grounddelay, time_out)

            Air_Delay_Matrix[i][j] = sumad
            """Ground_Delay_Matrix[i][j] = sumgd"""
            Unrecoverable_Delay_Matrix[i][j] = sumud
            CO2_Matrix[i][j] = (co2_emissions/1000)

    # Encontrar el valor mínimo de la matriz
    minimo = min(min(fila) for fila in Air_Delay_Matrix)

    # Crear listas para guardar las posiciones (x, y)
    pos_x = []
    pos_y = []

    # Recorrer la matriz para encontrar todas las posiciones del mínimo
    for i, fila in enumerate(Air_Delay_Matrix):
        for j, valor in enumerate(fila):
            if valor == minimo:
                pos_x.append(i)
                pos_y.append(j)

    # Mostrar resultados
    print("Posiciones óptimas:")
    i = 0
    while i < len(pos_x):
        print("("+str(min_to_hhmm(t[pos_x[i]],0))+","+str(y[pos_y[i]])+")")
        i += 1
    print(f"Valor mínimo: {minimo}")

    # Plot and show the graph
    fig = plt.figure(figsize=(25,14))
    T, Y = np.meshgrid(t, y)

    # We transpose the matrix to obtain the desired one
    Air_Delay_Matrix = Air_Delay_Matrix.transpose()
    """Ground_Delay_Matrix = Ground_Delay_Matrix.transpose()"""
    Unrecoverable_Delay_Matrix = Unrecoverable_Delay_Matrix.transpose()
    CO2_Matrix = CO2_Matrix.transpose()

    ax = fig.add_subplot(131, projection='3d', label='Air delay VS Radius of the regulation VS Time when the regulation is filed')
    ax.plot_surface(T, Y, Air_Delay_Matrix, label='Air delay', rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    ax.xaxis.set_major_formatter(FuncFormatter(min_to_hhmm))
    ax.xaxis.set_major_locator(MultipleLocator(60))
    ax.yaxis.set_major_locator(MultipleLocator(1000))
    ax.legend()
    ax.set_xlabel('Hfile', fontsize=10, rotation=30, labelpad=10)
    ax.set_ylabel('Radius (km)', fontsize=10, rotation=150, labelpad=10)
    ax.set_zlabel('Air delay (min)', fontsize=10, rotation=60, labelpad=10)

    """ax = fig.add_subplot(132, projection='3d', label='Ground delay VS Radius of the regulation VS Time when the regulation is filed')
    ax.plot_surface(T, Y, Ground_Delay_Matrix, label='Ground delay', rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    ax.xaxis.set_major_formatter(FuncFormatter(min_to_hhmm))
    ax.xaxis.set_major_locator(MultipleLocator(60))
    ax.yaxis.set_major_locator(MultipleLocator(1000))
    ax.legend()
    ax.set_xlabel('Hfile', fontsize=10, rotation=30, labelpad=10)
    ax.set_ylabel('Radius (km)', fontsize=10, rotation=150, labelpad=10)
    ax.set_zlabel('Ground delay (min)', fontsize=10, rotation=60, labelpad=10)"""

    ax = fig.add_subplot(133, projection='3d', label='Unrecoverable delay VS Radius of the regulation VS Time when the regulation is filed')
    ax.plot_surface(T, Y, Unrecoverable_Delay_Matrix, label='Unrecoverable delay', rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    ax.xaxis.set_major_formatter(FuncFormatter(min_to_hhmm))
    ax.xaxis.set_major_locator(MultipleLocator(60))
    ax.yaxis.set_major_locator(MultipleLocator(1000))
    ax.legend()
    ax.set_xlabel('Hfile', fontsize=10, rotation=30, labelpad=10)
    ax.set_ylabel('Radius (km)', fontsize=10, rotation=150, labelpad=10)
    ax.set_zlabel('Unrecoverable delay (min)', fontsize=10, rotation=60, labelpad=10)

    ax = fig.add_subplot(132, projection='3d', label='CO2 emissions VS Radius of the regulation VS Time when the regulation is filed')
    ax.plot_surface(T, Y, CO2_Matrix, label='CO2 emmissions', rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    ax.xaxis.set_major_formatter(FuncFormatter(min_to_hhmm))
    ax.xaxis.set_major_locator(MultipleLocator(60))
    ax.yaxis.set_major_locator(MultipleLocator(1000))
    ax.legend()
    ax.set_xlabel('Hfile', fontsize=10, rotation=30, labelpad=10)
    ax.set_ylabel('Radius (km)', fontsize=10, rotation=150, labelpad=10)
    ax.set_zlabel('CO2 emissions (tones)', fontsize=10, rotation=60, labelpad=10)

    plt.show()

PlotHfileVSRadiusVSDelay(Extension,StartRedCapacity,EndRedCapacity,LastDelay,Hstart)