#import os
import traci
#import traci.constants as tc
import matplotlib.pyplot as plt
import sys
#import numpy as np
#import math
#import seaborn as sns
#python loop_1_MAIN.py loop1.sumocfg ## Run this command in the terminal to execute the script
# can be used multiple simulations at the same time
# Define the filename for the saved state
STATE_FILENAME = "SAVE_state.xml.gz"  # Replace with your actual saved state file
# Check for command-line argument
if len(sys.argv) < 2:
    print("Usage: python script.py <sumo_config_file>")
    sys.exit(1)

sumo_config_file = sys.argv[1]
# Connect to the SUMO server
traci.start(["sumo-gui", "-c", sumo_config_file])

# Load the saved state
traci.simulation.loadState(STATE_FILENAME)

# Constants
BATTERY_CAPACITY = 640 # battery capacity of electric vehicles in Wh
BATTERY_CAPACITY_POD = 2000 # battery capacity of charging pods in Wh
LOW_BATTERY_THRESHOLD = 20 # 20% battery capacity
SLOWDOWN_SPEED_ZERO_RANGE = 3 # reduced speed for vehicles with zero remaining range
SLOWDOWN_SPEED_LOW_BATTERY = 6.5 # reduced speed for vehicles with low battery
WIRELESS_POD_POWER_RATING = 18000  # W
CHARGE_RATE = WIRELESS_POD_POWER_RATING / 3600  # Wh per second
DURATION = 80  # seconds
total_energy_charged = 0
elec_consumption = 0
total_energy_delivered = 0
total_energy_delivered_ini = 0
CHARGING_DISTANCE_THRESHOLD = 40  # meters
Max_charge_for_EVs= 80
parking_end = 480
edge_end=850

# Initialize sets to keep track of counted vehicles and a dictionary to keep track of assigned t_1 vehicles for each electric bus
zero_range_vehicles = set()
low_battery_vehicles = set()
assigned_charging_pod_for_electric_veh = {}
# Initialize a dictionary to keep track of the queues for each parking area
#parking_area_queues = {parking_area_id: set() for parking_area_id in traci.parkingarea.getIDList()}

# Lists to store timestamps and speeds of electric bus vehicles
timestamps = []
speeds = []

# Dictionary to track the last speed and time for each charging pod
charging_pod_speeds = {}

def handle_electric_vehicle(vehicle_id, distance, total_energy_consumed, actual_battery_capacity, electric_veh_lane):
    """
    Handle electric vehicle behavior.

    Args:
        vehicle_id (str): The ID of the electric vehicle.
        distance (float): Distance traveled by the vehicle.
        total_energy_consumed (float): Total energy consumed by the vehicle.
        actual_battery_capacity (float): Actual battery capacity of the vehicle.
        electric_veh_lane (str): Lane ID of the electric vehicle.

    Returns:
        None
    """
    global LOW_BATTERY_THRESHOLD
    global zero_range_vehicles
    global assigned_charging_pod_for_electric_veh
    if total_energy_consumed > 0:
        mWh = distance / total_energy_consumed
        remaining_range = actual_battery_capacity * mWh
        battery_capacity_percentage = (actual_battery_capacity / BATTERY_CAPACITY) * 100

        if remaining_range == 0 and battery_capacity_percentage==0 and vehicle_id not in zero_range_vehicles:
            edge_id = traci.vehicle.getRoadID(vehicle_id)
            print(f"Electric Veh {vehicle_id} on edge {edge_id} has zero remaining range at time {traci.simulation.getTime()}")
            zero_range_vehicles.add(vehicle_id)# Add vehicle to the set of vehicles with zero remaining range
            traci.vehicle.slowDown(vehicle_id, SLOWDOWN_SPEED_ZERO_RANGE, duration=0) # Reduce speed to 3 m/s
            traci.vehicle.setColor(vehicle_id, (255, 0, 0))  # Red color


        if battery_capacity_percentage < LOW_BATTERY_THRESHOLD and traci.vehicle.getLanePosition(vehicle_id) < edge_end:#and traci.vehicle.getLanePosition(vehicle_id) >460 and traci.vehicle.getLanePosition(vehicle_id) < 530:#
            handle_low_battery_vehicle(vehicle_id)
            #traci.vehicle.changeLane(vehicle_id, 1, duration=9999)
        elif battery_capacity_percentage >= LOW_BATTERY_THRESHOLD and vehicle_id not in assigned_charging_pod_for_electric_veh:
            traci.vehicle.setColor(vehicle_id, (255, 255, 255)) #white color
            traci.vehicle.changeLane(vehicle_id, 0, duration=80) # keep vehicle in the right lane with high battery

