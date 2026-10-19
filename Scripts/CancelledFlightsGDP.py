import pandas as pd

def PrintNewSlotsGDP(Inicio_Slot,Final_Slot,Compañia_Avion,Codigo_Avion,Tiempo_Llegada_Esperado,Delay,Cancelados):
    # --- Guardar copia original ---
    original_Compania = Compañia_Avion.copy()
    original_Codigo = Codigo_Avion.copy()
    original_Llegada = Tiempo_Llegada_Esperado.copy()
    original_Delay = Delay.copy()

    # Calcular delay total antes de cancelar
    delay_total = sum(
        d for d in original_Delay if isinstance(d, (int, float))
    )

    # Calcular delay total antes de reasignar (ignorando cancelados)
    delay_total_antes = sum(
        d for i, d in enumerate(original_Delay)
        if i not in Cancelados and isinstance(d, (int, float))
    )

    # --- Inicialización ---
    slots_libres = set(Cancelados)
    original_data = list(zip(Compañia_Avion, Codigo_Avion, Tiempo_Llegada_Esperado, Delay))
    Reubicado = ["No"] * len(Inicio_Slot)


    def buscar_y_reasignar(slot_vacio):
        """Busca un vuelo que pueda ocupar un slot vacío."""
        slot_inicio = Inicio_Slot[slot_vacio]
        compania_slot = original_data[slot_vacio][0]

        # --- 1. Buscar vuelo de la misma compañía ---
        for i in range(slot_vacio + 1, len(Inicio_Slot)):
            if i in slots_libres:
                continue
            comp, cod, llegada, delay = Compañia_Avion[i], Codigo_Avion[i], Tiempo_Llegada_Esperado[i], Delay[i]
            if comp == compania_slot and llegada is not None and llegada <= slot_inicio:
                mover_avion(i, slot_vacio)
                return True

        # --- 2. Buscar vuelo de otra compañía ---
        for i in range(slot_vacio + 1, len(Inicio_Slot)):
            if i in slots_libres:
                continue
            comp, cod, llegada, delay = Compañia_Avion[i], Codigo_Avion[i], Tiempo_Llegada_Esperado[i], Delay[i]
            if comp != compania_slot and llegada is not None and llegada <= slot_inicio:
                mover_avion(i, slot_vacio)
                return True

        return False


    def mover_avion(origen, destino):
        """Mueve un avión de un slot a otro y actualiza los huecos."""
        # Copiar información del avión
        Compañia_Avion[destino] = Compañia_Avion[origen]
        Codigo_Avion[destino] = Codigo_Avion[origen]
        Tiempo_Llegada_Esperado[destino] = Tiempo_Llegada_Esperado[origen]
        Delay[destino] = max(0, Inicio_Slot[destino] - Tiempo_Llegada_Esperado[destino])
        Reubicado[destino] = "Sí"

        # Marcar el slot de origen como libre
        slots_libres.add(origen)
        slots_libres.discard(destino)

        # El avión original deja de estar en su slot
        Compañia_Avion[origen] = None
        Codigo_Avion[origen] = None
        Tiempo_Llegada_Esperado[origen] = None
        Delay[origen] = None
        Reubicado[origen] = "—"


    # --- Aplicar reasignaciones ---
    # Marcar los vuelos cancelados como vacíos antes de iniciar
    for idx in Cancelados:
        Compañia_Avion[idx] = None
        Codigo_Avion[idx] = None
        Tiempo_Llegada_Esperado[idx] = None
        Delay[idx] = None
        Reubicado[idx] = "—"

    # Reasignar iterativamente hasta que no haya más cambios
    cambio = True
    while cambio:
        cambio = False
        for slot in sorted(list(slots_libres)):
            if buscar_y_reasignar(slot):
                cambio = True

    # --- Marcar visualmente los slots vacíos ---
    for i in slots_libres:
        Compañia_Avion[i] = "VACÍO"
        Codigo_Avion[i] = "—"
        Tiempo_Llegada_Esperado[i] = None
        Delay[i] = None
        Reubicado[i] = "—"

    # --- Calcular delay total después (ignorando vacíos) ---
    delay_total_despues = sum(
        d for d in Delay if isinstance(d, (int, float))
    )

    # Código para visualizar mejor las horas de los slots y la llegada
    def minutos_a_hhmm(minutos):
        if minutos is None or pd.isna(minutos):
            return ""
        minutos = int(minutos)
        h = minutos // 60
        m = minutos % 60
        return f"{h:02d}:{m:02d}"
    Inicio_Slot_HHMM = pd.Series(Inicio_Slot).apply(minutos_a_hhmm)
    Final_Slot_HHMM = pd.Series(Final_Slot).apply(minutos_a_hhmm)
    Tiempo_Llegada_Esperado_HHMM = pd.Series(Tiempo_Llegada_Esperado).apply(minutos_a_hhmm)

    # --- Mostrar resultados ---
    df = pd.DataFrame({
        "Slot_Inicio": Inicio_Slot_HHMM,
        "Slot_Final": Final_Slot_HHMM,
        "Compañia": Compañia_Avion,
        "Codigo": Codigo_Avion,
        "Llegada_Esperada": Tiempo_Llegada_Esperado_HHMM,
        "Delay": Delay,
        "Reubicado": Reubicado
    })

    print("\n📋 RESULTADO FINAL TRAS REASIGNACIÓN DE SLOTS\n")
    print(df.to_string(index=True))

    print("\n📊 COMPARATIVA DEL RETRASO TOTAL")
    print(f"→ Delay total antes de cancelar:   {delay_total} minutos")
    print(f"→ Delay total antes de reasignar:  {delay_total_antes} minutos")
    print(f"→ Delay total después de reasignar: {delay_total_despues} minutos")
    print(f"→ Mejora total:                    {delay_total - delay_total_despues} minutos")
    print(f"→ Mejora al reasignar:              {delay_total_antes - delay_total_despues} minutos")

    print("\nSlots finalmente vacíos:", sorted(list(slots_libres)))

    return Delay