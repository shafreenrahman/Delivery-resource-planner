"""
logic.py
Core entities and business logic for the Delivery Resource Planning System.
No terminal I/O here except the small read_* input helpers used by add_*.
"""

SPEED_BY_TYPE = {"Bike": 30, "Van": 25, "Truck": 20}  # km/h
TYPE_BY_CHOICE = {"1": "Bike", "2": "Van", "3": "Truck"}
PRIORITY_BY_CHOICE = {"1": "Express", "2": "Standard"}

# Change 6: vehicle capacity is built in (kg), not entered by the user.
CAPACITY_BY_TYPE = {"Bike": 15, "Van": 65, "Truck": 200}

# Built-in per-km rate (Rs/km), by order priority and vehicle type. This is the
# cost of running the trip and also the per-km part of the customer's charge.
RATE_BY_PRIORITY_AND_TYPE = {
    "Standard": {"Bike": 30, "Van": 55, "Truck": 70},
    "Express":  {"Bike": 55, "Van": 80, "Truck": 95},
}

# Per-kg charge billed to the customer (Rs/kg).
REVENUE_PER_KG = 20

# Change 1 and 4: order acceptance rules.
MIN_REVENUE = 100        # Rs
MIN_DISTANCE_KM = 0.2    # 200 m


def vehicle_class_for_weight(weight_kg):
    """Smallest vehicle type that can carry the weight, or None if too heavy."""
    for vtype in ("Bike", "Van", "Truck"):
        if weight_kg <= CAPACITY_BY_TYPE[vtype]:
            return vtype
    return None


def calculate_revenue(distance_km, weight_kg, priority):
    """Revenue = (weight x Rs20/kg) + (distance x per-km rate), where the per-km
    rate uses the order's priority and the smallest vehicle class that can
    carry its weight."""
    vtype = vehicle_class_for_weight(weight_kg)
    per_kg_part = weight_kg * REVENUE_PER_KG
    per_km_part = distance_km * RATE_BY_PRIORITY_AND_TYPE[priority][vtype]
    return per_kg_part + per_km_part


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class Order:
    def __init__(self, order_id, distance_km, weight_kg, priority, deadline_hr, revenue):
        self.order_id = order_id
        self.distance_km = distance_km
        self.weight_kg = weight_kg
        self.priority = priority          # "Express" or "Standard"
        self.deadline_hr = deadline_hr
        self.revenue = revenue
        self.status = "Pending"           # Pending / Assigned / Rejected
        self.reject_reason = None
        self.assigned_vehicle_id = None

    def profit_per_kg(self):
        return self.revenue / self.weight_kg


class Vehicle:
    def __init__(self, vehicle_id, vtype):
        self.vehicle_id = vehicle_id
        self.type = vtype                 # "Bike" / "Van" / "Truck"
        self.max_capacity_kg = CAPACITY_BY_TYPE[vtype]
        self.remaining_capacity = self.max_capacity_kg
        self.assigned_orders = []

    def rate_for(self, priority):
        """Built-in Rs/km for this vehicle type and the given order priority."""
        return RATE_BY_PRIORITY_AND_TYPE[priority][self.type]

    def cost_of(self, order):
        """Running cost this vehicle incurs to carry one order."""
        return order.distance_km * self.rate_for(order.priority)


class Personnel:
    def __init__(self, personnel_id, name):
        self.personnel_id = personnel_id
        self.name = name


# ---------------------------------------------------------------------------
# Input helpers (FR9, TC2/TC17/TC18/TC20)
# ---------------------------------------------------------------------------

def read_positive_number(prompt):
    while True:
        raw = input(prompt)
        try:
            num = float(raw)
        except ValueError:
            print("Invalid value, must be greater than 0.")
            continue
        if num <= 0:
            print("Invalid value, must be greater than 0.")
            continue
        return num


def read_choice(prompt, valid):
    while True:
        raw = input(prompt).strip()
        if raw not in valid:
            print("Invalid option.")
            continue
        return raw


def read_unique_id(prompt, existing):
    while True:
        raw = input(prompt).strip()
        if raw in existing:
            print("ID already exists.")
            continue
        return raw


# ---------------------------------------------------------------------------
# Add / view (FR1-FR3, FR10)
# ---------------------------------------------------------------------------

def add_order(orders):
    """Returns the new Order, or None if the order was not accepted.
    Revenue is calculated here, not entered by the user."""
    order_id = read_unique_id("Order ID: ", [o.order_id for o in orders])
    distance = read_positive_number("Distance (km): ")

    # Pickup-to-drop distance under 200 m is not accepted.
    if distance < MIN_DISTANCE_KM:
        print(f"Order not accepted: distance must be at least 200 m ({MIN_DISTANCE_KM} km).")
        return None

    weight = read_positive_number("Weight (kg): ")
    if vehicle_class_for_weight(weight) is None:
        print(f"Order not accepted: weight exceeds the largest vehicle ({CAPACITY_BY_TYPE['Truck']} kg).")
        return None

    priority_choice = read_choice("Priority (1. Express  2. Standard): ", ["1", "2"])
    priority = PRIORITY_BY_CHOICE[priority_choice]
    deadline = read_positive_number("Deadline (hours from now): ")

    revenue = calculate_revenue(distance, weight, priority)

    # Revenue below Rs100 is not accepted.
    if revenue < MIN_REVENUE:
        print(f"Order not accepted: calculated revenue Rs{revenue:.2f} is below the Rs{MIN_REVENUE} minimum.")
        return None

    order = Order(order_id, distance, weight, priority, deadline, revenue)
    orders.append(order)
    print(f"Order {order_id} added. Calculated revenue: Rs{revenue:.2f}")
    return order


