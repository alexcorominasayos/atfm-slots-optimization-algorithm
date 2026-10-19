"""Ground Delay Program (GDP): slots assigned by schedule, with exempt flights.

This module replaces slots.py, AircraftStatus.py, UnrecoverableDelay.py and the calculation part
of AssignSlotsGDP.py. Nothing runs when it is imported: call run_gdp() from a script.
"""
import numpy as np

from config import (EXEMPT_RADIUS_KM, FILING_EXTENSION_MIN, FILING_MINUTE, NOMINAL_CAPACITY,
                    REDUCED_CAPACITY, REGULATION_END_MIN, REGULATION_START_MIN)

REDUCED_SLOT_INTERVAL_MIN = 60 // REDUCED_CAPACITY                    # 20 per hour: one slot every 3 minutes
NOMINAL_BLOCK_MIN = 2                                                 # at nominal capacity the slots come in
NOMINAL_SLOTS_PER_BLOCK = NOMINAL_CAPACITY * NOMINAL_BLOCK_MIN // 60  # blocks of 2 minutes with 2 slots each


def exempt_mask(flights, filing_minute=FILING_MINUTE, extension=FILING_EXTENSION_MIN,
                radius_km=EXEMPT_RADIUS_KM):
    """True for the flights that cannot be held on the ground, so they can only absorb air delay.

    A flight is exempt if it is already airborne when the regulation is filed, if it comes from
    further than the radius, or if it departs from outside ECAC.
    """
    already_flying = flights["etd_min"] < filing_minute + extension
    too_far = flights["distance_km"] > radius_km
    return already_flying | too_far | flights["international"]


def build_slot_times(regulation_end):
    """Start minute of every slot: one every 3 minutes while the capacity is reduced, then 2 per 2 minutes.

    The nominal slots run 3 minutes past the end of the delay so the last delayed flight finds a slot
    (the original code did the same).
    """
    reduced = np.arange(REGULATION_START_MIN, REGULATION_END_MIN, REDUCED_SLOT_INTERVAL_MIN)
    block_starts = np.arange(REGULATION_END_MIN, regulation_end + 3 + 1, NOMINAL_BLOCK_MIN)
    nominal = np.repeat(block_starts, NOMINAL_SLOTS_PER_BLOCK)
    return np.concatenate([reduced, nominal])


def slot_window(flights, regulation_end):
    """Flights that take part in the regulation, and the start minute of their slots.

    There is one slot per flight: the first flights that arrive from the start of the regulation
    (in ETA order) are the ones that would use the slots if nobody were exempt.
    """
    slot_times = build_slot_times(regulation_end)
    first = flights["eta_min"].searchsorted(REGULATION_START_MIN)
    window = flights.iloc[first:first + len(slot_times)]
    if len(window) < len(slot_times):
        raise ValueError(f"The regulation has {len(slot_times)} slots but only {len(window)} flights "
                         f"arrive after the start of the regulation")
    return window, slot_times


def assign_slots(eta_min, has_priority, slot_times):
    """Give every flight a slot (one flight per slot) and return the start minute of each flight's slot.

    1. Flights with priority (the exempt ones), in ETA order, take the first free slot at or after
       their ETA, so they are delayed as little as possible.
    2. The remaining flights fill the free slots in ETA order.

    Args:
        eta_min: arrival time of each flight, sorted ascending.
        has_priority: True for the flights that pick their slot first.
        slot_times: start minute of each slot, sorted ascending (same length as eta_min).
    """
    if len(eta_min) != len(slot_times):
        raise ValueError("There must be exactly one slot per flight")
    taken = np.zeros(len(slot_times), dtype=bool)
    assigned = np.empty(len(eta_min), dtype=int)           # index of the slot given to each flight

    for flight in np.flatnonzero(has_priority):
        first_candidate = np.searchsorted(slot_times, eta_min[flight], side="left")
        free = np.flatnonzero(~taken[first_candidate:])
        if free.size == 0:
            raise ValueError(f"No free slot at or after minute {eta_min[flight]} for a priority flight")
        assigned[flight] = first_candidate + free[0]
        taken[assigned[flight]] = True

    assigned[~has_priority] = np.flatnonzero(~taken)
    return slot_times[assigned]


def run_gdp(flights, regulation_end, filing_minute=FILING_MINUTE, extension=FILING_EXTENSION_MIN,
            radius_km=EXEMPT_RADIUS_KM):
    """Run the GDP and return the schedule: one row per flight, sorted by slot.

    Steps:
      1. Build the slots and pick the flights that take part (slot_window).
      2. Give each flight a status: "unaffected" (arrives outside the regulation), "air" (exempt, can
         only be delayed in the air) or "ground" (can be held on the ground).
      3. Assign the slots (assign_slots): exempt flights have priority.
      4. Delay = slot - ETA (never negative). It counts as air delay or ground delay according to the status.

    Besides the columns of `flights`, the schedule has: status, slot, slot_end, delay, air_delay, ground_delay.
    """
    window, slot_times = slot_window(flights, regulation_end)
    eta = window["eta_min"]

    in_regulation = (eta >= REGULATION_START_MIN) & (eta < regulation_end)
    exempt = exempt_mask(window, filing_minute, extension, radius_km)
    status = np.where(~in_regulation, "unaffected", np.where(exempt, "air", "ground"))

    slot = assign_slots(eta.to_numpy(), status == "air", slot_times)
    slot_length = np.where(slot < REGULATION_END_MIN, 2, 1)          # only used to print the slot
    schedule = window.assign(status=status, slot=slot, slot_end=slot + slot_length)
    schedule["delay"] = (schedule["slot"] - schedule["eta_min"]).clip(lower=0)
    schedule["air_delay"] = schedule["delay"].where(schedule["status"] == "air", 0)
    schedule["ground_delay"] = schedule["delay"].where(schedule["status"] == "ground", 0)
    return schedule.sort_values(["slot", "arcid"]).reset_index(drop=True)


def unrecoverable_delay(schedule):
    """Ground delay minutes that fall before the regulation starts (the old code called them unrecoverable).

    A held flight waits on the ground from its ETD to ETD + delay. This counts the part of that wait
    that happens before the regulation starts.
    """
    minutes_before_start = (REGULATION_START_MIN - schedule["etd_min"]).clip(lower=0)
    return int(np.minimum(schedule["ground_delay"], minutes_before_start).sum())