def handle_low_battery_vehicle(vehicle_id):
    """
    Handle electric vehicle with low battery.

    Args:
        vehicle_id (str): The ID of the electric vehicle.
        electric_veh_lane (str): Lane ID of the electric vehicle.

    Returns:
        None
    """
    global low_battery_vehicles
    low_battery_vehicles.add(vehicle_id)
    traci.vehicle.slowDown(vehicle_id, SLOWDOWN_SPEED_LOW_BATTERY, duration=10)
    traci.vehicle.changeLane(vehicle_id, 1, duration=9999)
    traci.vehicle.setColor(vehicle_id, (255, 0, 0))  # Red color
    global assigned_charging_pod_for_electric_veh

    edge_id = traci.vehicle.getRoadID(vehicle_id)
    nearest_charging_pod_id = None
    min_distance = float('inf')
    electric_veh_position = traci.vehicle.getPosition(vehicle_id)
    electric_veh_lane_position = traci.vehicle.getLanePosition(vehicle_id)
    battery_capacity_percentage = (float(traci.vehicle.getParameter(vehicle_id, "device.battery.actualBatteryCapacity")) / BATTERY_CAPACITY) * 100

    if vehicle_id in traci.vehicle.getIDList():
        for charging_pod_id in traci.vehicle.getIDList():
            battery_capacity_percentage_pod = (float(traci.vehicle.getParameter(charging_pod_id,
                                                                                "device.battery.actualBatteryCapacity")) / BATTERY_CAPACITY_POD) * 100
            if (traci.vehicle.getTypeID(charging_pod_id) == "ChargingPod" and traci.vehicle.getRoadID(
                    charging_pod_id) == edge_id and traci.vehicle.isStoppedParking(charging_pod_id) and vehicle_id not in assigned_charging_pod_for_electric_veh and battery_capacity_percentage_pod > ((BATTERY_CAPACITY*2)/BATTERY_CAPACITY_POD)*100): # check if the pod has enough energy
                charging_pod_position = traci.vehicle.getPosition(charging_pod_id)
                #charging_pod_lane_position = traci.vehicle.getLanePosition(charging_pod_id)
                distance_to_electric_veh = traci.simulation.getDistance2D(electric_veh_position[0],
                                                                          electric_veh_position[1],
                                                                          charging_pod_position[0],
                                                                          charging_pod_position[1])

                if distance_to_electric_veh < min_distance and charging_pod_id not in assigned_charging_pod_for_electric_veh.values() and electric_veh_lane_position > parking_end:
                    nearest_charging_pod_id = charging_pod_id
                    min_distance = distance_to_electric_veh

        if nearest_charging_pod_id:
            assigned_charging_pod_for_electric_veh[vehicle_id] = nearest_charging_pod_id
            print(f"Electric Veh {vehicle_id} assigned to Charging Pod {nearest_charging_pod_id} at time {traci.simulation.getTime()}")


def share_energy(charging_pod_id, vehicle_id):
    """
    Share energy between a charging pod and an electric vehicle.

    Args:
        charging_pod_id (str): The ID of the charging pod.
        vehicle_id (str): The ID of the electric vehicle.
    Returns:
        None
    """
    global total_energy_charged
    actual_battery_capacity_pod = float(
        traci.vehicle.getParameter(charging_pod_id, "device.battery.actualBatteryCapacity"))
    #elec_consumption = float(traci.vehicle.getElectricityConsumption(charging_pod_id))
    new_energy_charging_pod = actual_battery_capacity_pod - CHARGE_RATE
    actual_battery_capacity = float(traci.vehicle.getParameter(vehicle_id, "device.battery.actualBatteryCapacity"))
    new_energy_electric = actual_battery_capacity + CHARGE_RATE
    traci.vehicle.setParameter(charging_pod_id, "device.battery.actualBatteryCapacity", new_energy_charging_pod)
    traci.vehicle.setParameter(vehicle_id, "device.battery.actualBatteryCapacity", new_energy_electric)
    if traci.simulation.getTime() >= 4000: #Steady state starts
        total_energy_charged += CHARGE_RATE
    #print(f"Energy shared: {new_energy_electric} kWh")
def simulate_step():
    """
    Perform a single simulation step.
    """
    traci.simulationStep()
    timestamps.append(traci.simulation.getTime())

