# Delivery Resource Planner

A terminal-based system that plans daily deliveries across a limited fleet of vehicles and personnel, maximizing profit under capacity and deadline constraints.

## Problem

A delivery company receives a large number of orders every day but has a limited number of vehicles and delivery personnel available. Deciding manually which orders go on which vehicle leads to wasted capacity, unnecessary fuel cost, missed deadlines, and lost revenue.

This system takes the day's orders, vehicles, and personnel as input and produces a delivery plan that decides:
- which orders get accepted,
- which vehicle and driver each order is assigned to,
- and which orders have to be rejected because resources ran out — with a reason why.

The objective throughout is **profit**, not just "deliver as much as possible" — every order has a revenue and every trip has a cost, and the plan is built to maximize revenue minus cost, not order count.

## Features

- Add orders, vehicles, and delivery personnel through a simple numbered menu
- Vehicles and personnel are paired up automatically when a plan is generated — no manual driver-vehicle assignment
- Orders are ranked by priority (Express before Standard), profit per kg, deadline urgency, and entry order, in that order
- Orders are only assigned to a vehicle if they fit its remaining capacity **and** can be delivered before the deadline
- Once orders are assigned, routes are re-checked at the vehicle level — if a vehicle's total trip cost would exceed the revenue of everything on it, the least profitable order on that route is dropped until the route is profitable again
- Full input validation (no negative, zero, or non-numeric values; no duplicate IDs)
- Handles edge cases gracefully: zero orders, zero vehicles, zero personnel, more vehicles than drivers (or vice versa), ties, and large order volumes
- Final report shows per-vehicle assignments, rejected orders with reasons, idle vehicles/personnel, total revenue, total cost, and net profit

## How it works

1. **Orders, vehicles, and personnel are entered** through the menu and validated on the way in.
2. **Generate Daily Delivery Plan** does the following, in order:
   - Pairs each vehicle with an available driver (sorted by ID, paired one-to-one; leftovers on either side are marked idle).
   - Ranks all pending orders by priority → profit-per-kg → deadline urgency → entry order.
   - Walks the ranked list and assigns each order to the first paired vehicle that has enough remaining capacity and can make the delivery before the deadline. Orders that don't fit anywhere are rejected.
   - Re-checks every vehicle's route: if the total trip cost exceeds the revenue of what's loaded on it, the lowest-revenue order on that route is dropped (and marked rejected) until the route is profitable, or the vehicle ends up empty.
3. **The report** lays out exactly what got delivered, by whom, what got turned away and why, and the resulting profit.

Delivery time is estimated from distance and a fixed average speed per vehicle type (Bike 30 km/h, Van 25 km/h, Truck 20 km/h). Trip cost is the vehicle's cost-per-km multiplied by the total distance of everything assigned to it.

## Sample output

```
========================================
  DELIVERY PLAN - SUMMARY
========================================
Vehicle V1 (Van, driver: Rohit)
  -> Order O3 (Express, 12kg, Rs450)
  -> Order O7 (Standard, 8kg, Rs200)
  Total load: 20/25 kg | Trip cost: Rs180.00

Vehicle V2 (Bike, driver: Anu)
  -> Order O1 (Express, 3kg, Rs150)
  Total load: 3/5 kg | Trip cost: Rs40.00

----------------------------------------
Orders Rejected (insufficient capacity/time/profit):
  O9 (Standard, 30kg) -- no vehicle had capacity/time
  O12 (Express, 2kg) -- unprofitable at route level

----------------------------------------
Total Revenue     : Rs800.00
Total Cost        : Rs220.00
NET PROFIT        : Rs580.00
Orders Completed  : 3 / 5
========================================
```

## Project structure

```
delivery-resource-planner/
├── main.py     # Menu loop — the entry point you run
├── logic.py    # Entities, input collection/validation, and all planning logic
├── test.py     # Unit tests covering the PRD's test cases
└── README.md
```

`main.py` only displays the menu and dispatches the user's choice — it has no business logic of its own. The planning functions that matter for grading (`rank_orders`, `allocate_orders`, `check_route_profitability`, `trip_cost`, `delivery_time`, `generate_plan`) are pure: they take plain Order/Vehicle/Personnel objects and return results, with no `input()`/`print()` inside them, which is what lets `test.py` call them directly without simulating a terminal session. The `add_*` and `view_all` functions in `logic.py` do their own prompting and printing, since that's where the input validation loops live.

## Getting started

Requires Python 3.8+. No external dependencies.

```bash
git clone https://github.com/<your-username>/delivery-resource-planner.git
cd delivery-resource-planner
python3 main.py
```

### Running the tests

```bash
python3 -m unittest test.py -v
```

## Menu options

```
1. Add Order                    - ID, distance (km), weight (kg), priority, deadline (hr), revenue
2. View All Orders              - lists all orders, vehicles, and personnel entered so far
3. Add Vehicle                  - ID, type (Bike/Van/Truck), max capacity (kg), cost per km
4. Add Delivery Personnel       - ID and name only (vehicle is assigned automatically)
5. Generate Daily Delivery Plan - runs the allocation and prints the plan
6. View Last Plan / Report      - reprints the most recently generated plan
7. Exit
```

## Design decisions worth knowing

- **Priority always outranks profit-per-kg.** Order ranking is a strict hierarchy (priority → profit/kg → deadline → entry order), not a weighted score — an Express order is always considered before a Standard one for a given slot, even if the Standard order is more profitable per kg.
- **Profitability is checked at the route level, not just per order.** An order can individually look fine (fits capacity, meets its deadline) but still get dropped if adding it tips the whole vehicle's trip into a loss.
- **Ties are broken deterministically** by whichever order was entered first, so results are reproducible across runs on the same input.
- **The allocation uses a fast, rule-based approach**, not a guaranteed-optimal solver — true optimal bin-packing across vehicles is NP-hard, so this favors a quick, deterministic, good-enough plan over an exhaustive search.

## Team

- Shafreen
- Abhishek
- Shahibha

Atria University, Bengaluru
