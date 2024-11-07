This repository contains the code to replicate the experiments proposed in the study Mobile autonomous pods for charging operations: Deployment feasibility study submitted to IEEE OJITS.

This code provides a simulation environment to simulate the behaviour of mobile autonomous pods (MAPs) for charging electric autonomous vehicles (eAVs). The charging is achieved through vehicle-to-vehicle energy transfer.

To model the autonomous behavior of eAVs and MAPs, we use the cooperative adaptive cruise control (CACC) [37] car following model available in SUMO. For the charge sharing between MAPs and EVs, we assume a conductive transfer through robotic conductive arms. We assume that eAVs cannot share charge among each other.

We adopt a stylized network to simulate and analyze the feasibility of the proposed charging system. The network consists of four edges, with one-way traffic, connected in a loop as shown in Fig.
![Khan1](https://github.com/user-attachments/assets/7d8639b8-7596-4841-b763-95d70c07d1cb)

Each edge has a parking lot in the middle where multiple MAPs are parked and charged at the same time, to represent the vertical parking presented in [36]. In the experiments, we assume all parking lots have fully charged MAPs at the beginning of the simulation and all MAPs are equally distributed on all edges.

To run the code run the the line in the terminal to execute the code- python loop_1_MAIN.py loop1.sumocfg

Needs SUMO 1.20.0 or higher to execute properly

The code various parameters to adjust and observe the relevant change in the results.

The main parameters that can be adjusted based on different scenarios are- 

BATTERY_CAPACITY = 640 # battery capacity of electric vehicles in Wh

BATTERY_CAPACITY_POD = 2000 # battery capacity of charging pods in Wh

These values also have to be changes in the .rou.xml file

LOW_BATTERY_THRESHOLD = 20 # determine the lowest SOC the eAV can get before needing recharge

SLOWDOWN_SPEED_ZERO_RANGE = 3 # reduced speed for vehicles with zero remaining range

SLOWDOWN_SPEED_LOW_BATTERY = 9.5 # reduced speed for vehicles with low battery to allow the MAPs to catch up

WIRELESS_POD_POWER_RATING = 18000  # W

CHARGE_RATE = WIRELESS_POD_POWER_RATING / 3600  # Wh per second (can be adjusted to represent wireless, conductive and battery swapping technologies)

parking_end = 480 #This is used to ensure the MAPs only leave the parking lot when the eAV is in front of them

edge_end=850 # The maximum distance the MAPs can be assigned to an eAV. After this distance, the nearest MAP on next edge is assigned

This repository includes four experiments as mentioned in the study

EXPERIMENT A- Determining the maximum number of eAVs that can be supported

This includes 20 MAPS in the network and the number of eAVs can be adjusted

EXPERIMENT B- Comparing alternative charging strategies

This experiment compares alternate charging strategy, where the MAPs only start charging when eAVs are near them.

EXPERIMENT C- Impact of eAV battery capacities

Based on the maximum number of EAVs determined from previous experiments, we check how much battery capacities we can reduce

EXPERIMENT D- Comparison with static charging

Compares the charging technology with static charging stations.

