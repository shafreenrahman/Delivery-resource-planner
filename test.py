"""
test.py
Covers the PRD's test cases (TC1-TC32) against logic.py.
Interactive helpers are tested by mocking input(); pure planning functions are
tested by calling them directly on hand-built Order/Vehicle/Personnel objects.
"""

import unittest
from unittest.mock import patch

from logic import (
    Order, Vehicle, Personnel,
    read_positive_number, read_choice, read_unique_id,
    add_order, add_vehicle, add_personnel, calculate_revenue,
    pair_vehicles_personnel, rank_orders, delivery_time, trip_cost,
    allocate_orders, check_route_profitability, generate_plan, build_report,
)


def make_order(order_id, distance, weight, priority, deadline, revenue):
    return Order(order_id, distance, weight, priority, deadline, revenue)


def make_vehicle(vehicle_id, vtype):
    return Vehicle(vehicle_id, vtype)


class TestInputValidation(unittest.TestCase):
    # TC1
    def test_add_valid_order(self):
        orders = []
        with patch("builtins.input", side_effect=["O1", "5", "3", "1", "2"]):
            add_order(orders)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].priority, "Express")
        self.assertEqual(orders[0].revenue, 335)  # 3kg x 20 + 5km x Rs55 (Express, Bike class)

    # TC2
    def test_negative_weight_reprompts(self):
        with patch("builtins.input", side_effect=["-5", "3"]):
            val = read_positive_number("Weight: ")
        self.assertEqual(val, 3)

    # TC3 (capacity is now built in, only ID and type are asked)
    def test_add_valid_vehicle(self):
        vehicles = []
        with patch("builtins.input", side_effect=["V1", "2"]):
            add_vehicle(vehicles)
        self.assertEqual(len(vehicles), 1)
        self.assertEqual(vehicles[0].type, "Van")
        self.assertEqual(vehicles[0].max_capacity_kg, 65)

    def test_add_personnel(self):
        personnel = []
        with patch("builtins.input", side_effect=["P1", "Rohit"]):
            add_personnel(personnel)
        self.assertEqual(len(personnel), 1)
        self.assertEqual(personnel[0].name, "Rohit")

    # TC16
    def test_duplicate_id_rejected(self):
        with patch("builtins.input", side_effect=["O1", "O2"]):
            val = read_unique_id("Order ID: ", ["O1"])
        self.assertEqual(val, "O2")

    # TC17
    def test_non_numeric_reprompts(self):
        with patch("builtins.input", side_effect=["five", "5"]):
            val = read_positive_number("Weight: ")
        self.assertEqual(val, 5)

    # TC18 / TC20
    def test_zero_rejected(self):
        with patch("builtins.input", side_effect=["0", "-1", "2"]):
            val = read_positive_number("Deadline: ")
        self.assertEqual(val, 2)

    def test_read_choice_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["9", "1"]):
            val = read_choice("Priority: ", ["1", "2"])
        self.assertEqual(val, "1")

    # TC24 - minimum revenue (calculated: 3kg x 20 + 1km x Rs30 = Rs90)
    def test_revenue_below_100_not_accepted(self):
        orders = []
        with patch("builtins.input", side_effect=["O1", "1", "3", "2", "2"]):
            result = add_order(orders)
        self.assertIsNone(result)
        self.assertEqual(len(orders), 0)

    # TC25 / EC16
    def test_revenue_exactly_100_accepted(self):
        orders = []
        # 2kg x 20 + 2km x Rs30 (Standard, Bike class) = Rs100
        with patch("builtins.input", side_effect=["O1", "2", "2", "2", "2"]):
            add_order(orders)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].revenue, 100)

    # TC26 - minimum distance
    def test_distance_below_200m_not_accepted(self):
        orders = []
        with patch("builtins.input", side_effect=["O1", "0.15"]), patch("builtins.print") as pr:
            result = add_order(orders)
        self.assertIsNone(result)
        self.assertIn("200 m", pr.call_args[0][0])

    # EC17
    def test_distance_exactly_200m_accepted_if_revenue_ok(self):
        orders = []
        # 5kg x 20 + 0.2km x Rs55 (Express, Bike class) = Rs111
        with patch("builtins.input", side_effect=["O1", "0.2", "5", "1", "2"]):
            add_order(orders)
        self.assertEqual(len(orders), 1)

    # TC9 / EC11 - Express wins the space even if Standard pays more
    def test_express_beats_higher_paying_standard_for_space(self):
        e = make_order("E", 3, 60, "Express", 5, 300)
        st = make_order("S", 3, 60, "Standard", 5, 900)
        generate_plan([st, e], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(e.status, "Assigned")
        self.assertEqual(st.status, "Rejected")

    # TC27 / EC18
    def test_overweight_order_not_accepted(self):
        orders = []
        with patch("builtins.input", side_effect=["O1", "5", "250"]):
            result = add_order(orders)
        self.assertIsNone(result)

    # TC20 - built-in capacity and per-km rates
    def test_built_in_capacity_and_rates(self):
        vs = [make_vehicle("a", t) for t in ("Bike", "Van", "Truck")]
        self.assertEqual([v.max_capacity_kg for v in vs], [15, 65, 200])
        self.assertEqual([v.rate_for("Standard") for v in vs], [30, 55, 70])
        self.assertEqual([v.rate_for("Express") for v in vs], [55, 80, 95])

    # TC28
    def test_calculated_revenue(self):
        self.assertEqual(calculate_revenue(10, 10, "Standard"), 500)    # 200 + 300, Bike class
        self.assertEqual(calculate_revenue(10, 20, "Express"), 1200)    # 400 + 800, Van class
        self.assertEqual(calculate_revenue(10, 100, "Standard"), 2700)  # 2000 + 700, Truck class
        self.assertEqual(calculate_revenue(10, 15, "Express"), 850)     # 300 + 550, 15kg still Bike

    # TC32
    def test_profit_on_matching_vehicle_is_per_kg_charge(self):
        order = make_order("O1", 5, 10, "Standard", 5, calculate_revenue(5, 10, "Standard"))
        bike = make_vehicle("V1", "Bike")
        plan = generate_plan([order], [bike], [Personnel("P1", "Anu")])
        self.assertEqual(order.status, "Assigned")
        self.assertEqual(order.revenue - trip_cost(bike, bike.assigned_orders), 200)  # 10kg x Rs20


class TestPlanningLogic(unittest.TestCase):
    # TC4
    def test_all_orders_fit(self):
        orders = [make_order("O1", 5, 3, "Standard", 2, 400),
                  make_order("O2", 4, 2, "Standard", 2, 400),
                  make_order("O3", 3, 4, "Standard", 2, 400)]
        vehicles = [make_vehicle("V1", "Van")]
        personnel = [Personnel("P1", "Rohit")]
        plan = generate_plan(orders, vehicles, personnel)
        self.assertEqual(len(plan["rejected"]), 0)
        self.assertTrue(all(o.status == "Assigned" for o in orders))
        # profit = total revenue - total cost = 1200 - (12km x Rs55)
        self.assertEqual(sum(o.revenue for o in orders) - trip_cost(vehicles[0], orders), 540)

    # TC5
    def test_capacity_exceeded_some_rejected(self):
        orders = [make_order(f"O{i}", 2, 10, "Standard", 5, 300) for i in range(8)]  # 80kg total
        vehicles = [make_vehicle("V1", "Van")]  # 65kg
        personnel = [Personnel("P1", "Rohit")]
        plan = generate_plan(orders, vehicles, personnel)
        self.assertEqual(len(plan["rejected"]), 2)
        self.assertEqual(sum(1 for o in orders if o.status == "Assigned"), 6)
        assigned_weight = sum(o.weight_kg for o in orders if o.status == "Assigned")
        self.assertLessEqual(assigned_weight, 65)

    # TC6
    def test_deadline_not_achievable(self):
        order = make_order("O1", 100, 2, "Express", 0.5, 5000)  # 100km @ 30km/h > 0.5hr
        vehicle = make_vehicle("V1", "Bike")
        plan = generate_plan([order], [vehicle], [Personnel("P1", "Anu")])
        self.assertEqual(order.status, "Rejected")
        self.assertIn("time", order.reject_reason)

    # TC7
    def test_zero_orders(self):
        plan = generate_plan([], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertIn("No orders to plan", build_report(plan))

    # TC8
    def test_zero_vehicles(self):
        order = make_order("O1", 5, 3, "Standard", 2, 400)
        generate_plan([order], [], [Personnel("P1", "Rohit")])
        self.assertEqual(order.status, "Rejected")
        self.assertEqual(order.reject_reason, "no vehicles available")

    # TC12
    def test_zero_personnel(self):
        order = make_order("O1", 5, 3, "Standard", 2, 400)
        generate_plan([order], [make_vehicle("V1", "Van")], [])
        self.assertEqual(order.status, "Rejected")
        self.assertEqual(order.reject_reason, "no personnel available")

    # TC13 - weight exactly equals capacity (Van = 65kg)
    def test_weight_equals_capacity_boundary(self):
        order = make_order("O1", 5, 65, "Standard", 2, 600)
        generate_plan([order], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(order.status, "Assigned")

    # TC14 - deadline exactly equals delivery time (Van 25 km/h, 25km = 1hr)
    def test_deadline_equals_delivery_time_boundary(self):
        order = make_order("O1", 25, 5, "Standard", 1, 2000)
        generate_plan([order], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(order.status, "Assigned")

    # route cost exactly equal to route revenue is still profitable enough to keep
    def test_cost_equals_revenue_boundary_kept(self):
        order = make_order("O1", 5, 10, "Standard", 5, 275)  # Van cost 5 x 55 = 275
        generate_plan([order], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(order.status, "Assigned")

    # TC15 / EC8
    def test_unprofitable_order_rejected(self):
        order = make_order("O1", 50, 5, "Standard", 5, 50)  # cost 50*55 = 2750 vs revenue 50
        generate_plan([order], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(order.status, "Rejected")
        self.assertEqual(order.reject_reason, "unprofitable at route level")

    # TC10
    def test_orders_split_across_vehicles(self):
        orders = [make_order("O1", 3, 30, "Standard", 5, 400),
                  make_order("O2", 3, 30, "Standard", 5, 400),
                  make_order("O3", 3, 30, "Standard", 5, 400),
                  make_order("O4", 3, 20, "Standard", 5, 300),
                  make_order("O5", 3, 10, "Standard", 5, 200)]
        vehicles = [make_vehicle("V1", "Van"), make_vehicle("V2", "Van")]
        personnel = [Personnel("P1", "Anu"), Personnel("P2", "Rohit")]
        generate_plan(orders, vehicles, personnel)
        used = {o.assigned_vehicle_id for o in orders if o.status == "Assigned"}
        self.assertEqual(used, {"V1", "V2"})  # 120kg total cannot fit one 65kg van
        self.assertGreaterEqual(sum(1 for o in orders if o.status == "Assigned"), 3)

    # TC19 / EC4
    def test_idle_due_to_incompatible_orders(self):
        orders = [make_order("O1", 5, 20, "Standard", 5, 400),
                  make_order("O2", 5, 30, "Standard", 5, 500)]
        bike = make_vehicle("VB", "Bike")  # 15kg, too small for both orders
        van = make_vehicle("VV", "Van")
        personnel = [Personnel("P1", "Anu"), Personnel("P2", "Rohit")]
        plan = generate_plan(orders, [bike, van], personnel)
        self.assertEqual(plan["empty_reason"].get("VB"), "no compatible orders")

    # TC11
    def test_more_vehicles_than_personnel(self):
        vehicles = [make_vehicle("V1", "Bike"), make_vehicle("V2", "Van"), make_vehicle("V3", "Truck")]
        personnel = [Personnel("P1", "Anu"), Personnel("P2", "Rohit")]
        pairs, idle_v, idle_p = pair_vehicles_personnel(vehicles, personnel)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(len(idle_v), 1)
        self.assertEqual(idle_v[0].vehicle_id, "V3")
        self.assertEqual(len(idle_p), 0)

    # TC22
    def test_tie_break_by_entry_order(self):
        a = make_order("A", 5, 10, "Standard", 5, 100)
        b = make_order("B", 5, 10, "Standard", 5, 100)
        self.assertEqual(rank_orders([a, b])[0].order_id, "A")

    # TC21 / EC9
    def test_route_level_unprofitability(self):
        o1 = make_order("O1", 5, 5, "Standard", 5, 300)   # cost 275, profitable alone
        o2 = make_order("O2", 20, 5, "Standard", 5, 300)  # cost 1100, loss alone
        vehicle = make_vehicle("V1", "Van")
        plan = generate_plan([o1, o2], [vehicle], [Personnel("P1", "Rohit")])
        self.assertEqual(o1.status, "Assigned")
        self.assertEqual(o2.status, "Rejected")
        self.assertEqual(o2.reject_reason, "unprofitable at route level")
        self.assertLessEqual(trip_cost(vehicle, vehicle.assigned_orders),
                             sum(o.revenue for o in vehicle.assigned_orders))
        self.assertIn("O2", {o.order_id for o in plan["rejected"]})

    # TC23
    def test_large_scale_stress(self):
        orders = [make_order(f"O{i}", 2 + (i % 5), 1 + (i % 10), "Standard" if i % 2 else "Express",
                             3, 50 + i) for i in range(500)]
        vehicles = [make_vehicle(f"V{i}", "Van") for i in range(5)]
        personnel = [Personnel(f"P{i}", f"Driver{i}") for i in range(5)]
        plan = generate_plan(orders, vehicles, personnel)
        self.assertIn("NET PROFIT", build_report(plan))

    # TC29 - higher paying order wins limited capacity
    def test_higher_paying_order_accepted_first(self):
        a = make_order("A", 3, 60, "Standard", 5, 500)  # person A pays more
        b = make_order("B", 3, 60, "Standard", 5, 300)
        generate_plan([b, a], [make_vehicle("V1", "Van")], [Personnel("P1", "Rohit")])
        self.assertEqual(a.status, "Assigned")
        self.assertEqual(b.status, "Rejected")

    # TC30 / EC19 - same cost, pick first delivery person
    def test_cost_tie_goes_to_first_personnel(self):
        order = make_order("O1", 5, 10, "Standard", 5, 500)
        v1, v2 = make_vehicle("V1", "Van"), make_vehicle("V2", "Van")
        generate_plan([order], [v2, v1], [Personnel("P2", "Rohit"), Personnel("P1", "Anu")])
        self.assertEqual(order.assigned_vehicle_id, "V1")  # paired with P1, first in list

    # TC31
    def test_cheaper_vehicle_preferred(self):
        order = make_order("O1", 5, 10, "Standard", 5, 500)
        van, bike = make_vehicle("V1", "Van"), make_vehicle("V2", "Bike")
        generate_plan([order], [van, bike], [Personnel("P1", "Anu"), Personnel("P2", "Rohit")])
        self.assertEqual(order.assigned_vehicle_id, "V2")  # bike Rs30/km < van Rs55/km


class TestEdgeCases(unittest.TestCase):
    # EC20 - a Bike-class order on a bigger vehicle costs more to carry
    def test_small_order_costs_more_on_bigger_vehicle(self):
        order = make_order("Z", 5, 10, "Standard", 5, calculate_revenue(5, 10, "Standard"))
        self.assertEqual(make_vehicle("B", "Bike").cost_of(order), 150)
        self.assertEqual(make_vehicle("V", "Van").cost_of(order), 275)
        self.assertEqual(order.revenue, 350)  # profit 200 on a Bike, only 75 on a Van


class TestPureFunctions(unittest.TestCase):
    def test_delivery_time(self):
        order = make_order("O1", 30, 2, "Standard", 5, 100)
        self.assertEqual(delivery_time(order, make_vehicle("V1", "Bike")), 1.0)

    def test_trip_cost_uses_priority_rate(self):
        vehicle = make_vehicle("V1", "Van")
        orders = [make_order("O1", 10, 2, "Standard", 5, 1000),   # 10 * 55
                  make_order("O2", 5, 2, "Express", 5, 1000)]     # 5 * 80
        self.assertEqual(trip_cost(vehicle, orders), 950)

    def test_rank_orders_priority_first(self):
        express = make_order("E1", 5, 5, "Express", 5, 100)
        standard = make_order("S1", 5, 5, "Standard", 5, 500)
        self.assertEqual(rank_orders([standard, express])[0].order_id, "E1")

    def test_rank_orders_higher_revenue_first_within_priority(self):
        low = make_order("S1", 5, 5, "Standard", 5, 200)
        high = make_order("S2", 5, 50, "Standard", 5, 500)
        self.assertEqual(rank_orders([low, high])[0].order_id, "S2")


if __name__ == "__main__":
    unittest.main()