def add_vehicle(vehicles):
    # Capacity and cost per km are built in, so only ID and type are asked.
    vehicle_id = read_unique_id("Vehicle ID: ", [v.vehicle_id for v in vehicles])
    type_choice = read_choice("Type (1. Bike  2. Van  3. Truck): ", ["1", "2", "3"])
    vehicle = Vehicle(vehicle_id, TYPE_BY_CHOICE[type_choice])
    vehicles.append(vehicle)
    print(f"Vehicle {vehicle_id} added ({vehicle.type}, capacity {vehicle.max_capacity_kg}kg).")
    return vehicle


def add_personnel(personnel):
    personnel_id = read_unique_id("Personnel ID: ", [p.personnel_id for p in personnel])
    name = input("Name: ").strip()
    person = Personnel(personnel_id, name)
    personnel.append(person)
    print(f"Personnel {personnel_id} added.")
    return person


def view_all(orders, vehicles, personnel):
    print("\n-- Orders --")
    if not orders:
        print("No orders added yet.")
    for o in orders:
        print(f"  {o.order_id}: {o.priority}, {o.weight_kg}kg, {o.distance_km}km, "
              f"deadline {o.deadline_hr}hr, Rs{o.revenue:.2f}, status={o.status}")

    print("\n-- Vehicles --")
    if not vehicles:
        print("No vehicles added yet.")
    for v in vehicles:
        print(f"  {v.vehicle_id}: {v.type}, capacity {v.max_capacity_kg}kg, "
              f"Rs{v.rate_for('Standard')}/km standard, Rs{v.rate_for('Express')}/km express")

    print("\n-- Personnel --")
    if not personnel:
        print("No personnel added yet.")
    for p in personnel:
        print(f"  {p.personnel_id}: {p.name}")
    print()


# ---------------------------------------------------------------------------
# Planning logic (FR4-FR8)
# ---------------------------------------------------------------------------

def pair_vehicles_personnel(vehicles, personnel):
    sorted_vehicles = sorted(vehicles, key=lambda v: v.vehicle_id)
    sorted_personnel = sorted(personnel, key=lambda p: p.personnel_id)
    n = min(len(sorted_vehicles), len(sorted_personnel))
    pairs = list(zip(sorted_vehicles[:n], sorted_personnel[:n]))
    idle_vehicles = sorted_vehicles[n:]
    idle_personnel = sorted_personnel[n:]
    return pairs, idle_vehicles, idle_personnel


def rank_orders(orders):
    """Change 2: Express first, then the order that pays more, then profit/kg,
    deadline urgency, and finally entry order."""
    pending = [o for o in orders if o.status == "Pending"]
    indexed = list(enumerate(pending))

    def key(item):
        idx, o = item
        priority_rank = 0 if o.priority == "Express" else 1
        return (priority_rank, -o.revenue, -o.profit_per_kg(), o.deadline_hr, idx)

    indexed.sort(key=key)
    return [o for _, o in indexed]


def delivery_time(order, vehicle):
    speed = SPEED_BY_TYPE[vehicle.type]
    return order.distance_km / speed


def trip_cost(vehicle, assigned_orders):
    return sum(vehicle.cost_of(o) for o in assigned_orders)


def allocate_orders(ranked_orders, paired_vehicles):
    for vehicle, _driver in paired_vehicles:
        vehicle.remaining_capacity = vehicle.max_capacity_kg
        vehicle.assigned_orders = []

    rejected = []
    for order in ranked_orders:
        # Every vehicle that can take this order (capacity + deadline).
        candidates = []
        for pair_idx, (vehicle, _driver) in enumerate(paired_vehicles):
            if order.weight_kg <= vehicle.remaining_capacity and \
                    delivery_time(order, vehicle) <= order.deadline_hr:
                candidates.append((vehicle.cost_of(order), pair_idx, vehicle))

        if candidates:
            # Change 3: cheapest vehicle wins; on an exact cost tie the
            # earliest pair (i.e. the first delivery person in the list) wins.
            _cost, _idx, vehicle = min(candidates, key=lambda c: (c[0], c[1]))
            vehicle.assigned_orders.append(order)
            vehicle.remaining_capacity -= order.weight_kg
            order.status = "Assigned"
            order.assigned_vehicle_id = vehicle.vehicle_id
        else:
            order.status = "Rejected"
            order.reject_reason = "no vehicle had capacity/time"
            rejected.append(order)

    return {"pairs": paired_vehicles, "rejected": rejected}


