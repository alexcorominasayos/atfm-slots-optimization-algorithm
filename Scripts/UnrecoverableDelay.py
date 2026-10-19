# Calcular Unrecoverable Delay

def UnrecoverableDelay(Delay_vector,Start_Red_Cap,ETDmin,Ground_Delay_vector):

    Total_Unrecoverable_Delay = 0
    Hstart = Start_Red_Cap*60
    unrecoverable = 0
    i = 0
    while i < len(Delay_vector):
        
        if not Ground_Delay_vector[i]:
            unrecoverable = 0
        else:
            Control_Time_Dep = ETDmin[i]+Delay_vector[i]
            if ETDmin[i] >= Hstart:
                unrecoverable = 0
            elif Control_Time_Dep <= Hstart:
                unrecoverable = Delay_vector[i]
            else:
                unrecoverable = Delay_vector[i]-(Control_Time_Dep-Hstart)

        Total_Unrecoverable_Delay += unrecoverable
        i += 1

    return Total_Unrecoverable_Delay