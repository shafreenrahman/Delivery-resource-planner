"""
main.py
Menu loop for the Delivery Resource Planning System.
"""

from logic import (
    add_order, add_vehicle, add_personnel, view_all,
    generate_plan, build_report,
)

MENU = """
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
----------------------------------------"""


def main():
    orders = []
    vehicles = []
    personnel = []
    last_plan = None

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_order(orders)
        elif choice == "2":
            view_all(orders, vehicles, personnel)
        elif choice == "3":
            add_vehicle(vehicles)
        elif choice == "4":
            add_personnel(personnel)
        elif choice == "5":
            last_plan = generate_plan(orders, vehicles, personnel)
            print()
            print(build_report(last_plan))
        elif choice == "6":
            if last_plan is None:
                print("No plan generated yet.")
            else:
                print()
                print(build_report(last_plan))
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option, please choose 1-7.")


if __name__ == "__main__":
    main()