def check_route_profitability(plan):
    for vehicle, _driver in plan["pairs"]:
        while vehicle.assigned_orders:
            cost = trip_cost(vehicle, vehicle.assigned_orders)
            revenue = sum(o.revenue for o in vehicle.assigned_orders)
            if cost <= revenue:
                break
            # drop the order that loses the most money on this vehicle
            worst = min(vehicle.assigned_orders, key=lambda o: o.revenue - vehicle.cost_of(o))
            vehicle.assigned_orders.remove(worst)
            worst.status = "Rejected"
            worst.reject_reason = "unprofitable at route level"
            worst.assigned_vehicle_id = None
            plan["rejected"].append(worst)
    return plan


def generate_plan(orders, vehicles, personnel):
    """Ties everything together per Program Flow step 5. Returns a plan dict
    consumed by build_report."""
    if not orders:
        return {"empty_message": "No orders to plan", "orders": orders}

    if not vehicles:
        for o in orders:
            if o.status == "Pending":
                o.status = "Rejected"
                o.reject_reason = "no vehicles available"
        return {"pairs": [], "idle_vehicles": [], "idle_personnel": [],
                "rejected": [o for o in orders if o.status == "Rejected"],
                "orders": orders, "empty_reason": {}}

    if not personnel:
        for o in orders:
            if o.status == "Pending":
                o.status = "Rejected"
                o.reject_reason = "no personnel available"
        return {"pairs": [], "idle_vehicles": vehicles, "idle_personnel": [],
                "rejected": [o for o in orders if o.status == "Rejected"],
                "orders": orders, "empty_reason": {}}

    pairs, idle_vehicles, idle_personnel = pair_vehicles_personnel(vehicles, personnel)
    ranked = rank_orders(orders)
    plan = allocate_orders(ranked, pairs)

    empty_after_allocate = {v.vehicle_id for v, _d in pairs if not v.assigned_orders}
    plan = check_route_profitability(plan)

    empty_reason = {}
    for v, _d in pairs:
        if not v.assigned_orders:
            if v.vehicle_id in empty_after_allocate:
                empty_reason[v.vehicle_id] = "no compatible orders"
            else:
                empty_reason[v.vehicle_id] = "no profitable orders"

    plan["idle_vehicles"] = idle_vehicles
    plan["idle_personnel"] = idle_personnel
    plan["empty_reason"] = empty_reason
    plan["orders"] = orders
    return plan


def build_report(plan):
    if "empty_message" in plan:
        return plan["empty_message"]

    lines = []
    line = "=" * 40
    lines.append(line)
    lines.append("  DELIVERY PLAN - SUMMARY")
    lines.append(line)

    total_revenue = 0.0
    total_cost = 0.0
    completed = 0

    for vehicle, driver in plan["pairs"]:
        if vehicle.assigned_orders:
            lines.append(f"Vehicle {vehicle.vehicle_id} ({vehicle.type}, driver: {driver.name})")
            load = 0
            for o in vehicle.assigned_orders:
                lines.append(f"  -> Order {o.order_id} ({o.priority}, {o.weight_kg}kg, Rs{o.revenue})")
                load += o.weight_kg
                completed += 1
            cost = trip_cost(vehicle, vehicle.assigned_orders)
            revenue = sum(o.revenue for o in vehicle.assigned_orders)
            total_revenue += revenue
            total_cost += cost
            lines.append(f"  Total load: {load}/{vehicle.max_capacity_kg} kg | Trip cost: Rs{cost:.2f}")
        else:
            reason = plan["empty_reason"].get(vehicle.vehicle_id, "no compatible orders")
            lines.append(f"Vehicle {vehicle.vehicle_id} ({vehicle.type}, driver: {driver.name}) "
                         f"-- IDLE ({reason})")
        lines.append("")

    for v in plan.get("idle_vehicles", []):
        lines.append(f"Vehicle {v.vehicle_id} ({v.type}) -- IDLE (no personnel available)")
    for p in plan.get("idle_personnel", []):
        lines.append(f"Personnel {p.personnel_id} ({p.name}) -- IDLE (no vehicle available)")

    lines.append("-" * 40)
    lines.append("Orders Rejected (insufficient capacity/time/profit):")
    if plan["rejected"]:
        for o in plan["rejected"]:
            lines.append(f"  {o.order_id} ({o.priority}, {o.weight_kg}kg) -- {o.reject_reason}")
    else:
        lines.append("  None")

    lines.append("-" * 40)
    net_profit = total_revenue - total_cost
    total_orders = len(plan["orders"])
    lines.append(f"Total Revenue     : Rs{total_revenue:.2f}")
    lines.append(f"Total Cost        : Rs{total_cost:.2f}")
    lines.append(f"NET PROFIT        : Rs{net_profit:.2f}")
    lines.append(f"Orders Completed  : {completed} / {total_orders}")
    lines.append(line)

    return "\n".join(lines)