def main():
    vehicle_data = {}
    charging_pod_data = {}
    simulation_duration = 7500  # Define the desired simulation duration
    warm_up_time = 4000  # Warm-up time before data collection starts
    global total_energy_charged
    global assigned_charging_pod_for_electric_veh
    global parking_area_queues
    global elec_consumption
    global total_energy_delivered
    global total_energy_delivered_ini
    global charging_pod_speeds
    cancelled_evs = set()

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
                handle_electric_vehicle(vehicle_id, distance, total_energy_consumed, actual_battery_capacity,
                                        electric_veh_lane)

                if vehicle_id not in vehicle_data:
                    vehicle_data[vehicle_id] = {'speed': [], 'battery_capacity': [], 'timestamps': [], 'distance': 0}
                vehicle_data[vehicle_id]['speed'].append(traci.vehicle.getSpeed(vehicle_id))
                vehicle_data[vehicle_id]['battery_capacity'].append((actual_battery_capacity / BATTERY_CAPACITY) * 100)
                vehicle_data[vehicle_id]['timestamps'].append(traci.simulation.getTime())
                vehicle_data[vehicle_id]['distance'] = distance

            elif vehicle_type == "ChargingPod":
                # state = traci.vehicle.getStopState(vehicle_id)
                # print(f"Charging pod {vehicle_id} stop state is {state}.")

                # Collect data for charging pods
                try:
                    battery_capacity = float(
                        traci.vehicle.getParameter(vehicle_id, "device.battery.actualBatteryCapacity"))
                    charging_pod_data.setdefault(vehicle_id, {'battery_capacity': [], 'timestamps': []})
                    charging_pod_data[vehicle_id]['battery_capacity'].append(
                        (battery_capacity / BATTERY_CAPACITY_POD) * 100)
                    charging_pod_data[vehicle_id]['timestamps'].append(traci.simulation.getTime())
                except traci.exceptions.TraCIException as e:
                    print(f"Error handling charging pod {vehicle_id}: {e}")
                    continue
        ##Calculate energy consumption of pods
        for charging_pod_id in traci.vehicle.getIDList():
            vehicle_type = traci.vehicle.getTypeID(charging_pod_id)
            if traci.simulation.getTime() >= warm_up_time and vehicle_type == "ChargingPod":
                elec_consumptn = float(traci.vehicle.getElectricityConsumption(charging_pod_id))
                elec_consumption += elec_consumptn
                #print(f"Energy consumed by electric vehicles: {elec_consumption} Wh for pod {charging_pod_id}")

        ##Calculate energy charged by charging stations
        for charging_station in traci.chargingstation.getIDList():
            if traci.simulation.getTime() == warm_up_time:  ##time it takes to charge every pod before they are engaged
                energy_charged = float(
                    traci.simulation.getParameter(charging_station, "chargingStation.totalEnergyCharged"))
                total_energy_delivered_ini += energy_charged
                print(f"Energy charged by charging station {charging_station} is {energy_charged} Wh.")
                print(f"Total energy delivered by charging stations: {total_energy_delivered_ini} Wh.")
            elif traci.simulation.getTime() == simulation_duration:
                energy_charged = float(
                    traci.simulation.getParameter(charging_station, "chargingStation.totalEnergyCharged"))
                total_energy_delivered += energy_charged
                print(f"Energy charged by charging station {charging_station} is {energy_charged} Wh.")
                print(f"Total energy delivered by charging stations: {total_energy_delivered} Wh.")

        ## Handle charging pods
        for vehicle_id, charging_pod_id in list(assigned_charging_pod_for_electric_veh.items()):
            # Get battery capacity percentage for the current vehicle
            battery_capacity_percentage = (float(traci.vehicle.getParameter(vehicle_id,
                                                                            "device.battery.actualBatteryCapacity")) / BATTERY_CAPACITY) * 100
            battery_capacity_percentage_pod = (float(traci.vehicle.getParameter(charging_pod_id,
                                                                            "device.battery.actualBatteryCapacity")) / BATTERY_CAPACITY_POD) * 100
            vehicle_1_position = traci.vehicle.getPosition(charging_pod_id)
            vehicle_2_position = traci.vehicle.getPosition(vehicle_id)
            distance = traci.simulation.getDistance2D(vehicle_1_position[0], vehicle_1_position[1],
                                                      vehicle_2_position[0], vehicle_2_position[1])
            # Check if battery capacity is less than 80%
            state = traci.vehicle.getStopState(charging_pod_id)
            if battery_capacity_percentage < Max_charge_for_EVs:
                # Continue charging process
                # electric_veh_lane_id = int(electric_veh_lane.split('_')[1])
                if traci.vehicle.isStoppedParking(charging_pod_id) and charging_pod_id in assigned_charging_pod_for_electric_veh.values():
                    traci.vehicle.resume(charging_pod_id)
                    print(f"Charging pod {charging_pod_id} resumed.")
                    # Initialize the charging pod's speed tracking data
                    charging_pod_speeds[charging_pod_id] = {'last_position': traci.vehicle.getLanePosition(charging_pod_id), 'last_time': traci.simulation.getTime()}
                    # Update the last speed and time for the charging pod
                    ###Comment
                # if battery_capacity_percentage <= 18: #SOME MAPs disappear from the simulation when parked together or waiting to enter the parking lot. This code reassigns the EVs
                #     current_time = traci.simulation.getTime()
                #     for charging_pod_id in list(charging_pod_speeds.keys()):
                #         data = charging_pod_speeds[charging_pod_id]
                #         last_position = data['last_position']
                #         last_time = data['last_time']
                #         current_position = traci.vehicle.getLanePosition(charging_pod_id)
                #         if current_position == last_position and traci.vehicle.getSpeed(charging_pod_id) < 2 and current_time - last_time >= 20:
                #                 #del assigned_charging_pod_for_electric_veh[vehicle_id] # Remove vehicle from charging assignment
                #             cancelled_evs.add(vehicle_id)
                #             print(f"Charging pod {charging_pod_id} position is {traci.vehicle.getLanePosition(charging_pod_id)}")
