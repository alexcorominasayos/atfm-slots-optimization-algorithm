"""Ground Holding Problem (GHP): choose the slot of every flight to minimise delay, emissions or cost.

Replaces GHP.py and GHP_reduced.py. The full schedule and the reduced one are the same problem
with a different set of flights, so there is a single solve_ghp().

The model: x[flight, slot] = 1 when the flight takes that slot.
  - every flight takes exactly one slot and every slot is taken by at most one flight;
  - no flight can take a slot before its ETA;
  - an exempt flight cannot take a slot that would delay it more than MAX_AIR_DELAY_MIN;
  - the objective adds up the cost of every chosen (flight, slot) pair.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import identity, kron

from config import MAX_AIR_DELAY_MIN
from gdp import exempt_mask
from models import delay_cost, delay_emissions_kg

MODES = ("delay", "emissions", "cost")   # what the GHP can minimise


def _delay_matrices(eta, slot_times, exempt):
    """Air and ground delay (minutes) of every flight in every slot: two (flights x slots) matrices.

    An exempt flight can only absorb delay in the air, and no more than MAX_AIR_DELAY_MIN of it.
    """
    delay = np.maximum(slot_times[None, :] - eta[:, None], 0)
    air = np.where(exempt[:, None], np.minimum(delay, MAX_AIR_DELAY_MIN), 0)
    ground = np.where(exempt[:, None], 0, delay)
    return air, ground


def _cost_matrix(flights, air, ground, mode):
    """What it costs to give every flight every slot, in the unit of the chosen objective."""
    if mode == "delay":
        return air + ground                                      # minutes

    def column(name):
        """One value per flight, shaped as a column so it combines with the (flights x slots) matrices."""
        return flights[name].to_numpy()[:, None]

    if mode == "emissions":
        air_kg, ground_kg = delay_emissions_kg(air, ground, column("co2_g_per_ask"), column("seats"),
                                               column("distance_km"), column("flight_min"))
        return air_kg + ground_kg                                # kg of CO2

    # mode == "cost" (EUR). delay_cost works on one flight at a time, so we loop over the pairs
    cost = np.empty(air.shape)
    flight_data = zip(flights["seats"], flights["distance_km"], flights["rotation_limit"])
    for i, (seats, distance, rotation_limit) in enumerate(flight_data):
        for j in range(air.shape[1]):
            cost[i, j] = sum(delay_cost(air[i, j], ground[i, j], seats, distance, rotation_limit))
    return cost


def _solve_assignment(cost, forbidden):
    """Cheapest assignment of flights to slots, never using a forbidden (flight, slot) pair.

    Returns the chosen slot of every flight and the value of the objective.
    """
    n_flights, n_slots = cost.shape
    each_flight_one_slot = kron(identity(n_flights), np.ones((1, n_slots)), format="csr")
    each_slot_at_most_one = kron(np.ones((1, n_flights)), identity(n_slots), format="csr")
    constraints = [LinearConstraint(each_flight_one_slot, 1, 1),
                   LinearConstraint(each_slot_at_most_one, 0, 1)]

    upper_bound = np.where(forbidden, 0, 1).ravel()              # a forbidden pair is fixed to 0
    result = milp(c=cost.ravel(), constraints=constraints, bounds=Bounds(0, upper_bound),
                  integrality=np.ones(cost.size))
    if not result.success:
        raise RuntimeError(f"The GHP optimisation failed: {result.message}")
    chosen_slot = result.x.reshape(cost.shape).argmax(axis=1)
    return chosen_slot, result.fun


def solve_ghp(flights, slot_times, mode):
    """Best slot of every flight when we minimise `mode`: "delay" (min), "emissions" (kg CO2) or "cost" (EUR).

    Args:
        flights: the flights to schedule; for the reduced schedule, only part of the regulation window.
        slot_times: start minute of every slot (see gdp.slot_window).
        mode: what to minimise.

    Returns:
        schedule: the columns of `flights` plus status ("air" for exempt flights, "ground" for the
                  rest), slot, delay, air_delay and ground_delay; sorted by slot.
        objective: value of the objective function.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode {mode!r}: use one of {MODES}")
    if len(flights) > len(slot_times):
        raise ValueError(f"{len(flights)} flights do not fit in {len(slot_times)} slots")

    eta = flights["eta_min"].to_numpy()
    exempt = exempt_mask(flights).to_numpy()
    air, ground = _delay_matrices(eta, slot_times, exempt)

    # Forbidden: a slot before the ETA, and (for exempt flights) a slot that delays them too much
    slot_delay = slot_times[None, :] - eta[:, None]
    forbidden = (slot_delay < 0) | (exempt[:, None] & (slot_delay > MAX_AIR_DELAY_MIN))
    has_no_slot = forbidden.all(axis=1)
    if has_no_slot.any():
        raise ValueError("No slot is allowed for these flights (they arrive after the last slot, or they are "
                         f"exempt and every slot would delay them too much): {flights.loc[has_no_slot, 'arcid'].tolist()}")

    chosen_slot, objective = _solve_assignment(_cost_matrix(flights, air, ground, mode), forbidden)

    schedule = flights.assign(status=np.where(exempt, "air", "ground"), slot=slot_times[chosen_slot])
    schedule["delay"] = schedule["slot"] - schedule["eta_min"]
    schedule["air_delay"] = schedule["delay"].where(schedule["status"] == "air", 0)
    schedule["ground_delay"] = schedule["delay"].where(schedule["status"] == "ground", 0)
    return schedule.sort_values(["slot", "arcid"]).reset_index(drop=True), objective
