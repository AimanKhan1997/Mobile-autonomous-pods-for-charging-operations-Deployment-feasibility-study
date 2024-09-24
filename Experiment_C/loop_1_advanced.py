import os
import traci
import traci.constants as tc
import matplotlib.pyplot as plt
import numpy as np
import math

# Connect to the SUMO server
traci.start(["sumo-gui", "-c", "loop1.sumocfg"])

# Constants
BATTERY_CAPACITY = 640
BATTERY_CAPACITY_POD = 2000
LOW_BATTERY_THRESHOLD = 20
SLOWDOWN_SPEED_ZERO_RANGE = 3
SLOWDOWN_SPEED_LOW_BATTERY = 6.5
WIRELESS_POD_POWER_RATING = 16000  # W
CHARGE_RATE = WIRELESS_POD_POWER_RATING / 3600  # Wh per second
DURATION = 80  # seconds
total_energy_charged = 0
elec_consumption = 0
total_energy_delivered = 0
total_energy_delivered_ini = 0
CHARGING_DISTANCE_THRESHOLD = 40  # meters
Max_charge_for_EVs= 80
parking_end = 475
total_distance = 0
# Initialize sets to keep track of counted vehicles and a dictionary to keep track of assigned t_1 vehicles for each electric bus
zero_range_vehicles = set()
low_battery_vehicles = set()
assigned_vehicle = set()
assigned_charging_pod_for_electric_veh = {}
# Initialize a dictionary to keep track of the queues for each parking area
parking_area_queues = {parking_area_id: set() for parking_area_id in traci.parkingarea.getIDList()}

# Lists to store timestamps and speeds of electric bus vehicles
timestamps = []
speeds = []

##USE CASE- when calculating the minimum amount needed to reach the next stop. Not used in the current implementation


def simulate_step():
    """
    Perform a single simulation step.
    """
    traci.simulationStep()
    timestamps.append(traci.simulation.getTime())