###Comment


                if distance <= CHARGING_DISTANCE_THRESHOLD:
                    #print(f"distance {distance} and pod {charging_pod_id} and veh {vehicle_id} at time {traci.simulation.getTime()}.")
                    #traci.vehicle.slowDown(charging_pod_id, 15, duration=0)
                    traci.vehicle.changeLane(charging_pod_id, 1, duration=700)
                    #print(f"Charging pod {charging_pod_id} is close to electric vehicle {vehicle_id} at time {traci.simulation.getTime()}.")
                    share_energy(charging_pod_id, vehicle_id)
                    traci.vehicle.setColor(vehicle_id, (0, 255, 0))  # Green color
                    if traci.vehicle.getLanePosition(vehicle_id) !=0:
                        lane_distance = (traci.vehicle.getLanePosition(charging_pod_id) -
                                            traci.vehicle.getLanePosition(vehicle_id))
                        #print(f"distance {distance} and lane distance {lane_distance}and pod {charging_pod_id} and veh {vehicle_id} at time {traci.simulation.getTime()}.")
                        if lane_distance < -100:
                            traci.vehicle.slowDown(charging_pod_id, 2, duration=0)
                            traci.vehicle.changeLane(charging_pod_id, 2, duration=700)
                            # print(f"Charging pod {charging_pod_id} is slowing down to allow EV {vehicle_id} to move forward as lane distance is {lane_distance}")

                    # energy_to_share = min_battery_capacity_to_next_stop(charging_pod_id)
                    # #print(f"Energy to share: {energy_to_share} kWh")
                        if lane_distance > 0 or distance >=50:
                            traci.vehicle.slowDown(charging_pod_id, 2, duration=0)
                            traci.vehicle.changeLane(charging_pod_id, 2, duration=700)
                            #print(f"Charging pod {charging_pod_id} is slowing down to allow EV {vehicle_id} to move forward as lane distance is {lane_distance}")

                    else:
                        traci.vehicle.slowDown(charging_pod_id, 7, duration=0)
                    next_stops = traci.vehicle.getNextStops(charging_pod_id)
                    if next_stops:
                        next_stop_id = next_stops[0][2]
                        next_stop_lane = next_stops[0][0]
                        edge_id = traci.lane.getEdgeID(next_stop_lane)  # Get the edge ID associated with the lane
                        #print(f"Next stop ID: {next_stop_id} and edge ID: {edge_id}")
                        next_stop_position = traci.parkingarea.getEndPos(next_stop_id)
                        #electric_veh_lane_position = traci.vehicle.getLanePosition(vehicle_id)
                        pod_id= traci.vehicle.getRoadID(charging_pod_id)
                        if pod_id == edge_id:
                            # Calculate the distance to the next stop
                            distance_to_next_stop = traci.simulation.getDistance2D(
                                traci.vehicle.getLanePosition(charging_pod_id), 0, next_stop_position,
                                0)
                            #distance_park= abs(next_stop_position - electric_veh_lane_position)
                            #print(f"check {distance_to_next_stop} and id {next_stop_id} and pod {charging_pod_id}.")
                            if distance_to_next_stop < 80 and battery_capacity_percentage < 80:
                                traci.vehicle.setParkingAreaStop(charging_pod_id, next_stop_id, duration=0)
                                #print(f"Parking duration set to zero for pod {charging_pod_id} and next stop {next_stop_id} and position {next_stop_position}")
                else:
                    traci.vehicle.changeLane(charging_pod_id, 2, duration=700) # if pod overtakes the EV change lane and allow EV to come in front
                    #print(f"Charging pod {charging_pod_id} speed is {traci.vehicle.getSpeed(charging_pod_id)} m/s.")
            elif battery_capacity_percentage < 15 and vehicle_id not in cancelled_evs: ## USE WHEN number of EVS is very low
                    del assigned_charging_pod_for_electric_veh[vehicle_id] # Remove vehicle from charging assignment
                    cancelled_evs.add(vehicle_id)
            elif battery_capacity_percentage_pod <= 20:

                    print(f"charging pod {charging_pod_id} has low energy")
                    print(f"Charging pod {charging_pod_id} stop state is {state}.")
                    traci.vehicle.changeLane(charging_pod_id, 2, duration=80)
                    traci.vehicle.setColor(vehicle_id, (255, 255, 255))  # White color
                    traci.vehicle.setColor(charging_pod_id, (100, 149, 237))  # White color
                    del assigned_charging_pod_for_electric_veh[vehicle_id]  # Remove vehicle from charging assignment
                    next_stops = traci.vehicle.getNextStops(charging_pod_id)
                    if next_stops:
                        next_stop_id = next_stops[0][2]
                        traci.vehicle.setParkingAreaStop(charging_pod_id, next_stop_id, duration=90000)
                        #print(f"Parking area stop duration set to maximum rare {next_stop_id} for pd {charging_pod_id}.")
            elif battery_capacity_percentage >= Max_charge_for_EVs:
                # Stop charging process if battery capacity is 80% or higher
                traci.vehicle.changeLane(charging_pod_id, 2, duration=80)
                traci.vehicle.setColor(vehicle_id, (255, 255, 255))  # White color
                del assigned_charging_pod_for_electric_veh[vehicle_id]  # Remove vehicle from charging assignment
                if vehicle_id in cancelled_evs:
                    cancelled_evs.remove(vehicle_id)
                next_stops = traci.vehicle.getNextStops(charging_pod_id)
                if next_stops:
                    next_stop_id = next_stops[0][2]
                    traci.vehicle.setParkingAreaStop(charging_pod_id, next_stop_id, duration=90000)
                    #print(f"Charging pod {charging_pod_id} stop state is {state}.")
                    #print(f"Parking area stop duration set to maximum at {next_stop_id} for nml pod {charging_pod_id} at time {traci.simulation.getTime()}.")

        # Check if the simulation time has exceeded the desired duration
        if traci.simulation.getTime() >= simulation_duration:
            print("Simulation time reached the specified duration. Closing the simulation.")
            break  # Exit the loop and close the simulation
    actual_energy_delivered = total_energy_delivered - total_energy_delivered_ini
    efficiency = total_energy_charged / actual_energy_delivered

    # Print the total count of vehicles with zero remaining range and low battery
    print(f"Total number of vehicles with zero remaining range: {len(zero_range_vehicles)}")
    print(f"Total number of vehicles with less than 25% battery capacity: {len(low_battery_vehicles)}")
    #print(f"Total number of vehicles with cancelled charging: {len(cancelled_evs)} and they are {cancelled_evs}")
    print(f"Total energy charged: {total_energy_charged} Wh")
    print(f"Total energy consumed by electric vehicles: {elec_consumption} Wh")
    print(f"Actual energy delivered by charging stations: {actual_energy_delivered} Wh")
    print(f"Efficiency: {efficiency}")
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

    # Plot charging pod data
    for pod_id, pod_data in charging_pod_data.items():
        plt.plot(pod_data['timestamps'], pod_data['battery_capacity'], color="blue")

    plt.xlabel('Time (seconds)')
    plt.ylabel('SOC %')
    plt.title('SOC of Charging Pods Over Time')
    #plt.legend()
    plt.xlim(warm_up_time, simulation_duration)
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()