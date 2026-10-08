# Delivery Resource Planning System

A terminal-based Python application that plans a delivery company's day. You enter orders, vehicles and delivery personnel; the system prices each order automatically, pairs drivers with vehicles, decides which vehicle carries which order, and prints a plan with revenue, cost and net profit.

It is built for an e-commerce delivery business that works like a porter service: customers are charged by **weight and distance**, and every trip has a running cost per km.

- Pure Python 3, no external dependencies
- Menu-driven command-line interface
- Greedy planning algorithm that stays fast with hundreds of orders
- Unit tests covering the PRD's test cases and the pricing rules

---

## Table of contents

1. [Features](#features)
2. [Project structure](#project-structure)
3. [Getting started](#getting-started)
4. [How to use it](#how-to-use-it)
5. [Business rules](#business-rules)
6. [How the planner works](#how-the-planner-works)
7. [Sample session](#sample-session)
8. [Running the tests](#running-the-tests)
9. [Known limitations](#known-limitations)
10. [Documentation](#documentation)
11. [Team](#team)

---

## Features

- **Automatic pricing.** Revenue is calculated from weight and distance. Nobody types a price.
- **Built-in vehicles.** Capacity and per-km rates are fixed by vehicle type (Bike, Van, Truck).
- **Order acceptance rules.** Orders under Rs100 revenue, under 200 m distance, or over 200 kg are refused at entry.
- **Priority handling.** Express orders are planned before Standard ones. Within the same priority, the order that pays more goes first.
- **Cheapest vehicle wins.** Each order goes to the lowest-cost vehicle that can carry it on time. Exact ties go to the first delivery person in the list.
- **Automatic driver pairing.** Vehicles and personnel are paired in ID order. Leftovers are reported as idle.
- **Profit safeguard.** Orders that lose money on their vehicle are dropped from the route and reported with a reason.
- **Clear report.** Per-vehicle load and cost, rejected orders with reasons, idle resources, and totals.
- **Input validation.** Non-numeric, zero and negative values re-prompt. Duplicate IDs are refused.

---

## Project structure

```
.
├── main.py      # Menu loop (user interface)
├── logic.py     # Entities, pricing, validation, planning, and report building
├── test.py      # Unit tests (unittest)
├── Delivery_Resource_Planning_System_PRD.pdf
├── Delivery_Resource_Planning_System_Design_Doc.pdf
└── README.md
```

| File | Role |
|---|---|
| `main.py` | Shows the menu, reads the choice, and calls the right function in `logic.py`. Holds the lists of orders, vehicles and personnel in memory. |
| `logic.py` | Everything else: the `Order`, `Vehicle` and `Personnel` classes, input helpers, `add_*` and `view_all`, pairing, ranking, allocation, route profitability, `generate_plan` and `build_report`. |
| `test.py` | Tests for input handling, pricing, the planning logic and the pure helper functions. |

---

## Getting started

**Requirements:** Python 3.8 or newer. No packages to install.

```bash
git clone <your-repo-url>
cd <your-repo-folder>
python main.py
```

On some systems the command is `python3 main.py`.

---

## How to use it

The program starts at this menu:

```
========================================
  DELIVERY RESOURCE PLANNING SYSTEM
========================================
1. Add Order
2. View All Orders
3. Add Vehicle
4. Add Delivery Personnel
5. Generate Daily Delivery Plan
6. View Last Plan / Report
7. Exit
----------------------------------------
```

A normal run looks like this:

1. **Add vehicles** (option 3). You enter an ID and a type. Capacity and rates are filled in for you.
2. **Add delivery personnel** (option 4). You enter an ID and a name.
3. **Add orders** (option 1). You enter ID, distance, weight, priority and deadline. The system prints the revenue it calculated, or tells you why the order was refused.
4. **Review** everything with option 2.
5. **Generate the plan** with option 5. Use option 6 to see the last plan again.

Order fields:

| Prompt | Meaning |
|---|---|
| Order ID | Unique text, for example `O1` |
| Distance (km) | Pickup to drop. Decimals allowed (`0.5` = 500 m) |
| Weight (kg) | Parcel weight |
| Priority | `1` Express, `2` Standard |
| Deadline (hours from now) | Latest acceptable delivery time |

---

## Business rules

All values below are fixed in `logic.py`.

### Vehicles

| Type | Max capacity | Average speed |
|---|---|---|
| Bike | 15 kg | 30 km/h |
| Van | 65 kg | 25 km/h |
| Truck | 200 kg | 20 km/h |

### Per-km rate (Rs per km)

| Priority | Bike | Van | Truck |
|---|---|---|---|
| Standard | 30 | 55 | 70 |
| Express | 55 | 80 | 95 |

This table is used twice:

- as the **running cost** of a trip, based on the vehicle that actually carries the order and the order's priority
- as the **per-km part of the customer charge**, based on the order's priority and its vehicle class

### Revenue

```
revenue = (weight_kg x 20) + (distance_km x per-km rate)
```

The per-km rate uses the order's **vehicle class**, which is the smallest vehicle that can carry its weight: up to 15 kg is Bike, up to 65 kg is Van, up to 200 kg is Truck.

Example: a 5 km, 10 kg Standard order is Bike class, so revenue = 10 x 20 + 5 x 30 = **Rs350**.

Because the running cost uses the same per-km rates, an order carried by a vehicle of its own class earns exactly its per-kg charge as profit (here 10 kg x Rs20 = Rs200). If a bigger vehicle has to carry it, the cost is higher and the profit shrinks, or turns into a loss.

### Orders that are refused

An order is refused, and not stored, when:

| Rule | Condition |
|---|---|
| Minimum revenue | Calculated revenue is under Rs100 |
| Minimum distance | Distance is under 200 m (0.2 km) |
| Maximum weight | Weight is over 200 kg |

Exactly Rs100 and exactly 0.2 km are accepted.

### Delivery time and trip cost

```
delivery time = distance_km / vehicle speed
trip cost     = sum of (order distance x vehicle's per-km rate for that order's priority)
net profit    = total revenue - total trip cost
```

An order can go on a vehicle only if its weight fits the remaining capacity (`<=`) and its delivery time is within the deadline (`<=`).

---

## How the planner works

When you choose **Generate Daily Delivery Plan**, the system runs these steps (`generate_plan` in `logic.py`):

1. **Edge checks.** No orders gives "No orders to plan". No vehicles or no personnel rejects every pending order with a reason.
2. **Pair vehicles with personnel.** Both lists are sorted by ID and paired one to one. Extra vehicles or people are reported as idle.
3. **Rank the pending orders** by:
   1. Priority (Express first)
   2. Revenue (higher first)
   3. Profit per kg (higher first)
   4. Deadline (smaller first)
   5. Entry order (earlier first)
4. **Allocate.** For each order in rank order, find every vehicle with enough remaining capacity and enough speed to meet the deadline. Pick the one with the lowest cost to carry the order. If costs tie exactly, pick the first pair in the list, which is the first delivery person. If nobody fits, reject the order with the reason "no vehicle had capacity/time".
5. **Check route profitability.** For each vehicle, while the trip cost is more than the route's revenue, remove the order that loses the most money and reject it as "unprofitable at route level".
6. **Report.** Per-vehicle orders, load and cost, idle vehicles and personnel, rejected orders with reasons, and the totals.

The approach is greedy rather than an exact solver. Optimal packing of orders into vehicles is NP-hard, and the greedy ranking stays quick even with 500+ orders.

---

## Sample session

Setup: one Van (V1) with driver Rohit, one Bike (V2) with driver Anu, then two orders.

```
Choose an option: 1
Order ID: O1
Distance (km): 5
Weight (kg): 3
Priority (1. Express  2. Standard): 1
Deadline (hours from now): 2
Order O1 added. Calculated revenue: Rs335.00

Choose an option: 1
Order ID: O2
Distance (km): 1
Weight (kg): 3
Priority (1. Express  2. Standard): 2
Deadline (hours from now): 2
Order not accepted: calculated revenue Rs90.00 is below the Rs100 minimum.
```

Generating the plan gives:

```
========================================
  DELIVERY PLAN - SUMMARY
========================================
Vehicle V1 (Van, driver: Rohit) -- IDLE (no compatible orders)

Vehicle V2 (Bike, driver: Anu)
  -> Order O1 (Express, 3.0kg, Rs335.0)
  Total load: 3.0/15 kg | Trip cost: Rs275.00

----------------------------------------
Orders Rejected (insufficient capacity/time/profit):
  None
----------------------------------------
Total Revenue     : Rs335.00
Total Cost        : Rs275.00
NET PROFIT        : Rs60.00
Orders Completed  : 1 / 1
========================================
```

O1 went on the Bike because it was the cheaper vehicle that could carry it (Rs55/km Express on a Bike versus Rs80/km on a Van). The Van stayed idle because nothing was left for it. The Rs60 profit equals the per-kg charge (3 kg x Rs20), which is what a Bike-class order earns on a Bike.

---

## Running the tests

```bash
python test.py
```

or with verbose output:

```bash
python -m unittest test -v
```

The suite (38 tests) covers:

- input validation: negative, zero, non-numeric and duplicate values
- the new acceptance rules: minimum revenue, minimum distance, maximum weight, and their exact boundaries
- revenue calculation and the built-in capacity and rate tables
- capacity and deadline boundaries (`<=`)
- profit-based rejection and the route-level check
- ordering: Express before Standard, higher payer first, tie-break by entry order
- vehicle choice: cheapest vehicle, and the first delivery person on an exact cost tie
- pairing, idle reasons, and a 500-order stress test

---

## Known limitations

- **Data is kept in memory only.** Closing the program loses all orders, vehicles and personnel.
- **Generating the plan twice does not work as expected.** After the first run, orders are marked Assigned or Rejected. A second run only looks at Pending orders, so it produces an empty plan. Restart the program, or re-enter the orders, to plan again.
- **Greedy, not optimal.** The plan is good and fast, not guaranteed to be the maximum possible profit.
- **One trip per vehicle per day.** There is no multi-trip scheduling or route ordering. Trip cost is based on summed order distances.
- **No editing or deleting.** Entered records cannot be changed from the menu.
- **Priority beats revenue.** An Express order always takes space before a Standard order, even if the Standard order pays more.

---

## Documentation

- **Product Requirements Document:** `Delivery_Resource_Planning_System_PRD.pdf` covers the problem, interface, business rules, functional requirements, test cases and edge cases.
- **Design Document:** `Delivery_Resource_Planning_System_Design_Doc.pdf` covers the formulae, ranking and selection rules, function signatures and the algorithm for each function.

---

## Team

- Shafreen
- Abhishek
- Shahiba