def main():
    vehicle_data = {}
    charging_pod_data = {}
    simulation_duration = 5000  # Define the desired simulation duration
    warm_up_time = 3000  # Warm-up time before data collection starts
    global total_energy_charged
    global elec_consumption
    global total_energy_delivered
    global total_energy_delivered_ini
    global LOW_BATTERY_THRESHOLD
    global zero_range_vehicles
    global total_distance


    for step in range(simulation_duration):  # You can adjust the number of steps as needed
        simulate_step()

        # Get the list of all active vehicles
        active_vehicles = traci.vehicle.getIDList()


        for vehicle_id in active_vehicles:
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)

            if vehicle_type == "ElectricVehicle":
                try:
                    distance = traci.vehicle.getDistance(vehicle_id)
                    total_energy_consumed = float(
                        traci.vehicle.getParameter(vehicle_id, "device.battery.totalEnergyConsumed"))
                    actual_battery_capacity = float(
                        traci.vehicle.getParameter(vehicle_id, "device.battery.actualBatteryCapacity"))
                    battery_capacity_percentage = (actual_battery_capacity / BATTERY_CAPACITY) * 100
                    electric_veh_lane = traci.vehicle.getLaneID(vehicle_id)
                except traci.exceptions.TraCIException as e:
                    print(f"Error handling vehicle {vehicle_id}: {e}")
                    continue


                if total_energy_consumed > 0:
                    elec_consumptn = float(traci.vehicle.getElectricityConsumption(vehicle_id))
                    elec_consumption += elec_consumptn
                    mWh = distance / total_energy_consumed
                    remaining_range = actual_battery_capacity * mWh


                    if remaining_range == 0 and vehicle_id not in zero_range_vehicles:
                        edge_id = traci.vehicle.getRoadID(vehicle_id)
                        print(f"Electric Veh {vehicle_id} on edge {edge_id} has zero remaining range.")
                        zero_range_vehicles.add(vehicle_id)
                        traci.vehicle.slowDown(vehicle_id, SLOWDOWN_SPEED_ZERO_RANGE, duration=0)
                        traci.vehicle.setColor(vehicle_id, (255, 0, 0))  # Red color

                    battery_capacity_percentage = (actual_battery_capacity / BATTERY_CAPACITY) * 100
                    if battery_capacity_percentage < LOW_BATTERY_THRESHOLD:
                        traci.vehicle.setColor(vehicle_id, (255, 0, 0))
                        traci.vehicle.slowDown(vehicle_id, SLOWDOWN_SPEED_LOW_BATTERY, duration=0)
                        traci.vehicle.changeLane(vehicle_id, 2, duration=80)
                        low_battery_vehicles.add(vehicle_id)
                        #print(f"assigned vehicle: {assigned_vehicle}")
                        print(
                            f"Electric Veh {vehicle_id} has low battery capacity: {battery_capacity_percentage}%.")
                        for parking_area_id in traci.parkingarea.getIDList():
                            edge_id = traci.vehicle.getRoadID(vehicle_id)
                            occupancy = traci.simulation.getParameter(parking_area_id, "parkingArea.occupancy")
                            capacity= traci.simulation.getParameter(parking_area_id, "parkingArea.capacity")
                            if edge_id == traci.lane.getEdgeID(traci.parkingarea.getLaneID(parking_area_id)) and occupancy < capacity:
                                traci.vehicle.setParkingAreaStop(vehicle_id, parking_area_id, duration=90000)
                                print(f"Electric Veh {vehicle_id} assigned to parking area {parking_area_id} for charging.")
                                break
                    elif battery_capacity_percentage >= Max_charge_for_EVs and traci.vehicle.isStoppedParking(
                            vehicle_id):  # and vehicle_id not in assigned_charging_pod_for_electric_veh:
                        traci.vehicle.setColor(vehicle_id, (255, 255, 255))  # white color
                        traci.vehicle.resume(vehicle_id)
                        #print(f"assigned vehicle: {assigned_vehicle}")
                        print(f"Electric Veh {vehicle_id} resumed from parking area.")
                    elif battery_capacity_percentage > LOW_BATTERY_THRESHOLD and not traci.vehicle.isStoppedParking(vehicle_id):
                        next_stops = traci.vehicle.getNextStops(vehicle_id)
                        if next_stops:
                            next_stop_id = next_stops[0][2]
                            traci.vehicle.setParkingAreaStop(vehicle_id, next_stop_id, duration=0)
                            print(
                                f"Parking area stop duration set to maximum at {next_stop_id} for nml pod {vehicle_id} at time {traci.simulation.getTime()}.")

                if vehicle_id not in vehicle_data:
                    vehicle_data[vehicle_id] = {'speed': [], 'battery_capacity': [], 'timestamps': [], 'distance': 0}
                vehicle_data[vehicle_id]['speed'].append(traci.vehicle.getSpeed(vehicle_id))
                vehicle_data[vehicle_id]['battery_capacity'].append((actual_battery_capacity / BATTERY_CAPACITY) * 100)
                vehicle_data[vehicle_id]['timestamps'].append(traci.simulation.getTime())
                #vehicle_data[vehicle_id]['distance']= distance
                if traci.simulation.getTime() == 5000 and not traci.vehicle.isStoppedParking(vehicle_id):
                    distance_1 = traci.vehicle.getDistance(vehicle_id)
                    vehicle_data[vehicle_id]['distance']= distance_1

        ##Calculate energy charged by charging stations
        for charging_station in traci.chargingstation.getIDList():
            if traci.simulation.getTime() == 5000:  ##time it takes to charge every pod before they are engaged
                energy_charged = float(
                    traci.simulation.getParameter(charging_station, "chargingStation.totalEnergyCharged"))
                total_energy_delivered_ini += energy_charged
                print(f"Energy charged by charging station {charging_station} is {energy_charged} Wh.")
                print(f"Total energy delivered by charging stations: {total_energy_delivered_ini} Wh.")

        # Check if the simulation time has exceeded the desired duration
        if traci.simulation.getTime() >= simulation_duration:
            print("Simulation time reached the specified duration. Closing the simulation.")
            break  # Exit the loop and close the simulation
    actual_energy_delivered = total_energy_delivered_ini
    #efficiency = total_energy_charged / actual_energy_delivered

    # Print the total count of vehicles with zero remaining range and low battery
    print(f"Total number of vehicles with zero remaining range: {len(zero_range_vehicles)}")
    print(f"Total number of vehicles with less than 25% battery capacity: {len(low_battery_vehicles)}")
 #   print(f"Total energy charged: {total_energy_charged} Wh")
    print(f"Total energy consumed by electric vehicles: {elec_consumption} Wh")
    print(f"Actual energy delivered by charging stations: {actual_energy_delivered} Wh")
    #print(f"Efficiency: {efficiency}")
    traci.close()

    # Plot the battery capacity over time for each vehicle
    for vehicle_id, data in vehicle_data.items():
        plt.plot(data['timestamps'], data['battery_capacity'], color="blue")
    plt.xlabel('Time (seconds)')
    plt.ylabel('SOC %')
    plt.title('SOC of Electric Vehicles Over Time')
    #plt.legend()
    plt.grid(True)
    plt.show()

    # Plot the distance traveled by each vehicle
    vehicle_ids = list(vehicle_data.keys())
    distances = [data['distance'] for data in vehicle_data.values()]
    plt.bar(vehicle_ids, distances, color="blue")
    plt.xlabel('Vehicle ID')
    plt.ylabel('Distance Traveled (m)')
    plt.title('Distance Traveled by Each Vehicle')
    plt.xticks(rotation=90)
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()