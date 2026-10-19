"""Cancel the flights with a very long delay and give their slots to flights that can use them earlier.

Replaces CancelledFlightsGDP.py (and the `cancelled` list that PrintSlotsGDP built).
"""
import numpy as np
import pandas as pd

CANCELLED_AIRLINE = "DLH"       # airline whose flights are cancelled in the study...
CANCELLATION_DELAY_MIN = 120    # ...when they are delayed more than this


def find_cancelled(schedule, airline=CANCELLED_AIRLINE, delay_limit=CANCELLATION_DELAY_MIN):
    """Positions (rows of the schedule) of the flights of `airline` delayed more than `delay_limit` minutes."""
    is_cancelled = (schedule["airline"] == airline) & (schedule["delay"] > delay_limit)
    return schedule.index[is_cancelled].tolist()


def _find_flight_for_slot(free_slot, holder, slot_start, eta, airline):
    """Row of the first later slot whose flight can use `free_slot`, or None.

    A flight can use the slot if it is ready by then (ETA at or before the slot start). Flights of
    the airline that owned the slot are tried first, then flights of any other airline.
    """
    for same_airline in (True, False):
        for later_slot in range(free_slot + 1, len(holder)):
            flight = holder[later_slot]
            if flight is None or eta[flight] > slot_start[free_slot]:
                continue
            if (airline[flight] == airline[free_slot]) == same_airline:
                return later_slot
    return None


def cancel_and_reassign(schedule, cancelled):
    """Cancel the flights in `cancelled` and fill the free slots with flights from later slots.

    Every move frees the slot the flight came from, so the search is repeated until nothing moves.

    Returns:
        after: one row per slot with the flight that finally uses it ("EMPTY" if none), its ETA,
               its delay and whether it was moved.
        summary: total delay before cancelling, before reassigning and after reassigning,
                 number of flights moved and list of the slots that stay empty.
    """
    cancelled = set(cancelled)
    slot_start = schedule["slot"].tolist()
    eta = schedule["eta_min"].tolist()
    airline = schedule["airline"].tolist()
    arcid = schedule["arcid"].tolist()

    # holder[slot] = row of the flight that sits in that slot (None = free slot)
    holder = [None if slot in cancelled else slot for slot in range(len(schedule))]
    moved = [False] * len(schedule)

    something_moved = True
    while something_moved:
        something_moved = False
        for free_slot in [slot for slot, flight in enumerate(holder) if flight is None]:
            later_slot = _find_flight_for_slot(free_slot, holder, slot_start, eta, airline)
            if later_slot is not None:
                holder[free_slot], holder[later_slot] = holder[later_slot], None
                moved[free_slot] = True
                moved[later_slot] = False      # that slot is free now, nobody sits there any more
                something_moved = True

    delay = [max(0, slot_start[slot] - eta[flight]) if flight is not None else np.nan
             for slot, flight in enumerate(holder)]
    after = pd.DataFrame({
        "slot": schedule["slot"],
        "slot_end": schedule["slot_end"],
        "arcid": [arcid[flight] if flight is not None else "EMPTY" for flight in holder],
        "eta_min": [eta[flight] if flight is not None else np.nan for flight in holder],
        "delay": delay,
        "moved": moved,
    })

    before_cancelling = int(schedule["delay"].sum())
    summary = {
        "before_cancelling": before_cancelling,
        "before_reassigning": before_cancelling - int(schedule.loc[list(cancelled), "delay"].sum()),
        "after_reassigning": int(np.nansum(delay)),
        "flights_moved": sum(moved),
        "empty_slots": [slot for slot, flight in enumerate(holder) if flight is None],
    }
    return after, summary
