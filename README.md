# Ground Delay Program at Munich airport (EDDM)

Python code to study a Ground Delay Program (GDP) at Munich airport (EDDM) on 10 August 2025. The arrival
capacity drops from 60 to 20 flights per hour between 05:00 and 13:00. The code assigns slots to the
arriving flights and measures the delay, CO₂ emissions and cost this causes. It then improves the
schedule with a Ground Holding Problem (GHP) and repeats the study after replacing short flights by
high-speed trains.

## What it does

- **GDP:** builds the slots, gives every flight a slot (exempt flights first), splits the delay into
  air and ground delay and computes the unrecoverable delay. It can also cancel the flights with a very
  long delay and reuse their slots.
- **Emissions and cost:** one shared model gives the fuel, CO₂ and delay cost of any schedule.
- **GHP:** a mixed-integer linear program that chooses the slots to minimise the total delay, the CO₂ of
  the delay or the cost.
- **Train substitution:** finds the flights a train could replace and compares delay, emissions, cost and
  door-to-door time with and without them.
- **Sweep:** runs the GDP for every filing time and exemption radius and draws three 3D surfaces.

## Project structure

```
.
├── Data/
│   ├── EDDM_10AUG2025.csv         arrivals of the day (input)
│   ├── fleet_cat_seat.csv         aircraft type -> category and seats (input)
│   └── EDDM_reduced_demand.csv    written by substitute_flights.py
├── Scripts/                       see the two tables below
├── README.md
├── requirements.txt
└── .gitignore
```

**Scripts you run** (always from the `Scripts` folder):

| Script | What it does |
|---|---|
| `substitute_flights.py` | Finds the flights a train could replace and saves the demand that remains |
| `run_gdp.py` | GDP: delays, emissions, cost, cancellations and plots |
| `run_ghp.py` | GHP of the full and the reduced schedule for the three objectives |
| `compare_delay_reduction.py` | Delay saved by the train, estimated in two ways |
| `compare_train_air.py` | CO₂ and door-to-door time, train against flight |
| `plot_hfile_vs_radius.py` | Sweep of filing time and exemption radius (about two minutes) |

**Modules they use:**

| Module | What it contains |
|---|---|
| `config.py` | Every constant and file path |
| `utils.py` | Conversion between clock times and minutes |
| `fleet.py` | Fleet table: aircraft type -> category and seats |
| `flight_data.py` | Loads the arrivals and builds the `flights` table (one row per flight) |
| `regulation.py` | Demand against capacity: when does the delay end? |
| `gdp.py` | Slots, exempt flights, slot assignment, unrecoverable delay |
| `cancellations.py` | Cancels long-delayed flights and reuses their slots |
| `models.py` | Emission and cost formulas, written once |
| `ghp.py` | The optimisation of the GHP |
| `train.py` | Airports with a train connection and the reduced demand |
| `reports.py`, `plots.py` | Everything that prints or draws |
| `emissions_fuel_model.py` | Fuel, CO₂ and other emissions per seat-km (calculations as provided) |
| `example_fuel_use.py` | Example of use: fuel and CO₂ of the whole day (calculations as provided) |

`python example_fuel_use.py` prints the fuel and CO₂ of all the flights of the day.

## Installation

Python 3.12 was used for development. In a terminal, inside the project folder:

```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS and Linux
pip install -r requirements.txt
```

## Data

All the input files go in `Data/`, next to `Scripts/`.

- **`EDDM_10AUG2025.csv`**: separated by `;`, with a header row. The code reads these columns by position:
  0 flight id (ARCID), 1 aircraft type, 2 departure airport, 3 arrival airport, 4 aircraft identifier
  (RM, used to link the flights of the same aircraft), 6 departure time (`HH:MM:SS`), 7 taxi time
  (minutes) and 8 arrival time (`HH:MM:SS`). Only the flights arriving at EDDM are used.
- **`fleet_cat_seat.csv`**: separated by `,`, with a header row. Columns by position: 1 aircraft type,
  2 category (A to F) and 3 number of seats. Every aircraft type of the arrivals file must be listed.
- **`EDDM_reduced_demand.csv`**: created by `substitute_flights.py` with the columns `ARCID`, `ADEP`, `ADES`
  and `ETAmin`. It holds the flights that stay when the train replaces the others.

## How to run

```
cd Scripts
python substitute_flights.py        # first: creates Data/EDDM_reduced_demand.csv
python run_gdp.py
python run_ghp.py                   # needs the reduced demand
python compare_delay_reduction.py   # needs the reduced demand
python compare_train_air.py
python plot_hfile_vs_radius.py
```

The switches at the top of `run_gdp.py`, `run_ghp.py` and `compare_train_air.py` (`SHOW_...`) choose how
much is printed. Times are in minutes, emissions in kg and costs in euros.

## How it works

1. **Demand against capacity** (`regulation.py`). The cumulative arrivals are compared with the cumulative
   capacity: 20 flights per hour until 13:00, then 60. The minute when the capacity line catches the demand
   again is the end of the delay, and the area between both curves is the total delay.
2. **Slots** (`gdp.py`). One slot every 3 minutes while the capacity is reduced, then two slots every two
   minutes until the delay ends. There is one slot per flight: the first flights arriving from 05:00, in
   order of arrival.
3. **Exempt flights.** A flight is exempt if it departs before 04:00 (filing time 03:30 plus 30 minutes),
   departs from outside ECAC or comes from further than 2,000 km. Exempt flights are delayed in the air and
   choose first: each takes the earliest free slot at or after its ETA. The rest fill the free slots in
   order of arrival and are delayed on the ground. Flights that arrive outside the regulation are unaffected.
4. **Emissions and cost** (`models.py`). CO₂ and fuel per seat-km come from `emissions_fuel_model.py`. A
   minute of air delay counts as one more minute flown at the average speed of the flight, and a minute of
   ground delay counts 33 % of that. The delay cost adds the operating cost (higher when the delay breaks the
   rotation of the aircraft), the EU261 compensation from three hours of delay and the passengers who miss a
   connection.
5. **GHP** (`ghp.py`). Each flight gets exactly one slot at or after its ETA, each slot is used at most
   once and an exempt flight cannot be delayed more than 30 minutes. The objective is the total delay, the CO₂
   of the delay or the cost. It is solved with `scipy.optimize.milp`.
6. **Train substitution** (`train.py`). The flights that arrive during the regulation from twelve airports with
   a train connection (Berlin, Vienna, Zurich, Basel, Linz, Prague, Frankfurt, Winterthur, Stuttgart,
   Dusseldorf, Salzburg and Strasbourg) are removed, and everything is evaluated again.

## Configuration

Every parameter is in `Scripts/config.py`: the capacities, the regulation window, the filing time, the exemption
radius, the maximum air delay, the emission factor of the ground delay and all the constants of the cost
model. Change them there and run the scripts again.

## Contributors

* **Àlex Coromina Sayós** - [@alexcorominasayos](https://github.com/alexcorominasayos)
* **Jan Rosés Puigdomènech** [@janrosesupc](https://github.com/janrosesupc)
* **Jordán Frank Soto Huarcaya** - [@jordanfranksoto-netizen](https://github.com/jordanfranksoto-netizen)

## License

**MIT**